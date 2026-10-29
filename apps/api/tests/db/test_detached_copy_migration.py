"""Migration 20261029_0039: copies stop cascading from their source; the downgrade refuses once
any copy is detached. SQLite stands in for the catalog; PostgreSQL evidence is the gated probe in
tests/birth/test_postgres_date_correction_probe.py."""

from collections.abc import Iterator
from importlib import import_module
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import Connection, create_engine, text

MIGRATION: Any = import_module("migrations.versions.20261029_0039_detached_saved_share_copies")

_PRE_0039 = (
    "CREATE TABLE guest_sessions (id TEXT PRIMARY KEY)",
    "CREATE TABLE daily_notes (id TEXT PRIMARY KEY)",
    "CREATE TABLE reading_revisions (id TEXT, guest_id TEXT, profile_id TEXT, "
    "UNIQUE (id, guest_id, profile_id))",
    *(
        f"CREATE TABLE {table} (id TEXT PRIMARY KEY, guest_id TEXT NOT NULL, "
        "daily_note_id TEXT NOT NULL, profile_id TEXT, revision_id TEXT, "
        "FOREIGN KEY (guest_id) REFERENCES guest_sessions (id) ON DELETE CASCADE, "
        # SQLite reflects a constraint name only when the clause sits on one line.
        f"CONSTRAINT {table}_daily_note_id_fkey FOREIGN KEY (daily_note_id) "
        "REFERENCES daily_notes (id) ON DELETE CASCADE, "
        f"CONSTRAINT fk_{table}_revision_owner FOREIGN KEY (revision_id, guest_id, profile_id) "
        "REFERENCES reading_revisions (id, guest_id, profile_id) ON DELETE CASCADE)"
        for table in ("saved_notes", "share_artifacts")
    ),
)


@pytest.fixture
def connection() -> Iterator[Connection]:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        for statement in _PRE_0039:
            connection.execute(text(statement))
        connection.execute(text("INSERT INTO guest_sessions VALUES ('g')"))
        connection.execute(text("INSERT INTO daily_notes VALUES ('n')"))
        connection.execute(text("INSERT INTO reading_revisions VALUES ('r', 'g', 'p')"))
        for table in MIGRATION.COPY_TABLES:
            connection.execute(text(f"INSERT INTO {table} VALUES ('c', 'g', 'n', 'p', 'r')"))  # noqa: S608
        yield connection


def test_upgrade_drops_only_the_source_cascades_found_in_the_catalog(
    connection: Connection,
) -> None:
    with (
        patch.object(MIGRATION.op, "get_bind", return_value=connection),
        patch.object(MIGRATION.op, "drop_constraint") as drop,
    ):
        MIGRATION.upgrade()
    dropped = {(call.args[0], call.args[1]) for call in drop.call_args_list}
    assert dropped == {
        ("saved_notes_daily_note_id_fkey", "saved_notes"),
        ("fk_saved_notes_revision_owner", "saved_notes"),
        ("share_artifacts_daily_note_id_fkey", "share_artifacts"),
        ("fk_share_artifacts_revision_owner", "share_artifacts"),
    }
    assert all(call.kwargs["type_"] == "foreignkey" for call in drop.call_args_list)


def test_attached_copies_count_as_attached(connection: Connection) -> None:
    assert MIGRATION.detached_copies(connection) == {"saved_notes": 0, "share_artifacts": 0}
    MIGRATION.assert_no_detached_copies(connection)


def test_downgrade_restores_the_cascades_while_nothing_is_detached(
    connection: Connection,
) -> None:
    with (
        patch.object(MIGRATION.op, "get_bind", return_value=connection),
        patch.object(MIGRATION.op, "create_foreign_key") as create,
    ):
        MIGRATION.downgrade()
    assert {call.args[0] for call in create.call_args_list} == {
        "saved_notes_daily_note_id_fkey",
        "fk_saved_notes_revision_owner",
        "share_artifacts_daily_note_id_fkey",
        "fk_share_artifacts_revision_owner",
    }
    assert all(call.kwargs["ondelete"] == "CASCADE" for call in create.call_args_list)


@pytest.mark.parametrize("detach", ["daily", "revision"])
def test_downgrade_refuses_while_any_copy_is_detached(connection: Connection, detach: str) -> None:
    connection.execute(text("PRAGMA foreign_keys=OFF"))  # the post-0039 schema has no such FK
    if detach == "daily":
        connection.execute(text("DELETE FROM daily_notes"))
    else:
        connection.execute(text("DELETE FROM reading_revisions"))
    assert MIGRATION.detached_copies(connection) == {"saved_notes": 1, "share_artifacts": 1}
    with (
        patch.object(MIGRATION.op, "get_bind", return_value=connection),
        patch.object(MIGRATION.op, "create_foreign_key") as create,
        pytest.raises(RuntimeError, match="No-Go: copies outlive their source"),
    ):
        MIGRATION.downgrade()
    create.assert_not_called()
    for table in MIGRATION.COPY_TABLES:
        assert connection.scalar(text(f"SELECT COUNT(*) FROM {table}")) == 1  # noqa: S608


def test_a_revisionless_copy_needs_only_its_daily_note(connection: Connection) -> None:
    connection.execute(text("PRAGMA foreign_keys=OFF"))
    connection.execute(text("UPDATE saved_notes SET revision_id = NULL, profile_id = NULL"))
    connection.execute(text("DELETE FROM reading_revisions"))
    assert MIGRATION.detached_copies(connection) == {"saved_notes": 0, "share_artifacts": 1}
