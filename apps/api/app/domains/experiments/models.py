from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domains.readings.models import BackgroundLens, ExperimentProjection


class ExperimentState(StrEnum):
    CHOSEN = "chosen"
    REFLECTED = "reflected"


class ExperimentOutcome(StrEnum):
    NOT_TRIED = "not_tried"
    HELPFUL = "helpful"
    NO_DIFFERENCE = "no_difference"
    NOT_FOR_NOW = "not_for_now"


@dataclass(frozen=True, slots=True)
class ExperimentDraft:
    id: UUID
    guest_id: UUID
    daily_note_id: UUID
    revision_id: UUID
    background_lens: BackgroundLens
    action_key: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class DailyExperiment:
    id: UUID
    version: int
    daily_note_id: UUID
    revision_id: UUID
    state: ExperimentState
    background_lens: BackgroundLens
    action_key: str
    projection: ExperimentProjection
    outcome: ExperimentOutcome | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    reflected_at: datetime | None
