from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class ReadingPlanRow(Base):
    __tablename__ = "reading_plans"
    __table_args__ = (
        UniqueConstraint("id", "guest_id", "profile_id", name="uq_reading_plans_id_owner"),
        UniqueConstraint("guest_id", "profile_id", "plan_key", name="uq_reading_plans_owner_key"),
        Index("ix_reading_plans_owner_created", "guest_id", "profile_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # Privacy-first: deleting source chart data also deletes every derived plan/revision.
    chart_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chart_snapshots.id", ondelete="CASCADE"), nullable=True
    )
    plan_key: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class ReadingRevisionRow(Base):
    __tablename__ = "reading_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ("plan_id", "guest_id", "profile_id"),
            ("reading_plans.id", "reading_plans.guest_id", "reading_plans.profile_id"),
            name="fk_reading_revisions_plan_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "guest_id", "profile_id", name="uq_reading_revisions_id_owner"),
        UniqueConstraint(
            "guest_id", "profile_id", "revision_key", name="uq_reading_revisions_owner_key"
        ),
        CheckConstraint("accepted IS TRUE", name="ck_reading_revisions_accepted_only"),
        Index("ix_reading_revisions_owner_created", "guest_id", "profile_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    plan_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    revision_key: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rules_version: Mapped[str] = mapped_column(String(64), nullable=False)
    gate_policy_version: Mapped[str] = mapped_column(String(255), nullable=False)
    accepted: Mapped[bool] = mapped_column(nullable=False, default=True)
    evaluation_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class ReadingProjectionRow(Base):
    __tablename__ = "reading_projections"
    __table_args__ = (
        ForeignKeyConstraint(
            ("active_revision_id", "guest_id", "profile_id"),
            (
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ),
            name="fk_reading_projections_active_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ("available_revision_id", "guest_id", "profile_id"),
            (
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ),
            name="fk_reading_projections_available_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "guest_id", "profile_id", "scope_key", name="uq_reading_projections_owner_scope"
        ),
        CheckConstraint(
            "active_revision_id IS NULL OR available_revision_id IS NULL "
            "OR active_revision_id <> available_revision_id",
            name="ck_reading_projections_distinct_pointers",
        ),
        CheckConstraint(
            "acknowledged_aura_transition_id IS NULL "
            "OR length(acknowledged_aura_transition_id) = 64",
            name="ck_reading_projections_aura_ack_length",
        ),
        Index("ix_reading_projections_owner_date", "guest_id", "profile_id", "local_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False
    )
    scope_key: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    tradition: Mapped[str] = mapped_column(String(16), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    lens_variant: Mapped[str | None] = mapped_column(String(64), nullable=True)
    local_date: Mapped[date] = mapped_column(Date(), nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    active_revision_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    available_revision_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    acknowledged_aura_transition_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class ReadingGenerationAttemptRow(Base):
    __tablename__ = "reading_generation_attempts"
    __table_args__ = (
        ForeignKeyConstraint(
            ("plan_id", "guest_id", "profile_id"),
            ("reading_plans.id", "reading_plans.guest_id", "reading_plans.profile_id"),
            name="fk_reading_generation_attempts_plan_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ("guest_id", "profile_id", "scope_key"),
            (
                "reading_projections.guest_id",
                "reading_projections.profile_id",
                "reading_projections.scope_key",
            ),
            name="fk_reading_generation_attempts_projection_owner",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ("accepted_revision_id", "guest_id", "profile_id"),
            (
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ),
            name="fk_reading_generation_attempts_revision_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "guest_id",
            "profile_id",
            "generation_key",
            name="uq_reading_generation_attempts_owner_key",
        ),
        CheckConstraint(
            "(status = 'leased' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) "
            "OR (status <> 'leased' AND lease_token IS NULL AND lease_expires_at IS NULL "
            "AND request_started_at IS NULL)",
            name="ck_reading_generation_attempts_lease",
        ),
        CheckConstraint(
            "(status = 'succeeded' AND accepted_revision_id IS NOT NULL) "
            "OR (status <> 'succeeded' AND accepted_revision_id IS NULL)",
            name="ck_reading_generation_attempts_winner",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND max_attempts BETWEEN 1 AND 3 AND attempt_count <= max_attempts",
            name="ck_reading_generation_attempts_bounds",
        ),
        Index(
            "ix_reading_generation_attempts_queue",
            "status",
            "next_attempt_at",
            "lease_expires_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    plan_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scope_key: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    deletion_epoch: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    lease_token: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    request_started_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    accepted_revision_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    last_result: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
