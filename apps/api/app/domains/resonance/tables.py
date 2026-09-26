from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class ResonanceFeedbackRow(Base):
    __tablename__ = "resonance_feedback"
    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at",
            name="ck_resonance_feedback_expiry_after_creation",
        ),
        Index(
            "ux_resonance_feedback_guest_note_revision",
            "guest_id",
            "daily_note_id",
            "revision_key",
            unique=True,
        ),
        Index("ix_resonance_feedback_expiry", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    daily_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_notes.id", ondelete="CASCADE"), nullable=False
    )
    revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reading_revisions.id", ondelete="CASCADE"), nullable=True
    )
    revision_key: Mapped[str] = mapped_column(String(36), nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
