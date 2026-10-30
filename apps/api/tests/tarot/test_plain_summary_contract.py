"""Codex r54 on #115: the plain-summary contract through the real rewrite and compile paths.

1. Synthesis coverage follows the framed summary's roles (every detailed position keeps its own
   meaning check; legacy keeps every position).
2. A framed synthesis names no card of the closed deck, selected or not, in any case or Unicode
   normal form.
3. A framed synthesis ends on exactly the shown step; nothing may follow it.
4. The provider instruction follows the brief version: framed v3 card-free, legacy names cards.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import JsonValue

from app.domains.content_rewrite.models import RewriteSurface
from app.domains.tarot.engine import TarotReadingEngine, _shown_step
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
from app.domains.tarot.rewrite import compile_tarot_rewrite_request, rewrite_tarot_reading
from app.infrastructure.generation.schemas import surface_output_contract

ENGINE = TarotReadingEngine()
NOW = datetime(2026, 10, 29, 12, tzinfo=UTC)
GUEST = UUID("20000000-0000-4000-8000-000000000915")
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
OPEN5 = ("major-sun", "major-star", "cups-ace", "pentacles-ace", "wands-ace")


def _framed(
    question: str,
    cards: tuple[str, ...],
    spread_map: TarotSpreadMap,
    context: TarotContext = TarotContext.WORK,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted and assessment.frame is not None
    return ENGINE.render(
        card_ids=cards,
        spread=SPREAD[len(cards)],
        spread_map=spread_map,
        context=context,
        question=question,
        voice=TarotVoice.PLAYFUL_GROUNDED,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )


def _legacy() -> TarotReading:
    return ENGINE.render(
        card_ids=("major-star", "cups-5", "wands-ace"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình cần nhìn rõ điều gì trước khi nói chuyện tiếp?",
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )


def _session(reading: TarotReading) -> TarotSessionView:
    selected = tuple(
        TarotSelectedCard(fan_index=index, position_key=p.key, position_label=p.label, card=p.card)
        for index, p in enumerate(reading.positions)
    )
    return TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000915"),
        version=4,
        state=TarotSessionState.COMPLETE,
        context=reading.context,
        spread=reading.spread,
        spread_map=reading.spread_map,
        voice=reading.voice,
        origin=TarotOrigin.DIRECT,
        question=reading.question,
        required_cards=len(reading.positions),
        selected_cards=selected,
        reading=reading,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(days=29),
    )


def _output(reading: TarotReading, synthesis: str | None = None) -> dict[str, JsonValue]:
    return {
        "headline": reading.headline,
        "synthesis": reading.summary if synthesis is None else synthesis,
        "closing_question": "Bạn muốn kiểm tra điều nào bằng chuyện thật?",
        "position_readings": [
            {"position_key": p.key, "reading": f"{p.card.title_vi}: {p.meaning_here}"}
            for p in reading.positions
        ],
    }


def _before_step(reading: TarotReading, inserted: str) -> str:
    step = _shown_step(reading.positions)
    assert step is not None
    ending = f"Trước hết, {step}"
    head, _, tail = reading.summary.rpartition(ending)
    return f"{head}{inserted} {ending}{tail}"


# ---------------------------------------------------------------- 1. coverage


def test_a_five_clarity_rewrite_keeping_the_summary_and_every_meaning_is_accepted() -> None:
    reading = _framed(
        "Mình có nên nhận thêm việc ở chỗ làm không?", OPEN5, TarotSpreadMap.FIVE_CLARITY
    )
    assert rewrite_tarot_reading(reading, _output(reading)) is not None


def test_every_detailed_position_still_needs_its_own_meaning() -> None:
    reading = _framed(
        "Mình có nên nhận thêm việc ở chỗ làm không?", OPEN5, TarotSpreadMap.FIVE_CLARITY
    )
    output = _output(reading)
    positions = output["position_readings"]
    assert isinstance(positions, list) and isinstance(positions[3], dict)
    title = reading.positions[3].card.title_vi
    positions[3] = {"position_key": reading.positions[3].key, "reading": f"{title}: ổn cả."}
    assert rewrite_tarot_reading(reading, output) is None


def test_only_framed_readings_narrow_the_synthesis_coverage() -> None:
    from app.domains.tarot.rewrite import _summarized_keys

    assert _summarized_keys(_legacy()) is None  # legacy: every position, unchanged
    reading = _framed(
        "Mình có nên nhận thêm việc ở chỗ làm không?", OPEN5, TarotSpreadMap.FIVE_CLARITY
    )
    assert _summarized_keys(reading) == frozenset({"facts", "assumption"})


# ---------------------------------------------------------------- 2. card names


@pytest.mark.parametrize(
    "inserted",
    [
        "Mặt Trăng cũng có mặt.",  # an unselected card
        "mặt trăng cũng có mặt.",  # case
        unicodedata.normalize("NFD", "Mặt Trăng cũng có mặt."),  # Unicode form
        "The Moon cũng có mặt.",  # the English name
        "Mặt Trời cũng có mặt.",  # a selected card
    ],
)
def test_a_framed_synthesis_naming_any_card_is_refused(inserted: str) -> None:
    reading = _framed(
        "Mình có nên nhắn lại cho đồng nghiệp không?",
        OPEN5[:3],
        TarotSpreadMap.THREE_UNBLOCK,
    )
    assert rewrite_tarot_reading(reading, _output(reading)) is not None
    named = _before_step(reading, inserted)
    assert rewrite_tarot_reading(reading, _output(reading, named)) is None


def test_card_words_inside_an_authored_anchor_do_not_trip_the_scan() -> None:
    # Energy · Năm Gậy's pitfall reads "đáp ứng mọi tiếng gọi ngay…"; "Tiếng Gọi" is a title.
    from app.domains.tarot import stance
    from app.domains.tarot.engine import CARD_TITLES, _position_views

    reading = _framed(
        "Mình cần nhìn rõ điều gì về sức của mình lúc này?",
        ("major-sun", "wands-5", "wands-ace"),
        TarotSpreadMap.THREE_UNBLOCK,
        context=TarotContext.ENERGY,
    )
    views = _position_views(reading.positions, reading.context)
    assert "tiếng gọi" in reading.summary
    assert stance.summary_covers(
        reading.summary, views, _shown_step(reading.positions), CARD_TITLES
    )


# ---------------------------------------------------------------- 3. ends on the step


def test_a_framed_synthesis_must_end_on_the_shown_step() -> None:
    reading = _framed(
        "Mình có nên nhắn lại cho đồng nghiệp không?",
        OPEN5[:3],
        TarotSpreadMap.THREE_UNBLOCK,
    )
    assert rewrite_tarot_reading(reading, _output(reading)) is not None
    extra = f"{reading.summary} Sau đó, gửi tin nhắn ngay."
    assert rewrite_tarot_reading(reading, _output(reading, extra)) is None


# ---------------------------------------------------------------- 4. instruction dispatch


def _instruction(reading: TarotReading) -> str:
    request = compile_tarot_rewrite_request(
        GUEST, _session(reading), model_version="gpt-6-luna", prompt_version="surface-rewrite-v3"
    )
    assert request is not None
    return surface_output_contract(RewriteSurface.TAROT, request.safe_payload).developer_instruction


def test_framed_requests_get_the_card_free_synthesis_rule() -> None:
    reading = _framed(
        "Mình có nên nhắn lại cho đồng nghiệp không?", OPEN5[:3], TarotSpreadMap.THREE_UNBLOCK
    )
    text = _instruction(reading)
    assert "Synthesis names no card_title" in text
    assert "must include every supplied card_title" not in text


def test_legacy_requests_keep_the_card_title_rule_their_gate_requires() -> None:
    reading = _legacy()
    text = _instruction(reading)
    assert "Synthesis must include every supplied card_title once" in text
    assert "names no card_title" not in text
    # The legacy gate still requires the names: a card-free synthesis is refused.
    unnamed = reading.summary
    for position in reading.positions:
        unnamed = unnamed.replace(position.card.title_vi, "lá này")
    assert rewrite_tarot_reading(reading, _output(reading, unnamed)) is None
    assert rewrite_tarot_reading(reading, _output(reading)) is not None


def test_no_payload_defaults_to_the_legacy_rule() -> None:
    text = surface_output_contract(RewriteSurface.TAROT).developer_instruction
    assert "Synthesis must include every supplied card_title once" in text


# ---------------------------------------------------------------- P3: opening normalisation


def test_the_opening_metric_uses_the_spec_normaliser() -> None:
    from scripts.audit_tarot_knowledge import opening_key

    nfd = unicodedata.normalize("NFD", "Chuyện công việc, nói gọn nè.")
    same = (
        opening_key("Chuyện công việc, nói gọn nè.", "Điểm chính: một việc nhỏ."),
        opening_key(nfd, "điểm chính:  một việc nhỏ"),
        opening_key("CHUYỆN CÔNG VIỆC, NÓI GỌN NÈ!", "Điểm chính: một việc nhỏ…"),
    )
    assert len(set(same)) == 1
    assert opening_key("Chuyện công việc.", "Một ý.") != opening_key("Chuyện công việc.", "Ý khác.")
