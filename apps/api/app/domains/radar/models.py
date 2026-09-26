from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class RadarStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    REVOKED = "revoked"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class RadarMode(StrEnum):
    PRIVATE_CHECK = "private_check"
    CONSENTED_INVITE = "consented_invite"


@dataclass(frozen=True, slots=True)
class RadarInviteView:
    id: UUID
    recipient_label: str
    context: str
    mode: RadarMode
    status: RadarStatus
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RadarPublicInvite:
    request_id: UUID
    recipient_label: str
    context: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RadarAcceptResult:
    request_id: UUID
    receipt_token: str
    result: dict[str, Any]
