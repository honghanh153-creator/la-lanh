import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.domains.daily.models import DailyNoteRecord
from app.domains.readings.models import PlanMode, ReadingContentProjection, ReadingPurpose
from app.domains.share.errors import ShareArtifactUnavailable
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.repository import ShareArtifactRepository

SHARE_ARTIFACT_TTL = timedelta(days=14)
CAPABILITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


class OwnedDailyNoteReader(Protocol):
    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord: ...


class ShareArtifactService:
    def __init__(
        self, repository: ShareArtifactRepository, daily_notes: OwnedDailyNoteReader
    ) -> None:
        self._repository = repository
        self._daily_notes = daily_notes

    async def create(
        self,
        *,
        guest_id: UUID,
        daily_note_id: UUID,
        format: ShareFormat,
        profile_id: UUID | None = None,
        reading: ReadingContentProjection | None = None,
        now: datetime | None = None,
    ) -> tuple[ShareArtifactRecord, str]:
        if (profile_id is None) != (reading is None):
            raise ValueError("profile_id and reading must be supplied together")
        if reading is not None and reading.purpose is not ReadingPurpose.DAILY_NOTE:
            raise ValueError("daily share artifacts require a daily reading revision")
        note = await self._daily_notes.find_owned(guest_id, daily_note_id)
        token = secrets.token_urlsafe(32)
        issued_at = now or datetime.now(UTC)
        is_vibe = reading is None or reading.mode is PlanMode.VIBE_FALLBACK
        safe_snapshot = SafeShareSnapshot(
            title=reading.sections.hook if reading is not None else note.title,
            body=reading.sections.manifestation if reading is not None else note.body,
            context_label=("Vibe · một lớp" if is_vibe else "Aura · bản đọc tổng hòa"),
            content_version=note.content_version,
            persona_mode="vibe" if is_vibe else "aura",
            persona_label=note.persona_label.value,
            persona_version=note.persona_version,
            watermark="Lá Lành",
        )
        record = await self._repository.create(
            ShareArtifactRecord(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily_note_id,
                profile_id=profile_id,
                revision_id=reading.revision_id if reading is not None else None,
                token_hash=hashlib.sha256(token.encode()).digest(),
                safe_snapshot=safe_snapshot,
                format=format,
                created_at=issued_at,
                expires_at=issued_at + SHARE_ARTIFACT_TTL,
            )
        )
        return record, token

    async def preview(
        self, token: str, *, now: datetime | None = None
    ) -> ShareArtifactRecord | None:
        if CAPABILITY_PATTERN.fullmatch(token) is None:
            return None
        record = await self._repository.find_by_token_hash(hashlib.sha256(token.encode()).digest())
        current = now or datetime.now(UTC)
        if record is None or record.revoked_at is not None or record.expires_at <= current:
            return None
        return record

    async def revoke(
        self, *, guest_id: UUID, artifact_id: UUID, now: datetime | None = None
    ) -> None:
        revoked = await self._repository.revoke_owned(
            guest_id,
            artifact_id,
            now or datetime.now(UTC),
        )
        if not revoked:
            raise ShareArtifactUnavailable
