from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

import pytest
from pydantic import JsonValue

from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotVoice,
)
from app.domains.tarot.rewrite import (
    TAROT_REWRITE_RENDERER_VERSION,
    compile_tarot_rewrite_request,
    rewrite_tarot_reading,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser, UnsafeRewritePayload

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _session() -> TarotSessionView:
    reading = TarotReadingEngine().render(
        card_ids=("major-star", "cups-5", "wands-ace"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình cần nhìn rõ điều gì trước khi nói chuyện tiếp?",
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    selected = tuple(
        TarotSelectedCard(
            fan_index=index,
            position_key=position.key,
            position_label=position.label,
            card=position.card,
        )
        for index, position in enumerate(reading.positions)
    )
    return TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000701"),
        version=4,
        state=TarotSessionState.COMPLETE,
        context=reading.context,
        spread=reading.spread,
        spread_map=reading.spread_map,
        voice=reading.voice,
        origin=TarotOrigin.DIRECT,
        question=reading.question,
        required_cards=3,
        selected_cards=selected,
        reading=reading,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(days=29),
    )


def _output(session: TarotSessionView) -> dict[str, JsonValue]:
    assert session.reading is not None
    return {
        "headline": "Ba lá đang chỉ vào một việc cần nói rõ.",
        "position_readings": [
            {
                "position_key": position.key,
                "reading": f"{position.card.title_vi}: {position.meaning_here}",
            }
            for position in session.reading.positions
        ],
        "synthesis": session.reading.summary,
        "closing_question": "Bạn muốn kiểm tra điều nào bằng một cuộc nói chuyện thật?",
    }


def test_tarot_compiler_never_forwards_the_raw_question() -> None:
    session = _session()

    request = compile_tarot_rewrite_request(
        UUID("20000000-0000-4000-8000-000000000701"),
        session,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    assert request is not None
    assert request.key.surface.value == "tarot"
    serialized = json.dumps(request.safe_payload, ensure_ascii=False)
    assert session.question not in serialized
    assert "Mình cần nhìn rõ điều gì trước khi nói chuyện tiếp?" not in serialized
    safe = PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    assert len(cast(list[JsonValue], safe["positions"])) == 3


def test_tarot_rewrite_preserves_cards_positions_and_private_question() -> None:
    session = _session()
    assert session.reading is not None

    candidate = rewrite_tarot_reading(session.reading, _output(session))

    assert candidate is not None
    assert candidate.question == session.reading.question
    assert [position.key for position in candidate.positions] == [
        position.key for position in session.reading.positions
    ]
    assert [position.card.id for position in candidate.positions] == [
        position.card.id for position in session.reading.positions
    ]
    assert candidate.provenance.renderer_version == TAROT_REWRITE_RENDERER_VERSION


def test_tarot_rewrite_rejects_missing_card_attribution_and_duplicate_positions() -> None:
    session = _session()
    assert session.reading is not None
    output = _output(session)
    positions = output["position_readings"]
    assert isinstance(positions, list)
    assert isinstance(positions[0], dict)
    positions[0]["reading"] = "Có một điều cần được nhìn lại."

    assert rewrite_tarot_reading(session.reading, output) is None


@pytest.mark.parametrize("field", ["headline", "synthesis", "closing_question"])
@pytest.mark.parametrize(
    "claim",
    [
        "Người kia chắc chắn yêu bạn, bạn muốn hỏi gì?",
        "Hãy ngừng thuốc để thấy rõ cảm xúc, bạn muốn hỏi gì?",
        "Ngày mai bạn sẽ nhận được lời tỏ tình, bạn muốn hỏi gì?",
    ],
)
def test_rewrite_rejects_unsafe_claims_in_every_summary_field(field: str, claim: str) -> None:
    session = _session()
    assert session.reading is not None
    output = _output(session)
    output[field] = f"{output[field]} {claim}"
    assert rewrite_tarot_reading(session.reading, output) is None


@pytest.mark.parametrize("field", ["position", "headline", "synthesis", "closing_question"])
@pytest.mark.parametrize(
    "claim",
    [
        "Người kia nhớ bạn và đang chờ bạn nhắn lại.",
        "Bình tĩnh nói rõ cảm xúc để thao túng người kia.",
    ],
)
def test_rewrite_cannot_append_mindreading_or_manipulation_to_supported_meaning(
    field: str, claim: str
) -> None:
    session = _session()
    assert session.reading is not None
    output = _output(session)
    if field == "position":
        positions = output["position_readings"]
        assert isinstance(positions, list) and isinstance(positions[0], dict)
        positions[0]["reading"] = f"{positions[0]['reading']} {claim}"
    else:
        output[field] = f"{output[field]} {claim}" + (
            " Bạn muốn hỏi gì?" if field == "closing_question" else ""
        )
    assert rewrite_tarot_reading(session.reading, output) is None


def test_rewrite_rejects_attributing_an_unselected_card() -> None:
    session = _session()
    assert session.reading is not None
    output = _output(session)
    output["synthesis"] = f"{output['synthesis']} The Tower cho thấy hai người cần dừng lại."
    assert rewrite_tarot_reading(session.reading, output) is None


def test_compiler_includes_a_closed_contextual_meaning_brief() -> None:
    session = _session()
    assert session.reading is not None
    request = compile_tarot_rewrite_request(
        UUID("20000000-0000-4000-8000-000000000701"),
        session,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v3",
    )
    assert request is not None
    brief = request.safe_payload.get("meaning_brief")
    assert isinstance(brief, dict)
    assert brief["topic"] == "relationships"
    assert brief["version"] == "tarot-meaning-brief-v2"
    assert brief["local_summary"] == session.reading.summary
    assert isinstance(brief["goals"], list) and brief["goals"]
    assert session.question not in json.dumps(brief, ensure_ascii=False)
    PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)


@pytest.mark.parametrize("version", ["tarot-meaning-brief-v1", "tarot-meaning-brief-v2"])
def test_privacy_contract_accepts_current_and_legacy_queued_meaning_brief(version: str) -> None:
    request = compile_tarot_rewrite_request(
        UUID("20000000-0000-4000-8000-000000000701"),
        _session(),
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v3",
    )
    assert request is not None
    brief = request.safe_payload["meaning_brief"]
    assert isinstance(brief, dict)
    payload = {**request.safe_payload, "meaning_brief": {**brief, "version": version}}
    safe = PrivacyMinimiser().minimise(request.key.surface, payload)
    assert isinstance(safe["meaning_brief"], dict)
    assert safe["meaning_brief"]["version"] == version
    for alteration in ({"version": "tarot-meaning-brief-v999"}, {"raw_question": "private"}):
        with pytest.raises(UnsafeRewritePayload):
            PrivacyMinimiser().minimise(
                request.key.surface,
                {**payload, "meaning_brief": {**brief, "version": version, **alteration}},
            )


@pytest.mark.parametrize("field", ["position", "headline", "synthesis", "closing_question"])
def test_rewrite_rejects_negating_a_positive_card_meaning(field: str) -> None:
    session = _session()
    baseline = TarotReadingEngine().render(
        card_ids=("cups-2", "major-tower", "major-hanged-man"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói gì để xin lỗi sau khi lỡ hẹn?",
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    output = _output(session.model_copy(update={"reading": baseline}))
    positions = output["position_readings"]
    assert isinstance(positions, list) and isinstance(positions[0], dict)
    contradiction = "Hai Cốc: Bạn không cần lắng nghe và đáp lại người kia khi nói lời xin lỗi"
    if field == "position":
        positions[0]["reading"] = f"{contradiction}."
    else:
        output[field] = f"{contradiction}?" if field == "closing_question" else f"{contradiction}."
    assert rewrite_tarot_reading(baseline, output) is None
