"""Add bounded Daily Note resonance feedback.

Revision ID: 20260914_0015
Revises: 20260907_0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260914_0015"
down_revision: str | None = "20260907_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resonance_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("daily_note_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=True),
        sa.Column("revision_key", sa.String(length=36), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_resonance_feedback_expiry_after_creation",
        ),
        sa.ForeignKeyConstraint(["daily_note_id"], ["daily_notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revision_id"], ["reading_revisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resonance_feedback_expiry",
        "resonance_feedback",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ux_resonance_feedback_guest_note_revision",
        "resonance_feedback",
        ["guest_id", "daily_note_id", "revision_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_resonance_feedback_guest_note_revision", table_name="resonance_feedback")
    op.drop_index("ix_resonance_feedback_expiry", table_name="resonance_feedback")
    op.drop_table("resonance_feedback")
