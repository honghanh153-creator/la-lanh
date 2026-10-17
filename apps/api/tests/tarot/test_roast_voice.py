import re
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotReading,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotVoice,
)
from app.domains.tarot.quality import prose_is_safe
from app.domains.tarot.rewrite import compile_tarot_rewrite_request
from app.domains.tarot.voice import (
    GENTLE_ACTION_FRAMES,
    GENTLE_HEADLINES,
    GENTLE_MEANING_TAILS,
    ROAST_ACTION_FRAMES,
    ROAST_HEADLINES,
    ROAST_MEANING_TAILS,
    SUMMARY_OPENERS,
    roast_allowed,
)
from tests.readings.test_voice import BANNED_WORDS
from tests.tarot.test_api import _guest_headers, tarot_client  # noqa: F401

QUESTIONS = {
    TarotContext.GENERAL: "Chuyện này cần được nhìn từ góc nào trước?",
    TarotContext.RELATIONSHIPS: "Giữa tụi mình, điều gì đáng hỏi thẳng thay vì tiếp tục đoán?",
    TarotContext.WORK: "Mình cần nói rõ điều gì trước khi nhận thêm việc?",
    TarotContext.COMMUNICATION: "Trong cuộc nói chuyện này, điều gì đáng hỏi lại cho rõ?",
    TarotContext.ENERGY: "Điều gì đang tiêu hao nhiều hơn giá trị nó trả lại?",
    TarotContext.SELF_CARE: "Nhu cầu nào của mình đang bị xếp sau mọi người?",
}
NOW = datetime(2026, 10, 11, tzinfo=UTC)
SPREADS = {
    TarotSpread.ONE_CARD: 1,
    TarotSpread.THREE_CARD: 3,
    TarotSpread.FIVE_CARD: 5,
}


def _render(
    spread: TarotSpread,
    context: TarotContext,
    voice: TarotVoice,
    *,
    offset: int = 0,
    question: str | None = None,
) -> TarotReading:
    cards = all_cards()
    card_ids = tuple(cards[(offset + index) % len(cards)].id for index in range(SPREADS[spread]))
    return TarotReadingEngine().render(
        card_ids=card_ids,
        spread=spread,
        context=context,
        question=question or QUESTIONS[context],
        voice=voice,
    )


def _step(action: str) -> str:
    return action.removeprefix("Thử nhé: ")


@pytest.mark.parametrize("spread", tuple(SPREADS))
@pytest.mark.parametrize("context", tuple(TarotContext))
def test_roast_keeps_cards_positions_scenes_and_action_steps(
    spread: TarotSpread, context: TarotContext
) -> None:
    for offset in (0, 17, 41):
        default = _render(spread, context, TarotVoice.PLAYFUL_GROUNDED, offset=offset)
        roast = _render(spread, context, TarotVoice.ROAST, offset=offset)

        assert roast.voice is TarotVoice.ROAST
        assert roast.spread_map == default.spread_map
        assert roast.question_intent == default.question_intent
        assert roast.disclaimer == default.disclaimer
        assert roast.provenance == default.provenance
        assert [(p.key, p.label, p.card) for p in roast.positions] == [
            (p.key, p.label, p.card) for p in default.positions
        ]
        assert roast.headline != default.headline
        assert default.summary in roast.summary or roast.summary == default.summary
        for direct, voiced in zip(default.positions, roast.positions, strict=True):
            assert voiced.everyday_scene == direct.everyday_scene
            assert voiced.reflection_question == direct.reflection_question
            assert voiced.meaning_here.startswith(direct.meaning_here)
            assert (voiced.small_action or "").endswith(_step(direct.small_action or ""))
        # Gates (safety, spread, card facts, summary coverage, plain-language review) ran
        # inside render; re-check the shared safety gate explicitly.
        assert prose_is_safe(roast)


@pytest.mark.parametrize("context", [TarotContext.ENERGY, TarotContext.SELF_CARE])
def test_energy_and_self_care_tarot_only_get_gentle_frames(context: TarotContext) -> None:
    roast = _render(TarotSpread.FIVE_CARD, context, TarotVoice.ROAST)
    sharp = (*ROAST_HEADLINES.values(), *ROAST_MEANING_TAILS.values(), *ROAST_ACTION_FRAMES)
    text = " ".join(
        [roast.headline, roast.summary]
        + [value for p in roast.positions for value in (p.meaning_here, p.small_action or "")]
    )

    assert roast.headline in GENTLE_HEADLINES.values()
    assert not any(line in text for line in sharp)
    assert any(tail in text for tail in GENTLE_MEANING_TAILS.values())
    assert any(frame in text for frame in GENTLE_ACTION_FRAMES)


@pytest.mark.parametrize(
    "question",
    [
        "Mình lo cho sức khỏe của mẹ, nên chuẩn bị gì?",
        "Mình đang rất tuyệt vọng, nên làm gì tiếp?",
        "Sau khi chia tay, mình nên nhìn lại điều gì?",
        "Mình không cảm thấy an toàn ở nhà, nên làm gì?",
        "Ba mình vừa qua đời, mình nên làm gì với cảm xúc này?",
        "Minh lo ve suc khoe cua ba, nen chuan bi gi?",
    ],
)
def test_sensitive_questions_fall_back_to_the_default_voice(question: str) -> None:
    assert not roast_allowed(question)
    engine = TarotReadingEngine()
    assessment = engine.assess_question(question, TarotContext.GENERAL)
    if not assessment.accepted:
        return  # Already redirected by the existing high-stakes question gate.
    default = _render(
        TarotSpread.THREE_CARD,
        TarotContext.GENERAL,
        TarotVoice.PLAYFUL_GROUNDED,
        question=question,
    )
    requested_roast = _render(
        TarotSpread.THREE_CARD, TarotContext.GENERAL, TarotVoice.ROAST, question=question
    )

    assert requested_roast.voice is TarotVoice.PLAYFUL_GROUNDED
    assert requested_roast == default


def test_everyday_questions_and_slow_wording_keep_roast_available() -> None:
    assert roast_allowed("Mình nên từ từ nói chuyện với nhóm thế nào?")
    assert roast_allowed(QUESTIONS[TarotContext.WORK])


def test_roast_copy_avoids_banned_words_and_fits_scan_budget() -> None:
    lines = (
        *ROAST_HEADLINES.values(),
        *GENTLE_HEADLINES.values(),
        *SUMMARY_OPENERS.values(),
        *ROAST_MEANING_TAILS.values(),
        *GENTLE_MEANING_TAILS.values(),
        *ROAST_ACTION_FRAMES,
        *GENTLE_ACTION_FRAMES,
    )
    for line in lines:
        folded = line.casefold()
        assert not any(
            re.search(rf"(?<!\w){re.escape(word)}(?!\w)", folded) for word in BANNED_WORDS
        ), line
        assert not re.search(r"\b(?:người kia|họ) (?:đang )?(?:nghĩ|yêu|thích|muốn)", folded)
    assert all(len(headline.split()) <= 18 for headline in ROAST_HEADLINES.values())
    assert all(len(headline.split()) <= 18 for headline in GENTLE_HEADLINES.values())


def test_roast_reading_is_never_sent_for_provider_rewrite() -> None:
    reading = _render(TarotSpread.THREE_CARD, TarotContext.RELATIONSHIPS, TarotVoice.ROAST)
    session = TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000702"),
        version=4,
        state=TarotSessionState.COMPLETE,
        context=reading.context,
        spread=reading.spread,
        spread_map=reading.spread_map,
        voice=reading.voice,
        origin=TarotOrigin.DIRECT,
        question=reading.question,
        required_cards=3,
        selected_cards=tuple(
            TarotSelectedCard(
                fan_index=index,
                position_key=position.key,
                position_label=position.label,
                card=position.card,
            )
            for index, position in enumerate(reading.positions)
        ),
        reading=reading,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW,
    )

    assert (
        compile_tarot_rewrite_request(
            UUID("70000000-0000-4000-8000-000000000703"),
            session,
            model_version="gpt-6-luna",
            prompt_version="surface-rewrite-v1",
        )
        is None
    )


def _start(client: TestClient, headers: dict[str, str], **extra: str) -> Any:
    body = {
        "context": "work",
        "question": "Mình cần nói rõ điều gì trước khi nhận thêm việc?",
        "spread": "one_card",
        "origin": "direct",
        "idempotency_key": "tarot-roast-start-1234567890",
        **extra,
    }
    return client.post("/v1/tarot/sessions", headers=headers, json=body)


def test_api_roast_voice_is_opt_in_and_stores_effective_voice(
    tarot_client: TestClient,  # noqa: F811
) -> None:
    headers = _guest_headers(tarot_client)
    default = _start(tarot_client, headers, idempotency_key="tarot-roast-default-1234567890")
    roast = _start(tarot_client, headers, voice="roast")
    replay = _start(tarot_client, headers, voice="roast")
    sensitive = _start(
        tarot_client,
        headers,
        voice="roast",
        question="Mình lo cho sức khỏe của mẹ, nên chuẩn bị gì?",
        idempotency_key="tarot-roast-sensitive-1234567890",
    )

    assert default.status_code == roast.status_code == replay.status_code == 201
    assert default.json()["voice"] == "playful_grounded"
    assert roast.json()["voice"] == "roast"
    assert replay.json()["id"] == roast.json()["id"]
    assert sensitive.status_code == 201
    assert sensitive.json()["voice"] == "playful_grounded"
    assert _start(tarot_client, headers, voice="savage").status_code == 422
    # Same idempotency key, different voice: a conflicting replay, not a silent reuse.
    assert _start(tarot_client, headers, voice="default").status_code == 409

    started = cast(dict[str, Any], roast.json())
    selected = tarot_client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 5, "expected_version": started["version"]},
    )
    assert selected.status_code == 200
    reading = selected.json()["reading"]
    assert reading["voice"] == "roast"
    assert (
        reading["positions"][0]["card"]["id"] == selected.json()["selected_cards"][0]["card"]["id"]
    )
