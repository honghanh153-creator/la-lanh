"""Add US03-US06 product loop tables and birth supplement fields.

Revision ID: 20260901_0003
Revises: 20260831_0002
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260901_0003"
down_revision: str | None = "20260831_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "birth_profiles",
        sa.Column("profile_level", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("birth_profiles", sa.Column("birth_time_ciphertext", sa.Text(), nullable=True))
    op.add_column("birth_profiles", sa.Column("birth_place_ciphertext", sa.Text(), nullable=True))
    op.add_column(
        "birth_profiles",
        sa.Column("time_precision", sa.String(length=32), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "birth_profiles", sa.Column("place_display_name", sa.String(length=120), nullable=True)
    )
    op.add_column("birth_profiles", sa.Column("timezone_id", sa.String(length=64), nullable=True))
    op.add_column(
        "birth_profiles",
        sa.Column("supplement_consent_version", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "daily_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("note_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=96), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("context_label", sa.String(length=96), nullable=False),
        sa.Column("content_version", sa.String(length=32), nullable=False),
        sa.Column("chart_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chart_snapshot_id"], ["chart_snapshots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_daily_notes_guest_date", "daily_notes", ["guest_id", "note_date"], unique=True
    )

    op.create_table(
        "mood_check_ins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("daily_note_id", sa.Uuid(), nullable=False),
        sa.Column("mood", sa.String(length=32), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["daily_note_id"], ["daily_notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_mood_check_ins_guest_note", "mood_check_ins", ["guest_id", "daily_note_id"], unique=True
    )

    op.create_table(
        "saved_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("daily_note_id", sa.Uuid(), nullable=False),
        sa.Column("note_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["daily_note_id"], ["daily_notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_saved_notes_guest_note", "saved_notes", ["guest_id", "daily_note_id"], unique=True
    )

    op.create_table(
        "share_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("daily_note_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("safe_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["daily_note_id"], ["daily_notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_share_artifacts_token_hash", "share_artifacts", ["token_hash"], unique=True)
    op.create_index(
        "ix_share_artifacts_guest_created",
        "share_artifacts",
        ["guest_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_share_artifacts_guest_created", table_name="share_artifacts")
    op.drop_index("ix_share_artifacts_token_hash", table_name="share_artifacts")
    op.drop_table("share_artifacts")
    op.drop_index("ux_saved_notes_guest_note", table_name="saved_notes")
    op.drop_table("saved_notes")
    op.drop_index("ux_mood_check_ins_guest_note", table_name="mood_check_ins")
    op.drop_table("mood_check_ins")
    op.drop_index("ux_daily_notes_guest_date", table_name="daily_notes")
    op.drop_table("daily_notes")
    op.drop_column("birth_profiles", "supplement_consent_version")
    op.drop_column("birth_profiles", "timezone_id")
    op.drop_column("birth_profiles", "place_display_name")
    op.drop_column("birth_profiles", "time_precision")
    op.drop_column("birth_profiles", "birth_place_ciphertext")
    op.drop_column("birth_profiles", "birth_time_ciphertext")
    op.drop_column("birth_profiles", "profile_level")
