from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class DailyNoteRow(Base):
    __tablename__ = "daily_notes"
    __table_args__ = (Index("ux_daily_notes_guest_date", "guest_id", "note_date", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    note_date: Mapped[date] = mapped_column(Date(), nullable=False)
    title: Mapped[str] = mapped_column(String(96), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    full_body: Mapped[str] = mapped_column(Text, nullable=False)
    context_label: Mapped[str] = mapped_column(String(96), nullable=False)
    content_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_version: Mapped[str] = mapped_column(String(32), nullable=False)
    persona_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    persona_label: Mapped[str] = mapped_column(String(16), nullable=False)
    persona_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_level: Mapped[str] = mapped_column(String(32), nullable=False)
    astrology_source_version: Mapped[str] = mapped_column(String(64), nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    fallback_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    chart_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chart_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
