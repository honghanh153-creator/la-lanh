from typing import Protocol
from uuid import UUID

from app.domains.mood.models import MoodCheckInRecord


class MoodRepository(Protocol):
    async def upsert(self, record: MoodCheckInRecord) -> MoodCheckInRecord: ...

    async def find(self, guest_id: UUID, daily_note_id: UUID) -> MoodCheckInRecord | None: ...
