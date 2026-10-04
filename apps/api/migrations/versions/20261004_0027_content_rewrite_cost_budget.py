"""Add atomic USD cost accounting to rewrite jobs.

Revision ID: 20261004_0027
Revises: 20261003_0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261004_0027"
down_revision: str | None = "20261003_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("content_rewrite_jobs", sa.Column("cost_nanos", sa.BigInteger(), nullable=True))
    op.add_column(
        "content_rewrite_jobs",
        sa.Column(
            "budget_reserved_cost_nanos",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "content_rewrite_jobs",
        sa.Column("pricing_version", sa.String(length=80), nullable=True),
    )
    op.create_check_constraint(
        "ck_content_rewrite_jobs_cost_reservation",
        "content_rewrite_jobs",
        "budget_reserved_cost_nanos >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_content_rewrite_jobs_cost_reservation",
        "content_rewrite_jobs",
        type_="check",
    )
    op.drop_column("content_rewrite_jobs", "pricing_version")
    op.drop_column("content_rewrite_jobs", "budget_reserved_cost_nanos")
    op.drop_column("content_rewrite_jobs", "cost_nanos")
