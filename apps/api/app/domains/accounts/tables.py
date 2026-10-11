from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class AccountRow(Base):
    __tablename__ = "accounts"

    subject_id: Mapped[UUID] = mapped_column(primary_key=True)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    masked_email: Mapped[str] = mapped_column(String(254), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class AccountDeviceRow(Base):
    __tablename__ = "account_devices"
    __table_args__ = (
        Index("ix_account_devices_expiry", "expires_at"),
        Index("ix_account_devices_guest", "guest_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.guest_id", ondelete="CASCADE"), nullable=False
    )
    # These use the guest-credential / guest-csrf domains, respectively, so existing
    # private APIs resolve the same owner without ever treating a digest as a bearer.
    credential_digest: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    csrf_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())


class LoginChallengeRow(Base):
    __tablename__ = "account_login_challenges"
    __table_args__ = (
        Index("ix_account_challenges_expiry", "expires_at"),
        CheckConstraint("attempts >= 0 AND attempts <= 5", name="ck_account_challenge_attempts"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    cookie_digest: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    csrf_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    initiating_guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE")
    )
    initiating_credential_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    target_guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE")
    )
    email_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    email_envelope: Mapped[str | None] = mapped_column(Text)
    oauth_verifier_envelope: Mapped[str | None] = mapped_column(Text)
    login_provider: Mapped[str] = mapped_column(String(16), nullable=False, default="email")
    storage_consent: Mapped[str | None] = mapped_column(String(64))
    subject_id: Mapped[UUID | None] = mapped_column()
    proof_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class LoginQuotaRow(Base):
    __tablename__ = "account_login_quotas"
    __table_args__ = (Index("ix_account_quotas_expiry", "expires_at"),)

    key_digest: Mapped[bytes] = mapped_column(LargeBinary(32), primary_key=True)
    used: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
