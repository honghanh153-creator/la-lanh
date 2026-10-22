"""T01 (audit 2026-10-22): a reading answers the action being asked, not a background action.

Census from the audit, plus moved background clauses, negation, timing and choice. Frame v2
reads topic, action and goals from the asked clause; stored v1 frames keep their labels.
"""

from __future__ import annotations

import pytest

from app.domains.tarot import question_frame, stance
from app.domains.tarot.engine import _POSITIONS, TarotReadingEngine
from app.domains.tarot.meaning_brief import goal_action, goal_by_key, question_goals
from app.domains.tarot.models import (
    QUESTION_FRAME_VERSION,
    QuestionFrame,
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotReading,
    TarotSpread,
    TarotSpreadMap,
    TarotStanceLevel,
    TarotVoice,
)

ENGINE = TarotReadingEngine()
R, W, S = TarotContext.RELATIONSHIPS, TarotContext.WORK, TarotContext.SELF_CARE
CENSUS = [
    ("Mình có nên xin lỗi không?", R, TarotAction.XIN_LOI, R, "apology"),
    ("Mình có nên xin lỗi sau lần nói chuyện vừa rồi không?", R, TarotAction.XIN_LOI, R, "apology"),
    (
        "Sau lần nói chuyện vừa rồi, mình có nên xin lỗi không?",
        R,
        TarotAction.XIN_LOI,
        R,
        "apology",
    ),
    ("Mình có nên xin lỗi sau khi lỡ hẹn không?", R, TarotAction.XIN_LOI, R, "apology"),
    (
        "Mình có nên xin góp ý sau buổi nói chuyện này không?",
        W,
        TarotAction.XIN_GOP_Y,
        W,
        "general",
    ),
    ("Mình có nên xin góp ý trước khi gửi báo cáo không?", W, TarotAction.XIN_GOP_Y, W, "general"),
    ("Mình có nên nghỉ ngơi sau cuộc nói chuyện này không?", S, TarotAction.NGHI_NGOI, S, "rest"),
    ("Sau cuộc nói chuyện này, mình có nên nghỉ ngơi không?", S, TarotAction.NGHI_NGOI, S, "rest"),
    ("Mình có nên nghỉ ngơi sau tuần làm việc này không?", S, TarotAction.NGHI_NGOI, S, "rest"),
]
MAPS = {
    TarotSpreadMap.ONE_FOCUS: (TarotSpread.ONE_CARD, ("major-hermit",)),
    TarotSpreadMap.THREE_UNBLOCK: (
        TarotSpread.THREE_CARD,
        ("major-hermit", "major-fool", "cups-ace"),
    ),
    TarotSpreadMap.FIVE_CLARITY: (
        TarotSpread.FIVE_CARD,
        ("major-hermit", "major-fool", "cups-ace", "swords-2", "wands-3"),
    ),
}


def _render(
    question: str,
    context: TarotContext,
    spread_map: TarotSpreadMap,
    voice: TarotVoice,
    frame: QuestionFrame | None = None,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted, question
    spread, cards = MAPS[spread_map]
    return ENGINE.render(
        card_ids=cards,
        spread=spread,
        spread_map=spread_map,
        context=context,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=frame or assessment.frame,
    )


@pytest.mark.parametrize(("question", "chosen", "action", "topic", "goal"), CENSUS)
def test_frame_labels_come_from_the_asked_clause(
    question: str, chosen: TarotContext, action: TarotAction, topic: TarotContext, goal: str
) -> None:
    frame = ENGINE.assess_question(question, chosen).frame
    assert frame is not None and frame.version == QUESTION_FRAME_VERSION
    assert (frame.form, frame.action, frame.topic) == (TarotQuestionForm.YES_NO, action, topic)
    text = question_frame.goal_text(question, frame.version)
    assert [g.key for g in question_goals(text, topic)] == [goal]


@pytest.mark.parametrize(("question", "chosen", "action", "topic", "goal"), CENSUS)
@pytest.mark.parametrize("spread_map", list(MAPS))
@pytest.mark.parametrize("voice", list(TarotVoice))
def test_stance_and_step_answer_the_same_target(
    question: str,
    chosen: TarotContext,
    action: TarotAction,
    topic: TarotContext,
    goal: str,
    spread_map: TarotSpreadMap,
    voice: TarotVoice,
) -> None:
    reading = _render(question, chosen, spread_map, voice)
    assert reading.stance is not None and reading.stance.action is action
    if action in stance.SELF_CARE_ACTIONS:
        assert reading.stance.level is not TarotStanceLevel.CONSIDER
    if goal != "general":
        step = reading.positions[-1]
        expected = goal_action(goal_by_key(goal), step.key)
        assert expected is not None and step.small_action is not None
        assert step.small_action.endswith(expected)
    assert [key for key, _ in _POSITIONS[spread_map]] == [p.key for p in reading.positions]


def test_negated_target_gives_no_label_rather_than_the_background_action() -> None:
    frame = ENGINE.assess_question(
        "Mình có nên không xin lỗi sau lần nói chuyện đó không?", R
    ).frame
    assert frame is not None and frame.action is None


def test_timing_question_keeps_its_form_and_target() -> None:
    frame = ENGINE.assess_question("Khi nào mình nên xin lỗi sau lần nói chuyện đó?", R).frame
    assert frame is not None
    assert (frame.form, frame.action) == (TarotQuestionForm.TIMING, TarotAction.XIN_LOI)


def test_a_background_clause_inside_a_choice_option_is_not_that_option() -> None:
    question = "Mình nên xin lỗi hay im lặng sau buổi nói chuyện đó?"
    assert stance.split_choice(question) == (TarotAction.XIN_LOI, TarotAction.NOI_RA)  # v1
    assert stance.split_choice(question, asked_clause=True) is None  # v2: clarify instead
    reading = _render(question, R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None
    assert reading.stance.level is TarotStanceLevel.CLARIFY_CHOICE


def test_high_stakes_boundary_still_rejects_before_any_draw() -> None:
    assert not ENGINE.assess_question(
        "Mình có nên ngừng thuốc sau buổi nói chuyện này không?", S
    ).accepted


def test_a_stored_v1_frame_keeps_its_labels_and_whole_question_goals() -> None:
    """AC17: frames stored before T01 are replayed as stored, never recomputed."""

    question = "Mình có nên xin lỗi sau lần nói chuyện vừa rồi không?"
    v1 = QuestionFrame(
        version="tarot-question-frame-v1",
        form=TarotQuestionForm.YES_NO,
        topic=R,
        action=TarotAction.NOI_RA,
    )
    assert question_frame.goal_text(question, v1.version) == question
    reading = _render(question, R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM, frame=v1)
    assert reading.stance is not None and reading.stance.action is TarotAction.NOI_RA


@pytest.mark.parametrize(
    ("question", "chosen", "action"),
    [
        # Question words and "thay vì" are part of what is asked, never a background clause.
        ("Có nên gọi điện thay vì nhắn tin cho chuyện này không?", R, TarotAction.NHAN_LAI),
        ("Vì sao mình khó từ chối lời rủ của bạn bè?", R, TarotAction.TU_CHOI),
        ("Khi nào là lúc phù hợp để mình xin góp ý về công việc?", W, TarotAction.XIN_GOP_Y),
        ("Khi nào là lúc nên dừng một cuộc tranh luận?", R, TarotAction.DUNG_LAI),
        # A reflective question's "khi" clause is the situation it reflects on.
        ("Tại sao mình thấy có lỗi khi nghỉ ngơi?", S, TarotAction.NGHI_NGOI),
        ("Tại sao mình hay nói vòng vo khi cần nói thẳng?", R, TarotAction.NOI_RA),
        # A decision question answers its asked action, not the event it comes before.
        (
            "Có nên dọn lại góc làm việc trước khi bắt đầu tuần mới không?",
            TarotContext.GENERAL,
            TarotAction.DON_DEP,
        ),
    ],
)
def test_question_words_and_reflective_situations_keep_their_label(
    question: str, chosen: TarotContext, action: TarotAction
) -> None:
    frame = ENGINE.assess_question(question, chosen).frame
    assert frame is not None and frame.action is action
