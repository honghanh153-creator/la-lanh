from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class RequestStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REPLACED = "replaced"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"


class IdentityMode(StrEnum):
    ANONYMOUS = "anonymous"
    ALIAS = "alias"


@dataclass(frozen=True, slots=True)
class Statement:
    id: str
    text: str
    domain: str


@dataclass(frozen=True, slots=True)
class InviteView:
    id: UUID
    recipient_label: str
    context: str
    status: RequestStatus
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PublicInvite:
    recipient_label: str
    context: str
    status: RequestStatus
    expires_at: datetime
    statements: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class SubmitResult:
    request_id: UUID
    receipt_token: str
    submitted_at: datetime
    resumed: bool


@dataclass(frozen=True, slots=True)
class OwnerResult:
    request_id: UUID
    recipient_label: str
    identity_mode: IdentityMode
    display_alias: str | None
    statements: tuple[str, ...]
    submitted_at: datetime
