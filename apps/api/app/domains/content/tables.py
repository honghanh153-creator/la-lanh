from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime

JSON_VALUE = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class ContentRevisionRow(Base):
    __tablename__ = "content_revisions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'validated', 'published')",
            name="ck_content_revisions_status",
        ),
        Index("ix_content_revisions_bundle_created", "bundle_key", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    bundle_key: Mapped[str] = mapped_column(String(64), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_revisions.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON_VALUE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class ContentChannelRow(Base):
    __tablename__ = "content_channels"

    bundle_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    active_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_revisions.id", ondelete="RESTRICT"), nullable=True
    )
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class ContentAuditEventRow(Base):
    __tablename__ = "content_audit_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('draft_created', 'validated', 'published', 'rolled_back')",
            name="ck_content_audit_events_action",
        ),
        Index("ix_content_audit_bundle_created", "bundle_key", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    bundle_key: Mapped[str] = mapped_column(String(64), nullable=False)
    request_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    previous_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_revisions.id", ondelete="RESTRICT"), nullable=True
    )
    channel_generation: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
