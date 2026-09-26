"""Add deterministic Vibe and Aura metadata to daily notes.

Revision ID: 20260902_0006
Revises: 20260902_0005
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_0006"
down_revision: str | None = "20260902_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("daily_notes", sa.Column("full_body", sa.Text(), nullable=True))
    op.execute("UPDATE daily_notes SET full_body = body WHERE full_body IS NULL")
    op.alter_column("daily_notes", "full_body", nullable=False)
    op.add_column(
        "daily_notes",
        sa.Column("persona_mode", sa.String(length=16), nullable=False, server_default="vibe"),
    )
    op.add_column(
        "daily_notes",
        sa.Column("persona_label", sa.String(length=16), nullable=False, server_default="Mềm"),
    )
    op.add_column(
        "daily_notes",
        sa.Column(
            "persona_version", sa.String(length=32), nullable=False, server_default="persona-v1"
        ),
    )
    op.add_column(
        "daily_notes",
        sa.Column(
            "source_level", sa.String(length=32), nullable=False, server_default="date_only_sun"
        ),
    )
    op.add_column(
        "daily_notes",
        sa.Column(
            "astrology_source_version",
            sa.String(length=64),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.add_column(
        "daily_notes",
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "daily_notes",
        sa.Column(
            "fallback_reason", sa.String(length=32), nullable=True, server_default="legacy_row"
        ),
    )


def downgrade() -> None:
    op.drop_column("daily_notes", "fallback_reason")
    op.drop_column("daily_notes", "fallback_used")
    op.drop_column("daily_notes", "astrology_source_version")
    op.drop_column("daily_notes", "source_level")
    op.drop_column("daily_notes", "persona_version")
    op.drop_column("daily_notes", "persona_label")
    op.drop_column("daily_notes", "persona_mode")
    op.drop_column("daily_notes", "full_body")
