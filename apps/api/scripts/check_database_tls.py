import asyncio
import os

from sqlalchemy import text

from app.db.session import Database


async def check_database_tls() -> None:
    database_url = os.environ["LA_LANH_DATABASE_URL"]
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("database TLS check requires PostgreSQL")
    database = Database(database_url)
    try:
        async with database.engine.connect() as connection:
            if await connection.scalar(text("SELECT 1")) != 1:
                raise RuntimeError("database liveness check failed")
    finally:
        await database.dispose()


def main() -> int:
    try:
        asyncio.run(check_database_tls())
    except Exception as error:
        print(f"database-tls-connect-failed:{type(error).__name__}")
        return 1
    print("database-tls-connect-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
