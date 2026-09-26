from datetime import UTC, date, datetime
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
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.service import SavedNoteService

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)


class MemorySavedRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, UUID], SavedNoteRecord] = {}

    async def save(self, record: SavedNoteRecord) -> SavedNoteRecord:
        return self.records.setdefault((record.guest_id, record.daily_note_id), record)

    async def list_for_guest(self, guest_id: UUID) -> tuple[SavedNoteRecord, ...]:
        return tuple(record for record in self.records.values() if record.guest_id == guest_id)

    async def delete(self, guest_id: UUID, daily_note_id: UUID) -> bool:
        return self.records.pop((guest_id, daily_note_id), None) is not None


class OwnedDailyNotes:
    def __init__(self, note: DailyNoteRecord) -> None:
        self.note = note

    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord:
        assert (guest_id, note_id) == (self.note.guest_id, self.note.id)
        return self.note


def _reading(revision_id: UUID, *, hook: str) -> ReadingContentProjection:
    return ReadingContentProjection(
        revision_id=revision_id,
        source=ReadingRevisionSource.DETERMINISTIC,
        mode=PlanMode.FULL_SYNTHESIS,
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        precision=TimePrecision.EXACT,
        sections=ReadingSectionsProjection(
            hook=hook,
            thesis="Bạn vừa muốn gần, vừa cần khoảng riêng.",
            manifestation="Ngoài đời, nhịp này dễ hiện ra khi bạn trì hoãn một câu trả lời.",
            transit=None,
            micro_action="Thử viết câu trả lời nháp rồi để đó mười phút.",
        ),
        evidence=ReadingEvidenceProjection(
            title="Căn cứ trong lá số",
            claims=("Mặt Trăng tam hợp Sao Thủy",),
            framework_disclosure="Chiêm tinh là một khung diễn giải.",
        ),
        disclaimer="Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
        created_at=NOW,
    )


@pytest.mark.asyncio
async def test_saved_note_freezes_first_active_revision_after_a_new_one_becomes_active() -> None:
    guest_id = uuid4()
    profile_id = uuid4()
    note = DailyNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 7),
        title="Legacy title",
        body="Legacy body",
        full_body="Legacy full body",
        context_label="Legacy context",
        content_version="daily-note-v3",
        chart_snapshot_id=uuid4(),
        created_at=NOW,
        persona_mode=PersonaMode.AURA,
        persona_label=PersonaLabel.DEEP,
        source_level=SourceLevel.NATAL_CHART,
    )
    repository = MemorySavedRepository()
    service = SavedNoteService(repository, OwnedDailyNotes(note))
    revision_a = _reading(uuid4(), hook="Bản A phải ở lại.")
    revision_b = _reading(uuid4(), hook="Bản B đang active sau đó.")

    saved_a = await service.save(
        guest_id=guest_id,
        daily_note_id=note.id,
        profile_id=profile_id,
        reading=revision_a,
    )
    replay_after_b = await service.save(
        guest_id=guest_id,
        daily_note_id=note.id,
        profile_id=profile_id,
        reading=revision_b,
    )

    assert saved_a.revision_id == revision_a.revision_id
    assert replay_after_b.revision_id == revision_a.revision_id
    assert replay_after_b.reading_snapshot == revision_a
    assert "provider" not in str(replay_after_b.reading_snapshot.model_dump()).lower()
