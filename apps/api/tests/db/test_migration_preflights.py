from importlib import import_module
from typing import Protocol, cast

import pytest
from sqlalchemy import Connection, create_engine, text


class Migration0012(Protocol):
    def assert_no_duplicate_la_chung_reports(self, connection: Connection) -> None: ...


MIGRATION_0012 = cast(
    Migration0012,
    import_module("migrations.versions.20260907_0012_encrypt_private_snapshots"),
)


def test_la_chung_duplicate_preflight_blocks_without_deleting_rows() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE la_chung_reports (request_id TEXT NOT NULL, reason TEXT NOT NULL)")
        )
        connection.execute(
            text(
                "INSERT INTO la_chung_reports (request_id, reason) "
                "VALUES ('request-1', 'unsafe'), ('request-1', 'unsafe')"
            )
        )

        with pytest.raises(RuntimeError, match="No-Go: duplicate la_chung_reports"):
            MIGRATION_0012.assert_no_duplicate_la_chung_reports(connection)

        assert connection.scalar(text("SELECT COUNT(*) FROM la_chung_reports")) == 2


def test_la_chung_duplicate_preflight_accepts_unique_rows() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE la_chung_reports (request_id TEXT NOT NULL, reason TEXT NOT NULL)")
        )
        connection.execute(
            text(
                "INSERT INTO la_chung_reports (request_id, reason) "
                "VALUES ('request-1', 'unsafe'), ('request-1', 'spam')"
            )
        )

        MIGRATION_0012.assert_no_duplicate_la_chung_reports(connection)
