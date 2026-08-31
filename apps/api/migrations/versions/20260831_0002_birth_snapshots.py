"""Create encrypted birth profiles and immutable chart snapshots.

Revision ID: 20260831_0002
Revises: 20260830_0001
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260831_0002"
down_revision: str | None = "20260830_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "birth_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("current_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guest_id"),
    )
    op.create_table(
        "chart_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("input_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("birth_date_ciphertext", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("calculation_profile", sa.String(length=64), nullable=False),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["birth_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chart_snapshots_guest_created",
        "chart_snapshots",
        ["guest_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ux_chart_snapshots_guest_input",
        "chart_snapshots",
        ["guest_id", "input_hash"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_birth_profiles_current_snapshot",
        "birth_profiles",
        "chart_snapshots",
        ["current_snapshot_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_birth_profiles_current_snapshot", "birth_profiles", type_="foreignkey")
    op.drop_index("ux_chart_snapshots_guest_input", table_name="chart_snapshots")
    op.drop_index("ix_chart_snapshots_guest_created", table_name="chart_snapshots")
    op.drop_table("chart_snapshots")
    op.drop_table("birth_profiles")
