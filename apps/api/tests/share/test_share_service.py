import hashlib
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domains.astro.models import TimePrecision, Tradition
from app.domains.daily.models import DailyNoteRecord, PersonaLabel, PersonaMode, SourceLevel
from app.domains.readings.models import (
    PlanMode,
    ReadingContentProjection,
    ReadingEvidenceProjection,
    ReadingPurpose,
    ReadingRevisionSource,
    ReadingSectionsProjection,
)
from app.domains.share.errors import ShareArtifactUnavailable
from app.domains.share.models import ShareArtifactRecord, ShareFormat
from app.domains.share.service import SHARE_ARTIFACT_TTL, ShareArtifactService


class MemoryShareRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, ShareArtifactRecord] = {}

    async def create(self, record: ShareArtifactRecord) -> ShareArtifactRecord:
        self.records[record.id] = record
        return record

    async def find_by_token_hash(self, token_hash: bytes) -> ShareArtifactRecord | None:
        return next(
            (record for record in self.records.values() if record.token_hash == token_hash),
            None,
        )

    async def revoke_owned(self, guest_id: UUID, artifact_id: UUID, revoked_at: datetime) -> bool:
        record = self.records.get(artifact_id)
        if record is None or record.guest_id != guest_id:
            return False
        self.records[artifact_id] = replace(record, revoked_at=revoked_at)
        return True


class OwnedDailyNotes:
    def __init__(self, note: DailyNoteRecord) -> None:
        self.note = note

    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord:
        assert guest_id == self.note.guest_id
        assert note_id == self.note.id
        return self.note


def _reading(revision_id: UUID) -> ReadingContentProjection:
    return ReadingContentProjection(
        revision_id=revision_id,
        source=ReadingRevisionSource.DETERMINISTIC,
        mode=PlanMode.FULL_SYNTHESIS,
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        precision=TimePrecision.EXACT,
        sections=ReadingSectionsProjection(
            hook="Đây là hook riêng của revision A.",
            thesis="Bạn vừa muốn gần, vừa cần khoảng riêng.",
            manifestation="Ngoài đời, nhịp này dễ lộ ra ở cách bạn trả lời tin nhắn.",
            transit=None,
            micro_action="Thử để câu trả lời nháp nghỉ mười phút.",
        ),
        evidence=ReadingEvidenceProjection(
            title="Căn cứ trong lá số",
            claims=("PRIVATE_EVIDENCE_CANARY",),
            framework_disclosure="PRIVATE_FRAMEWORK_CANARY",
        ),
        disclaimer="Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
        created_at=datetime(2026, 9, 2, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_expired_and_revoked_tokens_are_equally_unavailable() -> None:
    guest_id = uuid4()
    note = DailyNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 2),
        title="Safe title",
        body="Safe body",
        full_body="Safe full body",
        context_label="Safe context",
        content_version="daily-note-v1",
        persona_mode=PersonaMode.VIBE,
        persona_label=PersonaLabel.GROUNDED,
        persona_version="persona-v1",
        source_level=SourceLevel.DATE_ONLY_SUN,
        astrology_source_version="swisseph-v1",
        fallback_used=False,
        fallback_reason=None,
        chart_snapshot_id=uuid4(),
        created_at=datetime(2026, 9, 2, tzinfo=UTC),
    )
    repository = MemoryShareRepository()
    service = ShareArtifactService(repository, OwnedDailyNotes(note))
    issued_at = datetime(2026, 9, 2, 8, tzinfo=UTC)

    artifact, token = await service.create(
        guest_id=guest_id,
        daily_note_id=note.id,
        format=ShareFormat.STORY_9_16,
        now=issued_at,
    )

    assert artifact.expires_at == issued_at + SHARE_ARTIFACT_TTL
    assert artifact.token_hash == hashlib.sha256(token.encode()).digest()
    assert token.encode() not in artifact.token_hash
    assert await service.preview(token, now=artifact.expires_at - timedelta(microseconds=1))
    assert await service.preview(token, now=artifact.expires_at) is None

    await service.revoke(guest_id=guest_id, artifact_id=artifact.id, now=issued_at)
    assert await service.preview(token, now=issued_at) is None
    with pytest.raises(ShareArtifactUnavailable):
        await service.revoke(guest_id=uuid4(), artifact_id=artifact.id, now=issued_at)


@pytest.mark.asyncio
async def test_share_freezes_compact_revision_allowlist_without_private_evidence() -> None:
    guest_id = uuid4()
    profile_id = uuid4()
    note = DailyNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 2),
        title="Legacy title",
        body="Legacy body",
        full_body="PRIVATE_FULL_BODY_CANARY",
        context_label="Legacy context",
        content_version="daily-note-v3",
        chart_snapshot_id=uuid4(),
        created_at=datetime(2026, 9, 2, tzinfo=UTC),
    )
    reading = _reading(uuid4())
    service = ShareArtifactService(MemoryShareRepository(), OwnedDailyNotes(note))

    artifact, token = await service.create(
        guest_id=guest_id,
        daily_note_id=note.id,
        format=ShareFormat.STORY_9_16,
        profile_id=profile_id,
        reading=reading,
    )
    preview = await service.preview(token)

    assert preview is not None
    assert artifact.revision_id == reading.revision_id
    assert artifact.safe_snapshot.title == reading.sections.hook
    serialized = str(artifact.safe_snapshot)
    assert "PRIVATE_EVIDENCE_CANARY" not in serialized
    assert "PRIVATE_FRAMEWORK_CANARY" not in serialized
    assert "PRIVATE_FULL_BODY_CANARY" not in serialized
