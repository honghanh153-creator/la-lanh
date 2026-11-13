"""Rolling counter for birth-date corrections (US-23 D5: at most 3 per 24 hours).

One row per accepted correction: the owner and a time, no date or value. Pruned after 24 hours
by the next correction and the six-hourly cleanup; guest deletion cascades. Additive; the
downgrade drops the table, which holds nothing a later roll-forward needs.

Revision ID: 20261029_0040
Revises: 20261029_0039
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261029_0040"
down_revision: str | Sequence[str] | None = "20261029_0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "birth_date_changes"


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
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_birth_date_changes_guest_changed", TABLE, ["guest_id", "changed_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
        op.execute(f"""
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format('REVOKE ALL ON TABLE public.{TABLE} FROM %I', browser_role);
                END IF;
              END LOOP;
            END $protect$;
        """)  # noqa: S608 - TABLE is a fixed name


def downgrade() -> None:
    op.drop_index("ix_birth_date_changes_guest_changed", table_name=TABLE)
    op.drop_table(TABLE)
