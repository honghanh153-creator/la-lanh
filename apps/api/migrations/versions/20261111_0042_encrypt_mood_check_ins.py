"""Encrypt mood check-ins at rest (gap register PV-26).

Revision ID: 20261111_0042
Revises: 20261030_0041

Adds `mood_check_ins.mood_ciphertext` and lets the plain `mood` column be NULL. Once the setting
`mood_encrypted_writes` is on (a later release; legacy-plaintext-backfill-plan.md), new check-ins
store only the application envelope (it carries its own key version, as in 0012). Existing plain
rows are left as they are and stay readable; a SQL-only migration cannot create envelopes, and a
mood row is short-lived anyway (it goes with its Daily note or its own history window).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261111_0042"
down_revision: str | Sequence[str] | None = "20261030_0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mood_check_ins", sa.Column("mood_ciphertext", sa.Text(), nullable=True))
    op.alter_column("mood_check_ins", "mood", existing_type=sa.String(32), nullable=True)


def downgrade() -> None:
    # Restoring plain values needs the data key, so refuse instead of dropping encrypted moods.
    table = sa.table("mood_check_ins", sa.column("mood"), sa.column("mood_ciphertext"))
    encrypted_rows = op.get_bind().scalar(
        sa.select(sa.func.count())
        .select_from(table)
        .where(sa.or_(table.c.mood_ciphertext.is_not(None), table.c.mood.is_(None)))
    )
    if encrypted_rows:
        raise RuntimeError(
            "key-aware plaintext restoration is required before downgrading encrypted moods"
        )
    op.alter_column("mood_check_ins", "mood", existing_type=sa.String(32), nullable=False)
    op.drop_column("mood_check_ins", "mood_ciphertext")
