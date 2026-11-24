"""Hợp gu share-card links (owner AL1, 20.11.2026; direction C, first half).

Revision ID: 20261120_0044
Revises: 20261120_0043

A card link shows a frozen, encrypted snapshot of a Hợp gu result (tier name, one line, the
relationship and at most an initial): never a birth date or a real name. It lives no longer than
its result, goes with it (ON DELETE CASCADE, and explicitly on withdrawal) and is revocable.
The feature is off (`radar_share_card_links`); the table is created empty.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261120_0044"
down_revision: str | Sequence[str] | None = "20261120_0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "radar_share_cards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Uuid(),
            sa.ForeignKey("radar_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "principal_id",
            sa.Uuid(),
            sa.ForeignKey("principals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.LargeBinary(32), nullable=False),
        sa.Column("snapshot_ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("expires_at > created_at", name="ck_radar_card_expiry_after_creation"),
    )
    op.create_index("ix_radar_card_token_hash", "radar_share_cards", ["token_hash"], unique=True)
    op.create_index("ix_radar_card_request", "radar_share_cards", ["request_id", "created_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.radar_share_cards ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.radar_share_cards FROM PUBLIC")
        op.execute("""
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format(
                    'REVOKE ALL ON TABLE public.%I FROM %I', 'radar_share_cards', browser_role);
                END IF;
              END LOOP;
            END $protect$;
        """)


def downgrade() -> None:
    op.drop_index("ix_radar_card_request", table_name="radar_share_cards")
    op.drop_index("ix_radar_card_token_hash", table_name="radar_share_cards")
    op.drop_table("radar_share_cards")
