"""Persist the acknowledged Aura transition identity.

Revision ID: 20260916_0018
Revises: 20260916_0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0018"
down_revision: str | None = "20260916_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reading_projections",
        sa.Column("acknowledged_aura_transition_id", sa.String(length=64), nullable=True),
    )
    op.create_check_constraint(
        "ck_reading_projections_aura_ack_length",
        "reading_projections",
        "acknowledged_aura_transition_id IS NULL OR length(acknowledged_aura_transition_id) = 64",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_reading_projections_aura_ack_length",
        "reading_projections",
        type_="check",
    )
    op.drop_column("reading_projections", "acknowledged_aura_transition_id")
