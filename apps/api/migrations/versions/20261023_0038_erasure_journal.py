"""Deletion journal for explicit user erasures (audit P07, option A).

Revision ID: 20261023_0038
Revises: 20261018_0037
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261023_0038"
down_revision: str | Sequence[str] | None = "20261018_0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "erasure_journal",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("subject_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("scope", sa.String(64), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "kind", "subject_digest", "scope", "occurred_at", name="uq_erasure_entry"
        ),
    )
    op.create_index("ix_erasure_journal_occurred", "erasure_journal", ["occurred_at"])
    op.create_table(
        "erasure_journal_horizon",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purged_before", sa.DateTime(timezone=True), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.erasure_journal ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.erasure_journal FROM PUBLIC")
        op.execute("ALTER TABLE public.erasure_journal_horizon ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.erasure_journal_horizon FROM PUBLIC")
        op.execute("""
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format(
                    'REVOKE ALL ON TABLE public.erasure_journal FROM %I', browser_role);
                  EXECUTE format(
                    'REVOKE ALL ON TABLE public.erasure_journal_horizon FROM %I', browser_role);
                END IF;
              END LOOP;
            END $protect$;
        """)


def downgrade() -> None:
    # Older images ignore the table. Keep the facts so a roll-forward can still replay them.
    pass
