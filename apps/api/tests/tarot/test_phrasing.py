"""Tarot pass 2: card cores as clauses and position frames without header labels.

Owner feedback 29/10/2026 ("content tarot vẫn kỳ lắm"); docs/reviews/2026-10-29-tarot-pass2.md.
"""

from __future__ import annotations

import re
import string

import pytest

from app.domains.tarot import phrasing, provenance, roles, stance
from app.domains.tarot.engine import (
    _POSITIONS,
    TarotReadingEngine,
    _authored_by_engine,
    _CardMeaning,
)
from app.domains.tarot.knowledge import all_cards, card_by_id
from app.domains.tarot.models import (
    TarotContext,
    TarotReading,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.voice import ROAST_ACTION_FRAMES

ENGINE = TarotReadingEngine()
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
CLARITY = ("major-star", "swords-ace", "pentacles-4", "wands-3", "cups-5")
QUESTION = "Mình cần nhìn rõ điều gì trong công việc lúc này?"
OVERLAY_ADVICE = re.compile(r"(?<!\w)(?:hãy|nên|đừng|phải|khoan)(?!\w)", re.IGNORECASE)
# A core that opens on one of these has no subject; it needs a sentence in the overlay.
BARE_HEADS = ("muốn ", "cần ", "có thể ", "có hứng ", "chưa ", "đã ", "đang ")
# Labels the pass-2 frames retired: each restated or relabelled the position header.
RETIRED_LABELS = (
    "lá này cho thấy",
    "điều đã khá rõ:",
    "phần đang có sẵn:",
    "điều dễ trượt qua:",
    "chỗ dễ bỏ sót:",
    "điều cần tính tới:",
    "bước tiếp dựa vào:",
    "điều có thể dựa vào:",
    "dữ kiện đáng tin:",
    "bằng chứng thật:",
    "dữ kiện, không phải phim:",
    "kịch bản tự viết:",
    "não tự điền chỗ trống:",
    "phần đoán mò:",
    "điều bạn cần giữ:",
    "nhu cầu thật ở đây:",
    "nhu cầu chính chủ:",
    "phần nằm trong tay bạn:",
    "điểm khởi phát:",
    "phản xạ tủ của bạn:",
    "cái giá về sau:",
    "hóa đơn về sau:",
    "nền cho cách mới:",
    "hướng này mang lại:",
    "phần được:",
    "điểm cộng:",
    "điểm cần cân giữa hai hướng:",
    "một tiêu chí để tự chốt:",
    "cảm xúc gắn với:",
    "ranh giới có thể nói rõ:",
    "trước khi mở lời:",
)


def _fields(card_id: str, topic: TarotContext) -> tuple[str, str]:
    meaning = _CardMeaning.for_context(card_by_id(card_id), topic)
    return meaning.core, phrasing.core_sentence(card_id, topic, meaning.core)


def _render(
    spread_map: TarotSpreadMap,
    cards: tuple[str, ...],
    *,
    context: TarotContext = TarotContext.WORK,
    voice: TarotVoice = TarotVoice.STRAIGHT_WARM,
    framed: bool = True,
) -> TarotReading:
    assessment = ENGINE.assess_question(QUESTION, context)
    return ENGINE.render(
        card_ids=cards,
        spread=SPREAD[len(cards)],
        spread_map=spread_map if framed else None,
        context=context,
        question=QUESTION,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame if framed else None,
    )


# ---------------------------------------------------------------- the overlay


def test_every_overlay_sentence_is_a_short_plain_clause_for_a_real_card() -> None:
    ids = {card.id for card in all_cards()}
    assert set(phrasing.CORE_SENTENCES) == {topic.value for topic in TarotContext}
    for topic, sentences in phrasing.CORE_SENTENCES.items():
        for card_id, sentence in sentences.items():
            core, _ = _fields(card_id, TarotContext(topic))
            label = (topic, card_id, sentence)
            assert card_id in ids, label
            assert sentence != core, label
            assert sentence == sentence.strip() and not sentence.endswith((".", "!", "?")), label
            assert sentence[:1].islower(), label
            assert len(sentence.split()) <= 18, label
            assert not OVERLAY_ADVICE.search(sentence), label
            assert not any(re.search(p, sentence) for p in roles.DECISION_OR_PREDICTION), label
            assert not any(marker in sentence for marker in stance.MARKERS.values()), label
            assert not re.search(r"\bngười kia (?:sẽ|chắc|đang nghĩ)", sentence), label


def test_every_core_without_a_subject_has_a_sentence() -> None:
    for card in all_cards():
        for topic in TarotContext:
            core, sentence = _fields(card.id, topic)
            assert len(sentence.split()) <= 18, (topic, card.id)
            if core.startswith(BARE_HEADS):
                assert sentence != core, (topic, card.id, core)


def test_the_awkward_four_pentacles_work_line_reads_as_a_sentence() -> None:
    core, sentence = _fields("pentacles-4", TarotContext.WORK)
    assert core == "giữ nguồn lực ổn định cần phân biệt khoản dự phòng với việc giữ quá chặt"
    assert sentence.startswith("để giữ nguồn lực ổn định, bạn cần phân biệt")


def test_core_sentence_falls_back_to_the_authored_core() -> None:
    assert phrasing.core_sentence("major-star", TarotContext.WORK, "x") == "x"
    assert phrasing.core_sentence("pentacles-page", "general", "x") == (
        "bạn muốn học một điều có thể dùng được trong thực tế"
    )
    assert phrasing.contains_clause("Bạn muốn học.", "bạn muốn học")
    assert not phrasing.contains_clause("Họ muốn học.", "bạn muốn học")


# ---------------------------------------------------------------- legacy stays byte for byte


def test_legacy_readings_keep_the_authored_core_and_capitalized_roast_steps() -> None:
    reading = _render(TarotSpreadMap.FIVE_CLARITY, CLARITY, voice=TarotVoice.ROAST, framed=False)
    core, sentence = _fields("pentacles-4", TarotContext.WORK)
    prose = " ".join(p.meaning_here for p in reading.positions)
    assert core in prose and sentence not in prose
    for position in reading.positions:
        action = position.small_action or ""
        frame = next(f for f in ROAST_ACTION_FRAMES if action.startswith(f"{f} "))
        assert action[len(frame) + 1].isupper(), action


# ---------------------------------------------------------------- framed prose


@pytest.mark.parametrize("voice", [TarotVoice.STRAIGHT_WARM, TarotVoice.ROAST])
def test_framed_positions_read_the_sentence_without_the_header(voice: TarotVoice) -> None:
    reading = _render(TarotSpreadMap.FIVE_CLARITY, CLARITY, voice=voice)
    need = reading.positions[2]
    _, sentence = _fields("pentacles-4", TarotContext.WORK)
    assert sentence in need.meaning_here
    for position in reading.positions:
        text = position.meaning_here.casefold()
        assert position.label.casefold() not in text
        assert not [label for label in RETIRED_LABELS if label in text], text
    ENGINE.validate(reading)


def test_the_summary_states_the_core_as_a_sentence_without_a_label() -> None:
    reading = _render(TarotSpreadMap.FIVE_CLARITY, ("pentacles-page", *CLARITY[1:]))
    _, sentence = _fields("pentacles-page", TarotContext.WORK)
    assert reading.summary.startswith(f"{phrasing.capitalized(sentence)}.")
    assert "Điểm chính:" not in reading.summary
    choice = _render(TarotSpreadMap.FIVE_CHOICE, CLARITY)
    assert "Với hướng A, " in choice.summary and "Với hướng B, " in choice.summary
    assert "Hướng A:" not in choice.summary


def test_stance_reasons_quote_the_sentence() -> None:
    assessment = ENGINE.assess_question("Mình có nên nhận lời dự án mới không?", TarotContext.WORK)
    reading = ENGINE.render(
        card_ids=("pentacles-page", "swords-7", "major-sun"),
        spread=TarotSpread.THREE_CARD,
        spread_map=TarotSpreadMap.THREE_UNBLOCK,
        context=TarotContext.GENERAL,
        question="Mình có nên nhận lời dự án mới không?",
        voice=TarotVoice.STRAIGHT_WARM,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )
    assert reading.stance is not None
    _, sentence = _fields("pentacles-page", TarotContext.GENERAL)
    texts = [reason.text for reason in reading.stance.reasons]
    assert any(text.endswith(f"cho thấy {sentence}.") for text in texts if "Tiền" in text)


def test_framed_roast_steps_continue_in_lower_case_after_the_colon() -> None:
    reading = _render(TarotSpreadMap.FIVE_CLARITY, CLARITY, voice=TarotVoice.ROAST)
    step = reading.positions[-1].small_action or ""
    frame = next(f for f in ROAST_ACTION_FRAMES if step.startswith(f"{f} "))
    assert step[len(frame) + 1].islower(), step
    direct = _render(TarotSpreadMap.FIVE_CLARITY, CLARITY)
    assert step.endswith(
        f"{(direct.positions[-1].small_action or '')[:1].lower()}"
        f"{(direct.positions[-1].small_action or '')[1:]}"
    )


def test_the_role_fit_gate_expects_the_sentence() -> None:
    reading = _render(TarotSpreadMap.FIVE_CLARITY, CLARITY)
    core, sentence = _fields("pentacles-4", TarotContext.WORK)
    need = reading.positions[2]
    raw = need.model_copy(update={"meaning_here": f"Lúc này, {core}."})
    positions = (*reading.positions[:2], raw, *reading.positions[3:])
    with pytest.raises(Exception, match="role's field"):
        ENGINE.validate(reading.model_copy(update={"positions": positions}))
    assert sentence not in _authored_by_engine(reading)


def test_provenance_resolves_the_sentence_from_the_frame_code() -> None:
    text = provenance.resolve_meaning(
        "need.0", None, False, position_key="need", card_id="pentacles-4", topic="work"
    )
    _, sentence = _fields("pentacles-4", TarotContext.WORK)
    assert text == f"{phrasing.capitalized(sentence)}."


def test_frames_keep_their_slots_and_codes() -> None:
    def slots(template: str) -> set[str]:
        return {name for _, name, _, _ in string.Formatter().parse(template) if name}

    for key, role in roles.ROLES.items():
        assert key in {k for entries in _POSITIONS.values() for k, _ in entries}
        for direct, roast in zip(role.frames, role.roast, strict=True):
            assert slots(direct) == slots(roast)
            assert "core" not in slots(direct)  # framed prose reads the clause, never the field
        if role.field in {roles.RoleField.CORE, roles.RoleField.OPTION}:
            assert all("core_sentence" in slots(f) for f in (*role.frames, *role.roast))
