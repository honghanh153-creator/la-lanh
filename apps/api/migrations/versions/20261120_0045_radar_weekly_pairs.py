"""Hợp gu "Hai bạn tuần này" (owner AL1, 20.11.2026; direction C, second half).

Revision ID: 20261120_0045
Revises: 20261120_0044

A pair the owner chose to keep: the other person's birth date only (no time, no place) and the
nickname, both encrypted, plus the relationship. It expires on its own (90 days by default) and
is deleted on request or with the owner's data. The feature is off (`radar_weekly_pairs`); the
table is created empty.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261120_0045"
down_revision: str | Sequence[str] | None = "20261120_0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "radar_weekly_pairs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "principal_id",
            sa.Uuid(),
            sa.ForeignKey("principals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("context", sa.String(24), nullable=False),
        sa.Column("label_ciphertext", sa.Text(), nullable=False),
        sa.Column("birth_date_ciphertext", sa.Text(), nullable=False),
        sa.Column("consent_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_radar_weekly_expiry_after_creation"),
    )
    op.create_index(
        "ix_radar_weekly_principal", "radar_weekly_pairs", ["principal_id", "created_at"]
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.radar_weekly_pairs ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.radar_weekly_pairs FROM PUBLIC")
        op.execute("""
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format(
                    'REVOKE ALL ON TABLE public.%I FROM %I', 'radar_weekly_pairs', browser_role);
                END IF;
              END LOOP;
            END $protect$;
        """)


def downgrade() -> None:
    op.drop_index("ix_radar_weekly_principal", table_name="radar_weekly_pairs")
    op.drop_table("radar_weekly_pairs")
