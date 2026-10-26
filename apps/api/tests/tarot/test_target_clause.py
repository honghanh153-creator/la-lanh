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


@pytest.mark.parametrize(
    "question",
    [
        # Codex #45: a "rồi" continuation belongs to the background it continues.
        "Mình có nên nghỉ ngơi sau khi đi làm về rồi nói chuyện với sếp không?",
        "Mình có nên nghỉ ngơi nếu nói chuyện xong rồi xin góp ý không?",
        "Mình có nên nghỉ ngơi sau khi gặp bạn rồi xin lỗi bạn ấy không?",
    ],
)
def test_a_background_continuation_never_becomes_the_asked_action(question: str) -> None:
    frame = ENGINE.assess_question(question, S).frame
    assert frame is not None and frame.action is TarotAction.NGHI_NGOI
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is TarotAction.NGHI_NGOI
    assert reading.stance.level is not TarotStanceLevel.CONSIDER


def test_a_negated_target_never_borrows_the_background_continuation() -> None:
    frame = ENGINE.assess_question(
        "Mình có nên không nghỉ ngơi sau khi đã nói chuyện rồi xin góp ý xong không?", S
    ).frame
    assert frame is not None and frame.action is None


def test_a_fronted_condition_ends_at_thi_and_the_main_clause_is_asked() -> None:
    frame = ENGINE.assess_question("Nếu nói chuyện xong thì mình có nên nghỉ ngơi không?", S).frame
    assert frame is not None and frame.action is TarotAction.NGHI_NGOI


def test_when_the_background_swallows_the_only_action_the_label_is_none() -> None:
    """No punctuation after a mid-sentence background: scope is uncertain, so clarify."""

    frame = ENGINE.assess_question(
        "Mình có nên sau khi đi làm về nói chuyện với sếp không?", W
    ).frame
    assert frame is not None and frame.action is None


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # Codex #45 round 2: a "nhưng"/"mà" contrast inside a background clause stays background.
        (
            "Sau khi nói chuyện với sếp nhưng vẫn phải nhận thêm việc, "
            "mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên nghỉ ngơi sau khi nói chuyện với sếp nhưng vẫn phải nhận thêm việc không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên không nghỉ ngơi sau khi đã nói chuyện "
            "nhưng vẫn phải nhận thêm việc không?",
            None,
        ),
        (
            "Mình có nên nghỉ ngơi dù vẫn muốn gặp bạn nhưng còn phải nói chuyện với sếp không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_contrast_inside_a_background_never_supplies_the_action(
    question: str, expected: TarotAction | None
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    if expected is not None:
        reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
        assert reading.stance is not None and reading.stance.action is expected
        assert reading.stance.level is not TarotStanceLevel.CONSIDER
        assert "nhận lời" not in reading.stance.conclusion


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # Codex #45 @ 4e02c46: the asked clause is the one that carries the question. A fronted
        # background segment ends at its punctuation, whatever "thì"/"hay"/"hoặc" it contains.
        (
            "Khi mình nói chuyện với sếp thì vẫn phải nhận thêm việc, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sau khi nói chuyện với sếp hay nhận thêm việc, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Khi sếp giao thêm việc hoặc nhắn muộn, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Codex #45 @ 7328572: a question reported inside the background ("sếp hỏi có nên …") is
        # not the asked question, and a "rồi" segment continues the background.
        (
            "Sau khi sếp hỏi có nên nói chuyện hay nhận thêm việc, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sau khi nói chuyện với sếp, rồi phải nhận thêm việc, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Khi sếp giao việc, nhưng vẫn phải nhận thêm việc, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Codex #45 @ c912caf: a question reported in a later segment ("rồi sếp hỏi mình có nên …",
        # or with no connector at all) is still not the reader's question.
        (
            "Sau khi sếp hỏi có nên nói chuyện, rồi sếp hỏi mình có nên nhận thêm việc, "
            "mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sau khi sếp hỏi có nên nói chuyện, sếp lại hỏi mình có nên nhận thêm việc, "
            "mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sếp hỏi mình có nên nhận thêm việc không, mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Controls: "thì" opening the asked clause, and a background whose action is not asked.
        ("Khi nói chuyện với sếp thì mình có nên nghỉ ngơi không?", TarotAction.NGHI_NGOI),
        ("Khi sếp giao thêm việc, mình có nên nhận lời không?", TarotAction.NHAN_LOI),
    ],
)
def test_the_clause_carrying_the_question_supplies_the_action(
    question: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    if expected is TarotAction.NGHI_NGOI:
        assert "nhận lời" not in reading.stance.conclusion
        assert "nghỉ" in (reading.positions[-1].small_action or "")


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # The asked clause can sit inside a fronted segment, after "thì". These forms are open, so
        # only the frame is checked: the open form has no stance by design.
        (
            "Khi mệt thì mình có nên nghỉ ngơi không, dù sếp vẫn giao thêm việc?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_an_asked_clause_after_then_inside_a_fronted_segment_is_kept(
    question: str, expected: TarotAction
) -> None:
    assert question_frame.match_action(question_frame.asked_text(question)) is expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # The reader's question names no action and points back at a plain statement before it.
        ("Sếp muốn mình nhận thêm việc, mình có nên không?", TarotAction.NHAN_LOI),
        # It points back at a background clause only: no action is owned by the question, so the
        # label is None (clarify) rather than a guess from the background.
        ("Sau khi sếp giao thêm việc, mình có nên không?", None),
        # A choice keeps both alternatives as the asked clause.
        (
            "Khi mệt, mình nên nghỉ ngơi, hay nhận thêm việc?",
            question_frame.match_action("mình nên nghỉ ngơi, hay nhận thêm việc?"),
        ),
    ],
)
def test_the_question_owns_its_action_or_none(question: str, expected: TarotAction | None) -> None:
    assert question_frame.match_action(question_frame.asked_text(question)) is expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # Codex #45 @ c9cc3d9: one question can span a list. "có nên … không?" opens in the first
        # segment and closes in the last; the last alone is not an independent clause.
        ("Mình có nên xin lỗi bạn bè, gia đình và đồng nghiệp không?", TarotAction.XIN_LOI),
        (
            "Mình có nên xin lỗi vì bất đồng về chia việc, công sức và lịch gặp không?",
            TarotAction.XIN_LOI,
        ),
        # An antecedent is the plain statement just before the question.
        (
            "Sau khi nói chuyện với sếp, mình muốn nghỉ ngơi, mình có nên không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_question_spanning_a_list_keeps_its_action(question: str, expected: TarotAction) -> None:
    frame = ENGINE.assess_question(question, S).frame
    assert frame is not None and frame.action is expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # Codex #45 @ 87ca55f: a final clause with its own action that closes with "được không?"
        # is a complete question even without an opener; it is not a list tail of the reported
        # question before it.
        ("Sếp hỏi có nên nhận thêm việc, mình nghỉ ngơi được không?", TarotAction.NGHI_NGOI),
        ("Sếp hỏi có nên nói chuyện, mình xin lỗi được không?", TarotAction.XIN_LOI),
        ("Sếp hỏi có nên xin lỗi, mình học thêm được không?", TarotAction.HOC_THEM),
    ],
)
def test_a_closed_own_clause_is_not_a_list_tail(question: str, expected: TarotAction) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is None or reading.stance.action is expected


def test_a_closing_only_segment_without_a_list_mark_borrows_nothing_from_a_question() -> None:
    """No conjunction and no action of its own: the owner is unclear, so the label is None."""

    frame = ENGINE.assess_question("Sếp hỏi có nên nhận thêm việc, mình được không?", S).frame
    assert frame is None or frame.action is None


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # Codex #45 @ 00a87df: a list needs no conjunction. A segment that only closes the open
        # question ("…, đồng nghiệp không?") continues it; a clause with its own question frame
        # ("… được không?") does not, even when it contains "và".
        ("Mình có nên xin lỗi bạn bè, gia đình, đồng nghiệp không?", TarotAction.XIN_LOI),
        (
            "Mình có nên xin lỗi vì bất đồng về chia việc, công sức, lịch gặp không?",
            TarotAction.XIN_LOI,
        ),
        ("Mình có nên xin lỗi bạn bè, gia đình không?", TarotAction.XIN_LOI),
        ("Mình có nên xin lỗi vì bất đồng về chia việc, công sức không?", TarotAction.XIN_LOI),
        ("Mình có nên xin lỗi bạn bè, gia đình và đồng nghiệp không?", TarotAction.XIN_LOI),
        ("Sếp hỏi có nên nhận thêm việc, mình nghỉ ngơi và ngủ được không?", TarotAction.NGHI_NGOI),
        (
            "Mình có nên xin lỗi bạn bè, gia đình không, dù sếp vẫn giao thêm việc?",
            TarotAction.XIN_LOI,
        ),
    ],
)
def test_lists_and_own_clauses_by_clause_structure(question: str, expected: TarotAction) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is None or reading.stance.action is expected


@pytest.mark.parametrize(
    "question",
    [
        # Codex #45 @ 58cbd26: "được không" closes the question but the verb sits in an earlier
        # segment; a noun-list tail owns no predicate and must not drop or replace the action.
        "Liệu mình xin lỗi bạn bè, gia đình và đồng nghiệp được không?",
        "Liệu mình xin lỗi vì bất đồng về chia việc, công sức và lịch gặp được không?",
    ],
)
def test_a_predicate_free_tail_keeps_the_spanning_action(question: str) -> None:
    assessment = ENGINE.assess_question(question, R)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is TarotAction.XIN_LOI
    reading = _render(question, R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    control = _render(
        "Mình có nên xin lỗi không?", R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM
    )
    assert reading.stance is not None and reading.stance.action is TarotAction.XIN_LOI
    assert reading.stance.conclusion == control.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == control.positions[-1].small_action


def test_a_bare_own_clause_with_its_own_verb_stays_the_question() -> None:
    """Correct on 00a87df; 58cbd26 regressed it (Codex r13 supporting evidence)."""

    question = "Sếp hỏi có nên nhận thêm việc, mình nghỉ ngơi không?"
    assessment = ENGINE.assess_question(question, S)
    assert assessment.frame is not None and assessment.frame.action is TarotAction.NGHI_NGOI


@pytest.mark.parametrize(
    ("question", "goals"),
    [
        # Same goals as c912caf/87ca55f; "meeting" is the reason list's own pre-existing goal.
        ("Liệu mình xin lỗi bạn bè, gia đình và đồng nghiệp được không?", ["apology"]),
        (
            "Liệu mình xin lỗi vì bất đồng về chia việc, công sức và lịch gặp được không?",
            ["apology", "meeting"],
        ),
        (
            "Mình có nên xin lỗi vì bất đồng về chia việc, công sức, lịch gặp không?",
            ["apology", "meeting"],
        ),
    ],
)
def test_stored_v2_goal_extraction_follows_the_spanning_list(
    question: str, goals: list[str]
) -> None:
    """Rendering a stored v2 frame reads goals from goal_text: the list span must hold there too
    (apology stays the leading goal), while a stored v1 frame keeps whole-question goals."""

    frame = ENGINE.assess_question(question, R).frame
    assert frame is not None and frame.version == QUESTION_FRAME_VERSION
    assert frame.action is TarotAction.XIN_LOI
    text = question_frame.goal_text(question, frame.version)
    assert [g.key for g in question_goals(text, R)] == goals
    v1 = frame.model_copy(update={"version": "tarot-question-frame-v1"})
    assert question_frame.goal_text(question, v1.version) == question


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # Codex #45 @ e348902: a reason inside a reported question ("vì dự án đang gấp") does not
        # make the reader's own complete question that follows part of that reason list.
        (
            "Sếp hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sếp hỏi có nên nói chuyện vì dự án đang gấp, mình xin lỗi được không?",
            "Mình có nên xin lỗi không?",
            TarotAction.XIN_LOI,
        ),
        (
            "Sếp hỏi có nên xin lỗi vì dự án đang gấp, mình học thêm được không?",
            "Mình có nên học thêm không?",
            TarotAction.HOC_THEM,
        ),
        (
            "Sếp hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_reported_reason_does_not_absorb_the_readers_own_question(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # Codex #45 @ 84703df: a degree or result clause after the reader's own open reason
        # continues that reason; words before its action do not make it a clause with its own
        # subject. With and without the comma, and after the reader's own introduction.
        (
            "Mình có nên nghỉ ngơi vì mình quá mệt, đến mức không tập trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên nghỉ ngơi vì mình quá mệt đến mức không tập trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên xin lỗi vì mình lỡ lời, khiến bạn ấy không nói chuyện được không?",
            "Mình có nên xin lỗi không?",
            TarotAction.XIN_LOI,
        ),
        (
            "Mình muốn hỏi có nên nghỉ ngơi vì mình quá mệt, đến mức không tập trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Control: after someone else's reported question, the reader's complete question stays.
        (
            "Sếp hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_dependent_clause_continues_the_readers_own_reason(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # Codex #45 @ 5b5b9e1: the reporting verb is bound to the interrogative it introduces; an
        # earlier non-interrogative "nào" (indefinite subject, habitual time) does not hide it.
        (
            "Một người nào đó hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sếp hôm nào cũng hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Controls: plain reported subjects, a question reported inside the reader's own reason,
        # and an indefinite time phrase inside the reader's own reason with a dependent clause.
        (
            "Ai đó hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên nghỉ ngơi vì sếp hỏi có nên nhận thêm việc, đến mức không tập trung "
            "được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên nghỉ ngơi vì ngày nào cũng quá mệt, đến mức không tập trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_reporting_verb_binds_to_the_question_it_introduces(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # Codex #45 @ e3a4e67: the reader's own question opens first, so a report and its question
        # after it are nested inside it and never take ownership.
        (
            "Mình có nên hỏi lại xem mình nên làm gì vì quá mệt, đến mức không tập trung được "
            "không?",
            "Mình có nên hỏi lại không?",
            TarotAction.HOI_LAI,
        ),
        (
            "Mình có nên nghỉ ngơi để biết mình nên làm gì vì quá mệt, đến mức không tập trung "
            "được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên nghỉ ngơi mà không biết mình nên làm gì vì quá mệt, đến mức không tập "
            "trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Controls: indefinite "nào" before a real report, and a report of a wh-question.
        (
            "Một người nào đó hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sếp hỏi mình nên làm gì vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
    ],
)
def test_a_question_nested_in_the_readers_own_question_stays_nested(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # Codex #45 @ 70f612c: a bare "nên" after a clause is causal ("so"), not the reader's
        # question, so the report it introduces is still someone else's.
        (
            "Sếp mệt nên hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Sếp thấy thiếu người nên hỏi có nên nhận thêm việc vì dự án đang gấp, mình nghỉ ngơi "
            "được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình mệt nên hỏi có nên nhận thêm việc vì thiếu người, mình nghỉ ngơi được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        # Controls: "nên" with the reader as its subject opens the reader's own question, so a
        # report after it stays nested; and the dependent tail keeps the reader's action.
        (
            "Mình nên nghỉ ngơi để biết mình nên làm gì vì quá mệt, đến mức không tập trung được "
            "không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Nên nghỉ ngơi để biết mình nên làm gì vì quá mệt, đến mức không tập trung được không?",
            "Mình có nên nghỉ ngơi không?",
            TarotAction.NGHI_NGOI,
        ),
        (
            "Mình có nên hỏi lại xem mình nên làm gì vì quá mệt, đến mức không tập trung được "
            "không?",
            "Mình có nên hỏi lại không?",
            TarotAction.HOI_LAI,
        ),
    ],
)
def test_a_causal_nen_does_not_open_the_readers_question(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, S)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, S, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "control", "expected"),
    [
        # T01 follow-up: in a yes/no clause the action right after "có nên" is the asked
        # predicate; a longer action word that a dependent marker places after it ("trong buổi
        # nói chuyện", "rồi nói chuyện lại") no longer takes the label.
        (
            "Mình có nên xin lỗi bạn ấy trong buổi nói chuyện tối nay không?",
            "Mình có nên xin lỗi không?",
            TarotAction.XIN_LOI,
        ),
        (
            "Mình có nên xin lỗi bạn ấy trong buổi nói chuyện tối nay hay không?",
            "Mình có nên xin lỗi không?",
            TarotAction.XIN_LOI,
        ),
        (
            "Mình có nên xin lỗi rồi nói chuyện lại với bạn ấy không?",
            "Mình có nên xin lỗi không?",
            TarotAction.XIN_LOI,
        ),
        # Controls that keep the longest-signal label: the asked predicate itself, a choice, and an
        # auxiliary-like "bắt đầu" before the real action.
        (
            "Mình có nên nói chuyện thẳng thắn về việc chia tay không?",
            "Mình có nên nói ra không?",
            TarotAction.NOI_RA,
        ),
        (
            "Mình có nên đợi thêm thời gian rồi mới chia tay không?",
            "Mình có nên cho thêm thời gian không?",
            TarotAction.CHO_THEM,
        ),
    ],
)
def test_the_action_after_the_modal_is_the_asked_predicate(
    question: str, control: str, expected: TarotAction
) -> None:
    assessment = ENGINE.assess_question(question, R)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is expected
    reading = _render(question, R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    reference = _render(control, R, TarotSpreadMap.ONE_FOCUS, TarotVoice.STRAIGHT_WARM)
    assert reading.stance is not None and reading.stance.action is expected
    assert reading.stance.conclusion == reference.stance.conclusion  # type: ignore[union-attr]
    assert reading.positions[-1].small_action == reference.positions[-1].small_action


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Khi mệt, mình nên nghỉ ngơi, hay nhận thêm việc?", TarotAction.NHAN_LOI),
        ("Bao giờ thì nên bắt đầu tìm cơ hội mới?", TarotAction.DOI_VIEC),
        # Purpose "để" is not a dependent marker: the light verb "dừng" does not take the label.
        ("Khi nào là lúc mình nên dừng để nghỉ?", TarotAction.NGHI_NGOI),
        # "trước" marks the later action word as dependent, so the asked "viết ra" wins.
        ("Mình có nên viết ra trước những điều muốn nói không?", TarotAction.VIET_RA),
    ],
)
def test_choices_and_auxiliary_verbs_keep_the_longest_signal(
    question: str, expected: TarotAction
) -> None:
    assert question_frame.match_action(question_frame.asked_text(question)) is expected
