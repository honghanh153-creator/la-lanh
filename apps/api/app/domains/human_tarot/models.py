from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domains.tarot.models import TarotCard, TarotContext, TarotSpread


class RequestStatus(StrEnum):
    """Stored states. ``ready`` means imported and frozen, not necessarily visible yet."""

    ACCEPTED = "accepted"
    READY = "ready"
    UNFULFILLED = "unfulfilled"
    CANCELLED = "cancelled"


class SheetState(StrEnum):
    PENDING_EXPORT = "pending_export"
    ON_SHEET = "on_sheet"
    CLEAR_DUE = "clear_due"
    CLEAR_SENT = "clear_sent"
    CLEARED = "cleared"


class VisibleStatus(StrEnum):
    """What the owner of a request sees; decided by the server clock on every read (R9)."""

    WAITING = "waiting"
    READY = "ready"
    LATE = "late"
    UNFULFILLED = "unfulfilled"
    CANCELLED = "cancelled"


class AvailabilityReason(StrEnum):
    OPEN = "open"
    FULL = "full"
    CLOSED = "closed"
    ALREADY_REQUESTED = "already_requested"
    DISABLED = "disabled"


class HumanTarotAvailability(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool
    accepting: bool
    reason: AvailabilityReason
    local_date: date
    closes_at: datetime
    release_at: datetime
    daily_limit: int
    remaining: int
    consent_version: str
    current_request_id: UUID | None = None


class HumanTarotCardPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    position_key: str
    position_label: str
    card: TarotCard


class HumanTarotResult(BaseModel):
    """The owner's frozen reading. Never rewritten by the engine or Luna."""

    model_config = ConfigDict(frozen=True)

    reader: Literal["human"] = "human"
    cards: tuple[HumanTarotCardPosition, ...]
    reading: str
    step: str
    imported_at: datetime


class HumanTarotRequestView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    status: VisibleStatus
    delivery: Literal["pending", "delivered", "error"] | None = None
    copy_cleared: bool | None = None
    local_date: date
    release_at: datetime
    context: TarotContext
    spread: TarotSpread
    question: str | None = None
    result: HumanTarotResult | None = None
    expires_at: datetime
