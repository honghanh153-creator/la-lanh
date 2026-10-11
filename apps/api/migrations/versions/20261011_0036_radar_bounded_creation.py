"""radar_bounded_creation

Revision ID: 20261011_0036
Revises: 20261010_0035
Create Date: 2026-10-11 10:38:09.729265
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261011_0036"
down_revision: str | Sequence[str] | None = "20261010_0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("radar_requests", sa.Column("idempotency_hash", sa.LargeBinary(32)))
    op.add_column("radar_requests", sa.Column("request_hash", sa.LargeBinary(32)))
    op.create_index(
        "ix_radar_idempotency_hash", "radar_requests", ["idempotency_hash"], unique=True
    )


def downgrade() -> None:
    # Old images ignore the nullable fields. Preserve replay protection on rollback.
    pass
