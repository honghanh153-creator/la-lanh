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
        Index("ix_radar_idempotency_hash", "idempotency_hash", unique=True),
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
    voice: Mapped[str] = mapped_column(String(32), nullable=False, default="straight_warm")
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    consent_version: Mapped[str | None] = mapped_column(String(64))
    authorization_attested_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    token_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    token_ciphertext: Mapped[str | None] = mapped_column(Text)
    result_ciphertext: Mapped[str | None] = mapped_column(Text)
    idempotency_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    request_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    receipt_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    receipt_ciphertext: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    withdrawn_at: Mapped[datetime | None] = mapped_column(UtcDateTime())


class RadarWeeklyPairRow(Base):
    """A pair kept for "Hai bạn tuần này" because the invited person ticked their own box on the
    link page (owner AR1, 21.11.2026; the only way in).

    Holds the invited person's birth date only (no time, no place), encrypted, plus the nickname
    (encrypted) and the relationship. Expires on its own and is deleted when the sender turns it
    off, with the sender's guest data, or when the invited person withdraws: through the result
    while it lives (``request_id``), and through the invite link for the whole 90 days
    (``invite_token_hash``, the same HMAC as the invite's ``token_hash``). ``request_id`` has no
    foreign key on purpose: the pair outlives the 30-day result.
    """

    __tablename__ = "radar_weekly_pairs"
    __table_args__ = (
        Index("ix_radar_weekly_principal", "principal_id", "created_at"),
        Index("ix_radar_weekly_request", "request_id"),
        Index("ix_radar_weekly_invite_token", "invite_token_hash"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    owner_guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    context: Mapped[str] = mapped_column(String(24), nullable=False)
    label_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    consent_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    request_id: Mapped[UUID | None] = mapped_column(Uuid)
    invite_token_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))


class RadarShareCardRow(Base):
    """A revocable link to a frozen Hợp gu card (AL1 direction C). No birth data, no real name:
    the encrypted snapshot holds the tier name, one line, the relationship and at most an
    initial. It never outlives its result and goes with it."""

    __tablename__ = "radar_share_cards"
    __table_args__ = (
        Index("ix_radar_card_token_hash", "token_hash", unique=True),
        Index("ix_radar_card_request", "request_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("radar_requests.id", ondelete="CASCADE"), nullable=False
    )
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    snapshot_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
