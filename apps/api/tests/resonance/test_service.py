from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select, text

from app.db.session import Database
from app.domains.daily.models import (
    DailyNoteRecord,
    PersonaLabel,
    PersonaMode,
    SourceLevel,
)
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.guest.errors import ConsentVersionInvalid
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.readings.models import BackgroundLens
from app.domains.resonance.errors import ResonanceTargetNotFound
from app.domains.resonance.models import ResonanceChoice
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.domains.resonance.service import ResonanceService
from app.domains.resonance.tables import ResonanceFeedbackRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)


@pytest.fixture
async def storage(tmp_path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'resonance.db'}")
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"f" * 32))
    repository = PostgresResonanceRepository(database.sessions, envelope)
    service = ResonanceService(repository)
    try:
        yield database, repository, service, envelope
    finally:
        await database.dispose()


async def _owner_with_note(
    database: Database,
    envelope: AesGcmEnvelopeCipher,
) -> tuple[UUID, UUID]:
    guest_id = uuid4()
    note_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes,
                state="active",
                onboarding_status="completed",
                created_at=NOW,
                last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )
    await PostgresDailyNoteRepository(database.sessions, envelope).get_or_create(
        DailyNoteRecord(
            id=note_id,
            guest_id=guest_id,
            note_date=date(2026, 9, 14),
            title="Bounded note",
            body="Body",
            full_body="Full body",
            context_label="Context",
            content_version="daily-note-v3",
            persona_mode=PersonaMode.VIBE,
            persona_label=PersonaLabel.SOFT,
            persona_version="persona-v2",
            source_level=SourceLevel.DATE_ONLY_SUN,
            astrology_source_version="test",
            fallback_used=False,
            fallback_reason=None,
            chart_snapshot_id=None,
            created_at=NOW,
        )
    )
    return guest_id, note_id


@pytest.mark.asyncio
async def test_feedback_is_atomic_encrypted_idempotent_and_expires(storage) -> None:  # type: ignore[no-untyped-def]
    database, _repository, service, envelope = storage
    guest_id, note_id = await _owner_with_note(database, envelope)

    first = await service.record(
        guest_id=guest_id,
        daily_note_id=note_id,
        revision_id=None,
        choice=ResonanceChoice.HIT,
        background_lens=BackgroundLens.RELATIONSHIPS,
        consent_version="reading-resonance-v1",
        now=NOW,
    )
    second = await service.record(
        guest_id=guest_id,
        daily_note_id=note_id,
        revision_id=None,
        choice=ResonanceChoice.MISS,
        background_lens=BackgroundLens.WORK,
        consent_version="reading-resonance-v1",
        now=NOW + timedelta(minutes=1),
    )

    assert second.id == first.id
    assert second.choice is ResonanceChoice.MISS
    assert second.background_lens is BackgroundLens.WORK
    assert second.expires_at == NOW + timedelta(days=30, minutes=1)
    status = await service.status(guest_id, now=NOW + timedelta(days=29))
    assert status.consented is True
    assert status.feedback_count == 1
    assert status.last_choice is ResonanceChoice.MISS

    async with database.sessions() as session:
        raw = (
            await session.execute(text("SELECT payload_ciphertext FROM resonance_feedback"))
        ).scalar_one()
        columns = {
            row[1]
            for row in (await session.execute(text("PRAGMA table_info(resonance_feedback)"))).all()
        }
    assert raw.startswith("aesgcm:")
    assert "hit" not in raw and "miss" not in raw and "work" not in raw
    assert "choice" not in columns and "background_lens" not in columns

    expired = await service.status(guest_id, now=NOW + timedelta(days=31))
    assert expired.feedback_count == 0
    assert expired.last_choice is None
    assert expired.consented is True


@pytest.mark.asyncio
async def test_ownership_and_consent_validation_happen_before_any_write(storage) -> None:  # type: ignore[no-untyped-def]
    database, _repository, service, envelope = storage
    guest_id, _note_id = await _owner_with_note(database, envelope)

    with pytest.raises(ConsentVersionInvalid):
        await service.record(
            guest_id=guest_id,
            daily_note_id=uuid4(),
            revision_id=None,
            choice=ResonanceChoice.HIT,
            background_lens=None,
            consent_version="old-version",
            now=NOW,
        )
    with pytest.raises(ResonanceTargetNotFound):
        await service.record(
            guest_id=guest_id,
            daily_note_id=uuid4(),
            revision_id=None,
            choice=ResonanceChoice.HIT,
            background_lens=None,
            consent_version="reading-resonance-v1",
            now=NOW,
        )

    async with database.sessions() as session:
        consent_count = await session.scalar(
            select(func.count())
            .select_from(ConsentRow)
            .where(ConsentRow.purpose == "reading_resonance")
        )
        feedback_count = await session.scalar(
            select(func.count()).select_from(ResonanceFeedbackRow)
        )
    assert consent_count == feedback_count == 0


@pytest.mark.asyncio
async def test_consent_feedback_and_clear_revoke_roll_back_together(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository, service, envelope = storage
    guest_id, note_id = await _owner_with_note(database, envelope)

    async def fail_after_consent() -> None:
        raise RuntimeError("fault after consent")

    repository._after_consent = fail_after_consent
    with pytest.raises(RuntimeError, match="fault after consent"):
        await service.record(
            guest_id=guest_id,
            daily_note_id=note_id,
            revision_id=None,
            choice=ResonanceChoice.HIT,
            background_lens=None,
            consent_version="reading-resonance-v1",
            now=NOW,
        )
    async with database.sessions() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ConsentRow)
                .where(ConsentRow.purpose == "reading_resonance")
            )
            == 0
        )
        assert await session.scalar(select(func.count()).select_from(ResonanceFeedbackRow)) == 0

    async def pass_hook() -> None:
        return None

    repository._after_consent = pass_hook
    await service.record(
        guest_id=guest_id,
        daily_note_id=note_id,
        revision_id=None,
        choice=ResonanceChoice.HIT,
        background_lens=None,
        consent_version="reading-resonance-v1",
        now=NOW,
    )

    async def fail_after_clear() -> None:
        raise RuntimeError("fault after clear")

    repository._after_clear = fail_after_clear
    with pytest.raises(RuntimeError, match="fault after clear"):
        await service.clear(guest_id, revoke_consent=True, now=NOW + timedelta(hours=1))
    assert (await service.status(guest_id, now=NOW)).feedback_count == 1
    assert (await service.status(guest_id, now=NOW)).consented is True

    repository._after_clear = pass_hook
    await service.clear(guest_id, revoke_consent=False, now=NOW + timedelta(hours=2))
    kept = await service.status(guest_id, now=NOW)
    assert kept.feedback_count == 0 and kept.consented is True

    await service.record(
        guest_id=guest_id,
        daily_note_id=note_id,
        revision_id=None,
        choice=ResonanceChoice.MISS,
        background_lens=None,
        consent_version="reading-resonance-v1",
        now=NOW + timedelta(hours=3),
    )
    await service.clear(guest_id, revoke_consent=True, now=NOW + timedelta(hours=4))
    revoked = await service.status(guest_id, now=NOW + timedelta(hours=4))
    assert revoked.feedback_count == 0 and revoked.consented is False


@pytest.mark.asyncio
async def test_guest_deletion_cascades_feedback_and_consent(storage) -> None:  # type: ignore[no-untyped-def]
    database, _repository, service, envelope = storage
    guest_id, note_id = await _owner_with_note(database, envelope)
    await service.record(
        guest_id=guest_id,
        daily_note_id=note_id,
        revision_id=None,
        choice=ResonanceChoice.HIT,
        background_lens=BackgroundLens.ENERGY,
        consent_version="reading-resonance-v1",
        now=NOW,
    )

    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest_id))
    async with database.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(ResonanceFeedbackRow)) == 0
        assert (
            await session.scalar(
                select(func.count()).select_from(ConsentRow).where(ConsentRow.guest_id == guest_id)
            )
            == 0
        )
