from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domains.daily.service import DailyNoteService
from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.repository import MoodRepository


class MoodService:
    def __init__(self, repository: MoodRepository, daily_notes: DailyNoteService) -> None:
        self._repository = repository
        self._daily_notes = daily_notes

    async def check_in(
        self, *, guest_id: UUID, daily_note_id: UUID, mood: MoodValue
    ) -> MoodCheckInRecord:
        await self._daily_notes.find_owned(guest_id, daily_note_id)
        return await self._repository.upsert(
            MoodCheckInRecord(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily_note_id,
                mood=mood,
                checked_in_at=datetime.now(UTC),
            )
        )

    async def current(self, *, guest_id: UUID, daily_note_id: UUID) -> MoodCheckInRecord | None:
        await self._daily_notes.find_owned(guest_id, daily_note_id)
        return await self._repository.find(guest_id, daily_note_id)
