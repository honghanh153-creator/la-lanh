from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class Database:
    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )

    async def ping(self) -> bool:
        async with self.engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
        return bool(result.scalar_one() == 1)

    async def dispose(self) -> None:
        await self.engine.dispose()
