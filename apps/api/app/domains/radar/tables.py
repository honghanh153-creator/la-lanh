from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class RadarRequestRow(Base):
    __tablename__ = "radar_requests"
    __table_args__ = (
        Index("ix_radar_capability_hash", "token_hash", unique=True),
        Index("ix_radar_owner_created", "principal_id", "created_at"),
        Index("ix_radar_receipt_hash", "receipt_hash", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    owner_guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    recipient_guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE")
    )
    recipient_label_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(String(24), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    consent_version: Mapped[str | None] = mapped_column(String(64))
    authorization_attested_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    token_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    token_ciphertext: Mapped[str | None] = mapped_column(Text)
    result_ciphertext: Mapped[str | None] = mapped_column(Text)
    receipt_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    receipt_ciphertext: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    withdrawn_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
