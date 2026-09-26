"""Add consent-first Vong La readiness persistence.

Revision ID: 20260917_0019
Revises: 20260916_0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260917_0019"
down_revision: str | None = "20260916_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "matching_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("display_name_ciphertext", sa.Text(), nullable=False),
        sa.Column("gender_identity", sa.String(length=24), nullable=False),
        sa.Column("intent", sa.String(length=24), nullable=False),
        sa.Column("gender_preference", sa.String(length=24), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=False),
        sa.Column("max_age", sa.Integer(), nullable=False),
        sa.Column("region_code", sa.String(length=64), nullable=False),
        sa.Column("weekly_intent", sa.String(length=24), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("min_age >= 18", name="ck_matching_profiles_min_age"),
        sa.CheckConstraint("max_age <= 120", name="ck_matching_profiles_max_age"),
        sa.CheckConstraint("min_age <= max_age", name="ck_matching_profiles_age_range"),
        sa.CheckConstraint(
            "intent IN ('dating', 'friendship', 'open')", name="ck_matching_profiles_intent"
        ),
        sa.CheckConstraint(
            "gender_identity IN ('woman', 'man', 'nonbinary')",
            name="ck_matching_profiles_gender_identity",
        ),
        sa.CheckConstraint(
            "gender_preference IN ('women', 'men', 'nonbinary', 'everyone')",
            name="ck_matching_profiles_gender_preference",
        ),
        sa.CheckConstraint(
            "weekly_intent IN ('de_noi_chuyen', 'di_cham', 'goc_moi', 'de_la_can')",
            name="ck_matching_profiles_weekly_intent",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("principal_id"),
    )
    op.create_index(
        "ix_matching_profiles_active_region",
        "matching_profiles",
        ["active", "region_code"],
    )
    op.create_table(
        "matching_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_matching_consents_active",
        "matching_consents",
        ["principal_id", "revoked_at"],
    )
    op.create_index(
        "ux_matching_consents_principal_active",
        "matching_consents",
        ["principal_id"],
        unique=True,
        sqlite_where=sa.text("revoked_at IS NULL"),
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_table(
        "matching_verifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('not_started', 'pending', 'pass', 'fail')",
            name="ck_matching_verifications_status",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("principal_id"),
    )


def downgrade() -> None:
    op.drop_table("matching_verifications")
    op.drop_index("ux_matching_consents_principal_active", table_name="matching_consents")
    op.drop_index("ix_matching_consents_active", table_name="matching_consents")
    op.drop_table("matching_consents")
    op.drop_index("ix_matching_profiles_active_region", table_name="matching_profiles")
    op.drop_table("matching_profiles")
