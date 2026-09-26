from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domains.experiments.errors import ExperimentConflict
from app.domains.experiments.models import DailyExperiment, ExperimentDraft, ExperimentOutcome
from app.domains.experiments.repository import ExperimentRepository
from app.domains.guest.errors import ConsentVersionInvalid
from app.domains.readings.models import BackgroundLens


class ExperimentService:
    CONSENT_VERSION = "action-experiment-v1"
    # Leave a six-hour deletion margin for the mandatory cleanup schedule so
    # physical retention never crosses the published 30-day ceiling.
    RETENTION_WINDOW = timedelta(days=29, hours=18)

    def __init__(self, repository: ExperimentRepository) -> None:
        self._repository = repository

    async def choose(
        self,
        *,
        guest_id: UUID,
        daily_note_id: UUID,
        revision_id: UUID,
        background_lens: BackgroundLens,
        action_key: str,
        consent_version: str,
        expected_experiment_id: UUID | None = None,
        expected_version: int | None = None,
        now: datetime | None = None,
    ) -> DailyExperiment:
        if consent_version != self.CONSENT_VERSION:
            raise ConsentVersionInvalid
        if (expected_experiment_id is None) != (expected_version is None):
            raise ExperimentConflict
        if len(action_key) != 64:
            raise ExperimentConflict
        current = now or datetime.now(UTC)
        return await self._repository.choose_with_consent(
            ExperimentDraft(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily_note_id,
                revision_id=revision_id,
                background_lens=background_lens,
                action_key=action_key,
                created_at=current,
                expires_at=current + self.RETENTION_WINDOW,
            ),
            consent_version=consent_version,
            expected_experiment_id=expected_experiment_id,
            expected_version=expected_version,
        )

    async def current(
        self, guest_id: UUID, *, now: datetime | None = None
    ) -> DailyExperiment | None:
        return await self._repository.current(guest_id, now=now or datetime.now(UTC))

    async def undo(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        now: datetime | None = None,
    ) -> None:
        if expected_version < 1 or not await self._repository.undo(
            guest_id,
            experiment_id=experiment_id,
            expected_version=expected_version,
            now=now or datetime.now(UTC),
        ):
            raise ExperimentConflict

    async def reflect(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        outcome: ExperimentOutcome,
        now: datetime | None = None,
    ) -> DailyExperiment:
        if expected_version < 1:
            raise ExperimentConflict
        record = await self._repository.reflect(
            guest_id,
            experiment_id=experiment_id,
            expected_version=expected_version,
            outcome=outcome,
            now=now or datetime.now(UTC),
        )
        if record is None:
            raise ExperimentConflict
        return record

    async def cleanup(self, *, batch_size: int = 500, now: datetime | None = None) -> int:
        if batch_size < 1 or batch_size > 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        return await self._repository.purge_expired(
            now=now or datetime.now(UTC),
            batch_size=batch_size,
        )
