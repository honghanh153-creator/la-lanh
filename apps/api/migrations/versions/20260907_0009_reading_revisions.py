"""Add immutable encrypted reading plans, revisions, and explicit projections.

Revision ID: 20260907_0009
Revises: 20260904_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0009"
down_revision: str | None = "20260904_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reading_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("chart_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("plan_key", sa.String(length=64), nullable=False),
        sa.Column("plan_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["birth_profiles.id"], ondelete="CASCADE"),
        # A removed chart must not leave its derived interpretation behind.
        sa.ForeignKeyConstraint(["chart_snapshot_id"], ["chart_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "guest_id", "profile_id", name="uq_reading_plans_id_owner"),
        sa.UniqueConstraint(
            "guest_id", "profile_id", "plan_key", name="uq_reading_plans_owner_key"
        ),
    )
    op.create_index(
        "ix_reading_plans_owner_created",
        "reading_plans",
        ["guest_id", "profile_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "reading_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("revision_key", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("renderer_version", sa.String(length=64), nullable=False),
        sa.Column("content_version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("rules_version", sa.String(length=64), nullable=False),
        sa.Column("gate_policy_version", sa.String(length=255), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("evaluation_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("accepted IS TRUE", name="ck_reading_revisions_accepted_only"),
        sa.ForeignKeyConstraint(
            ["plan_id", "guest_id", "profile_id"],
            ["reading_plans.id", "reading_plans.guest_id", "reading_plans.profile_id"],
            name="fk_reading_revisions_plan_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "guest_id", "profile_id", name="uq_reading_revisions_id_owner"),
        sa.UniqueConstraint(
            "guest_id", "profile_id", "revision_key", name="uq_reading_revisions_owner_key"
        ),
    )
    op.create_index(
        "ix_reading_revisions_owner_created",
        "reading_revisions",
        ["guest_id", "profile_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "reading_projections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("tradition", sa.String(length=16), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("timezone_name", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active_revision_id", sa.Uuid(), nullable=True),
        sa.Column("available_revision_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "active_revision_id IS NULL OR available_revision_id IS NULL "
            "OR active_revision_id <> available_revision_id",
            name="ck_reading_projections_distinct_pointers",
        ),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["birth_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["active_revision_id", "guest_id", "profile_id"],
            [
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ],
            name="fk_reading_projections_active_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["available_revision_id", "guest_id", "profile_id"],
            [
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ],
            name="fk_reading_projections_available_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "guest_id", "profile_id", "scope_key", name="uq_reading_projections_owner_scope"
        ),
    )
    op.create_index(
        "ix_reading_projections_owner_date",
        "reading_projections",
        ["guest_id", "profile_id", "local_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reading_projections_owner_date", table_name="reading_projections")
    op.drop_table("reading_projections")
    op.drop_index("ix_reading_revisions_owner_created", table_name="reading_revisions")
    op.drop_table("reading_revisions")
    op.drop_index("ix_reading_plans_owner_created", table_name="reading_plans")
    op.drop_table("reading_plans")
