import pytest

from app.domains.readings.review_agent import OPAQUE_CORE_FRAGMENTS
from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.examples import CARD_EXAMPLES
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.meaning_brief import question_goals
from app.domains.tarot.models import (
    TarotContext,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.relationship_readings import RELATIONSHIP_EXAMPLES, RELATIONSHIP_READINGS


def test_five_card_multiple_goals_keep_all_card_meanings_within_summary_budget() -> None:
    cards = ("swords-10", "pentacles-page", "pentacles-king", "cups-queen", "swords-king")
    reading = TarotReadingEngine().render(
        card_ids=cards,
        spread=TarotSpread.FIVE_CARD,
        context=TarotContext.COMMUNICATION,
        question="Mình nên nói gì để xin lỗi vì bất đồng về chia việc, công sức và lịch gặp?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    assert len(reading.summary.split()) <= 180
    assert tuple(position.card.id for position in reading.positions) == cards
    assert all(position.card.title_vi in reading.summary for position in reading.positions)
    assert all(position.meaning_here and position.small_action for position in reading.positions)
    assert reading.summary.startswith("Khi muốn xin lỗi")
    assert "Khi muốn được ghi nhận" not in reading.summary
    assert "Khi muốn chốt lịch gặp" not in reading.summary


def test_sharing_effort_does_not_invent_a_need_for_recognition() -> None:
    goals = question_goals("Chia việc và công sức thế nào?", TarotContext.COMMUNICATION)
    assert [goal.key for goal in goals] == ["task_handoff"]
    assert [
        goal.key for goal in question_goals("Mình muốn công sức được ghi nhận", TarotContext.WORK)
    ] == ["recognition"]


def test_five_card_rest_has_distinct_position_questions_and_steps_without_invented_motive() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("cups-king", "wands-3", "pentacles-6", "major-hermit", "swords-4"),
        spread=TarotSpread.FIVE_CARD,
        context=TarotContext.SELF_CARE,
        question="Mình cần nghỉ nhưng vẫn chưa dừng việc được, cần nhìn rõ điều gì?",
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    assert len({p.reflection_question for p in reading.positions}) == 5
    assert len({p.small_action for p in reading.positions}) == 5
    assert "làm vừa lòng" not in " ".join(p.reflection_question for p in reading.positions)


def test_recognised_goal_never_replaces_card_meaning_with_generic_goal_advice() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("cups-king", "wands-3", "pentacles-6"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói gì để xin lỗi sau khi lỡ hẹn?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    assert "bình tĩnh" in reading.positions[0].meaning_here
    assert "xin lỗi" in (reading.positions[0].small_action or "")
    assert (
        "Nhà Vua Cốc" in reading.summary
        and "Ba Gậy" in reading.summary
        and "Sáu Tiền" in reading.summary
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
    assert first.provenance.knowledge_version == "tarot-knowledge-v4"
    assert {
        "bunning-learning-tarot",
        "cynova-kitchen-table-tarot",
        "tishman-mindful-tarot",
    } <= set(first.provenance.source_ids)


def test_three_card_summary_explains_the_entire_reported_spread() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("cups-king", "wands-3", "pentacles-6"),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói rõ điều gì với người mình đang tìm hiểu?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    for position in reading.positions:
        assert position.card.title_vi in reading.summary
    assert "khả năng dẫn dắt và chịu trách nhiệm khi xử lý" not in reading.summary
    assert "một việc cần thêm người hoặc nguồn lực phối hợp" not in reading.summary
    assert "sự điều chỉnh để dòng trao đổi cân hơn" not in reading.summary


def test_relationship_reading_does_not_turn_a_conversation_into_a_work_opportunity() -> None:
    engine = TarotReadingEngine()
    cards = ("pentacles-ace", "major-sun", "major-empress")
    relationship = engine.render(
        card_ids=cards,
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói rõ chuyện đang khó chịu với một người thế nào?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    work = engine.render(
        card_ids=cards,
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.WORK,
        question="Mình nên nói rõ việc đang khó chịu với đồng nghiệp thế nào?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    assert "thời gian gặp nhau" in relationship.positions[0].meaning_here
    assert "người kia" in (relationship.positions[2].small_action or "")
    assert relationship.positions[0].meaning_here != work.positions[0].meaning_here
    assert tuple(position.card for position in relationship.positions) == tuple(
        position.card for position in work.positions
    )
    assert "hai người chưa chọn ngày" in relationship.positions[0].everyday_scene


def test_relationship_matrix_has_meaning_and_example_for_every_selected_card() -> None:
    ids = {card.id for card in all_cards()}
    assert set(RELATIONSHIP_READINGS) == set(RELATIONSHIP_EXAMPLES) == ids
    assert len(set(RELATIONSHIP_EXAMPLES.values())) == 78


def test_every_card_has_its_own_example_not_a_repeated_pitfall() -> None:
    cards = all_cards()
    assert set(CARD_EXAMPLES) == {card.id for card in cards}
    assert len(set(CARD_EXAMPLES.values())) == 78
    for card in cards:
        reading = TarotReadingEngine().render(
            card_ids=(card.id,),
            spread=TarotSpread.ONE_CARD,
            context=TarotContext.GENERAL,
            question="Chuyện này cần nhìn rõ điều gì trước?",
            voice=TarotVoice.STRAIGHT_WARM,
        )
        scene = reading.positions[0].everyday_scene
        assert scene.startswith("Ví dụ")
        assert scene != reading.positions[0].meaning_here
        assert card.tension not in scene


def test_card_example_changes_with_relevant_context_without_guessing_private_facts() -> None:
    engine = TarotReadingEngine()
    readings = [
        engine.render(
            card_ids=("cups-king",),
            spread=TarotSpread.ONE_CARD,
            context=context,
            question="Mình nên nói rõ điều gì trong chuyện này?",
            voice=TarotVoice.STRAIGHT_WARM,
        )
        for context in (TarotContext.RELATIONSHIPS, TarotContext.WORK)
    ]
    assert readings[0].positions[0].everyday_scene != readings[1].positions[0].everyday_scene
    assert "chia việc" in readings[1].positions[0].everyday_scene
    assert all(reading.positions[0].everyday_scene.startswith("Ví dụ") for reading in readings)


def test_tarot_gate_rejects_the_reported_mechanical_explanation() -> None:
    reading = TarotReadingEngine().render(
        card_ids=("cups-king",),
        spread=TarotSpread.ONE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói rõ điều gì với người mình đang tìm hiểu?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    position = reading.positions[0].model_copy(
        update={
            "meaning_here": (
                "Ý chính của lá: khả năng dẫn dắt và chịu trách nhiệm khi xử lý cảm xúc "
                "và cách bạn đón nhận sự gần gũi."
            )
        }
    )
    with pytest.raises(TarotContentRejected):
        TarotReadingEngine.validate(reading.model_copy(update={"positions": (position,)}))


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


@pytest.mark.parametrize(
    ("spread", "card_ids"),
    [
        (TarotSpread.ONE_CARD, ("major-moon",)),
        (TarotSpread.THREE_CARD, ("major-temperance", "major-tower", "major-star")),
        (
            TarotSpread.FIVE_CARD,
            ("major-moon", "wands-king", "cups-2", "swords-8", "pentacles-4"),
        ),
    ],
)
def test_generated_reading_avoids_opaque_copy(
    spread: TarotSpread, card_ids: tuple[str, ...]
) -> None:
    reading = TarotReadingEngine().render(
        card_ids=card_ids,
        spread=spread,
        context=TarotContext.RELATIONSHIPS,
        question="Mình cần nhìn rõ điều gì trước khi nói chuyện tiếp?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    visible_copy = " ".join(
        (
            reading.headline,
            reading.summary,
            reading.closing_prompt,
            *(
                text
                for position in reading.positions
                for text in (
                    position.meaning_here,
                    position.everyday_scene,
                    position.reflection_question,
                    position.small_action or "",
                )
            ),
        )
    ).casefold()

    assert not any(fragment in visible_copy for fragment in OPAQUE_CORE_FRAGMENTS)


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
    assert "Điểm có ích" in reading.positions[1].meaning_here
    assert "Đổi lại" in reading.positions[1].meaning_here
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


@pytest.mark.parametrize("mutation", ["card", "position", "spread", "summary"])
def test_content_gate_preserves_selected_card_and_spread(mutation: str) -> None:
    reading = TarotReadingEngine().render(
        card_ids=("cups-king",),
        spread=TarotSpread.ONE_CARD,
        context=TarotContext.RELATIONSHIPS,
        question="Mình nên nói rõ điều gì với người mình đang tìm hiểu?",
        voice=TarotVoice.STRAIGHT_WARM,
    )
    position = reading.positions[0]
    if mutation == "card":
        card = position.card.model_copy(update={"core": "người kia chắc chắn thích bạn"})
        reading = reading.model_copy(
            update={"positions": (position.model_copy(update={"card": card}),)}
        )
    elif mutation == "position":
        reading = reading.model_copy(
            update={"positions": (position.model_copy(update={"label": "Tương lai chắc chắn"}),)}
        )
    elif mutation == "spread":
        reading = reading.model_copy(update={"spread": TarotSpread.FIVE_CARD})
    else:
        reading = reading.model_copy(update={"summary": "Chuyện này có thể khiến bạn bối rối."})
    with pytest.raises(TarotContentRejected):
        TarotReadingEngine.validate(reading)
