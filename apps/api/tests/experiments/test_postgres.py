from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput, TimePrecision
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.experiments.models import (
    DailyExperiment,
    ExperimentDraft,
    ExperimentOutcome,
    ExperimentState,
)
from app.domains.experiments.postgres import (
    EXPERIMENT_PURPOSE,
    PostgresExperimentRepository,
)
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.models import BackgroundLens, ExperimentProjection, ReadingPurpose
from app.domains.readings.postgres import PostgresReadingRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)
Storage = tuple[Database, AesGcmEnvelopeCipher, PostgresExperimentRepository]


@dataclass(frozen=True)
class ExperimentTarget:
    guest_id: UUID
    profile_id: UUID
    snapshot: BirthSnapshotRecord
    daily_note_id: UUID
    revision_id: UUID
    projection: ExperimentProjection


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Storage]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'experiments.db'}")
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))
    try:
        yield (
            database,
            envelope,
            PostgresExperimentRepository(database.sessions, envelope),
        )
    finally:
        await database.dispose()


async def _create_target(
    database: Database,
    envelope: AesGcmEnvelopeCipher,
) -> ExperimentTarget:
    guest_id = uuid4()
    profile_id = uuid4()
    snapshot_id = uuid4()
    daily_note_id = uuid4()
    engine = NatalChartEngine()
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    snapshot = BirthSnapshotRecord(
        id=snapshot_id,
        guest_id=guest_id,
        profile_id=profile_id,
        input_hash=b"experiment-exact-snapshot",
        birth_date_ciphertext="encrypted",
        result=chart,
        created_at=NOW,
    )

    async with database.sessions() as session, session.begin():
        guest = GuestSessionRow(
            id=guest_id,
            token_hash=uuid4().bytes + uuid4().bytes,
            csrf_hash=uuid4().bytes + uuid4().bytes,
            state="active",
            onboarding_status="birth_ready",
            created_at=NOW,
            last_active_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
        session.add(guest)
        await session.flush([guest])
        profile = BirthProfileRow(
            id=profile_id,
            guest_id=guest_id,
            current_snapshot_id=None,
            profile_level=2,
            time_precision=TimePrecision.EXACT.value,
            created_at=NOW,
            updated_at=NOW,
        )
        session.add(profile)
        await session.flush([profile])
        session.add(
            ChartSnapshotRow(
                id=snapshot_id,
                guest_id=guest_id,
                profile_id=profile_id,
                input_hash=snapshot.input_hash,
                birth_date_ciphertext=snapshot.birth_date_ciphertext,
                schema_version="chart-snapshot/v1",
                engine_version=chart.provenance.version,
                calculation_profile=chart.provenance.profile,
                result_payload=None,
                result_ciphertext=envelope.encrypt(
                    chart.model_dump_json().encode(),
                    context=f"chart-snapshot:{snapshot_id}".encode(),
                ),
                created_at=NOW,
            )
        )
        await session.flush()
        profile.current_snapshot_id = snapshot_id
        session.add(
            DailyNoteRow(
                id=daily_note_id,
                guest_id=guest_id,
                note_date=date(2026, 9, 7),
                title="",
                body="",
                full_body="",
                context_label="",
                content_ciphertext="encrypted-note",
                content_version="daily-note-v3",
                persona_mode="aura",
                persona_label="deep",
                persona_version="persona-v2",
                source_level="natal_chart",
                astrology_source_version="test",
                fallback_used=False,
                fallback_reason=None,
                chart_snapshot_id=snapshot_id,
                created_at=NOW,
            )
        )

    reading = await ReadingApplicationService(
        PostgresReadingRepository(database.sessions, envelope),
        engine,
    ).project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        background_lens=BackgroundLens.WORK,
    )
    experiment = reading.active.experiment
    assert experiment is not None
    return ExperimentTarget(
        guest_id=guest_id,
        profile_id=profile_id,
        snapshot=snapshot,
        daily_note_id=daily_note_id,
        revision_id=reading.active.revision_id,
        projection=experiment,
    )


def _draft(target: ExperimentTarget, *, experiment_id: UUID | None = None) -> ExperimentDraft:
    return ExperimentDraft(
        id=experiment_id or uuid4(),
        guest_id=target.guest_id,
        daily_note_id=target.daily_note_id,
        revision_id=target.revision_id,
        background_lens=BackgroundLens.WORK,
        action_key=target.projection.action_key,
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )


async def _choose(
    repository: PostgresExperimentRepository,
    target: ExperimentTarget,
) -> DailyExperiment:
    return await repository.choose_with_consent(
        _draft(target),
        consent_version="action-experiment-v1",
        expected_experiment_id=None,
        expected_version=None,
    )


@pytest.mark.asyncio
async def test_payload_is_encrypted_without_action_lens_or_outcome_canaries(storage) -> None:  # type: ignore[no-untyped-def]
    database, envelope, repository = storage
    target = await _create_target(database, envelope)
    chosen = await _choose(repository, target)
    reflected = await repository.reflect(
        target.guest_id,
        experiment_id=chosen.id,
        expected_version=chosen.version,
        outcome=ExperimentOutcome.HELPFUL,
        now=NOW + timedelta(minutes=5),
    )
    assert reflected is not None

    async with database.sessions() as session:
        row = await session.get(DailyExperimentRow, chosen.id)
    assert row is not None
    assert row.payload_ciphertext.startswith("aesgcm:")
    for plaintext_canary in (
        target.projection.action,
        target.projection.action_key,
        BackgroundLens.WORK.value,
        ExperimentOutcome.HELPFUL.value,
    ):
        assert plaintext_canary not in row.payload_ciphertext


@pytest.mark.asyncio
async def test_consent_and_experiment_roll_back_atomically_after_injected_failure(storage) -> None:  # type: ignore[no-untyped-def]
    database, envelope, _ = storage
    target = await _create_target(database, envelope)

    class InjectedFailure(RuntimeError):
        pass

    class FailingRepository(PostgresExperimentRepository):
        async def _after_consent(self) -> None:
            raise InjectedFailure("after consent")

    repository = FailingRepository(database.sessions, envelope)
    with pytest.raises(InjectedFailure, match="after consent"):
        await _choose(repository, target)

    async with database.sessions() as session:
        consent_count = await session.scalar(
            select(func.count())
            .select_from(ConsentRow)
            .where(
                ConsentRow.guest_id == target.guest_id,
                ConsentRow.purpose == EXPERIMENT_PURPOSE,
            )
        )
        experiment_count = await session.scalar(
            select(func.count())
            .select_from(DailyExperimentRow)
            .where(DailyExperimentRow.guest_id == target.guest_id)
        )
    assert consent_count == 0
    assert experiment_count == 0


@pytest.mark.asyncio
async def test_purge_expired_physically_deletes_only_the_requested_batch(storage) -> None:  # type: ignore[no-untyped-def]
    database, envelope, repository = storage
    target = await _create_target(database, envelope)
    expired_ids = tuple(uuid4() for _ in range(3))
    live_id = uuid4()
    note_ids = tuple(uuid4() for _ in range(4))

    async with database.sessions() as session, session.begin():
        for index, note_id in enumerate(note_ids):
            session.add(
                DailyNoteRow(
                    id=note_id,
                    guest_id=target.guest_id,
                    note_date=date(2026, 8, index + 1),
                    title="",
                    body="",
                    full_body="",
                    context_label="",
                    content_ciphertext="encrypted-note",
                    content_version="daily-note-v3",
                    persona_mode="aura",
                    persona_label="deep",
                    persona_version="persona-v2",
                    source_level="natal_chart",
                    astrology_source_version="test",
                    fallback_used=False,
                    fallback_reason=None,
                    chart_snapshot_id=target.snapshot.id,
                    created_at=NOW,
                )
            )
        await session.flush()
        for index, experiment_id in enumerate(expired_ids):
            created_at = NOW - timedelta(days=10 - index)
            session.add(
                DailyExperimentRow(
                    id=experiment_id,
                    version=1,
                    guest_id=target.guest_id,
                    daily_note_id=note_ids[index],
                    revision_id=target.revision_id,
                    state=ExperimentState.REFLECTED.value,
                    payload_ciphertext=repository._encrypt_payload(
                        experiment_id,
                        background_lens=BackgroundLens.WORK,
                        action_key=target.projection.action_key,
                        outcome=ExperimentOutcome.NO_DIFFERENCE,
                    ),
                    created_at=created_at,
                    updated_at=created_at + timedelta(hours=1),
                    expires_at=NOW - timedelta(days=3 - index),
                    reflected_at=created_at + timedelta(hours=1),
                )
            )
        session.add(
            DailyExperimentRow(
                id=live_id,
                version=1,
                guest_id=target.guest_id,
                daily_note_id=note_ids[3],
                revision_id=target.revision_id,
                state=ExperimentState.REFLECTED.value,
                payload_ciphertext=repository._encrypt_payload(
                    live_id,
                    background_lens=BackgroundLens.WORK,
                    action_key=target.projection.action_key,
                    outcome=ExperimentOutcome.HELPFUL,
                ),
                created_at=NOW - timedelta(days=1),
                updated_at=NOW - timedelta(hours=12),
                expires_at=NOW + timedelta(days=29),
                reflected_at=NOW - timedelta(hours=12),
            )
        )

    assert await repository.purge_expired(now=NOW, batch_size=2) == 2
    async with database.sessions() as session:
        remaining = set(await session.scalars(select(DailyExperimentRow.id)))
    assert remaining == {expired_ids[2], live_id}

    assert await repository.purge_expired(now=NOW, batch_size=2) == 1
    async with database.sessions() as session:
        remaining = set(await session.scalars(select(DailyExperimentRow.id)))
    assert remaining == {live_id}


@pytest.mark.asyncio
async def test_precision_and_current_snapshot_change_physically_removes_stale_experiment(
    storage: Storage,
) -> None:
    database, envelope, repository = storage
    target = await _create_target(database, envelope)
    chosen = await _choose(repository, target)
    replacement_snapshot_id = uuid4()

    async with database.sessions() as session, session.begin():
        profile = await session.get(BirthProfileRow, target.profile_id)
        assert profile is not None
        session.add(
            ChartSnapshotRow(
                id=replacement_snapshot_id,
                guest_id=target.guest_id,
                profile_id=target.profile_id,
                input_hash=b"experiment-approximate-snapshot",
                birth_date_ciphertext="encrypted-replacement",
                schema_version="chart-snapshot/v1",
                engine_version="test",
                calculation_profile="test",
                result_payload=None,
                result_ciphertext="encrypted-replacement-result",
                created_at=NOW + timedelta(minutes=1),
            )
        )
        await session.flush()
        profile.time_precision = TimePrecision.APPROXIMATE.value
        profile.current_snapshot_id = replacement_snapshot_id
        profile.updated_at = NOW + timedelta(minutes=1)

    assert await repository.current(target.guest_id, now=NOW + timedelta(minutes=2)) is None
    async with database.sessions() as session:
        assert await session.get(DailyExperimentRow, chosen.id) is None
