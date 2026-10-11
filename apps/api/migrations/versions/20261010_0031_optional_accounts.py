"""Private optional managed accounts and independent device credentials.

Account data retains the existing guest ID and expires_at clock. No backfill
extends unconsented guests. Roll back the application with auth disabled;
downgrade deliberately preserves all private account data and revocations.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261010_0031"
down_revision: str | None = "20261008_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("subject_id", sa.Uuid(), primary_key=True),
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("masked_email", sa.String(254), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "account_devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "guest_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.guest_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("credential_digest", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("csrf_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_account_devices_expiry", "account_devices", ["expires_at"])
    op.create_index("ix_account_devices_guest", "account_devices", ["guest_id"])
    op.create_table(
        "account_login_challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cookie_digest", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("csrf_digest", sa.LargeBinary(32), nullable=False),
        sa.Column(
            "initiating_guest_id", sa.Uuid(), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE")
        ),
        sa.Column("initiating_credential_digest", sa.LargeBinary(32)),
        sa.Column(
            "target_guest_id", sa.Uuid(), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE")
        ),
        sa.Column("email_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("email_envelope", sa.Text()),
        sa.Column("storage_consent", sa.String(64)),
        sa.Column("subject_id", sa.Uuid()),
        sa.Column("proof_digest", sa.LargeBinary(32)),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts >= 0 AND attempts <= 5", name="ck_account_challenge_attempts"),
    )
    op.create_index("ix_account_challenges_expiry", "account_login_challenges", ["expires_at"])
    op.create_table(
        "account_login_quotas",
        sa.Column("key_digest", sa.LargeBinary(32), primary_key=True),
        sa.Column("used", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_quotas_expiry", "account_login_quotas", ["expires_at"])
    for table in (
        "accounts",
        "account_devices",
        "account_login_challenges",
        "account_login_quotas",
    ):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
        op.execute(f"""
            DO $protect$ DECLARE browser_role text;
            BEGIN
              FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
                  EXECUTE format('REVOKE ALL ON TABLE public.{table} FROM %I', browser_role);
                END IF;
              END LOOP;
            END $protect$;
        """)  # noqa: S608 - fixed table allowlist, no caller input


def downgrade() -> None:
    # Never drop private identity/data or revive pre-link anonymous credentials.
    pass
