import pytest

from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.models import (
    TarotContext,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)


def test_one_card_reading_is_concrete_and_deterministic() -> None:
    engine = TarotReadingEngine()

    first = engine.render(
        card_ids=("major-hermit",),
        spread=TarotSpread.ONE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nhìn rõ điều gì trước khi nhắn lại?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    second = engine.render(
        card_ids=("major-hermit",),
        spread=TarotSpread.ONE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nhìn rõ điều gì trước khi nhắn lại?",
        voice=TarotVoice.STRAIGHT_WARM,
    )

    assert first == second
    assert first.positions[0].card.title_vi == "Ẩn Sĩ"
    assert "tin nhắn" in first.positions[0].everyday_scene.lower()
    assert first.positions[0].reflection_question.endswith("?")
    assert first.positions[0].small_action
    assert first.provenance.knowledge_version == "tarot-knowledge-v2"
    assert {
        "bunning-learning-tarot",
        "cynova-kitchen-table-tarot",
        "tishman-mindful-tarot",
    } <= set(first.provenance.source_ids)


def test_three_card_reading_uses_reflective_positions() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("major-star", "cups-5", "wands-ace"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.WORK,
        question="Mình cần nhìn lại điều gì trước khi nhận thêm việc?",
        voice=TarotVoice.GENTLE_SPECIFIC,
    )

    assert [position.label for position in reading.positions] == [
        "Điều đã rõ",
        "Điều dễ bỏ sót",
        "Một bước nhỏ có thể thử",
    ]
    assert all(position.everyday_scene for position in reading.positions)
    assert "tương lai" not in reading.summary.lower()


def test_five_card_choice_map_compares_both_directions_without_deciding() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("major-star", "cups-5", "wands-ace", "major-hermit", "swords-2"),
        spread=TarotSpread.FIVE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên ở lại hay rời đi, và điều gì không nên đánh đổi?",
        voice=TarotVoice.STRAIGHT_WARM,
    )

    assert reading.spread_map is TarotSpreadMap.FIVE_CHOICE
    assert [position.key for position in reading.positions] == [
        "need",
        "option_a",
        "option_b",
        "tradeoff",
        "criterion",
    ]
    assert "đáp án hoàn hảo" in reading.positions[1].meaning_here
    assert "không phải dự đoán" in reading.disclaimer


@pytest.mark.parametrize(
    ("question", "expected_hint"),
    [
        ("Người ấy chắc chắn đang nghĩ gì về mình?", "phần mình"),
        ("Lá này có nói mình nên bỏ thuốc không?", "chuyên gia"),
        ("Bao giờ họ sẽ quay lại?", "quan sát"),
    ],
)
def test_question_gate_reframes_influence_and_high_stakes_questions(
    question: str, expected_hint: str
) -> None:
    decision = TarotReadingEngine().assess_question(question, TarotContext.RELATIONSHIPS)

    assert decision.accepted is False
    assert decision.suggested_reframe is not None
    assert decision.explanation is not None
    assert expected_hint in decision.explanation.lower()


def test_engine_rejects_invalid_card_count() -> None:
    with pytest.raises(TarotContentRejected):
        TarotReadingEngine().render(
            card_ids=("major-star", "major-hermit"),
            spread=TarotSpread.ONE_CARD,
            context=TarotContext.GENERAL,
            question="Mình nên nhìn điều gì?",
            voice=TarotVoice.PLAYFUL_GROUNDED,
        )
