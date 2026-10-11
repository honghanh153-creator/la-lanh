from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_rewrite_session: ContextVar[tuple[async_sessionmaker[AsyncSession], AsyncSession] | None] = (
    ContextVar("rewrite_session", default=None)
)


@asynccontextmanager
async def rewrite_session(
    sessions: async_sessionmaker[AsyncSession], *, transaction: bool = False
) -> AsyncIterator[AsyncSession]:
    """Borrow the worker's fenced transaction; never commit a projection separately."""
    current = _rewrite_session.get()
    if current is not None:
        if current[0] is not sessions:
            raise RuntimeError("rewrite projection crossed database session factories")
        yield current[1]
        return
    async with sessions() as session:
        if transaction:
            async with session.begin():
                yield session
        else:
            yield session


@asynccontextmanager
async def bind_rewrite_session(
    sessions: async_sessionmaker[AsyncSession], session: AsyncSession
) -> AsyncIterator[None]:
    token = _rewrite_session.set((sessions, session))
    try:
        yield
    finally:
        _rewrite_session.reset(token)
