"""Tarot privacy canary for the paths beside the framed matrix (Codex #73, non-blocking).

#73 pins framed readings. This file persists the two controls Codex also ran by hand: legacy
readings (brief v2) never carry the question or its private details, and Roast, legacy or
framed, never produces a rewrite request at all.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domains.content_rewrite.models import RewriteSurface
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotReading,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.rewrite import compile_tarot_rewrite_request
from app.infrastructure.generation.privacy import PrivacyMinimiser

NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
ENGINE = TarotReadingEngine()
# Synthetic private details: a person's name and a place, inside an ordinary question.
NAME, PLACE = "Thảo Nhi", "phòng kế toán tầng ba"
QUESTIONS = (
    (f"Mình có nên nói với {NAME} chuyện ở {PLACE} không?", TarotContext.RELATIONSHIPS),
    (
        f"Mình có nên nghỉ ngơi sau khi {NAME} giao thêm việc ở {PLACE} không?",
        TarotContext.SELF_CARE,
    ),
    (f"Mình nên chuẩn bị gì trước khi gặp {NAME} ở {PLACE}?", TarotContext.WORK),
)
CARDS = {
    TarotSpread.ONE_CARD: ("major-sun",),
    TarotSpread.THREE_CARD: ("major-moon", "cups-ace", "wands-3"),
}
DIRECT_VOICES = [voice for voice in TarotVoice if voice is not TarotVoice.ROAST]


def _view(reading: TarotReading, question: str, context: TarotContext) -> TarotSessionView:
    selected = tuple(
        TarotSelectedCard(fan_index=i, position_key=p.key, position_label=p.label, card=p.card)
        for i, p in enumerate(reading.positions)
    )
    return TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000703"), version=4,
        state=TarotSessionState.COMPLETE, context=context, spread=reading.spread,
        spread_map=reading.spread_map, voice=reading.voice, origin=TarotOrigin.DIRECT,
        question=question, required_cards=len(selected), selected_cards=selected,
        reading=reading, created_at=NOW, updated_at=NOW, expires_at=NOW + timedelta(days=29),
    )  # fmt: skip


def _legacy(
    question: str, context: TarotContext, spread: TarotSpread, voice: TarotVoice
) -> TarotReading:
    return ENGINE.render(
        card_ids=CARDS[spread], spread=spread, context=context, question=question, voice=voice
    )


def _framed(question: str, context: TarotContext, voice: TarotVoice) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted, question
    return ENGINE.render(
        card_ids=CARDS[TarotSpread.THREE_CARD], spread=TarotSpread.THREE_CARD,
        spread_map=TarotSpreadMap.THREE_UNBLOCK, context=context, question=question, voice=voice,
        question_intent=assessment.intent, frame=assessment.frame,
    )  # fmt: skip


@pytest.mark.parametrize(("question", "context"), QUESTIONS)
@pytest.mark.parametrize("spread", list(CARDS))
@pytest.mark.parametrize("voice", DIRECT_VOICES)
def test_legacy_payload_never_carries_the_question_or_its_details(
    question: str, context: TarotContext, spread: TarotSpread, voice: TarotVoice
) -> None:
    reading = _legacy(question, context, spread, voice)
    request = compile_tarot_rewrite_request(
        uuid4(), _view(reading, question, context),
        model_version="gpt-6-luna", prompt_version="test",
    )  # fmt: skip
    assert request is not None
    outgoing = PrivacyMinimiser().minimise(RewriteSurface.TAROT, request.safe_payload)
    assert outgoing["meaning_brief"]["version"] == "tarot-meaning-brief-v2"  # type: ignore[index,call-overload]
    for payload in (request.safe_payload, outgoing):
        text = json.dumps(payload, ensure_ascii=False).casefold()
        for canary in (question, NAME, PLACE, "70000000-0000-4000-8000-000000000703"):
            assert canary.casefold() not in text, canary


@pytest.mark.parametrize(("question", "context"), QUESTIONS)
@pytest.mark.parametrize("framed", [False, True])
def test_roast_never_produces_a_rewrite_request(
    question: str, context: TarotContext, framed: bool
) -> None:
    reading = (
        _framed(question, context, TarotVoice.ROAST)
        if framed
        else _legacy(question, context, TarotSpread.THREE_CARD, TarotVoice.ROAST)
    )
    assert reading.voice is TarotVoice.ROAST
    request = compile_tarot_rewrite_request(
        uuid4(), _view(reading, question, context),
        model_version="gpt-6-luna", prompt_version="test",
    )  # fmt: skip
    assert request is None
