from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class MoodValue(StrEnum):
    RUC = "Rực"
    CHILL = "Chill"
    DUOI = "Đuối"
    CANG = "Căng"
    LAC_TROI = "Lạc trôi"


@dataclass(frozen=True, slots=True)
class MoodCheckInRecord:
    id: UUID
    guest_id: UUID
    daily_note_id: UUID
    mood: MoodValue
    checked_in_at: datetime
