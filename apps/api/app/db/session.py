import ssl
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def verified_engine_options(database_url: str) -> dict[str, Any]:
    """Verify PostgreSQL identity for every API, worker and migration connection."""
    url = make_url(database_url)
    if url.drivername != "postgresql+asyncpg":
        return {"url": url}
    cafile = url.query.get("sslrootcert")
    if isinstance(cafile, tuple):
        raise ValueError("database URL must specify at most one trusted CA file")
    context = ssl.create_default_context(cafile=cafile)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    # Python 3.13 adds RFC 5280 "strict" checks by default. Supabase's own root CA
    # ("Supabase Root 2021 CA") omits the keyUsage extension and fails them. Chain
    # validation against the pinned CA, hostname checking and CERT_REQUIRED stay on.
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return {
        "url": url.difference_update_query(["ssl", "sslmode", "sslrootcert"]),
        "connect_args": {"ssl": context},
    }


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def _begin_sqlite_transaction(connection: Connection) -> None:
    connection.exec_driver_sql(
        "BEGIN IMMEDIATE" if connection.get_execution_options().get("sqlite_write") else "BEGIN"
    )


class Database:
    def __init__(self, database_url: str) -> None:
        self.is_local_sqlite = database_url.startswith("sqlite+")
        self.engine: AsyncEngine = create_async_engine(
            **verified_engine_options(database_url),
            pool_pre_ping=True,
            pool_recycle=300,
        )
        if self.is_local_sqlite:
            event.listen(self.engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
            event.listen(self.engine.sync_engine, "begin", _begin_sqlite_transaction)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def initialize(self) -> None:
        if not self.is_local_sqlite:
            return
        from app.db.base import Base

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def ping(self) -> bool:
        async with self.engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
        return bool(result.scalar_one() == 1)

    async def dispose(self) -> None:
        await self.engine.dispose()
