from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, update

from app.db.session import Database
from app.domains.daily.models import DailyNoteRecord
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.tables import DailyNoteRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.errors import HistoryBusy, HistoryUnavailable
from app.domains.history.postgres import (
    DAILY_HISTORY_WINDOW,
    DAILY_PURGE_WINDOW,
    PRODUCT_TIMEZONE,
    PostgresHistoryRepository,
    activate_policy,
    unavailable_daily,
)
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.postgres import PostgresMoodRepository
from app.domains.mood.tables import MoodCheckInRow
from app.domains.saved.errors import SavedRevisionUnavailable
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime.now(UTC)
OLD = NOW - timedelta(days=40)


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'history.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


def cipher() -> AesGcmEnvelopeCipher:
    return AesGcmEnvelopeCipher(StaticDataKeyProvider(b"h" * 32))


async def owner(database: Database) -> UUID:
    identity = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=identity,
                token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes,
                state="active",
                onboarding_status="birth_ready",
                created_at=OLD,
                last_active_at=NOW,
                expires_at=NOW + timedelta(days=365),
            )
        )
    return identity


async def note(database: Database, guest_id: UUID, created: datetime) -> DailyNoteRecord:
    return await PostgresDailyNoteRepository(database.sessions, cipher()).get_or_create(
        DailyNoteRecord(
            id=uuid4(),
            guest_id=guest_id,
            note_date=created.date(),
            title="synthetic",
            body="private",
            context_label="test",
            content_version="test",
            chart_snapshot_id=None,
            created_at=created,
        )
    )


async def test_mood_edit_keeps_original_creation_clock(storage: Database) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions)
    first = await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.CHILL,
            checked_in_at=OLD,
        )
    )
    await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.CHILL,
            checked_in_at=NOW,
        )
    )
    async with storage.sessions() as session:
        row = await session.get(MoodCheckInRow, first.id)
        assert row is not None
        assert row.created_at == OLD


async def test_expired_unsaved_hidden_but_saved_and_current_sources_survive(
    storage: Database,
) -> None:
    guest_id, other = await owner(storage), await owner(storage)
    expired = await note(storage, guest_id, OLD)
    saved = await note(storage, guest_id, OLD + timedelta(days=1))
    current = await note(storage, guest_id, NOW)
    foreign = await note(storage, other, OLD)
    saves = PostgresSavedNoteRepository(storage.sessions, cipher())
    frozen = await saves.save(
        SavedNoteRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=saved.id,
            note_snapshot={"body": "saved"},
            saved_at=NOW,
        )
    )
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD)
    daily = PostgresDailyNoteRepository(storage.sessions, cipher())
    assert await daily.find(guest_id, expired.id) is None
    assert await daily.find(guest_id, saved.id) is not None
    assert await daily.find(guest_id, current.id) is not None
    await PostgresHistoryRepository(storage.sessions, cipher()).clear(guest_id, NOW)
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, expired.id) is None
        assert await session.get(DailyNoteRow, foreign.id) is not None
        assert await session.get(GuestSessionRow, guest_id) is not None
    assert await saves.list_for_guest(guest_id) == (frozen,)


@pytest.mark.parametrize("terminal", ["succeeded", "failed"])
async def test_terminal_rewrite_allows_clear_and_keeps_conservative_spend(
    storage: Database,
    terminal: str,
) -> None:
    from app.domains.content_rewrite.models import LeasedRewriteJob, RewriteJobResult
    from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
    from app.domains.content_rewrite.tables import (
        ContentRewriteJobRow,
        ContentRewriteSpendDayRow,
        ContentRewriteSpendMonthRow,
    )
    from tests.content_rewrite.test_repository import _record

    guest_id = await owner(storage)
    await note(storage, guest_id, OLD)
    record = _record()
    rewrites = PostgresContentRewriteRepository(storage.sessions, cipher())
    row = rewrites._row(record)
    row.owner_guest_id = guest_id
    row.status, row.lease_token = "leased", uuid4()
    row.lease_expires_at, row.request_started_at = NOW + timedelta(minutes=1), NOW
    row.budget_reserved_cost_nanos = 1234
    async with storage.sessions() as session, session.begin():
        session.add_all(
            [
                row,
                ContentRewriteSpendMonthRow(month="2026-10", reserved_cost_nanos=1234),
                ContentRewriteSpendDayRow(
                    day="2026-10-10", reserved_cost_nanos=1234, reserved_tokens=100
                ),
            ]
        )
    assert row.lease_token is not None
    if terminal == "succeeded":
        assert await rewrites.succeed(
            lease=LeasedRewriteJob(
                id=row.id,
                request=record.request,
                deletion_epoch=row.deletion_epoch,
                lease_token=row.lease_token,
                lease_expires_at=NOW + timedelta(minutes=1),
                attempt_count=1,
                max_attempts=3,
            ),
            gate_receipt_id="synthetic",
            output_fingerprint="f" * 64,
            completed_at=NOW,
            input_tokens=None,
            output_tokens=None,
            cost_nanos=None,
        )
    else:
        assert await rewrites.fail(
            job_id=row.id,
            lease_token=row.lease_token,
            deletion_epoch=row.deletion_epoch,
            result=RewriteJobResult.AMBIGUOUS,
            updated_at=NOW,
        )
    assert await PostgresHistoryRepository(storage.sessions, cipher()).clear(guest_id, NOW) == 1
    async with storage.sessions() as session:
        completed = await session.get(ContentRewriteJobRow, row.id)
        month = await session.get(ContentRewriteSpendMonthRow, "2026-10")
        day = await session.get(ContentRewriteSpendDayRow, "2026-10-10")
        assert completed is not None and completed.request_started_at is None
        assert completed.status == terminal
        assert month is not None and month.reserved_cost_nanos == 1234
        assert day is not None and day.reserved_cost_nanos == 1234


async def test_legacy_opt_in_has_full_grace_and_never_slides(storage: Database) -> None:
    guest_id = await owner(storage)
    old = await note(storage, guest_id, OLD)
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    assert await repository.status(guest_id) is None
    assert await repository.purge_expired(NOW) == 0
    assert await repository.activate(guest_id, NOW) == NOW
    assert await repository.activate(guest_id, NOW + timedelta(days=1)) == NOW
    async with storage.sessions() as session:
        assert (
            await session.scalar(
                select(DailyNoteRow.id).where(
                    DailyNoteRow.id == old.id,
                    unavailable_daily(NOW + timedelta(days=30) - timedelta(seconds=1)),
                )
            )
            is None
        )
        assert (
            await session.scalar(
                select(DailyNoteRow.id).where(
                    DailyNoteRow.id == old.id, unavailable_daily(NOW + timedelta(days=30))
                )
            )
            == old.id
        )
    assert await repository.purge_expired(NOW + timedelta(days=29, hours=23)) == 0
    assert await repository.purge_expired(NOW + timedelta(days=30)) == 1
    assert await repository.status(guest_id) == NOW


async def test_reopening_and_rewriting_do_not_extend_daily_clock(storage: Database) -> None:
    from dataclasses import replace

    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW - timedelta(days=10))
    repository = PostgresDailyNoteRepository(storage.sessions, cipher())
    rewritten = await repository.get_or_create(
        replace(daily, created_at=NOW, content_version="rewritten", body="new text")
    )
    assert rewritten.id == daily.id
    assert rewritten.created_at == daily.created_at
    assert (await repository.find(guest_id, daily.id)) == rewritten


async def test_expired_mood_hidden_and_cannot_be_extended_by_edit(storage: Database) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions)
    original = await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.CHILL,
            checked_in_at=OLD,
        )
    )
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD)
    assert await moods.find(guest_id, daily.id) is None
    with pytest.raises(HistoryUnavailable):
        await moods.upsert(
            MoodCheckInRecord(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily.id,
                mood=MoodValue.RUC,
                checked_in_at=NOW,
            )
        )
    async with storage.sessions() as session:
        row = await session.get(MoodCheckInRow, original.id)
        assert row is not None and row.created_at == OLD and row.mood == MoodValue.CHILL


async def test_save_rechecks_missing_expired_and_other_owner_sources(storage: Database) -> None:
    guest_id, other = await owner(storage), await owner(storage)
    missing = await note(storage, guest_id, NOW)
    expired = await note(storage, guest_id, OLD)
    foreign = await note(storage, other, NOW)
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD)
        await session.execute(delete(DailyNoteRow).where(DailyNoteRow.id == missing.id))
    saves = PostgresSavedNoteRepository(storage.sessions, cipher())
    for source in (missing, expired, foreign):
        with pytest.raises(SavedRevisionUnavailable):
            await saves.save(
                SavedNoteRecord(
                    id=uuid4(),
                    guest_id=guest_id,
                    daily_note_id=source.id,
                    note_snapshot={"body": "synthetic"},
                    saved_at=NOW,
                )
            )
    assert await saves.list_for_guest(guest_id) == ()


async def test_busy_marker_preserves_authority_and_drain_fails_observably(
    storage: Database,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
    from app.domains.content_rewrite.tables import ContentRewriteJobRow, RewriteSendFenceRow
    from scripts.cleanup_expired import _drain
    from tests.content_rewrite.test_repository import _record

    guest_id = await owner(storage)
    expired = await note(storage, guest_id, OLD)
    job = PostgresContentRewriteRepository(storage.sessions, cipher())._row(_record())
    job.owner_guest_id = guest_id
    job.status, job.lease_token = "leased", uuid4()
    job.lease_expires_at = NOW + timedelta(minutes=1)
    job.request_started_at = NOW
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD)
        session.add(job)
        session.add(
            RewriteSendFenceRow(
                job_id=job.id,
                lease_token=job.lease_token,
                subject_id=guest_id,
                expires_at=NOW + timedelta(minutes=2),
            )
        )
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    with pytest.raises(HistoryBusy):
        await repository.clear(guest_id, NOW)
    with pytest.raises(RuntimeError, match="remaining=1"):
        await _drain(repository, NOW, 2)
    assert "remaining=1" in capsys.readouterr().out
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, expired.id) is not None
        kept = await session.get(ContentRewriteJobRow, job.id)
        assert kept is not None and kept.request_started_at == NOW
        assert await session.get(HistoryRetentionPolicyRow, guest_id) is not None


@pytest.mark.parametrize("manual", [False, True])
async def test_crashed_rewrite_does_not_block_history_after_send_fence_expires(
    storage: Database,
    manual: bool,
) -> None:
    from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
    from app.domains.content_rewrite.tables import RewriteSendFenceRow
    from tests.content_rewrite.test_repository import _record

    guest_id = await owner(storage)
    expired = await note(storage, guest_id, OLD)
    job = PostgresContentRewriteRepository(storage.sessions, cipher())._row(_record())
    job.owner_guest_id = guest_id
    job.status, job.lease_token = "leased", uuid4()
    job.lease_expires_at = NOW - timedelta(minutes=2)
    job.request_started_at = NOW - timedelta(minutes=3)
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD)
        session.add(job)
        session.add(
            RewriteSendFenceRow(
                job_id=job.id,
                lease_token=job.lease_token,
                subject_id=guest_id,
                expires_at=NOW - timedelta(minutes=1),
            )
        )
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    removed = (
        await repository.clear(guest_id, NOW) if manual else await repository.purge_expired(NOW)
    )
    assert removed >= 1
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, expired.id) is None
        assert await session.get(GuestSessionRow, guest_id) is not None


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("status", ["pending", "retry_wait", "leased"])
async def test_unsent_attempt_does_not_hide_or_prevent_history_erasure(
    storage: Database, manual: bool, status: str
) -> None:
    from app.domains.birth.tables import BirthProfileRow
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.tables import (
        ReadingGenerationAttemptRow,
        ReadingPlanRow,
        ReadingRevisionRow,
    )
    from tests.readings.test_worker import NOW as QUEUED_AT
    from tests.readings.test_worker import _queued_attempt

    repository = PostgresReadingRepository(storage.sessions, cipher())
    guest_id, profile_id, attempt, _ = await _queued_attempt(storage, repository)
    async with storage.sessions() as session, session.begin():
        await session.execute(
            update(GuestSessionRow)
            .where(GuestSessionRow.id == guest_id)
            .values(expires_at=NOW + timedelta(days=365))
        )
        await activate_policy(session, guest_id, QUEUED_AT)
        if status == "retry_wait":
            await session.execute(
                update(ReadingGenerationAttemptRow)
                .where(ReadingGenerationAttemptRow.id == attempt.id)
                .values(status="retry_wait", attempt_count=1)
            )
    lease = None
    if status == "leased":
        lease = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=60)
        assert lease is not None
    history = PostgresHistoryRepository(storage.sessions, cipher())
    assert await history.remaining(NOW) == 1
    removed = await history.clear(guest_id, NOW) if manual else await history.purge_expired(NOW)
    assert removed == 1 and await history.remaining(NOW) == 0
    async with storage.sessions() as session:
        assert await session.get(ReadingPlanRow, attempt.plan_id) is None
        assert await session.get(ReadingGenerationAttemptRow, attempt.id) is None
        assert (
            await session.scalar(
                select(ReadingRevisionRow.id).where(ReadingRevisionRow.plan_id == attempt.plan_id)
            )
            is None
        )
        assert await session.get(GuestSessionRow, guest_id) is not None
        assert await session.get(BirthProfileRow, profile_id) is not None
    if lease is not None:
        assert not await repository.mark_generation_request_started(
            attempt_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            started_at=NOW,
        )


async def test_provider_started_history_remains_counted_until_its_fence_finishes(
    storage: Database,
) -> None:
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.tables import ReadingPlanRow
    from tests.readings.test_worker import NOW as QUEUED_AT
    from tests.readings.test_worker import _queued_attempt

    repository = PostgresReadingRepository(storage.sessions, cipher())
    guest_id, _, attempt, _ = await _queued_attempt(storage, repository)
    async with storage.sessions() as session, session.begin():
        await session.execute(
            update(GuestSessionRow)
            .where(GuestSessionRow.id == guest_id)
            .values(expires_at=NOW + timedelta(days=365))
        )
        await activate_policy(session, guest_id, QUEUED_AT)
    lease = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=60)
    assert lease is not None
    assert await repository.mark_generation_request_started(
        attempt_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )
    history = PostgresHistoryRepository(storage.sessions, cipher())
    with pytest.raises(HistoryBusy):
        await history.clear(guest_id, NOW)
    assert await history.purge_expired(NOW) == 0
    assert await history.remaining(NOW) == 1
    async with storage.sessions() as session:
        assert await session.get(ReadingPlanRow, attempt.plan_id) is not None


async def test_cleanup_drains_more_than_one_bounded_batch(
    storage: Database,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.cleanup_expired import _drain

    guest_id = await owner(storage)
    for days in range(5):
        await note(storage, guest_id, OLD - timedelta(days=days))
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, OLD - timedelta(days=10))
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    assert await _drain(repository, NOW, 2) == 5
    output = capsys.readouterr().out
    assert "purged=2 remaining=3" in output
    assert "purged=2 remaining=1" in output
    assert "purged=1 remaining=0" in output


async def test_fixed_tarot_and_radar_ttls_physically_purge_without_policy(
    storage: Database,
) -> None:
    from app.domains.identity.tables import PrincipalRow
    from app.domains.radar.tables import RadarRequestRow
    from app.domains.tarot.tables import TarotSessionRow

    guest_id = await owner(storage)
    tarot_id, radar_id, principal_id = uuid4(), uuid4(), uuid4()
    async with storage.sessions() as session, session.begin():
        session.add(PrincipalRow(id=principal_id, source_guest_id=guest_id, created_at=OLD))
        await session.flush()
        session.add_all(
            [
                TarotSessionRow(
                    id=tarot_id,
                    guest_id=guest_id,
                    state="complete",
                    context="general",
                    spread="single",
                    voice="straight_warm",
                    origin="test",
                    idempotency_hash=uuid4().bytes + uuid4().bytes,
                    payload_ciphertext="synthetic",
                    created_at=OLD,
                    updated_at=NOW,
                    expires_at=OLD + timedelta(days=30),
                ),
                RadarRequestRow(
                    id=radar_id,
                    principal_id=principal_id,
                    owner_guest_id=guest_id,
                    recipient_label_ciphertext="synthetic",
                    context="friend",
                    mode="private",
                    status="completed",
                    created_at=OLD,
                    completed_at=OLD,
                    expires_at=OLD + timedelta(days=30),
                ),
            ]
        )
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    assert await repository.purge_expired(NOW) == 2
    async with storage.sessions() as session:
        assert await session.get(TarotSessionRow, tarot_id) is None
        assert await session.get(RadarRequestRow, radar_id) is None
        assert await session.get(GuestSessionRow, guest_id) is not None


async def test_physical_daily_cleanup_starts_at_18_hours_and_takes_its_mood(
    storage: Database,
) -> None:
    """Owner decision 2026-10-20: automatic Daily history is kept at most 24 hours. Purging from
    18 hours keeps physical deletion within 24 hours under the six-hour cleanup. The note's mood
    is attached to the note and goes with it; a saved note and its mood stay."""

    guest_id = await owner(storage)
    vn_today = NOW.astimezone(PRODUCT_TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    created = (vn_today - timedelta(hours=23)).astimezone(UTC)  # 01:00 yesterday, Vietnam time
    daily = await note(storage, guest_id, created)
    kept = await note(storage, guest_id, created - timedelta(days=1))
    moods = PostgresMoodRepository(storage.sessions)
    mood = await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.CHILL,
            checked_in_at=created,
        )
    )
    await PostgresSavedNoteRepository(storage.sessions, cipher()).save(
        SavedNoteRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=kept.id,
            note_snapshot={"body": "saved"},
            saved_at=created,
        )
    )
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, created - timedelta(days=1))
    repository = PostgresHistoryRepository(storage.sessions, cipher())
    assert await repository.purge_expired(created + DAILY_PURGE_WINDOW - timedelta(seconds=1)) == 0
    assert await repository.purge_expired(created + DAILY_PURGE_WINDOW) == 1
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, daily.id) is None
        assert await session.get(MoodCheckInRow, mood.id) is None
        assert await session.get(DailyNoteRow, kept.id) is not None


async def test_unsaved_daily_note_is_hidden_after_24_hours(storage: Database) -> None:
    guest_id = await owner(storage)
    stale = await note(storage, guest_id, NOW - DAILY_HISTORY_WINDOW - timedelta(minutes=1))
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, NOW - timedelta(days=2))
    daily = PostgresDailyNoteRepository(storage.sessions, cipher())
    assert await daily.find(guest_id, stale.id) is None
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, stale.id) is not None  # hidden, purged by cleanup


async def test_mood_without_a_daily_purge_keeps_the_30_day_window(storage: Database) -> None:
    """Only Daily history moved to 24 hours: a mood on today's note is untouched at 24 hours."""

    guest_id = await owner(storage)
    current = await note(storage, guest_id, NOW)
    mood = await PostgresMoodRepository(storage.sessions).upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=current.id,
            mood=MoodValue.CHILL,
            checked_in_at=NOW - DAILY_HISTORY_WINDOW - timedelta(hours=1),
        )
    )
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, guest_id, NOW - timedelta(days=2))
    assert await PostgresHistoryRepository(storage.sessions, cipher()).purge_expired(NOW) == 0
    async with storage.sessions() as session:
        assert await session.get(MoodCheckInRow, mood.id) is not None
