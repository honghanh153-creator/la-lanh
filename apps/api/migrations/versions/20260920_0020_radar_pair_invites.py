"""Add private consent-first Radar pair invitations.

Revision ID: 20260920_0020
Revises: 20260917_0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_0020"
down_revision: str | None = "20260917_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "radar_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("owner_guest_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_guest_id", sa.Uuid(), nullable=True),
        sa.Column("recipient_label_ciphertext", sa.Text(), nullable=False),
        sa.Column("context", sa.String(length=24), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("consent_version", sa.String(length=64), nullable=True),
        sa.Column("authorization_attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=True),
        sa.Column("token_ciphertext", sa.Text(), nullable=True),
        sa.Column("result_ciphertext", sa.Text(), nullable=True),
        sa.Column("receipt_hash", sa.LargeBinary(length=32), nullable=True),
        sa.Column("receipt_ciphertext", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_radar_capability_hash", "radar_requests", ["token_hash"], unique=True)
    op.create_index("ix_radar_owner_created", "radar_requests", ["principal_id", "created_at"])
    op.create_index("ix_radar_receipt_hash", "radar_requests", ["receipt_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_radar_receipt_hash", table_name="radar_requests")
    op.drop_index("ix_radar_owner_created", table_name="radar_requests")
    op.drop_index("ix_radar_capability_hash", table_name="radar_requests")
    op.drop_table("radar_requests")
