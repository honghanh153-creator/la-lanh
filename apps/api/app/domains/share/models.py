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


class ShareLinkStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class ShareLinkSummary:
    """What the owner may see about one of their links: never the token or the snapshot."""

    id: UUID
    format: ShareFormat
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    def status(self, now: datetime) -> ShareLinkStatus:
        if self.revoked_at is not None:
            return ShareLinkStatus.REVOKED
        if self.expires_at <= now:
            return ShareLinkStatus.EXPIRED
        return ShareLinkStatus.ACTIVE
