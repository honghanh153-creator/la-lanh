from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from app.domains.astro.models import DateOnlySunResult, NatalChart

ChartResult = DateOnlySunResult | NatalChart


class BirthTimeMode(StrEnum):
    EXACT = "exact"
    APPROX_WINDOW = "approx_window"
    UNKNOWN = "unknown"


class ApproxWindow(StrEnum):
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


@dataclass(frozen=True, slots=True)
class BirthSnapshotRecord:
    id: UUID
    guest_id: UUID
    profile_id: UUID
    input_hash: bytes
    birth_date_ciphertext: str
    result: ChartResult
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BirthReveal:
    profile_id: UUID
    snapshot_id: UUID
    birth_date: date
    result: ChartResult
    created_at: datetime
    resumed: bool


@dataclass(frozen=True, slots=True)
class BirthSupplement:
    birth_time_mode: BirthTimeMode
    birth_time_ciphertext: str | None
    approx_window: ApproxWindow | None
    birth_place_ciphertext: str | None
    consent_version: str


@dataclass(frozen=True, slots=True)
class BirthSupplementResult:
    profile_id: UUID
    snapshot_id: UUID | None
    profile_level: int
    time_precision: str
    place_display_name: str | None
    timezone_id: str | None
    chart: NatalChart | None


@dataclass(frozen=True, slots=True)
class BirthSupplementStored:
    profile_id: UUID
    profile_level: int
    birth_time_ciphertext: str | None
    birth_place_ciphertext: str | None
    time_precision: str
    supplement_consent_version: str | None


@dataclass(frozen=True, slots=True)
class BirthSupplementState:
    profile_id: UUID
    profile_level: int
    time_precision: str
    birth_time_mode: BirthTimeMode
    approx_window: ApproxWindow | None
    place_display_name: str | None
    timezone_id: str | None
