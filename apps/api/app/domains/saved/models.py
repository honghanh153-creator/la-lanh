from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domains.readings.models import ReadingContentProjection


@dataclass(frozen=True, slots=True)
class SavedNoteRecord:
    id: UUID
    guest_id: UUID
    daily_note_id: UUID
    note_snapshot: dict[str, object]
    saved_at: datetime
    profile_id: UUID | None = None
    revision_id: UUID | None = None
    reading_snapshot: ReadingContentProjection | None = None
