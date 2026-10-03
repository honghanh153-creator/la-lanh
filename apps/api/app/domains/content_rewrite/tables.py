from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class ContentRewriteJobRow(Base):
    __tablename__ = "content_rewrite_jobs"
    __table_args__ = (
        CheckConstraint(
            "(status = 'leased' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) "
            "OR (status <> 'leased' AND lease_token IS NULL AND lease_expires_at IS NULL "
            "AND request_started_at IS NULL)",
            name="ck_content_rewrite_jobs_lease",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND max_attempts BETWEEN 1 AND 3 AND attempt_count <= max_attempts",
            name="ck_content_rewrite_jobs_attempt_bounds",
        ),
        Index(
            "ix_content_rewrite_jobs_queue",
            "status",
            "next_attempt_at",
            "lease_expires_at",
        ),
        Index("ix_content_rewrite_jobs_owner", "owner_fingerprint", "created_at"),
        Index(
            "ix_content_rewrite_jobs_authorization",
            "authorization_fingerprint",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    generation_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    surface: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_namespace: Mapped[str] = mapped_column(String(40), nullable=False)
    owner_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    authorization_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_variant: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    gate_version: Mapped[str] = mapped_column(String(80), nullable=False)
    request_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    provider_output_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gate_receipt_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    deletion_epoch: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    lease_token: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    request_started_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    last_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
