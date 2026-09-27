"""Add encrypted guest Tarot sessions.

Revision ID: 20260927_0022
Revises: 20260927_0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260927_0022"
down_revision: str | None = "20260927_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tarot_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("context", sa.String(length=24), nullable=False),
        sa.Column("spread", sa.String(length=24), nullable=False),
        sa.Column("voice", sa.String(length=32), nullable=False),
        sa.Column("origin", sa.String(length=24), nullable=False),
        sa.Column("idempotency_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tarot_guest_updated", "tarot_sessions", ["guest_id", "updated_at"])
    op.create_index("ix_tarot_expires", "tarot_sessions", ["expires_at"])
    op.create_index(
        "ux_tarot_guest_create_key",
        "tarot_sessions",
        ["guest_id", "idempotency_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_tarot_guest_create_key", table_name="tarot_sessions")
    op.drop_index("ix_tarot_expires", table_name="tarot_sessions")
    op.drop_index("ix_tarot_guest_updated", table_name="tarot_sessions")
    op.drop_table("tarot_sessions")
