from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UtcDateTime


class GuestSessionRow(Base):
    __tablename__ = "guest_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_guest_expiry_after_creation"),
        Index("ix_guest_sessions_expiry", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    csrf_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    onboarding_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

    consents: Mapped[list["ConsentRow"]] = relationship(
        back_populates="guest", cascade="all, delete-orphan", passive_deletes=True
    )
    creations: Mapped[list["GuestCreationRow"]] = relationship(
        back_populates="guest", cascade="all, delete-orphan", passive_deletes=True
    )


class ConsentRow(Base):
    __tablename__ = "consents"
    __table_args__ = (Index("ix_consents_guest_purpose", "guest_id", "purpose", unique=True),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())

    guest: Mapped[GuestSessionRow] = relationship(back_populates="consents")


class GuestCreationRow(Base):
    __tablename__ = "guest_session_creations"
    __table_args__ = (
        CheckConstraint("replay_expires_at >= created_at", name="ck_guest_creation_replay_window"),
        Index("ix_guest_creation_replay_expiry", "replay_expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    idempotency_hash: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    request_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    credential_envelope: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    replay_expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

    guest: Mapped[GuestSessionRow] = relationship(back_populates="creations")
