"""Durable bounded rewrite send fences, independent of source cascades.

Revision ID: 20261010_0034
Revises: 20261010_0033
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261010_0034"
down_revision: str | None = "20261010_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rewrite_send_fences",
        sa.Column("job_id", sa.Uuid(), primary_key=True),
        sa.Column("lease_token", sa.Uuid(), primary_key=True),
        sa.Column("subject_id", sa.Uuid(), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_rewrite_send_subject_expiry", "rewrite_send_fences", ["subject_id", "expires_at"]
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.rewrite_send_fences ENABLE ROW LEVEL SECURITY")
        op.execute(
            "REVOKE ALL ON TABLE public.rewrite_send_fences FROM PUBLIC, anon, authenticated"
        )


def downgrade() -> None:
    pass
