"""Create secure guest sessions, consent, and idempotent issuance records.

Revision ID: 20260830_0001
Revises:
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guest_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("csrf_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("onboarding_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_guest_expiry_after_creation"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_guest_sessions_expiry", "guest_sessions", ["expires_at"], unique=False)
    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_consents_guest_purpose",
        "consents",
        ["guest_id", "purpose"],
        unique=True,
    )
    op.create_table(
        "guest_session_creations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("request_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("credential_envelope", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replay_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "replay_expires_at >= created_at", name="ck_guest_creation_replay_window"
        ),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_hash"),
    )
    op.create_index(
        "ix_guest_creation_replay_expiry",
        "guest_session_creations",
        ["replay_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_guest_creation_replay_expiry", table_name="guest_session_creations")
    op.drop_table("guest_session_creations")
    op.drop_index("ix_consents_guest_purpose", table_name="consents")
    op.drop_table("consents")
    op.drop_index("ix_guest_sessions_expiry", table_name="guest_sessions")
    op.drop_table("guest_sessions")
