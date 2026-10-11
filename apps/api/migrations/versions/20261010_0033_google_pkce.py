"""Add encrypted, short-lived Google PKCE proof to private login challenges.

Revision ID: 20261010_0033
Revises: 20261010_0032
Rollback is application flags-off; never remove live account/session data.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261010_0033"
down_revision: str | None = "20261010_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("account_login_challenges", sa.Column("oauth_verifier_envelope", sa.Text()))
    op.add_column(
        "account_login_challenges",
        sa.Column("login_provider", sa.String(16), nullable=False, server_default="email"),
    )


def downgrade() -> None:
    pass
