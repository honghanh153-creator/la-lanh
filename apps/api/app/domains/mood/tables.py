from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class MoodCheckInRow(Base):
    __tablename__ = "mood_check_ins"
    __table_args__ = (
        Index("ux_mood_check_ins_guest_note", "guest_id", "daily_note_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    daily_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_notes.id", ondelete="CASCADE"), nullable=False
    )
    mood: Mapped[str] = mapped_column(String(32), nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
