from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.experiments.models import DailyExperiment, ExperimentDraft, ExperimentOutcome


class ExperimentRepository(Protocol):
    async def choose_with_consent(
        self,
        draft: ExperimentDraft,
        *,
        consent_version: str,
        expected_experiment_id: UUID | None,
        expected_version: int | None,
    ) -> DailyExperiment: ...

    async def current(self, guest_id: UUID, *, now: datetime) -> DailyExperiment | None: ...

    async def undo(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        now: datetime,
    ) -> bool: ...

    async def reflect(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        outcome: ExperimentOutcome,
        now: datetime,
    ) -> DailyExperiment | None: ...

    async def purge_expired(self, *, now: datetime, batch_size: int) -> int: ...
