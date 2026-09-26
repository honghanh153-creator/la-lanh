from typing import Protocol
from uuid import UUID

from app.domains.birth.models import BirthSnapshotRecord, BirthSupplement, BirthSupplementStored


class BirthRepository(Protocol):
    async def save_or_replay(
        self, record: BirthSnapshotRecord
    ) -> tuple[BirthSnapshotRecord, bool]: ...

    async def find_current(self, guest_id: UUID) -> BirthSnapshotRecord | None: ...

    async def find_by_input_hash(
        self, guest_id: UUID, input_hash: bytes
    ) -> BirthSnapshotRecord | None: ...

    async def save_supplement(
        self, guest_id: UUID, snapshot: BirthSnapshotRecord | None, supplement: BirthSupplement
    ) -> BirthSnapshotRecord | None: ...

    async def find_supplement(self, guest_id: UUID) -> BirthSupplementStored | None: ...

    async def clear_supplement(
        self, guest_id: UUID, *, remove_time: bool, remove_place: bool
    ) -> BirthSupplementStored: ...
