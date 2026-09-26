"""Encrypt chart snapshot result payloads at rest.

Revision ID: 20260904_0007
Revises: 20260902_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0007"
down_revision: str | None = "20260902_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chart_snapshots", sa.Column("result_ciphertext", sa.Text(), nullable=True))
    op.alter_column("chart_snapshots", "result_payload", existing_type=sa.JSON(), nullable=True)


def downgrade() -> None:
    op.alter_column("chart_snapshots", "result_payload", existing_type=sa.JSON(), nullable=False)
    op.drop_column("chart_snapshots", "result_ciphertext")
