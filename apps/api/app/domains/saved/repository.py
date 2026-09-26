from typing import Protocol
from uuid import UUID

from app.domains.saved.models import SavedNoteRecord


class SavedNoteRepository(Protocol):
    async def save(self, record: SavedNoteRecord) -> SavedNoteRecord: ...

    async def list_for_guest(self, guest_id: UUID) -> tuple[SavedNoteRecord, ...]: ...

    async def delete(self, guest_id: UUID, daily_note_id: UUID) -> bool: ...
