"""The cursor rehearsal's portable part runs on SQLite here; the PostgreSQL role/RLS part runs only
in infra/hetzner/rehearse-migration.sh against the disposable restored database."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.session import Database
from scripts import rehearse_tarot_cursor


async def test_cursor_rehearsal_passes_and_leaves_nothing_behind(tmp_path: Path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'rehearsal.db'}"
    db = Database(url)
    await db.initialize()
    await db.dispose()
    await rehearse_tarot_cursor.rehearse(url)
    db = Database(url)
    try:
        from sqlalchemy import func, select

        from app.domains.guest.tables import GuestSessionRow
        from app.domains.tarot.tables import TarotSessionRow, TarotVariantCursorRow

        async with db.sessions() as session:
            for table in (GuestSessionRow, TarotSessionRow, TarotVariantCursorRow):
                assert await session.scalar(select(func.count()).select_from(table)) == 0
    finally:
        await db.dispose()


async def test_cursor_rehearsal_fails_when_a_deletion_rewinds_the_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: a service whose delete also drops the cursor must fail the rehearsal."""

    from sqlalchemy import delete

    from app.domains.tarot.service import TarotSessionService
    from app.domains.tarot.tables import TarotVariantCursorRow

    url = f"sqlite+aiosqlite:///{tmp_path / 'rehearsal.db'}"
    db = Database(url)
    await db.initialize()
    await db.dispose()
    original = TarotSessionService.delete

    async def rewinding_delete(self: TarotSessionService, guest_id, session_id) -> None:  # type: ignore[no-untyped-def]
        await original(self, guest_id, session_id)
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(TarotVariantCursorRow).where(TarotVariantCursorRow.guest_id == guest_id)
            )

    monkeypatch.setattr(TarotSessionService, "delete", rewinding_delete)
    with pytest.raises(rehearse_tarot_cursor.RehearsalFailed, match="deletion-rewound"):
        await rehearse_tarot_cursor.rehearse(url)


def test_main_reports_a_code_without_details(monkeypatch: pytest.MonkeyPatch, capsys) -> None:  # type: ignore[no-untyped-def]
    async def failing(_: str) -> None:
        raise rehearse_tarot_cursor.RehearsalFailed("connection-role-is-superuser")

    monkeypatch.setenv("LA_LANH_DATABASE_URL", "postgresql+asyncpg://secret@host/db")
    monkeypatch.setattr(rehearse_tarot_cursor, "rehearse", failing)
    assert rehearse_tarot_cursor.main() == 1
    out = capsys.readouterr().out
    assert out.strip() == "tarot-cursor-rehearsal-failed:connection-role-is-superuser"
    assert "secret" not in out


def test_rehearsal_script_runs_the_app_as_the_least_privileged_backend_role() -> None:
    """Static contract of infra/hetzner/rehearse-migration.sh (it needs Docker and a backup, so it
    runs on the server): the app never connects as the container superuser."""

    script = (
        Path(__file__).resolve().parents[4] / "infra/hetzner/rehearse-migration.sh"
    ).read_text()
    assert 'BACKEND_ROLE="la_lanh_rehearsal_backend"' in script
    lib = (Path(__file__).resolve().parents[4] / "infra/hetzner/rehearsal-lib.sh").read_text()
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS" in lib
    assert '--role="$BACKEND_ROLE"' in script  # restored objects owned by the backend role
    assert "tableowner <> '${BACKEND_ROLE}'" in script
    url_line = next(line for line in script.splitlines() if "postgresql+asyncpg://" in line)
    assert "postgres:" not in url_line and "%s:%s@" in url_line
    assert '"$BACKEND_ROLE" "$backend_password"' in script
    order = [
        script.index("run_app alembic upgrade head"),
        script.index("run_app python -m scripts.check_database_privacy"),
        script.index("run_app python -m scripts.rehearse_tarot_cursor"),
        script.index("Rehearsal readiness OK"),
    ]
    assert order == sorted(order)
    assert 'source "$(dirname "$0")/rehearsal-lib.sh"' in script
    assert 'create_backend_role "$NAME" "$BACKEND_ROLE" "$backend_password"' in script
    assert "-v pw" not in script and "pw=" not in script  # no password on a command line


# ---------------------------------------------------------------- Codex P2 regressions (#31)


async def _empty_database(tmp_path: Path) -> str:
    url = f"sqlite+aiosqlite:///{tmp_path / 'rehearsal.db'}"
    db = Database(url)
    await db.initialize()
    await db.dispose()
    return url


async def test_rehearsal_rejects_sessions_that_store_the_same_position(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real upsert runs twice (counter = 2) but both sessions store position 0."""

    from app.domains.tarot import service as tarot_service

    original = tarot_service._allocate_position

    async def duplicate(database, guest):  # type: ignore[no-untyped-def]
        await original(database, guest)
        return 0

    monkeypatch.setattr(tarot_service, "_allocate_position", duplicate)
    with pytest.raises(rehearse_tarot_cursor.RehearsalFailed, match="positions-0-and-1"):
        await rehearse_tarot_cursor.rehearse(await _empty_database(tmp_path))


async def test_rehearsal_rejects_a_cleanup_that_never_reaches_the_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.domains.tarot.service import TarotSessionService

    async def no_cleanup(self, **kwargs):  # type: ignore[no-untyped-def]
        return 0

    monkeypatch.setattr(TarotSessionService, "cleanup", no_cleanup)
    with pytest.raises(rehearse_tarot_cursor.RehearsalFailed, match="did-not-reach"):
        await rehearse_tarot_cursor.rehearse(await _empty_database(tmp_path))


async def test_rehearsal_drains_cleanup_past_many_older_expired_sessions(tmp_path: Path) -> None:
    """A restored copy may hold >= 500 older expired sessions ahead of the synthetic ones; the
    rehearsal drains bounded batches until its own sessions are gone."""

    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    from sqlalchemy import func, select

    from app.domains.guest.tables import GuestSessionRow
    from app.domains.tarot.tables import TarotSessionRow

    url = await _empty_database(tmp_path)
    db = Database(url)
    now = datetime.now(UTC)
    old_guest = uuid4()
    try:
        async with db.sessions() as session, session.begin():
            session.add(
                GuestSessionRow(
                    id=old_guest,
                    token_hash=old_guest.bytes * 2,
                    csrf_hash=b"c" * 32,
                    state="active",
                    onboarding_status="birth_pending",
                    created_at=now - timedelta(days=60),
                    last_active_at=now,
                    expires_at=now + timedelta(days=1),
                )
            )
            for index in range(1_250):
                created = now - timedelta(days=40, minutes=index)
                session.add(
                    TarotSessionRow(
                        id=uuid4(),
                        guest_id=old_guest,
                        version=1,
                        state="choosing",
                        context="work",
                        spread="three_card",
                        voice="playful_grounded",
                        origin="direct",
                        idempotency_hash=index.to_bytes(32, "big"),
                        payload_ciphertext="synthetic",
                        created_at=created,
                        updated_at=created,
                        expires_at=created + timedelta(days=29, hours=18),
                    )
                )
    finally:
        await db.dispose()
    await rehearse_tarot_cursor.rehearse(url)
    db = Database(url)
    try:
        async with db.sessions() as session:
            assert await session.scalar(select(func.count()).select_from(TarotSessionRow)) == 0
    finally:
        await db.dispose()


def _stub_docker(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "docker"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$*" >> "{tmp_path}/argv.log"\n'
        f'cat > "{tmp_path}/stdin.log"\n'
    )
    stub.chmod(0o755)
    return bin_dir


def test_backend_password_reaches_psql_on_stdin_only(tmp_path: Path) -> None:
    import os
    import subprocess

    canary = "SYNTHETICcanary4rehearsal7xq"
    lib = Path(__file__).resolve().parents[4] / "infra/hetzner/rehearsal-lib.sh"
    env = {**os.environ, "PATH": f"{_stub_docker(tmp_path)}:{os.environ['PATH']}"}
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "bash",
            "-c",
            f'source "{lib}"; create_backend_role rehearsal-db la_lanh_rehearsal_backend "$1"',
            "bash",
            canary,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    argv = (tmp_path / "argv.log").read_text()
    stdin = (tmp_path / "stdin.log").read_text()
    assert "exec -i rehearsal-db psql" in argv
    assert canary not in argv  # not on the docker/psql command line
    assert canary not in result.stdout and canary not in result.stderr
    assert f"\\set pw '{canary}'" in stdin and "PASSWORD :'pw'" in stdin
    assert "NOSUPERUSER" in stdin and "NOBYPASSRLS" in stdin


@pytest.mark.parametrize("password", ["short", "has space and long enough", "quote'injection12345"])
def test_backend_role_helper_refuses_unsafe_passwords(tmp_path: Path, password: str) -> None:
    import os
    import subprocess

    lib = Path(__file__).resolve().parents[4] / "infra/hetzner/rehearsal-lib.sh"
    env = {**os.environ, "PATH": f"{_stub_docker(tmp_path)}:{os.environ['PATH']}"}
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "bash",
            "-c",
            f'source "{lib}"; create_backend_role rehearsal-db la_lanh_rehearsal_backend "$1"',
            "bash",
            password,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not (tmp_path / "argv.log").exists()  # docker never ran
    assert password not in result.stderr
