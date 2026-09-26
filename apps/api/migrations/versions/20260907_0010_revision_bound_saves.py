"""Bind rich saves/shares to exact revisions and make guest deletion complete.

Revision ID: 20260907_0010
Revises: 20260907_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260907_0010"
down_revision: str | None = "20260907_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("saved_notes", sa.Column("profile_id", sa.Uuid(), nullable=True))
    op.add_column("saved_notes", sa.Column("revision_id", sa.Uuid(), nullable=True))
    op.add_column(
        "saved_notes",
        sa.Column(
            "reading_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_saved_notes_revision_owner",
        "saved_notes",
        "reading_revisions",
        ["revision_id", "guest_id", "profile_id"],
        ["id", "guest_id", "profile_id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_saved_notes_revision_bundle",
        "saved_notes",
        "(revision_id IS NULL AND profile_id IS NULL AND reading_snapshot IS NULL) OR "
        "(revision_id IS NOT NULL AND profile_id IS NOT NULL AND reading_snapshot IS NOT NULL)",
    )

    op.add_column("share_artifacts", sa.Column("profile_id", sa.Uuid(), nullable=True))
    op.add_column("share_artifacts", sa.Column("revision_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_share_artifacts_revision_owner",
        "share_artifacts",
        "reading_revisions",
        ["revision_id", "guest_id", "profile_id"],
        ["id", "guest_id", "profile_id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_share_artifacts_revision_bundle",
        "share_artifacts",
        "(revision_id IS NULL AND profile_id IS NULL) OR "
        "(revision_id IS NOT NULL AND profile_id IS NOT NULL)",
    )

    op.drop_constraint("principals_source_guest_id_fkey", "principals", type_="foreignkey")
    op.create_foreign_key(
        "fk_principals_source_guest",
        "principals",
        "guest_sessions",
        ["source_guest_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_principals_source_guest", "principals", type_="foreignkey")
    op.create_foreign_key(
        "principals_source_guest_id_fkey",
        "principals",
        "guest_sessions",
        ["source_guest_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("ck_share_artifacts_revision_bundle", "share_artifacts", type_="check")
    op.drop_constraint("fk_share_artifacts_revision_owner", "share_artifacts", type_="foreignkey")
    op.drop_column("share_artifacts", "revision_id")
    op.drop_column("share_artifacts", "profile_id")

    op.drop_constraint("ck_saved_notes_revision_bundle", "saved_notes", type_="check")
    op.drop_constraint("fk_saved_notes_revision_owner", "saved_notes", type_="foreignkey")
    op.drop_column("saved_notes", "reading_snapshot")
    op.drop_column("saved_notes", "revision_id")
    op.drop_column("saved_notes", "profile_id")
