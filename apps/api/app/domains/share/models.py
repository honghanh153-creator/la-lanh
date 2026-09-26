from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ShareFormat(StrEnum):
    STORY_9_16 = "story_9_16"
    SQUARE_1_1 = "square_1_1"


@dataclass(frozen=True, slots=True)
class SafeShareSnapshot:
    title: str
    body: str
    context_label: str
    content_version: str
    persona_mode: str
    persona_label: str
    persona_version: str
    watermark: str


@dataclass(frozen=True, slots=True)
class ShareArtifactRecord:
    id: UUID
    guest_id: UUID
    daily_note_id: UUID
    token_hash: bytes
    safe_snapshot: SafeShareSnapshot
    format: ShareFormat
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    profile_id: UUID | None = None
    revision_id: UUID | None = None
