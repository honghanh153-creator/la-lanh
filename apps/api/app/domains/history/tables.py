from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class HistoryRetentionPolicyRow(Base):
    __tablename__ = "history_retention_policies"
    __table_args__ = (Index("ix_history_policy_activation", "activated_at"),)

    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    consent_version: Mapped[str] = mapped_column(String(64), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
