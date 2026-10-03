"""Add privacy-minimised content rewrite queue.

Revision ID: 20261003_0024
Revises: 20260930_0023
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261003_0024"
down_revision: str | None = "20260930_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_rewrite_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("generation_key", sa.String(length=64), nullable=False),
        sa.Column("surface", sa.String(length=32), nullable=False),
        sa.Column("owner_namespace", sa.String(length=40), nullable=False),
        sa.Column("owner_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("candidate_variant", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("prompt_version", sa.String(length=80), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("gate_version", sa.String(length=80), nullable=False),
        sa.Column("request_ciphertext", sa.Text(), nullable=False),
        sa.Column("provider_output_ciphertext", sa.Text(), nullable=True),
        sa.Column("output_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("gate_receipt_id", sa.String(length=240), nullable=True),
        sa.Column("deletion_epoch", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_result", sa.String(length=32), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'leased' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) "
            "OR (status <> 'leased' AND lease_token IS NULL AND lease_expires_at IS NULL "
            "AND request_started_at IS NULL)",
            name="ck_content_rewrite_jobs_lease",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND max_attempts BETWEEN 1 AND 3 AND attempt_count <= max_attempts",
            name="ck_content_rewrite_jobs_attempt_bounds",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("generation_key", name="uq_content_rewrite_jobs_generation_key"),
    )
    op.create_index(
        "ix_content_rewrite_jobs_queue",
        "content_rewrite_jobs",
        ["status", "next_attempt_at", "lease_expires_at"],
    )
    op.create_index(
        "ix_content_rewrite_jobs_owner",
        "content_rewrite_jobs",
        ["owner_fingerprint", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_rewrite_jobs_owner", table_name="content_rewrite_jobs")
    op.drop_index("ix_content_rewrite_jobs_queue", table_name="content_rewrite_jobs")
    op.drop_table("content_rewrite_jobs")
