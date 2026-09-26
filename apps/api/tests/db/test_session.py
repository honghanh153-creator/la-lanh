from sqlalchemy import text

from app.db.session import Database


async def test_sqlite_enforces_foreign_keys(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'foreign-keys.db'}")
    try:
        async with database.engine.connect() as connection:
            enabled = await connection.scalar(text("PRAGMA foreign_keys"))
        assert enabled == 1
    finally:
        await database.dispose()
