from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domains.astro.models import DateOnlySunResult


@dataclass(frozen=True, slots=True)
class BirthSnapshotRecord:
    id: UUID
    guest_id: UUID
    profile_id: UUID
    input_hash: bytes
    birth_date_ciphertext: str
    result: DateOnlySunResult
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BirthReveal:
    profile_id: UUID
    snapshot_id: UUID
    birth_date: date
    result: DateOnlySunResult
    created_at: datetime
    resumed: bool
