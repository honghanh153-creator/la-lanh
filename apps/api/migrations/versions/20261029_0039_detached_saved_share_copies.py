"""Saved notes and share links outlive their Daily note and reading revision (US-23 D2).

The foreign keys from `saved_notes` and `share_artifacts` to `daily_notes` and `reading_revisions`
cascaded a deleted source into the copies. A birth-date correction deletes the old subject but keeps
the copies the person chose to save or share, so the cascades go. The identifier columns
(`daily_note_id`, `revision_id`, `profile_id`) stay, so the unsave key, queued unsaves and revoke by
id keep working. The `guest_id` cascades stay: guest deletion still removes every copy. Paths that
must keep removing copies with their source (birth time/place removal, manual history clear) now
delete them explicitly in application code.

Additive and reversible while nothing is detached: the downgrade refuses to run once any copy has
outlived its source, because the old cascade cannot hold such a row. There is no automatic
downgrade in production.

Revision ID: 20261029_0039
Revises: 20261023_0038
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision: str = "20261029_0039"
down_revision: str | Sequence[str] | None = "20261023_0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COPY_TABLES = ("saved_notes", "share_artifacts")
# Names the constraints had before this migration (PostgreSQL's default for the unnamed daily FK).
DAILY_FK = {table: f"{table}_daily_note_id_fkey" for table in COPY_TABLES}
REVISION_FK = {table: f"fk_{table}_revision_owner" for table in COPY_TABLES}


def _detached(table: str) -> str:
    # ``table`` is one of the fixed COPY_TABLES names, never input.
    return f"""
        SELECT count(*) FROM {table} AS copy
        WHERE NOT EXISTS (SELECT 1 FROM daily_notes AS note WHERE note.id = copy.daily_note_id)
           OR (copy.revision_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM reading_revisions AS rev
                WHERE rev.id = copy.revision_id
                  AND rev.guest_id = copy.guest_id
                  AND rev.profile_id = copy.profile_id))
    """  # noqa: S608


def detached_copies(connection: Connection) -> dict[str, int]:
    """How many copies per table no longer have their Daily note or exact revision."""

    return {table: int(connection.scalar(sa.text(_detached(table))) or 0) for table in COPY_TABLES}


def assert_no_detached_copies(connection: Connection) -> None:
    counts = {table: count for table, count in detached_copies(connection).items() if count}
    if counts:
        detail = ", ".join(f"{table}={count}" for table, count in sorted(counts.items()))
        raise RuntimeError(
            f"No-Go: copies outlive their source ({detail}); the pre-0039 cascade cannot hold "
            "them. Do not downgrade below 20261029_0039; roll forward instead."
        )


def source_foreign_keys(connection: Connection, table: str) -> list[str]:
    """The live names of the copy table's foreign keys to a Daily note or reading revision."""

    names: list[str] = []
    for foreign_key in sa.inspect(connection).get_foreign_keys(table):
        if foreign_key["referred_table"] in {"daily_notes", "reading_revisions"}:
            name = foreign_key.get("name")
            if not name:
                raise RuntimeError(f"No-Go: unnamed source foreign key on {table}")
            names.append(name)
    return names


def upgrade() -> None:
    bind = op.get_bind()
    for table in COPY_TABLES:
        # Read the names from the catalog rather than assuming them, so a database created by an
        # older SQLAlchemy naming rule is handled too. Idempotent: a missing key is already gone.
        for name in source_foreign_keys(bind, table):
            op.drop_constraint(name, table, type_="foreignkey")


def downgrade() -> None:
    # A friendly preflight. PostgreSQL would also refuse ADD FOREIGN KEY over a detached row, but
    # this names the cause and keeps the schema untouched.
    assert_no_detached_copies(op.get_bind())
    for table in COPY_TABLES:
        op.create_foreign_key(
            DAILY_FK[table], table, "daily_notes", ["daily_note_id"], ["id"], ondelete="CASCADE"
        )
        op.create_foreign_key(
            REVISION_FK[table],
            table,
            "reading_revisions",
            ["revision_id", "guest_id", "profile_id"],
            ["id", "guest_id", "profile_id"],
            ondelete="CASCADE",
        )
