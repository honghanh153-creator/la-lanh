"""Opt-in synthetic PostgreSQL proof, never a live Supabase connection."""

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Database
from app.domains.accounts import postgres as account_postgres
from app.domains.accounts.erasure import SupabaseIdentityEraser
from app.domains.accounts.provider import SupabaseOtpProvider
from app.domains.accounts.service import AccountService
from app.domains.accounts.tables import AccountDeviceRow
from app.domains.guest.errors import GuestExpired
from app.domains.guest.models import GuestSessionRecord
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.service import GuestSessionService
from app.domains.guest.tables import GuestSessionRow
from app.domains.mood.tables import MoodCheckInRow
from app.domains.readings.postgres import PostgresReadingRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider
from tests.accounts import test_service as checks
from tests.accounts.support import FakeTransport, settings
from tests.guest import test_guest_cleanup as cleanup_checks
from tests.history import test_retention as history_checks


@pytest.fixture
async def pg_runtime(tmp_path: Path) -> AsyncIterator[checks.Runtime]:
    raw = os.environ.get("LA_LANH_ACCOUNT_TEST_POSTGRES_URL")
    if not raw:
        pytest.skip("requires the separately created disposable PostgreSQL cluster")
    url = make_url(raw)
    if (url.drivername, url.host, url.port, url.database) != (
        "postgresql+asyncpg",
        "127.0.0.1",
        55434,
        "la_lanh_security_test",
    ):
        pytest.fail("refusing any database except isolated loopback test cluster 55434")
    config = settings(tmp_path / "unused.db").model_copy(update={"database_url": raw})
    db = Database(raw)
    async with db.engine.begin() as connection:
        assert (
            await connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "20261011_0036"
        )
        await connection.execute(
            text("TRUNCATE guest_sessions, account_login_quotas, rewrite_send_fences CASCADE")
        )
    fake = FakeTransport()
    hasher = SecretHasher(b"h" * 32)
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))
    try:
        yield checks.Runtime(
            db,
            config,
            fake,
            AccountService(
                db.sessions,
                hasher,
                envelope,
                SupabaseOtpProvider(config, transport=httpx.MockTransport(fake.handle)),
                config,
            ),
            GuestSessionService(
                PostgresGuestRepository(
                    db.sessions,
                    identity_eraser=SupabaseIdentityEraser(
                        config, transport=httpx.MockTransport(fake.handle)
                    ),
                ),
                hasher,
                envelope,
                consent_version="birth-profile-v1",
                consent_purpose="birth_profile_basic",
            ),
            hasher,
            envelope,
        )
    finally:
        await db.dispose()


@pytest.mark.parametrize(
    "scenario",
    [
        checks.test_device_credential_clock_does_not_shorten_account_clock_and_cleanup_survives,
        checks.test_two_devices_logout_is_independent_and_expired_credentials_cannot_erase,
        checks.test_delete_fences_pending_restore_and_never_resurrects_local_data,
        checks.test_duplicate_verify_uses_database_claim_not_inprocess_lock,
        checks.test_concurrent_subject_link_preserves_unselected_guest_and_one_owner,
        checks.test_distinct_subjects_racing_one_guest_cannot_relink_it,
        checks.test_cancel_during_provider_verification_fences_attachment,
        checks.test_account_erasure_racing_restore_cannot_leave_usable_device,
        checks.test_first_link_transaction_rolls_back_guest_consent_and_replay_envelope,
        checks.test_durable_send_quotas_cover_email_peer_global_and_hash_only_storage,
        checks.test_device_iam_denies_cross_account_and_wrong_csrf,
        checks.test_revoke_other_devices_preserves_profile_and_current_device,
        checks.test_consent_write_rechecks_owner_lifetime_after_preflight,
    ],
)
async def test_real_postgres_account_lifecycle(pg_runtime: checks.Runtime, scenario):  # type: ignore[no-untyped-def]
    await scenario(pg_runtime)


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("status", ["pending", "retry_wait", "leased"])
async def test_real_postgres_unsent_history_erasure(
    pg_runtime: checks.Runtime, manual: bool, status: str
) -> None:
    await history_checks.test_unsent_attempt_does_not_hide_or_prevent_history_erasure(
        pg_runtime.database, manual, status
    )


async def test_real_postgres_busy_history_backlog_remains_visible(
    pg_runtime: checks.Runtime,
) -> None:
    await history_checks.test_provider_started_history_remains_counted_until_its_fence_finishes(
        pg_runtime.database
    )


@pytest.mark.parametrize("started", [False, True])
@pytest.mark.parametrize("days_later", [0, 31])
async def test_real_postgres_interrupted_deletion_recovers_without_crossing_send_fence(
    pg_runtime: checks.Runtime,
    monkeypatch: pytest.MonkeyPatch,
    started: bool,
    days_later: int,
) -> None:
    await cleanup_checks.test_cleanup_recovers_interrupted_committed_deletion(
        (
            pg_runtime.database,
            PostgresGuestRepository(pg_runtime.database.sessions),
            PostgresReadingRepository(pg_runtime.database.sessions, pg_runtime.envelope),
        ),
        monkeypatch,
        started,
        days_later,
    )


async def test_previous_image_mood_insert_and_update_preserve_creation_clock(
    pg_runtime: checks.Runtime,
) -> None:
    owner_id = await history_checks.owner(pg_runtime.database)
    daily = await history_checks.note(pg_runtime.database, owner_id, history_checks.NOW)
    mood_id = uuid4()
    async with pg_runtime.database.sessions() as session, session.begin():
        # The previous image deliberately omits created_at; execute its SQL shape,
        # not a current ORM insert which might mask a missing migration default.
        await session.execute(
            text("""INSERT INTO mood_check_ins
                (id, guest_id, daily_note_id, mood, checked_in_at)
                VALUES (:id, :owner, :note, 'chill', :now)"""),
            {"id": mood_id, "owner": owner_id, "note": daily.id, "now": history_checks.NOW},
        )
        row = await session.get(MoodCheckInRow, mood_id)
        assert row is not None and row.created_at is not None
        original = row.created_at
        await session.execute(
            text("UPDATE mood_check_ins SET mood = 'ruc', checked_in_at = :now WHERE id = :id"),
            {"now": history_checks.NOW + timedelta(days=1), "id": mood_id},
        )
    async with pg_runtime.database.sessions() as session:
        row = await session.get(MoodCheckInRow, mood_id)
        assert row is not None and row.created_at == original


async def test_populated_history_upgrade_backfills_mood_without_legacy_opt_in(
    pg_runtime: checks.Runtime,
) -> None:
    db = pg_runtime.database
    owner_id = await history_checks.owner(db)
    daily = await history_checks.note(db, owner_id, history_checks.OLD)
    mood_id = uuid4()
    async with db.engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("DROP TABLE history_retention_policies"))
            await connection.execute(text("ALTER TABLE mood_check_ins DROP COLUMN created_at"))
            await connection.execute(
                text(
                    "INSERT INTO mood_check_ins "
                    "(id, guest_id, daily_note_id, mood, checked_in_at) "
                    "VALUES (:id, :owner, :note, 'chill', :checked)"
                ),
                {"id": mood_id, "owner": owner_id, "note": daily.id, "checked": history_checks.OLD},
            )

            def upgrade(sync_connection):  # type: ignore[no-untyped-def]
                with Operations.context(MigrationContext.configure(sync_connection)):
                    import_module("migrations.versions.20261010_0032_history_retention").upgrade()

            await connection.run_sync(upgrade)
            assert (
                await connection.scalar(
                    text("SELECT created_at FROM mood_check_ins WHERE id=:id"), {"id": mood_id}
                )
                == history_checks.OLD
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM history_retention_policies"))
                == 0
            )
        finally:
            await transaction.rollback()


async def test_real_postgres_waiting_private_reader_rejects_committed_revocation(
    pg_runtime: checks.Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, linked = await pg_runtime.link("revocation-barrier")
    assert linked.token is not None and linked.guest is not None
    owner_id = linked.guest.id
    digest = pg_runtime.hasher.digest("guest-credential", linked.token)
    reached = asyncio.Event()
    reader_pid: int | None = None
    original_lock = account_postgres.lock_owner

    async def observe_wait(session: AsyncSession, guest_id: UUID) -> GuestSessionRow | None:
        nonlocal reader_pid
        reader_pid = await session.scalar(text("SELECT pg_backend_pid()"))
        reached.set()
        return await original_lock(session, guest_id)

    reader: asyncio.Task[GuestSessionRecord] | None = None
    try:
        async with account_postgres.account_transaction(pg_runtime.database.sessions) as revoker:
            assert await original_lock(revoker, owner_id) is not None
            monkeypatch.setattr(account_postgres, "lock_owner", observe_wait)
            reader = asyncio.create_task(
                pg_runtime.guests.resume(linked.token, now=checks.NOW, touch=False)
            )
            await asyncio.wait_for(reached.wait(), timeout=5)
            # Verify actual PostgreSQL waiting, not just a simulated application seam.
            async with pg_runtime.database.engine.connect() as monitor:
                deadline = datetime.now(UTC) + timedelta(seconds=5)
                while True:
                    waiting = await monitor.scalar(
                        text("SELECT wait_event_type FROM pg_stat_activity WHERE pid=:pid"),
                        {"pid": reader_pid},
                    )
                    if waiting == "Lock":
                        break
                    if datetime.now(UTC) >= deadline:
                        pytest.fail("private reader did not wait on the held owner lock")
                    await asyncio.sleep(0.01)
            assert not reader.done()
            await revoker.execute(
                update(AccountDeviceRow)
                .where(AccountDeviceRow.credential_digest == digest)
                .values(revoked_at=checks.NOW)
            )
        # Revocation commits before the waiting private request can authorize.
        with pytest.raises(GuestExpired):
            await asyncio.wait_for(reader, timeout=5)
        async with pg_runtime.database.sessions() as session:
            assert (
                await session.scalar(
                    select(AccountDeviceRow.revoked_at).where(
                        AccountDeviceRow.credential_digest == digest
                    )
                )
                == checks.NOW
            )
    finally:
        if reader is not None and not reader.done():
            reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)


async def test_real_postgres_new_tables_not_exposed_to_browser_roles(
    pg_runtime: checks.Runtime,
) -> None:
    async with pg_runtime.database.engine.connect() as connection:
        for table in (
            "accounts",
            "account_devices",
            "account_login_challenges",
            "account_login_quotas",
            "history_retention_policies",
        ):
            assert await connection.scalar(
                text("SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:table)"),
                {"table": table},
            )
            for role in ("anon", "authenticated"):
                assert not await connection.scalar(
                    text("SELECT has_table_privilege(:role, :table, 'SELECT')"),
                    {"role": role, "table": table},
                )
