"""Add versioned Content Studio matrices.

Revision ID: 20260930_0023
Revises: 20260927_0022
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260930_0023"
down_revision: str | None = "20260927_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("bundle_key", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=64), nullable=False),
        sa.Column("parent_revision_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("validation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'validated', 'published')",
            name="ck_content_revisions_status",
        ),
        sa.ForeignKeyConstraint(
            ["parent_revision_id"], ["content_revisions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payload_hash", name="uq_content_revisions_payload_hash"),
    )
    op.create_index(
        "ix_content_revisions_bundle_created",
        "content_revisions",
        ["bundle_key", "created_at"],
    )
    op.create_table(
        "content_channels",
        sa.Column("bundle_key", sa.String(length=64), nullable=False),
        sa.Column("active_revision_id", sa.Uuid(), nullable=True),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["active_revision_id"], ["content_revisions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("bundle_key"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO content_channels (
                bundle_key, active_revision_id, generation, updated_at
            ) VALUES (
                'daily-astrology', NULL, 0, CURRENT_TIMESTAMP
            )
            ON CONFLICT (bundle_key) DO NOTHING
            """
        )
    )
    op.create_table(
        "content_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("bundle_key", sa.String(length=64), nullable=False),
        sa.Column("request_key_hash", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("previous_revision_id", sa.Uuid(), nullable=True),
        sa.Column("channel_generation", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action IN ('draft_created', 'validated', 'published', 'rolled_back')",
            name="ck_content_audit_events_action",
        ),
        sa.ForeignKeyConstraint(["revision_id"], ["content_revisions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["previous_revision_id"], ["content_revisions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_key_hash", name="uq_content_audit_request_key_hash"),
    )
    op.create_index(
        "ix_content_audit_bundle_created",
        "content_audit_events",
        ["bundle_key", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION guard_content_revision_history() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'content revisions are append-only';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
               OR NEW.bundle_key IS DISTINCT FROM OLD.bundle_key
               OR NEW.contract_version IS DISTINCT FROM OLD.contract_version
               OR NEW.parent_revision_id IS DISTINCT FROM OLD.parent_revision_id
               OR NEW.payload IS DISTINCT FROM OLD.payload
               OR NEW.payload_hash IS DISTINCT FROM OLD.payload_hash
               OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION 'content revision identity and payload are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_content_revision_history
        BEFORE UPDATE OR DELETE ON content_revisions
        FOR EACH ROW EXECUTE FUNCTION guard_content_revision_history();
        """
    )
    op.execute(
        """
        CREATE FUNCTION guard_content_audit_history() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'content audit events are append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_content_audit_history
        BEFORE UPDATE OR DELETE ON content_audit_events
        FOR EACH ROW EXECUTE FUNCTION guard_content_audit_history();
        """
    )


def downgrade() -> None:
    revision_count = (
        op.get_bind().execute(sa.text("SELECT COUNT(*) FROM content_revisions")).scalar_one()
    )
    if revision_count:
        raise RuntimeError(
            "refusing to drop Content Studio history; use a forward application rollback"
        )
    op.execute("DROP TRIGGER IF EXISTS trg_content_audit_history ON content_audit_events")
    op.execute("DROP FUNCTION IF EXISTS guard_content_audit_history()")
    op.execute("DROP TRIGGER IF EXISTS trg_content_revision_history ON content_revisions")
    op.execute("DROP FUNCTION IF EXISTS guard_content_revision_history()")
    op.drop_index("ix_content_audit_bundle_created", table_name="content_audit_events")
    op.drop_table("content_audit_events")
    op.drop_table("content_channels")
    op.drop_index("ix_content_revisions_bundle_created", table_name="content_revisions")
    op.drop_table("content_revisions")
