from typing import Protocol
from uuid import UUID

from app.domains.daily.models import DailyNoteRecord


class DailyNoteRepository(Protocol):
    async def get_or_create(self, record: DailyNoteRecord) -> DailyNoteRecord: ...

    async def find(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord | None: ...
