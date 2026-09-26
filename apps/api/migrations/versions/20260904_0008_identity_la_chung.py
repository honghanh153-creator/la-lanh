"""Add owner identity and Lá Chứng lifecycle tables.

Revision ID: 20260904_0008
Revises: 20260904_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0008"
down_revision: str | None = "20260904_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "principals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_guest_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_guest_id"], ["guest_sessions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_guest_id"),
    )
    op.create_table(
        "owner_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_owner_sessions_token_hash", "owner_sessions", ["token_hash"], unique=True)
    op.create_table(
        "la_chung_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_label", sa.String(length=40), nullable=False),
        sa.Column("context", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("bank_version", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("token_ciphertext", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_la_chung_capability_hash", "la_chung_requests", ["token_hash"], unique=True)
    op.create_index(
        "ix_la_chung_principal_created",
        "la_chung_requests",
        ["principal_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "la_chung_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("selections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("identity_mode", sa.String(length=16), nullable=False),
        sa.Column("display_alias", sa.String(length=24), nullable=True),
        sa.Column("idempotency_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("receipt_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("receipt_ciphertext", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["la_chung_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_la_chung_response_request", "la_chung_responses", ["request_id"], unique=True
    )
    op.create_index("ix_la_chung_receipt_hash", "la_chung_responses", ["receipt_hash"], unique=True)
    op.create_index(
        "ix_la_chung_response_idempotency", "la_chung_responses", ["idempotency_hash"], unique=True
    )
    op.create_table(
        "la_chung_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["la_chung_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_la_chung_report_request_created",
        "la_chung_reports",
        ["request_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_la_chung_report_request_created", table_name="la_chung_reports")
    op.drop_table("la_chung_reports")
    op.drop_index("ix_la_chung_response_idempotency", table_name="la_chung_responses")
    op.drop_index("ix_la_chung_receipt_hash", table_name="la_chung_responses")
    op.drop_index("ux_la_chung_response_request", table_name="la_chung_responses")
    op.drop_table("la_chung_responses")
    op.drop_index("ix_la_chung_principal_created", table_name="la_chung_requests")
    op.drop_index("ix_la_chung_capability_hash", table_name="la_chung_requests")
    op.drop_table("la_chung_requests")
    op.drop_index("ix_owner_sessions_token_hash", table_name="owner_sessions")
    op.drop_table("owner_sessions")
    op.drop_table("principals")
