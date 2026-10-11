"""Disclosed creation-based history policy, independent of profile/session clocks.

No policy backfill: legacy owners explicitly activate with a 30-day transition.
Application rollback preserves the policy receipts and immutable mood clocks.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261010_0032"
down_revision: str | None = "20261010_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "history_retention_policies",
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("consent_version", sa.String(64), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_history_policy_activation", "history_retention_policies", ["activated_at"])
    op.add_column("mood_check_ins", sa.Column("created_at", sa.DateTime(timezone=True)))
    op.execute(
        "UPDATE public.mood_check_ins SET created_at = checked_in_at WHERE created_at IS NULL"
    )
    # Previous application images omit this newly introduced field on insert.
    # Retain a database clock during rolling deploy/rollback; updates never reset it.
    op.alter_column(
        "mood_check_ins", "created_at", nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
    )
    op.execute("ALTER TABLE public.history_retention_policies ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.history_retention_policies FROM PUBLIC")
    op.execute("""
        DO $protect$ DECLARE browser_role text;
        BEGIN
          FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
              EXECUTE format(
                'REVOKE ALL ON TABLE public.history_retention_policies FROM %I', browser_role);
            END IF;
          END LOOP;
        END $protect$;
    """)


def downgrade() -> None:
    pass
