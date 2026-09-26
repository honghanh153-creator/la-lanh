"""Add durable, deletion-safe reading generation attempts.

Revision ID: 20260907_0011
Revises: 20260907_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0011"
down_revision: str | None = "20260907_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reading_generation_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("generation_key", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("deletion_epoch", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_revision_id", sa.Uuid(), nullable=True),
        sa.Column("last_result", sa.String(length=24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'leased' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) "
            "OR (status <> 'leased' AND lease_token IS NULL AND lease_expires_at IS NULL "
            "AND request_started_at IS NULL)",
            name="ck_reading_generation_attempts_lease",
        ),
        sa.CheckConstraint(
            "(status = 'succeeded' AND accepted_revision_id IS NOT NULL) "
            "OR (status <> 'succeeded' AND accepted_revision_id IS NULL)",
            name="ck_reading_generation_attempts_winner",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND max_attempts BETWEEN 1 AND 3 AND attempt_count <= max_attempts",
            name="ck_reading_generation_attempts_bounds",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id", "guest_id", "profile_id"],
            ["reading_plans.id", "reading_plans.guest_id", "reading_plans.profile_id"],
            name="fk_reading_generation_attempts_plan_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["guest_id", "profile_id", "scope_key"],
            [
                "reading_projections.guest_id",
                "reading_projections.profile_id",
                "reading_projections.scope_key",
            ],
            name="fk_reading_generation_attempts_projection_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["accepted_revision_id", "guest_id", "profile_id"],
            [
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ],
            name="fk_reading_generation_attempts_revision_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "guest_id",
            "profile_id",
            "generation_key",
            name="uq_reading_generation_attempts_owner_key",
        ),
    )
    op.create_index(
        "ix_reading_generation_attempts_queue",
        "reading_generation_attempts",
        ["status", "next_attempt_at", "lease_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reading_generation_attempts_queue",
        table_name="reading_generation_attempts",
    )
    op.drop_table("reading_generation_attempts")
