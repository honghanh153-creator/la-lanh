from typing import Protocol
from uuid import UUID

from app.domains.birth.models import BirthSnapshotRecord


class BirthRepository(Protocol):
    async def save_or_replay(
        self, record: BirthSnapshotRecord
    ) -> tuple[BirthSnapshotRecord, bool]: ...

    async def find_current(self, guest_id: UUID) -> BirthSnapshotRecord | None: ...
