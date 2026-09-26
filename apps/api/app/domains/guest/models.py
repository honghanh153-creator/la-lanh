from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class GuestState(StrEnum):
    ACTIVE = "active"
    DELETING = "deleting"
    REVOKED = "revoked"


class OnboardingStatus(StrEnum):
    BIRTH_PENDING = "birth_pending"
    COMPUTING = "computing"
    BASIC_REVEALED = "basic_revealed"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class GuestSessionRecord:
    id: UUID
    token_hash: bytes
    csrf_hash: bytes
    state: GuestState
    onboarding_status: OnboardingStatus
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime

    def is_active(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return self.state is GuestState.ACTIVE and self.expires_at > current


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    guest_id: UUID
    version: str
    purpose: str
    accepted_at: datetime


@dataclass(frozen=True, slots=True)
class CreationResult:
    guest: GuestSessionRecord
    token: str
    csrf_token: str
    resumed: bool


@dataclass(frozen=True, slots=True)
class CreationMaterial:
    guest: GuestSessionRecord
    consent: ConsentRecord
    idempotency_hash: bytes
    request_hash: bytes
    credential_envelope: str
    replay_expires_at: datetime


@dataclass(frozen=True, slots=True)
class StoredCreation:
    guest: GuestSessionRecord
    request_hash: bytes
    credential_envelope: str | None
    replay_expires_at: datetime
