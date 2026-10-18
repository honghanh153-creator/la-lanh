"""Per-guest monotonic Tarot variant cursor (US-20 AC15, B2-4a).

Revision ID: 20261018_0037
Revises: 20261011_0036
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_0037"
down_revision: str | Sequence[str] | None = "20261011_0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tarot_variant_cursors",
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("next_position", sa.Integer(), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.tarot_variant_cursors ENABLE ROW LEVEL SECURITY")
        op.execute(
            "REVOKE ALL ON TABLE public.tarot_variant_cursors FROM PUBLIC, anon, authenticated"
        )


def downgrade() -> None:
    # Older images ignore the table; keep cursors so a roll-forward never reuses a position.
    pass
