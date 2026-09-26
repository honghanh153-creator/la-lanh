"""Add revocation state and temporal constraints to share artifacts.

Revision ID: 20260902_0005
Revises: 20260901_0003
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_0005"
down_revision: str | None = "20260901_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "share_artifacts",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_share_artifact_expiry_after_creation",
        "share_artifacts",
        "expires_at > created_at",
    )
    op.create_check_constraint(
        "ck_share_artifact_revocation_after_creation",
        "share_artifacts",
        "revoked_at IS NULL OR revoked_at >= created_at",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_share_artifact_revocation_after_creation",
        "share_artifacts",
        type_="check",
    )
    op.drop_constraint(
        "ck_share_artifact_expiry_after_creation",
        "share_artifacts",
        type_="check",
    )
    op.drop_column("share_artifacts", "revoked_at")
