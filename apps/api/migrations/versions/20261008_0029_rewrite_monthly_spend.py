"""Durable, anonymous, conservative monthly rewrite cap.

Revision ID: 20261008_0029
Revises: 20261008_0028
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0029"
down_revision: str | None = "20261008_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_rewrite_spend_months",
        sa.Column("month", sa.String(7), primary_key=True),
        sa.Column("reserved_cost_nanos", sa.BigInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("reserved_cost_nanos >= 0", name="ck_rewrite_month_nonnegative"),
    )
    op.execute("ALTER TABLE public.content_rewrite_spend_months ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.content_rewrite_spend_months FROM PUBLIC")
    op.execute("""
        DO $protect$ DECLARE browser_role text;
        BEGIN
          FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
              EXECUTE format(
                'REVOKE ALL ON TABLE public.content_rewrite_spend_months FROM %I', browser_role);
            END IF;
          END LOOP;
        END $protect$;
    """)
    # Carry forward existing reservations conservatively if upgrading a previously paid runtime.
    op.execute("""
        INSERT INTO public.content_rewrite_spend_months (month, reserved_cost_nanos)
        SELECT to_char(updated_at AT TIME ZONE 'UTC', 'YYYY-MM'),
               sum(coalesce(cost_nanos, 0) + coalesce(budget_reserved_cost_nanos, 0))
        FROM public.content_rewrite_jobs
        GROUP BY 1
        ON CONFLICT (month) DO NOTHING
    """)


def downgrade() -> None:
    # Preserve spend history even when rolling code back. Never reset an approved limit.
    pass
