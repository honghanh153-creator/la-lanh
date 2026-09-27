"""Store the user's explicit Radar reading voice.

Revision ID: 20260927_0021
Revises: 20260920_0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260927_0021"
down_revision: str | None = "20260920_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "radar_requests",
        sa.Column("voice", sa.String(length=32), server_default="straight_warm", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("radar_requests", "voice")
