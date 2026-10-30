from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class HumanTarotDayRow(Base):
    """Requests accepted on one Vietnam day (US-24 R5). Holds no person; never decremented."""

    __tablename__ = "human_tarot_days"
    __table_args__ = (
        CheckConstraint("accepted_count BETWEEN 0 AND 10", name="ck_human_tarot_day_cap"),
    )

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Set after a restore during an intake day: the restored count may be lower than reality.
    intake_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class HumanTarotRequestRow(Base):
    """A guest's request and, once imported, the frozen reading. Removed with the guest."""

    __tablename__ = "human_tarot_requests"
    __table_args__ = (
        Index("ux_human_tarot_guest_key", "guest_id", "idempotency_hash", unique=True),
        Index("ix_human_tarot_guest_created", "guest_id", "created_at"),
        Index("ix_human_tarot_expires", "expires_at"),
        CheckConstraint(
            "status IN ('accepted', 'ready', 'unfulfilled', 'cancelled')",
            name="ck_human_tarot_request_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    idempotency_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    context: Mapped[str] = mapped_column(String(24), nullable=False)
    spread: Mapped[str] = mapped_column(String(24), nullable=False)
    spread_map: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    # Question, then also the frozen reading; NULL once both are gone (cancel, purge).
    payload_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    imported_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    question_purged_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class HumanTarotSlotRow(Base):
    """One of the day's 10 Sheet rows: the admission ledger and the Sheet copy's state.

    No question here. When the request disappears for any reason (guest deletion, retention,
    journal replay) ``request_id`` becomes NULL and the Sheet bridge clears the row; when the
    guest disappears ``guest_id`` becomes NULL. Either way the day's count stays.
    """

    __tablename__ = "human_tarot_slots"
    __table_args__ = (
        UniqueConstraint("day", "slot_no", name="uq_human_tarot_slot"),
        UniqueConstraint("day", "guest_id", name="uq_human_tarot_slot_guest"),
        UniqueConstraint("request_code", name="uq_human_tarot_slot_code"),
        CheckConstraint("slot_no BETWEEN 1 AND 10", name="ck_human_tarot_slot_no"),
        CheckConstraint(
            "sheet_state IN ('pending_export', 'on_sheet', 'clear_due', 'clear_sent', 'cleared')",
            name="ck_human_tarot_sheet_state",
        ),
        Index("ix_human_tarot_slot_state", "sheet_state", "day"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    day: Mapped[date] = mapped_column(ForeignKey("human_tarot_days.day"), nullable=False)
    slot_no: Mapped[int] = mapped_column(Integer, nullable=False)
    request_code: Mapped[str] = mapped_column(String(12), nullable=False)
    guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="SET NULL"), nullable=True
    )
    request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("human_tarot_requests.id", ondelete="SET NULL"), nullable=True
    )
    sheet_state: Mapped[str] = mapped_column(String(16), nullable=False)
    # A closed error code (never content), attempts and back-off for the Sheet bridge.
    sheet_error: Mapped[str | None] = mapped_column(String(48), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    # The last validation feedback written to the Sheet, so it is not rewritten every minute.
    feedback_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
