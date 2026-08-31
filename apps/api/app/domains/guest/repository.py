from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from app.domains.guest.models import CreationMaterial, StoredCreation


class GuestRepository(Protocol):
    async def create_or_replay(self, material: CreationMaterial) -> StoredCreation: ...

    async def find_by_token_hash(
        self, token_hash: bytes, now: datetime, *, touch_until: datetime | None = None
    ) -> StoredCreation | None: ...

    async def delete_by_token_hash(self, token_hash: bytes, now: datetime) -> bool: ...

    async def purge_expired(self, now: datetime, batch_size: int) -> int: ...


RepositoryFactory = Callable[[], GuestRepository]
