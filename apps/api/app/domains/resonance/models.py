from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domains.readings.models import BackgroundLens


class ResonanceChoice(StrEnum):
    HIT = "hit"
    MISS = "miss"


@dataclass(frozen=True, slots=True)
class ResonanceRecord:
    id: UUID
    guest_id: UUID
    daily_note_id: UUID
    revision_id: UUID | None
    choice: ResonanceChoice
    background_lens: BackgroundLens | None
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ResonanceStatus:
    consented: bool
    feedback_count: int
    last_choice: ResonanceChoice | None
