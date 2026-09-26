from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.domains.daily.models import DailyNoteRecord
from app.domains.readings.models import ReadingContentProjection, ReadingPurpose
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.repository import SavedNoteRepository


class OwnedDailyNoteReader(Protocol):
    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord: ...


class SavedNoteService:
    def __init__(self, repository: SavedNoteRepository, daily_notes: OwnedDailyNoteReader) -> None:
        self._repository = repository
        self._daily_notes = daily_notes

    async def save(
        self,
        *,
        guest_id: UUID,
        daily_note_id: UUID,
        profile_id: UUID | None = None,
        reading: ReadingContentProjection | None = None,
    ) -> SavedNoteRecord:
        if (profile_id is None) != (reading is None):
            raise ValueError("profile_id and reading must be supplied together")
        if reading is not None and reading.purpose is not ReadingPurpose.DAILY_NOTE:
            raise ValueError("saved daily notes require a daily reading revision")
        note = await self._daily_notes.find_owned(guest_id, daily_note_id)
        snapshot: dict[str, object] = {
            "daily_note_id": str(note.id),
            "note_date": note.note_date.isoformat(),
            "title": note.title,
            "body": note.body,
            "full_body": note.full_body,
            "context_label": note.context_label,
            "content_version": note.content_version,
            "persona_mode": note.persona_mode.value,
            "persona_label": note.persona_label.value,
            "persona_version": note.persona_version,
        }
        return await self._repository.save(
            SavedNoteRecord(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily_note_id,
                note_snapshot=snapshot,
                saved_at=datetime.now(UTC),
                profile_id=profile_id,
                revision_id=reading.revision_id if reading is not None else None,
                reading_snapshot=reading,
            )
        )

    async def list_for_guest(self, guest_id: UUID) -> tuple[SavedNoteRecord, ...]:
        return await self._repository.list_for_guest(guest_id)

    async def unsave(self, *, guest_id: UUID, daily_note_id: UUID) -> bool:
        return await self._repository.delete(guest_id, daily_note_id)
