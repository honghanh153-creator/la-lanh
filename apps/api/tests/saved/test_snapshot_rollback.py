"""A saved note written by this release must stay readable by the release before it (#634).

The earlier reader validates the stored reading with ``extra="forbid"``, so one unknown key in
the snapshot breaks the saved list and the data export after a rollback. Synthetic data only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.domains.astro.models import TimePrecision, Tradition
from app.domains.readings.lighter_action import lighter_experiment_for
from app.domains.readings.models import (
    LighterActionProjection,
    PlanMode,
    ReadingContentProjection,
    ReadingEvidenceProjection,
    ReadingPurpose,
    ReadingRevisionSource,
    ReadingSectionsProjection,
)
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.postgres import _encrypt_snapshot, _snapshot_context
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 11, 17, 12, tzinfo=UTC)
LIGHTER = "Uống một cốc nước rồi ngồi yên hai phút."


class ReleasedReadingSnapshot(BaseModel):
    """The top-level reading fields of the release before the lighter action, strict as it is."""

    model_config = ConfigDict(extra="forbid")

    revision_id: str
    source: str
    mode: str
    purpose: str
    tradition: str
    precision: str
    sections: dict[str, object]
    evidence: dict[str, object]
    disclaimer: str
    created_at: str
    experiment: dict[str, object] | None = None


def _reading(*, lighter: bool) -> ReadingContentProjection:
    revision_id = uuid4()
    return ReadingContentProjection(
        revision_id=revision_id,
        source=ReadingRevisionSource.DETERMINISTIC,
        mode=PlanMode.FULL_SYNTHESIS,
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        precision=TimePrecision.EXACT,
        sections=ReadingSectionsProjection(
            hook="Tiêu đề thử.",
            thesis="Ý chính thử.",
            manifestation="Cảnh ngoài đời thử.",
            micro_action="Viết một dòng nháp.",
        ),
        evidence=ReadingEvidenceProjection(
            title="Căn cứ", claims=("Một căn cứ thử",), framework_disclosure="Khung diễn giải."
        ),
        disclaimer="Quyền quyết định vẫn ở bạn.",
        created_at=NOW,
        lighter_action=(
            LighterActionProjection(
                action=LIGHTER, experiment=lighter_experiment_for(revision_id, LIGHTER)
            )
            if lighter
            else None
        ),
    )


def _stored_reading(reading: ReadingContentProjection) -> dict[str, object]:
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32))
    record = SavedNoteRecord(
        id=uuid4(),
        guest_id=uuid4(),
        daily_note_id=uuid4(),
        note_snapshot={"title": "Ghi chú thử"},
        saved_at=NOW,
        profile_id=uuid4(),
        revision_id=reading.revision_id,
        reading_snapshot=reading,
    )
    payload = json.loads(
        envelope.decrypt(_encrypt_snapshot(record, envelope), context=_snapshot_context(record.id))
    )
    stored = payload["reading_snapshot"]
    assert isinstance(stored, dict)
    return stored


def test_snapshot_without_a_lighter_action_reads_under_the_released_contract() -> None:
    stored = _stored_reading(_reading(lighter=False))
    assert "lighter_action" not in stored
    ReleasedReadingSnapshot.model_validate(stored)


def test_snapshot_with_an_approved_lighter_action_still_reads_after_rollback() -> None:
    stored = _stored_reading(_reading(lighter=True))
    assert "lighter_action" not in stored
    assert LIGHTER not in json.dumps(stored, ensure_ascii=False)
    ReleasedReadingSnapshot.model_validate(stored)
    # This release reads it back as a saved copy without the live offer.
    assert ReadingContentProjection.model_validate(stored).lighter_action is None
