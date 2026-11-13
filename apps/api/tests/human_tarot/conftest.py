from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.db.session import Database


@pytest.fixture
async def database(tmp_path: Any) -> AsyncIterator[Database]:
    # A file database: each session gets its own connection, so BEGIN IMMEDIATE really
    # serializes concurrent writers the way the account transaction relies on.
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'human-tarot.db'}")
    await db.initialize()
    try:
        yield db
    finally:
        await db.dispose()
