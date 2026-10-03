"""Reserve rewrite token budget atomically.

Revision ID: 20261003_0026
Revises: 20261003_0025
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261003_0026"
down_revision: str | None = "20261003_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "content_rewrite_jobs",
        sa.Column(
            "budget_reserved_tokens",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "ck_content_rewrite_jobs_budget_reservation",
        "content_rewrite_jobs",
        "budget_reserved_tokens >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_content_rewrite_jobs_budget_reservation",
        "content_rewrite_jobs",
        type_="check",
    )
    op.drop_column("content_rewrite_jobs", "budget_reserved_tokens")
