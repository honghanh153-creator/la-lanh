"""Encrypt personalized daily, saved, and share snapshots at rest.

Revision ID: 20260907_0012
Revises: 20260907_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.engine import Connection

revision: str = "20260907_0012"
down_revision: str | None = "20260907_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DUPLICATE_REPORT_QUERY = sa.text(
    """
    SELECT request_id, reason, COUNT(*) AS duplicate_count
    FROM la_chung_reports
    GROUP BY request_id, reason
    HAVING COUNT(*) > 1
    ORDER BY duplicate_count DESC, request_id, reason
    LIMIT 1
    """
)

_OFFLINE_DUPLICATE_GUARD = sa.text(
    """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM la_chung_reports
            GROUP BY request_id, reason
            HAVING COUNT(*) > 1
        ) THEN
            RAISE EXCEPTION USING MESSAGE =
                'No-Go: duplicate la_chung_reports (request_id, reason) rows must be '
                'resolved under the retention policy before migration 20260907_0012';
        END IF;
    END
    $$
    """
)


def assert_no_duplicate_la_chung_reports(connection: Connection) -> None:
    """Block the unique-index build without modifying duplicate report data."""

    duplicate = connection.execute(_DUPLICATE_REPORT_QUERY).mappings().first()
    if duplicate is None:
        return
    raise RuntimeError(
        "No-Go: duplicate la_chung_reports rows exist for "
        f"request_id={duplicate['request_id']}, reason={duplicate['reason']!r}, "
        f"count={duplicate['duplicate_count']}; resolve them under the retention policy "
        "before migration 20260907_0012"
    )


def upgrade() -> None:
    if context.is_offline_mode():
        op.execute(_OFFLINE_DUPLICATE_GUARD)
    else:
        assert_no_duplicate_la_chung_reports(op.get_bind())

    op.add_column("daily_notes", sa.Column("content_ciphertext", sa.Text(), nullable=True))
    op.add_column("saved_notes", sa.Column("snapshot_ciphertext", sa.Text(), nullable=True))
    op.add_column(
        "share_artifacts",
        sa.Column("safe_snapshot_ciphertext", sa.Text(), nullable=True),
    )
    op.create_index(
        "ux_la_chung_reports_request_reason",
        "la_chung_reports",
        ["request_id", "reason"],
        unique=True,
    )

    # Existing plaintext rows intentionally remain readable. Encrypt them only through a
    # key-aware operational backfill; a SQL-only migration cannot safely create envelopes.


def downgrade() -> None:
    for table_name, column_name in (
        ("daily_notes", "content_ciphertext"),
        ("saved_notes", "snapshot_ciphertext"),
        ("share_artifacts", "safe_snapshot_ciphertext"),
    ):
        table = sa.table(table_name, sa.column(column_name))
        encrypted_rows = op.get_bind().scalar(
            sa.select(sa.func.count()).select_from(table).where(table.c[column_name].is_not(None))
        )
        if encrypted_rows:
            raise RuntimeError(
                "key-aware plaintext restoration is required before downgrading "
                "encrypted private snapshots"
            )

    op.drop_index("ux_la_chung_reports_request_reason", table_name="la_chung_reports")
    op.drop_column("share_artifacts", "safe_snapshot_ciphertext")
    op.drop_column("saved_notes", "snapshot_ciphertext")
    op.drop_column("daily_notes", "content_ciphertext")
