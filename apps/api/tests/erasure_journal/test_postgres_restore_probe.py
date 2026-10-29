"""Disposable PostgreSQL probe for the deletion journal (audit P07; operator evidence, not CI).

Skipped unless ``LA_LANH_JOURNAL_PROBE_POSTGRES_URL`` names a migrated, disposable database on
localhost whose name starts with ``lalanh_probe_``. Synthetic rows only. Procedure, guards and the
evidence to record: docs/operations/disposable-postgres-journal-probe.md. Never point it at
staging, production or a copy of real data.

It checks what SQLite cannot: ``DELETE … RETURNING`` and ``rowcount`` under two PostgreSQL
connections, and an erasure that is still in flight while ``pg_dump`` takes its snapshot, followed
by restore into a fresh database and replay.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql.asyncpg import dialect as asyncpg_dialect
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import Database, verified_engine_options
from app.domains.daily.models import DailyNoteRecord
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.erasure_journal.replay import export_entries, purge_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalHorizonRow, ErasureJournalRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.la_chung.models import RequestStatus
from app.domains.la_chung.service import LaChungService
from app.domains.la_chung.tables import LaChungRequestRow
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

PROBE_ENV = "LA_LANH_JOURNAL_PROBE_POSTGRES_URL"
PREFIX = "lalanh_probe_"
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
TOOLS = ("pg_dump", "pg_restore", "createdb", "dropdb")
MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
# Synthetic keys: the probe never sees the server hash key or the data key.
HASHER = SecretHasher(b"p" * 32)
JOURNAL = ErasureJournal(HASHER)
ENVELOPE = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"q" * 32))
NOW = datetime.now(UTC)
BOUND_SECONDS = 10  # only so a missing observation fails instead of hanging


def disposable_target(raw: str) -> URL:
    """The probe URL, or ValueError unless it is a disposable localhost database over verified TLS.

    The query may carry only ``sslrootcert``: one absolute path to the disposable CA. asyncpg lets
    any other query key (``host``, ``database``, ``port``, ``user``, …) override the URL's own
    target, so the engine could reach a database these checks never saw (Codex r44 P1). The target
    the application's own engine options would connect to must equal the checked one.
    """

    url = make_url(raw)
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("the probe needs the postgresql+asyncpg driver")
    if url.host not in LOCAL_HOSTS:
        raise ValueError("the probe runs only against a database on localhost")
    name = url.database or ""
    if not name.startswith(PREFIX) or re.fullmatch(r"[a-z0-9_]{1,50}", name) is None:
        raise ValueError(f"the probe database name must start with {PREFIX} (a-z, 0-9, _)")
    extra = sorted(set(url.query) - {"sslrootcert"})
    if extra:
        raise ValueError(f"the probe URL may not carry query keys {extra}")
    cafile = url.query.get("sslrootcert")
    if not isinstance(cafile, str) or not Path(cafile).is_absolute() or not Path(cafile).is_file():
        raise ValueError("the probe needs one absolute sslrootcert: the disposable cluster's CA")
    effective = _effective_target(raw)
    expected = {"host": url.host, "port": url.port, "database": name, "user": url.username}
    if {key: effective.get(key) for key in expected} != expected:
        raise ValueError("the engine would connect to a different target than the one checked")
    return url


def _effective_target(raw: str) -> dict[str, Any]:
    """Where the application's engine options would connect: asyncpg merges ``url.query`` in."""

    dialect = cast(Any, asyncpg_dialect)()
    _, arguments = dialect.create_connect_args(verified_engine_options(raw)["url"])
    return cast(dict[str, Any], arguments)


def libpq_env(url: URL) -> dict[str, str]:
    """Connection settings for the PostgreSQL tools.

    The password goes only in PGPASSWORD, and the tools verify the server against the same CA
    as the application (``verify-full``). No inherited PG* variable can redirect them.
    """

    env = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
    env |= {
        "PGHOST": str(url.host),
        "PGPORT": str(url.port or 5432),
        "PGSSLMODE": "verify-full",
        "PGSSLROOTCERT": str(url.query["sslrootcert"]),
    }
    if url.username:
        env["PGUSER"] = url.username
    if url.password:
        env["PGPASSWORD"] = str(url.password)
    return env


async def _tool(env: dict[str, str], *args: str) -> None:
    process = await asyncio.create_subprocess_exec(
        *args, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        _, stderr = await asyncio.wait_for(process.communicate(), 300)
    except TimeoutError:
        # Reap the child so it releases its connection before teardown drops the database.
        process.kill()
        await process.wait()
        raise AssertionError(f"{args[0]} did not finish within 300 s") from None
    first = stderr.decode(errors="replace").splitlines()[:1]
    assert process.returncode == 0, f"{args[0]} exited {process.returncode}: {first}"


async def _bounded(awaitable: Awaitable[Any]) -> Any:
    return await asyncio.wait_for(awaitable, BOUND_SECONDS)


class _HeldCommit:
    """Sessions whose transaction flushes, then awaits ``hold`` before it commits.

    The erasure's statements and its journal row are written but not committed while ``hold``
    runs, which is how a second connection or ``pg_dump`` meets an erasure in flight.
    """

    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], hold: Callable[[], Awaitable[None]]
    ) -> None:
        self._sessions = sessions
        self._hold = hold

    def __call__(self) -> _HeldSession:
        return _HeldSession(self._sessions(), self._hold)


class _HeldSession:
    def __init__(self, session: AsyncSession, hold: Callable[[], Awaitable[None]]) -> None:
        self._session = session
        self._hold = hold

    async def __aenter__(self) -> _HeldSession:
        await self._session.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self._session.__aexit__(*exc)

    def begin(self) -> _HeldTransaction:
        return _HeldTransaction(self._session, self._hold)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


class _HeldTransaction:
    def __init__(self, session: AsyncSession, hold: Callable[[], Awaitable[None]]) -> None:
        self._session = session
        self._hold = hold
        self._transaction = session.begin()

    async def __aenter__(self) -> _HeldTransaction:
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            await self._session.flush()
            await self._hold()
        await self._transaction.__aexit__(exc_type, exc, tb)


def _held(sessions: async_sessionmaker[AsyncSession], hold: Callable[[], Awaitable[None]]) -> Any:
    return cast(Any, _HeldCommit(sessions, hold))


async def _lock_waiters(database: Database, expected: int) -> None:
    """Until ``expected`` backends of this database wait on a lock (PostgreSQL decides)."""

    while True:
        async with database.engine.connect() as connection:
            waiting = await connection.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
        if int(waiting or 0) >= expected:
            return
        await asyncio.sleep(0.05)


@pytest.fixture
async def probe(tmp_path: Path) -> AsyncIterator[tuple[Database, URL, dict[str, str]]]:
    raw = os.environ.get(PROBE_ENV)
    if not raw:
        pytest.skip(f"set {PROBE_ENV} to run the disposable PostgreSQL journal probe")
    try:
        url = disposable_target(raw)
    except ValueError as error:
        pytest.fail(f"refusing to run the probe: {error}")
    missing = [tool for tool in TOOLS if shutil.which(tool) is None]
    if missing:
        pytest.fail(f"the probe needs PostgreSQL client tools on PATH: {missing}")
    env = libpq_env(url)
    database = Database(url.render_as_string(hide_password=False))
    restore = f"{url.database}_restore"
    try:
        async with database.engine.begin() as connection:
            head = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert head == ScriptDirectory(str(MIGRATIONS)).get_current_head(), (
                "run `alembic upgrade head` on the probe database first"
            )
            await connection.execute(
                text("TRUNCATE guest_sessions, erasure_journal, erasure_journal_horizon CASCADE")
            )
        await _tool(env, "dropdb", "--if-exists", restore)
        yield database, url, env
    finally:
        await database.dispose()
        await _tool(env, "dropdb", "--if-exists", restore)


async def _guest(database: Database) -> UUID:
    guest_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id, token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes, state="claimed",
                onboarding_status="birth_ready", created_at=NOW, last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )  # fmt: skip
    return guest_id


async def _saved_note(database: Database, guest_id: UUID, day: int) -> tuple[UUID, UUID]:
    note = await PostgresDailyNoteRepository(database.sessions, ENVELOPE).get_or_create(
        DailyNoteRecord(
            id=uuid4(), guest_id=guest_id, note_date=(NOW - timedelta(days=day)).date(),
            title="synthetic", body="synthetic", context_label="probe", content_version="probe",
            chart_snapshot_id=None, created_at=NOW,
        )
    )  # fmt: skip
    saved_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            SavedNoteRow(
                id=saved_id, guest_id=guest_id, daily_note_id=note.id, note_snapshot={},
                saved_at=NOW,
            )
        )  # fmt: skip
    return note.id, saved_id


async def _principal(database: Database, guest_id: UUID) -> UUID:
    # One principal per guest: ``principals.source_guest_id`` is unique (Codex r44 P2).
    principal_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(PrincipalRow(id=principal_id, source_guest_id=guest_id, created_at=NOW))
    return principal_id


async def _invite(database: Database, principal_id: UUID) -> UUID:
    view, _ = await LaChungService(database.sessions, HASHER, ENVELOPE).create(
        principal_id=principal_id, recipient_label="Bạn tổng hợp", context="friend",
        idempotency_key=uuid4().hex,
    )  # fmt: skip
    return view.id


async def _seed_interleaved(database: Database) -> dict[str, Any]:
    guest_id = await _guest(database)
    principal_id = await _principal(database, guest_id)
    return {
        "guest": guest_id,
        "principal": principal_id,
        "notes": {
            name: await _saved_note(database, guest_id, day)
            for day, name in enumerate(("before", "in_flight", "after", "kept"))
        },
        "invite": await _invite(database, principal_id),
        "invite_kept": await _invite(database, principal_id),
    }


async def _seed_horizon(database: Database) -> tuple[UUID, UUID]:
    guest_id = await _guest(database)
    note_id, _ = await _saved_note(database, guest_id, 0)
    share_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            ShareArtifactRow(
                id=share_id, guest_id=guest_id, daily_note_id=note_id,
                token_hash=uuid4().bytes + uuid4().bytes, safe_snapshot={},
                format="story_9_16", created_at=NOW - timedelta(days=21),
                expires_at=NOW + timedelta(days=7),
            )
        )  # fmt: skip
    return guest_id, share_id


def _saved(sessions: Any) -> PostgresSavedNoteRepository:
    return PostgresSavedNoteRepository(sessions, ENVELOPE, JOURNAL)


async def _journal(database: Database) -> list[tuple[str, bytes]]:
    async with database.sessions() as session:
        rows = await session.scalars(select(ErasureJournalRow))
        return sorted((row.kind, row.subject_digest) for row in rows)


async def test_concurrent_unsave_returns_and_journals_the_row_once(probe: Any) -> None:
    """``DELETE … RETURNING`` on two connections: one gets the row and the one journal entry."""

    database, _, _ = probe
    guest_id = await _guest(database)
    note_id, saved_id = await _saved_note(database, guest_id, 0)
    deleted, release = asyncio.Event(), asyncio.Event()

    async def hold() -> None:
        deleted.set()
        await _bounded(release.wait())

    first = asyncio.create_task(_saved(_held(database.sessions, hold)).delete(guest_id, note_id))
    await _bounded(deleted.wait())
    second = asyncio.create_task(_saved(database.sessions).delete(guest_id, note_id))
    await _bounded(_lock_waiters(database, 1))  # the second DELETE waits on the row lock
    release.set()
    assert await _bounded(first) is True
    assert await _bounded(second) is False
    digest = JOURNAL.digest(ErasureKind.SAVED_NOTE_REMOVED, saved_id)
    assert await _journal(database) == [(ErasureKind.SAVED_NOTE_REMOVED.value, digest)]


async def test_a_dump_taken_mid_erasure_restores_and_replays(probe: Any, tmp_path: Path) -> None:
    """Interleaving: before the dump → reflected; in flight and after the dump → applied."""

    database, url, env = probe
    seed = await _seed_interleaved(database)
    guest_id, principal_id, notes = seed["guest"], seed["principal"], seed["notes"]
    invite_id, invite_kept = seed["invite"], seed["invite_kept"]
    dump = tmp_path / "probe.dump"

    assert await _saved(database.sessions).delete(guest_id, notes["before"][0])

    async def dump_while_open() -> None:
        await _tool(
            env, "pg_dump", "--format=custom", "--schema=public", f"--file={dump}",
            f"--dbname={url.database}",
        )  # fmt: skip

    held = _held(database.sessions, dump_while_open)
    assert await _saved(held).delete(guest_id, notes["in_flight"][0])
    assert await _saved(database.sessions).delete(guest_id, notes["after"][0])
    await LaChungService(database.sessions, HASHER, ENVELOPE, JOURNAL).revoke(
        principal_id, invite_id
    )
    exported = await export_entries(database.sessions)

    restore = f"{url.database}_restore"
    await _tool(env, "createdb", restore)
    await _tool(env, "pg_restore", "--no-owner", f"--dbname={restore}", str(dump))
    restored = Database(url.set(database=restore).render_as_string(hide_password=False))
    try:
        async with restored.sessions() as session:
            present = {
                name: await session.get(SavedNoteRow, saved_id) is not None
                for name, (_, saved_id) in notes.items()
            }
            invite = await session.get(LaChungRequestRow, invite_id)
            held_entries = len(tuple(await session.scalars(select(ErasureJournalRow))))
        # The snapshot holds only the erasure committed before it, with its journal row.
        assert present == {"before": False, "in_flight": True, "after": True, "kept": True}
        assert invite is not None and invite.status == RequestStatus.PENDING.value
        assert held_entries == 1

        report = await replay(restored.sessions, JOURNAL, ENVELOPE, exported)
        saved = ErasureKind.SAVED_NOTE_REMOVED.value
        revoked = ErasureKind.LA_CHUNG_INVITE_REVOKED.value
        assert report.reflected[saved] == 1 and report.applied[saved] == 2
        assert report.applied[revoked] == 1 and not report.unmatched

        async with restored.sessions() as session:
            for name, (_, saved_id) in notes.items():
                assert (await session.get(SavedNoteRow, saved_id) is not None) == (name == "kept")
            invite = await session.get(LaChungRequestRow, invite_id)
            assert invite is not None and invite.status == RequestStatus.REVOKED.value
            assert invite.token_ciphertext is None
            kept = await session.get(LaChungRequestRow, invite_kept)
            assert kept is not None and kept.status == RequestStatus.PENDING.value

        again = await replay(restored.sessions, JOURNAL, ENVELOPE, exported)
        assert sum(again.reflected.values()) == 4 and not again.applied
    finally:
        await restored.dispose()


async def test_the_purge_horizon_travels_with_the_dump(probe: Any, tmp_path: Path) -> None:
    """An export taken before a purge replays as reflected on a snapshot taken after it."""

    database, url, env = probe
    guest_id, share_id = await _seed_horizon(database)
    old = NOW - timedelta(days=20)
    shares = PostgresShareArtifactRepository(database.sessions, ENVELOPE, JOURNAL)
    assert await shares.revoke_owned(guest_id, share_id, old)
    exported = await export_entries(database.sessions)
    assert await purge_entries(database.sessions, before=NOW - timedelta(days=15)) == 1
    dump = tmp_path / "horizon.dump"
    await _tool(
        env, "pg_dump", "--format=custom", "--schema=public", f"--file={dump}",
        f"--dbname={url.database}",
    )  # fmt: skip

    restore = f"{url.database}_restore"
    await _tool(env, "createdb", restore)
    await _tool(env, "pg_restore", "--no-owner", f"--dbname={restore}", str(dump))
    restored = Database(url.set(database=restore).render_as_string(hide_password=False))
    try:
        async with restored.sessions() as session:
            assert await session.get(ErasureJournalHorizonRow, 1) is not None
        report = await replay(restored.sessions, JOURNAL, ENVELOPE, exported)
        revoked = ErasureKind.SHARE_REVOKED.value
        assert report.reflected[revoked] == 1 and not report.applied and not report.unmatched
    finally:
        await restored.dispose()


@pytest.fixture
def ca_file(tmp_path: Path) -> Path:
    """A throwaway self-signed CA certificate, so the guard can build the real TLS context."""

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "lalanh probe test CA")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(NOW - timedelta(days=1))
        .not_valid_after(NOW + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    path = tmp_path / "probe-ca.crt"
    path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return path


def _probe_url(ca: Path, query: str = "", *, database: str = "lalanh_probe_a") -> str:
    return (
        f"postgresql+asyncpg://probe:synthetic-pw@127.0.0.1:55440/{database}"
        f"?sslrootcert={ca}{query}"
    )


_DRIVER = "postgresql\\+asyncpg driver"
_LOCAL = "only against a database on localhost"
_NAME = "must start with lalanh_probe_"


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("postgresql+asyncpg://probe:synthetic@db.example.com:5432/lalanh_probe_a", _LOCAL),
        ("postgresql+asyncpg://probe:synthetic@10.0.0.5:5432/lalanh_probe_a", _LOCAL),
        ("postgresql+psycopg://probe:synthetic@127.0.0.1:5432/lalanh_probe_a", _DRIVER),
        ("postgresql+asyncpg://probe:synthetic@127.0.0.1:5432/la_lanh", _NAME),
        ("postgresql+asyncpg://probe:synthetic@127.0.0.1:5432/lalanh_probe_A;drop", _NAME),
        ("sqlite+aiosqlite:///lalanh_probe_a.db", _DRIVER),
    ],
)
def test_the_guard_refuses_anything_but_a_disposable_localhost_database(
    ca_file: Path, raw: str, reason: str
) -> None:
    """Each URL carries a valid CA, so only the named check can refuse it (Codex r46 P2)."""

    with pytest.raises(ValueError, match=reason):
        disposable_target(f"{raw}?sslrootcert={ca_file}")


_QUERY = "may not carry query keys"
_CA = "one absolute sslrootcert"


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("&database=la_lanh", _QUERY),
        ("&host=outside.example.invalid", _QUERY),
        ("&port=5432", _QUERY),
        ("&user=postgres", _QUERY),
        ("&password=other", _QUERY),
        ("&server_settings=search_path", _QUERY),
        ("&ssl=disable", _QUERY),
        ("&sslmode=disable", _QUERY),
        ("&database=la_lanh&database=lalanh_probe_a", _QUERY),
        ("&sslrootcert=/etc/ssl/cert.pem", _CA),
    ],
)
def test_the_guard_refuses_query_keys_that_could_move_the_target(
    ca_file: Path, query: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        disposable_target(_probe_url(ca_file, query))


def test_the_guard_requires_one_absolute_existing_ca(tmp_path: Path) -> None:
    base = "postgresql+asyncpg://probe:synthetic@127.0.0.1:55440/lalanh_probe_a"
    for raw in (base, f"{base}?sslrootcert=probe-ca.crt", f"{base}?sslrootcert={tmp_path}/no.crt"):
        with pytest.raises(ValueError, match=_CA):
            disposable_target(raw)


PROCEDURE = (
    Path(__file__).resolve().parents[4] / "docs/operations/disposable-postgres-journal-probe.md"
)


def test_the_procedure_orders_pg_hba_and_creates_the_role_stubs() -> None:
    """Static check of the operator procedure (Codex r46): PostgreSQL takes the first matching
    pg_hba line, so the TLS allowance comes before every reject and plaintext TCP still ends in
    a reject; the browser-role stubs exist before Alembic, whose migrations revoke from them."""

    text = PROCEDURE.read_text()
    block = re.search(r"```\n\s*(# TYPE.*?)```", text, re.DOTALL)
    assert block is not None, "the procedure must give the complete pg_hba.conf"
    lines = [line.split() for line in block.group(1).splitlines()[1:] if line.strip()]
    kinds = [(line[0], line[-1]) for line in lines]
    tls = kinds.index(("hostssl", "scram-sha-256"))
    rejects = [i for i, (_, method) in enumerate(kinds) if method == "reject"]
    assert rejects and all(tls < i for i in rejects)
    assert all(kind != "host" or method == "reject" for kind, method in kinds)
    assert {line[3] for line in lines if line[0] == "host"} == {"0.0.0.0/0", "::/0"}
    stubs = text.index("CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN;")
    assert stubs < text.index("CREATE ROLE lalanh_probe LOGIN") < text.index("alembic upgrade head")


def test_the_procedure_keeps_the_server_log_before_teardown() -> None:
    """Static check of the operator procedure (after the r50 attempt): the start-up controls run
    before the first start, and teardown copies a sanitized server log to the receipt directory
    outside $P before the cluster is stopped or $P is deleted, so a failed start keeps its cause."""

    text = PROCEDURE.read_text()
    receipt_dir = text.index("**Receipt directory** `$R`")
    assert receipt_dir < text.index("1. **Tools.**")
    assert "**outside** `$P`" in text[receipt_dir : text.index("1. **Tools.**")]
    start = text.index("pg_ctl -D $P/data -l $P/server.log -w -t 60 start")
    controls = ("postgres -D $P/data -C ssl", "$P/.s.PGSQL.55440", 's.bind(("127.0.0.1", 55440))')
    assert all(text.index(control) < start for control in controls)
    teardown = text.index("9. **Teardown**")
    keep = text.index("> $R/server-log.sanitized.txt", teardown)
    stop = text.index("pg_ctl -D $P/data -m fast stop", teardown)
    delete = text.index("Delete `$P` entirely", teardown)
    assert keep < stop < delete


def test_the_checked_target_is_the_one_the_engine_and_tools_use(ca_file: Path) -> None:
    url = disposable_target(_probe_url(ca_file))
    effective = _effective_target(url.render_as_string(hide_password=False))
    assert (effective["host"], effective["port"], effective["database"], effective["user"]) == (
        "127.0.0.1", 55440, "lalanh_probe_a", "probe",
    )  # fmt: skip
    env = libpq_env(url)
    assert env["PGPASSWORD"] == "synthetic-pw"
    assert (env["PGHOST"], env["PGPORT"], env["PGUSER"]) == ("127.0.0.1", "55440", "probe")
    assert (env["PGSSLMODE"], env["PGSSLROOTCERT"]) == ("verify-full", str(ca_file))
    assert "PGDATABASE" not in env  # every tool call names its database explicitly


async def test_every_probe_seed_runs_on_sqlite(tmp_path: Path) -> None:
    """The seeds respect the schema's constraints before any PostgreSQL run (Codex r44 P2)."""

    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}")
    await database.initialize()
    try:
        seed = await _seed_interleaved(database)
        assert seed["invite"] != seed["invite_kept"]
        async with database.sessions() as session:
            owners = set(
                await session.scalars(
                    select(LaChungRequestRow.principal_id).where(
                        LaChungRequestRow.id.in_((seed["invite"], seed["invite_kept"]))
                    )
                )
            )
        assert owners == {seed["principal"]}
        await _seed_horizon(database)
    finally:
        await database.dispose()


async def test_a_held_commit_writes_first_and_commits_only_after_the_hold(tmp_path: Path) -> None:
    """On SQLite: while held, another connection still sees the row and no journal entry."""

    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'held.db'}")
    await database.initialize()
    try:
        guest_id = await _guest(database)
        note_id, saved_id = await _saved_note(database, guest_id, 0)
        seen: list[bool] = []

        async def hold() -> None:
            async with database.sessions() as other:
                seen.append(await other.get(SavedNoteRow, saved_id) is not None)
                seen.append(bool(tuple(await other.scalars(select(ErasureJournalRow.id)))))

        assert await _saved(_held(database.sessions, hold)).delete(guest_id, note_id)
        assert seen == [True, False]  # flushed, not committed, while the hold ran
        async with database.sessions() as session:
            assert await session.get(SavedNoteRow, saved_id) is None
        digest = JOURNAL.digest(ErasureKind.SAVED_NOTE_REMOVED, saved_id)
        assert await _journal(database) == [(ErasureKind.SAVED_NOTE_REMOVED.value, digest)]
    finally:
        await database.dispose()
