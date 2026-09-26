"""Add encrypted bounded Daily Note experiments.

Revision ID: 20260916_0017
Revises: 20260914_0016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0017"
down_revision: str | None = "20260914_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("daily_note_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reflected_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version >= 1", name="ck_daily_experiments_positive_version"),
        sa.CheckConstraint(
            "state IN ('chosen', 'reflected')",
            name="ck_daily_experiments_state",
        ),
        sa.CheckConstraint(
            "(state = 'chosen' AND reflected_at IS NULL) OR "
            "(state = 'reflected' AND reflected_at IS NOT NULL)",
            name="ck_daily_experiments_reflection_state",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_daily_experiments_expiry_after_creation",
        ),
        sa.ForeignKeyConstraint(["daily_note_id"], ["daily_notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["reading_revisions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "guest_id",
            "daily_note_id",
            "revision_id",
            name="uq_daily_experiments_immutable_target",
        ),
    )
    op.create_index(
        "ix_daily_experiments_expiry",
        "daily_experiments",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ux_daily_experiments_guest_open",
        "daily_experiments",
        ["guest_id"],
        unique=True,
        postgresql_where=sa.text("state = 'chosen'"),
        sqlite_where=sa.text("state = 'chosen'"),
    )


def downgrade() -> None:
    op.drop_index("ux_daily_experiments_guest_open", table_name="daily_experiments")
    op.drop_index("ix_daily_experiments_expiry", table_name="daily_experiments")
    op.drop_table("daily_experiments")
