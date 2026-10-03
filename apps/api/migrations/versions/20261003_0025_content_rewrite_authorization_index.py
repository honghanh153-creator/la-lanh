"""Index content rewrite jobs by authorization receipt fingerprint.

Revision ID: 20261003_0025
Revises: 20261003_0024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261003_0025"
down_revision: str | None = "20261003_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "content_rewrite_jobs",
        sa.Column("authorization_fingerprint", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE content_rewrite_jobs "
        "SET authorization_fingerprint = repeat('0', 64) "
        "WHERE authorization_fingerprint IS NULL"
    )
    op.alter_column("content_rewrite_jobs", "authorization_fingerprint", nullable=False)
    op.create_index(
        "ix_content_rewrite_jobs_authorization",
        "content_rewrite_jobs",
        ["authorization_fingerprint", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_rewrite_jobs_authorization",
        table_name="content_rewrite_jobs",
    )
    op.drop_column("content_rewrite_jobs", "authorization_fingerprint")
