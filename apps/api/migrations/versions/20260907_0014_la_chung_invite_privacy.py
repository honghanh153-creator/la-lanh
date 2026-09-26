"""Add idempotent invite creation and encrypted recipient labels.

Revision ID: 20260907_0014
Revises: 20260907_0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0014"
down_revision: str | None = "20260907_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "la_chung_requests",
        sa.Column("recipient_label_ciphertext", sa.Text(), nullable=True),
    )
    op.add_column(
        "la_chung_requests",
        sa.Column("idempotency_hash", sa.LargeBinary(length=32), nullable=True),
    )
    op.add_column(
        "la_chung_requests",
        sa.Column("draft_hash", sa.LargeBinary(length=32), nullable=True),
    )
    op.alter_column(
        "la_chung_requests",
        "recipient_label",
        existing_type=sa.String(length=40),
        nullable=True,
    )
    op.create_index(
        "ux_la_chung_request_idempotency_hash",
        "la_chung_requests",
        ["idempotency_hash"],
        unique=True,
    )

    # Existing labels intentionally remain in the compatibility column. A SQL-only
    # migration has no envelope key and cannot safely bind ciphertext to request-ID AAD.


def downgrade() -> None:
    request = sa.table(
        "la_chung_requests",
        sa.column("recipient_label"),
        sa.column("recipient_label_ciphertext"),
    )
    encrypted_without_plaintext = op.get_bind().scalar(
        sa.select(sa.func.count())
        .select_from(request)
        .where(
            request.c.recipient_label_ciphertext.is_not(None),
            request.c.recipient_label.is_(None),
        )
    )
    if encrypted_without_plaintext:
        raise RuntimeError("key-aware recipient-label restoration is required before downgrade")

    op.drop_index("ux_la_chung_request_idempotency_hash", table_name="la_chung_requests")
    op.alter_column(
        "la_chung_requests",
        "recipient_label",
        existing_type=sa.String(length=40),
        nullable=False,
    )
    op.drop_column("la_chung_requests", "draft_hash")
    op.drop_column("la_chung_requests", "idempotency_hash")
    op.drop_column("la_chung_requests", "recipient_label_ciphertext")
