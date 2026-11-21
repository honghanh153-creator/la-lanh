"""Saved month answers: kept only when the person taps "Lưu" (AK2, US-25 AC12)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class SavedMonthAnswerRow(Base):
    __tablename__ = "saved_month_answers"
    # The answer text lives only in ``snapshot_ciphertext`` (AES-GCM, bound to the row id). The
    # answer is recomputed on the server from closed values (topic, preset) before saving.
    # Guest deletion cascades; removing birth time or place deletes these copies too.
    __table_args__ = (
        Index("ux_saved_month_answers_guest_key", "guest_id", "answer_key", unique=True),
        Index("ix_saved_month_answers_guest_saved", "guest_id", "saved_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    answer_key: Mapped[str] = mapped_column(String(32), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    topic: Mapped[str] = mapped_column(String(16), nullable=False)
    snapshot_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
