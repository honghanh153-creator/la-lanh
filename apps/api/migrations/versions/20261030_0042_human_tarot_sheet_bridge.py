"""Human Tarot Sheet bridge: Google call budget and the sync lease (US-24, U5).

Revision ID: 20261030_0042
Revises: 20261030_0041
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261030_0042"
down_revision: str | Sequence[str] | None = "20261030_0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("human_tarot_google_usage", "human_tarot_sync_lease")


def upgrade() -> None:
    op.create_table(
        "human_tarot_google_usage",
        sa.Column("bucket", sa.String(32), primary_key=True),
        sa.Column("used", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "human_tarot_sync_lease",
        sa.Column("name", sa.String(16), primary_key=True),
        sa.Column("holder", sa.Uuid(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
        op.execute("""
            DO $protect$ DECLARE browser_role text; private_table text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  FOREACH private_table IN ARRAY ARRAY[
                    'human_tarot_google_usage', 'human_tarot_sync_lease'
                  ] LOOP
                    EXECUTE format(
                      'REVOKE ALL ON TABLE public.%I FROM %I', private_table, browser_role);
                  END LOOP;
                END IF;
              END LOOP;
            END $protect$;
        """)


def downgrade() -> None:
    # Older images ignore both tables; the counters expire on their own.
    pass
