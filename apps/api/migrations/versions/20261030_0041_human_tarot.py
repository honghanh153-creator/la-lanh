"""Human Tarot reader: day tally, requests and Sheet slots (US-24, U4).

Revision ID: 20261030_0041
Revises: 20261023_0038

Kept apart from the birth-correction migrations (0039, 0040) so each can be reviewed and rolled
back alone (plan KTD8). Whichever merges second rebases its ``down_revision`` onto the other.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261030_0041"
down_revision: str | Sequence[str] | None = "20261023_0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("human_tarot_days", "human_tarot_requests", "human_tarot_slots")


def upgrade() -> None:
    op.create_table(
        "human_tarot_days",
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("intake_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("accepted_count BETWEEN 0 AND 10", name="ck_human_tarot_day_cap"),
    )
    op.create_table(
        "human_tarot_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("idempotency_hash", sa.LargeBinary(32), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("context", sa.String(24), nullable=False),
        sa.Column("spread", sa.String(24), nullable=False),
        sa.Column("spread_map", sa.String(32), nullable=False),
        sa.Column("consent_version", sa.String(32), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=True),
        sa.Column("release_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("question_purged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('accepted', 'ready', 'unfulfilled', 'cancelled')",
            name="ck_human_tarot_request_status",
        ),
    )
    op.create_index(
        "ux_human_tarot_guest_key",
        "human_tarot_requests",
        ["guest_id", "idempotency_hash"],
        unique=True,
    )
    op.create_index(
        "ix_human_tarot_guest_created", "human_tarot_requests", ["guest_id", "created_at"]
    )
    op.create_index("ix_human_tarot_expires", "human_tarot_requests", ["expires_at"])
    op.create_table(
        "human_tarot_slots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("day", sa.Date(), sa.ForeignKey("human_tarot_days.day"), nullable=False),
        sa.Column("slot_no", sa.Integer(), nullable=False),
        sa.Column("request_code", sa.String(12), nullable=False),
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "request_id",
            sa.Uuid(),
            sa.ForeignKey("human_tarot_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sheet_state", sa.String(16), nullable=False),
        sa.Column("sheet_error", sa.String(48), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback_digest", sa.String(64), nullable=True),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("day", "slot_no", name="uq_human_tarot_slot"),
        sa.UniqueConstraint("day", "guest_id", name="uq_human_tarot_slot_guest"),
        sa.UniqueConstraint("request_code", name="uq_human_tarot_slot_code"),
        sa.CheckConstraint("slot_no BETWEEN 1 AND 10", name="ck_human_tarot_slot_no"),
        sa.CheckConstraint(
            "sheet_state IN ('pending_export', 'on_sheet', 'clear_due', 'clear_sent', 'cleared')",
            name="ck_human_tarot_sheet_state",
        ),
    )
    op.create_index("ix_human_tarot_slot_state", "human_tarot_slots", ["sheet_state", "day"])
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
                    'human_tarot_days', 'human_tarot_requests', 'human_tarot_slots'
                  ] LOOP
                    EXECUTE format(
                      'REVOKE ALL ON TABLE public.%I FROM %I', private_table, browser_role);
                  END LOOP;
                END IF;
              END LOOP;
            END $protect$;
        """)


def downgrade() -> None:
    # Older images ignore these tables. Keep them: a dropped slot would lose the Sheet rows that
    # still have to be cleared, and a dropped tally would reopen a day's quota.
    pass
