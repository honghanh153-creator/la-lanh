"""Saved month answers (US-25 AC12): explicit "Lưu", own list, deletable.

Revision ID: 20261120_0043
Revises: 20261111_0042
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261120_0043"
down_revision: str | Sequence[str] | None = "20261111_0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "saved_month_answers"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer_key", sa.String(32), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("topic", sa.String(16), nullable=False),
        sa.Column("snapshot_ciphertext", sa.Text(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ux_saved_month_answers_guest_key", TABLE, ["guest_id", "answer_key"], unique=True
    )
    op.create_index("ix_saved_month_answers_guest_saved", TABLE, ["guest_id", "saved_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
        op.execute(
            """
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format(
                    'REVOKE ALL ON TABLE public.saved_month_answers FROM %I', browser_role);
                END IF;
              END LOOP;
            END $protect$;
            """
        )


def downgrade() -> None:
    op.drop_index("ix_saved_month_answers_guest_saved", table_name=TABLE)
    op.drop_index("ux_saved_month_answers_guest_key", table_name=TABLE)
    op.drop_table(TABLE)
