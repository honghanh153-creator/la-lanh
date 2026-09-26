"""Add opaque context identity to reading projections.

Revision ID: 20260914_0016
Revises: 20260914_0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260914_0016"
down_revision: str | None = "20260914_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NULL is the legacy/automatic projection variant, preserving every existing
    # auto scope key. Explicit lenses use an opaque hash and a distinct scope key.
    op.add_column(
        "reading_projections",
        sa.Column("lens_variant", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reading_projections", "lens_variant")
