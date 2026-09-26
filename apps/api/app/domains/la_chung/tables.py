from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Index, LargeBinary, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class LaChungRequestRow(Base):
    __tablename__ = "la_chung_requests"
    __table_args__ = (
        Index("ix_la_chung_capability_hash", "token_hash", unique=True),
        Index("ux_la_chung_request_idempotency_hash", "idempotency_hash", unique=True),
        Index("ix_la_chung_principal_created", "principal_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    # Kept nullable only for key-aware migration compatibility with pre-encryption rows.
    recipient_label: Mapped[str | None] = mapped_column(String(40))
    recipient_label_ciphertext: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    bank_version: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    token_ciphertext: Mapped[str | None] = mapped_column(Text)
    # Nullable legacy rows predate the client-create idempotency contract.
    idempotency_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    draft_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime())


class LaChungResponseRow(Base):
    __tablename__ = "la_chung_responses"
    __table_args__ = (
        Index("ux_la_chung_response_request", "request_id", unique=True),
        Index("ix_la_chung_receipt_hash", "receipt_hash", unique=True),
        Index("ix_la_chung_response_idempotency", "idempotency_hash", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("la_chung_requests.id", ondelete="CASCADE"), nullable=False
    )
    selections: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    identity_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    display_alias: Mapped[str | None] = mapped_column(String(24))
    idempotency_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    receipt_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    receipt_ciphertext: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    hidden_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    deleted_at: Mapped[datetime | None] = mapped_column(UtcDateTime())


class LaChungReportRow(Base):
    __tablename__ = "la_chung_reports"
    __table_args__ = (
        UniqueConstraint("request_id", "reason", name="uq_la_chung_report_request_reason"),
        Index("ix_la_chung_report_request_created", "request_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("la_chung_requests.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
