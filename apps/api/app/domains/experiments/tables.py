from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class DailyExperimentRow(Base):
    __tablename__ = "daily_experiments"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_daily_experiments_positive_version"),
        CheckConstraint(
            "state IN ('chosen', 'reflected')",
            name="ck_daily_experiments_state",
        ),
        CheckConstraint(
            "(state = 'chosen' AND reflected_at IS NULL) OR "
            "(state = 'reflected' AND reflected_at IS NOT NULL)",
            name="ck_daily_experiments_reflection_state",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_daily_experiments_expiry_after_creation",
        ),
        UniqueConstraint(
            "guest_id",
            "daily_note_id",
            "revision_id",
            name="uq_daily_experiments_immutable_target",
        ),
        Index(
            "ux_daily_experiments_guest_open",
            "guest_id",
            unique=True,
            sqlite_where=text("state = 'chosen'"),
            postgresql_where=text("state = 'chosen'"),
        ),
        Index("ix_daily_experiments_expiry", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    daily_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_notes.id", ondelete="CASCADE"), nullable=False
    )
    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("reading_revisions.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    reflected_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
