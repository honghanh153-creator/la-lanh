"""Anonymous daily cap and cascading owner erasure for rewrite jobs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0030"
down_revision: str | None = "20261008_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_rewrite_spend_days",
        sa.Column("day", sa.String(10), primary_key=True),
        sa.Column("reserved_cost_nanos", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("reserved_cost_nanos >= 0", name="ck_rewrite_day_nonnegative_cost"),
        sa.CheckConstraint("reserved_tokens >= 0", name="ck_rewrite_day_nonnegative_tokens"),
    )
    op.execute("ALTER TABLE public.content_rewrite_spend_days ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.content_rewrite_spend_days FROM PUBLIC")
    op.execute("""
        DO $protect$ DECLARE browser_role text;
        BEGIN
          FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
              EXECUTE format(
                'REVOKE ALL ON TABLE public.content_rewrite_spend_days FROM %I', browser_role);
            END IF;
          END LOOP;
        END $protect$;
    """)
    # Preserve all visible costs before discarding legacy encrypted queue envelopes.
    op.execute("""
        INSERT INTO public.content_rewrite_spend_days (day, reserved_cost_nanos, reserved_tokens)
        SELECT to_char(updated_at AT TIME ZONE 'UTC', 'YYYY-MM-DD'),
               sum(coalesce(cost_nanos, 0) + coalesce(budget_reserved_cost_nanos, 0)),
               sum(coalesce(input_tokens, 0) + coalesce(output_tokens, 0)
                   + coalesce(budget_reserved_tokens, 0))
        FROM public.content_rewrite_jobs GROUP BY 1
        ON CONFLICT (day) DO NOTHING
    """)
    # Cannot safely recover old ownership without decrypting personal data in a migration.
    # Stop the worker before upgrade; deterministic readings remain available, jobs requeue.
    op.execute("DELETE FROM public.content_rewrite_jobs")
    op.add_column("content_rewrite_jobs", sa.Column("owner_guest_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_rewrite_guest",
        "content_rewrite_jobs",
        "guest_sessions",
        ["owner_guest_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_content_rewrite_jobs_owner_guest_id", "content_rewrite_jobs", ["owner_guest_id"]
    )
    for column, parent in (
        ("reading_plan_id", "reading_plans"),
        ("tarot_session_id", "tarot_sessions"),
        ("radar_request_id", "radar_requests"),
    ):
        op.add_column("content_rewrite_jobs", sa.Column(column, sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"fk_rewrite_{column}",
            "content_rewrite_jobs",
            parent,
            [column],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_content_rewrite_jobs_{column}", "content_rewrite_jobs", [column])


def downgrade() -> None:
    # Preserve debit history and erasure linkage. Rollback application with worker disabled.
    pass
