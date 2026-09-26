import asyncio
import os

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


async def check_database_tls() -> None:
    database_url = os.environ["LA_LANH_DATABASE_URL"]
    if make_url(database_url).query.get("ssl") != "require":
        raise RuntimeError("database URL does not require TLS")
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            if await connection.scalar(text("SELECT 1")) != 1:
                raise RuntimeError("database liveness check failed")
    finally:
        await engine.dispose()


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
