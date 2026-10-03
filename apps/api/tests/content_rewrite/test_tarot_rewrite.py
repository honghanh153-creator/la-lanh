from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

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
from app.infrastructure.generation.privacy import PrivacyMinimiser

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
