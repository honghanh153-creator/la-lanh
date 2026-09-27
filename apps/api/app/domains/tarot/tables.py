from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class TarotSessionRow(Base):
    __tablename__ = "tarot_sessions"
    __table_args__ = (
        Index("ix_tarot_guest_updated", "guest_id", "updated_at"),
        Index("ix_tarot_expires", "expires_at"),
        Index("ux_tarot_guest_create_key", "guest_id", "idempotency_hash", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    context: Mapped[str] = mapped_column(String(24), nullable=False)
    spread: Mapped[str] = mapped_column(String(24), nullable=False)
    voice: Mapped[str] = mapped_column(String(32), nullable=False)
    origin: Mapped[str] = mapped_column(String(24), nullable=False)
    idempotency_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
