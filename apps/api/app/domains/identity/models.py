from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OwnerSession:
    principal_id: UUID
    source_guest_id: UUID
    token: str
    expires_at: datetime
    resumed: bool


@dataclass(frozen=True, slots=True)
class OwnerIdentity:
    principal_id: UUID
    source_guest_id: UUID
    expires_at: datetime
