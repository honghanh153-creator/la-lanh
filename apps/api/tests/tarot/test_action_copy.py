"""T02/T03: the asked action's scene and step at the step role (decisions C4/C5).

Copy: docs/reviews/2026-10-22-t02-t03-tarot-copy-workbook.md (decided under owner delegation on
26/10/2026; wiring edits listed there). Stored readings keep their text (US-20 AC15/AC17).
Codex r47: the step agrees with the stance in every voice, and no scene or opening presumes a
partner or an event the question's closed labels do not establish.
"""

from __future__ import annotations

import itertools
import json
import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.db.session import Database
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS
from app.domains.tarot import action_copy, question_frame, roles, stance
from app.domains.tarot import voice as tarot_voice
from app.domains.tarot.engine import _POSITIONS, TarotReadingEngine, card_scene
from app.domains.tarot.meaning_brief import goal_action, question_goals
from app.domains.tarot.models import (
    QuestionFrame,
    TarotAction,
    TarotContext,
    TarotOrigin,
    TarotQuestionForm,
    TarotReading,
    TarotSpread,
    TarotSpreadMap,
    TarotStanceLevel,
    TarotVoice,
)
from app.domains.tarot.service import TarotSessionService
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

ENGINE = TarotReadingEngine()
STEP_KEYS = frozenset({"focus", "next", "alternative", "criterion", "opening"})
SPREADS = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
# Every card leans "open" (LEAN_TRY), every card "hold" (CONSIDER; "unclear" for self-care).
CARDS = ("major-sun", "major-star", "wands-8", "cups-9", "pentacles-8")
HOLD_CARDS = ("major-hermit", "swords-4", "pentacles-7", "major-moon", "swords-2")
QUESTIONS = {
    TarotQuestionForm.YES_NO: "Mình có nên làm việc này trong tuần này không?",
    TarotQuestionForm.TIMING: "Khi nào mình nên làm việc này?",
    TarotQuestionForm.HOW: "Làm sao để mình làm việc này?",
    TarotQuestionForm.CHOICE: "Mình nên làm việc này hay để sau?",
}
# Lead-ins that urge acting now; a reading whose cards ask for care never uses them.
URGING = frozenset(tarot_voice.ROAST_ACTION_FRAMES) - frozenset(tarot_voice.ROAST_PREP_FRAMES)
# Words that presume a romantic partner, a date or another event the labels do not establish.
PARTNER_MARKERS = re.compile(
    r"người yêu|người cũ|buổi hẹn|hẹn hò|mới quen|buổi gặp đầu|cà phê đầu tiên"
)
EVENT_MARKERS = re.compile(r"đi chơi|cà phê|món quà|quà|chia việc|tình cảm|lâu rồi|hôm qua")
DROPPED = (
    ("dat_ranh_gioi", "relationships"),
    ("tap_trung", "self_care"),
    ("sap_xep_lai", "self_care"),
)
SOLO_ACTIONS = frozenset(
    {
        "hoc_them",
        "tap_trung",
        "don_dep",
        "ra_ngoai",
        "o_nha",
        "doi_thoi_quen",
        "tu_thuong",
        "viet_ra",
    }
)


def _shows_step(action: str, step: str) -> bool:
    """Direct voices show the step as written; Roast puts its lead-in first and continues in
    lower case after the colon (Tarot pass 2). An empty step matches, as ``endswith`` did."""

    return not step or action == step or action.endswith(f": {step[:1].lower()}{step[1:]}")


def _render(
    action: TarotAction | None,
    topic: TarotContext,
    spread_map: TarotSpreadMap,
    *,
    voice: TarotVoice = TarotVoice.STRAIGHT_WARM,
    question: str | None = None,
    cards: tuple[str, ...] = CARDS,
    form: TarotQuestionForm = TarotQuestionForm.YES_NO,
) -> TarotReading:
    count = len(_POSITIONS[spread_map])
    return ENGINE.render(
        card_ids=cards[:count],
        spread=SPREADS[count],
        spread_map=spread_map,
        context=topic,
        question=question or QUESTIONS[form],
        voice=voice,
        frame=QuestionFrame(form=form, topic=topic, action=action),
    )


def _intake(
    question: str,
    topic: TarotContext,
    cards: tuple[str, ...],
    voice: TarotVoice = TarotVoice.STRAIGHT_WARM,
    spread: TarotSpread | None = None,
) -> TarotReading:
    """Through intake, map selection and render, as the service does."""

    assessment = ENGINE.assess_question(question, topic)
    assert assessment.accepted and assessment.frame is not None, question
    return ENGINE.render(
        card_ids=cards,
        spread=spread or SPREADS[len(cards)],
        context=topic,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )


# ---------------------------------------------------------------- tables


def test_tables_cover_every_action_with_known_keys() -> None:
    actions = {a.value for a in TarotAction}
    topics = {t.value for t in TarotContext}
    assert {a for a, _ in action_copy.ACTION_SCENES} == actions
    assert all(t in topics for _, t in action_copy.ACTION_SCENES)
    assert all((a, "general") in action_copy.ACTION_SCENES for a in actions)
    assert all(r in STEP_KEYS and r in roles.STEP_ROLES for _, r in action_copy.ACTION_STEPS)
    assert (len(action_copy.ACTION_SCENES), len(action_copy.ACTION_STEPS)) == (130, 142)
    for action in actions:
        expected = STEP_KEYS - ({"opening"} if action in SOLO_ACTIONS else set())
        assert {r for a, r in action_copy.ACTION_STEPS if a == action} == expected, action
    # A topic opening exists only where the action has an opening, for a topic it covers.
    for action, topic in action_copy.ACTION_OPENINGS_BY_TOPIC:
        assert (action, "opening") in action_copy.ACTION_STEPS
        assert (action, topic) in action_copy.ACTION_SCENES or (action, topic) in DROPPED


def test_dropped_and_skipped_topics_fall_back_to_the_general_row() -> None:
    for action, topic in DROPPED:
        assert (action, topic) not in action_copy.ACTION_SCENES
        assert (
            action_copy.action_scene(TarotAction(action), TarotContext(topic))
            == (action_copy.ACTION_SCENES[(action, "general")])
        )
    assert action_copy.action_scene(None, TarotContext.WORK) is None
    assert action_copy.action_step(None, "focus", TarotContext.WORK) is None
    assert action_copy.action_step(TarotAction.VIET_RA, "opening", TarotContext.WORK) is None


_ADVICE = re.compile(r"\b(?:nên|hãy|thử|đừng|có thể)\b")
_PREDICTION = re.compile(r"\b(?:sẽ|chắc chắn|định mệnh|số phận|vũ trụ)\b")
_FORCE = re.compile(r"\b(?:phải|nhất định|bắt buộc|chắc chắn)\b")
_PONDER = re.compile(r"cân nhắc thêm|suy nghĩ thêm")


def _steps() -> list[tuple[tuple[str, str], str]]:
    return [*action_copy.ACTION_STEPS.items(), *action_copy.ACTION_OPENINGS_BY_TOPIC.items()]


def test_scenes_follow_c4() -> None:
    """One observable everyday line in the second person: no advice, prediction or verdict."""

    for key, scene in action_copy.ACTION_SCENES.items():
        text = scene.casefold()
        assert len(scene.split()) <= 28, key
        assert "bạn" in text, key
        assert not _ADVICE.search(text), key
        assert not _PREDICTION.search(text), key
        assert not any(f in text for f in BANNED_CORE_FRAGMENTS + OPAQUE_CORE_FRAGMENTS), key


def test_steps_follow_c5() -> None:
    """One small concrete step: no coercion, no promised outcome, no "think it over" for
    self-care, an opening is a sample line, and no step states a lean of its own."""

    markers = tuple(stance.MARKERS.values())
    for key, step in _steps():
        text = step.casefold()
        assert len(step.split()) <= 25, key  # a Roast lead-in adds at most five words
        assert not _FORCE.search(text), key
        assert not _PONDER.search(text), key
        assert not any(m in text for m in markers), key
        assert not any(f in text for f in BANNED_CORE_FRAGMENTS + OPAQUE_CORE_FRAGMENTS), key
    for (_, role), step in action_copy.ACTION_STEPS.items():
        assert step.startswith("Mở lời: “") == (role == "opening")
    assert all(s.startswith("Mở lời: “") for s in action_copy.ACTION_OPENINGS_BY_TOPIC.values())


def test_copy_is_varied_enough_to_read_across_readings() -> None:
    """Wiring condition 2 (AC16): no repeated line; the images the decision flagged stay rare."""

    scenes = list(action_copy.ACTION_SCENES.values())
    steps = list(action_copy.ACTION_STEPS.values())
    assert len(set(scenes)) == len(scenes)
    assert len(set(steps)) == len(steps)
    folded = [s.casefold() for s in scenes]
    assert sum(bool(re.search(r"gõ.*x[oó]a", s)) for s in folded) <= 2
    assert sum("đọc lại" in s for s in folded) <= 3
    step_text = [s.casefold() for s in steps]
    assert sum(bool(re.search(r"ghi lại.*thấy (?:thế nào|ra sao)", s)) for s in step_text) <= 2
    assert sum("tờ giấy dán ở màn hình" in s for s in step_text) <= 1
    for action in TarotAction:
        own = [t for (a, _), t in action_copy.ACTION_STEPS.items() if a == action.value]
        assert len(set(own)) == len(own), action


# ---------------------------------------------------------------- engine


def test_the_step_role_shows_the_action_scene_and_step_and_other_roles_keep_the_card() -> None:
    reading = _render(TarotAction.XIN_LOI, TarotContext.RELATIONSHIPS, TarotSpreadMap.THREE_UNBLOCK)
    *others, step = reading.positions
    assert step.everyday_scene == action_copy.ACTION_SCENES[("xin_loi", "relationships")]
    assert step.small_action == action_copy.ACTION_STEPS[("xin_loi", "next")]
    for position in others:
        assert position.everyday_scene == roles.scene_without_label(
            card_scene(position.card.id, TarotContext.RELATIONSHIPS)
        )
        assert position.small_action is None
    assert reading.provenance.renderer_version == "tarot-renderer-v9"


def test_the_bug_question_gets_an_apology_scene_not_a_dating_scene() -> None:
    """The workbook's root example: an apology question with The Fool no longer shows the
    dating scene; scene and step both speak about the apology."""

    question = "Mình có nên xin lỗi người yêu sau lần cãi nhau tối qua không?"
    assessment = ENGINE.assess_question(question, TarotContext.RELATIONSHIPS)
    assert assessment.accepted and assessment.frame is not None
    assert assessment.frame.action is TarotAction.XIN_LOI
    reading = ENGINE.render(
        card_ids=("major-fool",),
        spread=TarotSpread.ONE_CARD,
        spread_map=TarotSpreadMap.ONE_FOCUS,
        context=TarotContext.RELATIONSHIPS,
        question=question,
        voice=TarotVoice.STRAIGHT_WARM,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )
    (focus,) = reading.positions
    assert "rủ người mới quen" not in focus.everyday_scene
    assert focus.everyday_scene == action_copy.ACTION_SCENES[("xin_loi", "relationships")]
    assert focus.small_action == action_copy.ACTION_STEPS[("xin_loi", "focus")]


def test_the_action_step_wins_over_a_keyword_goal() -> None:
    """Workbook finding 2: "mệt" no longer swaps a writing question's step for the rest step."""

    question = "Mình có nên ghi lại những việc làm mình mệt trong tuần không?"
    topic = TarotContext.ENERGY
    assert "rest" in {goal.key for goal in question_goals(question, topic)}
    reading = _render(TarotAction.VIET_RA, topic, TarotSpreadMap.FIVE_CLARITY, question=question)
    step = reading.positions[-1]
    assert step.small_action == action_copy.ACTION_STEPS[("viet_ra", "next")]


def test_openings_use_the_topic_line_and_solo_actions_keep_the_previous_step() -> None:
    reading = _render(
        TarotAction.DE_XUAT, TarotContext.RELATIONSHIPS, TarotSpreadMap.FIVE_CONVERSATION
    )
    assert (
        reading.positions[-1].small_action
        == (action_copy.ACTION_OPENINGS_BY_TOPIC[("de_xuat", "relationships")])
    )
    work = _render(TarotAction.DE_XUAT, TarotContext.WORK, TarotSpreadMap.FIVE_CONVERSATION)
    assert work.positions[-1].small_action == action_copy.ACTION_STEPS[("de_xuat", "opening")]
    solo = _render(TarotAction.VIET_RA, TarotContext.WORK, TarotSpreadMap.FIVE_CONVERSATION)
    opening = solo.positions[-1]
    previous = goal_action(
        question_goals("Mình có nên làm việc này trong tuần này không?", TarotContext.WORK)[0],
        "opening",
    ) or roles.action_for(_meaning_resource(opening.card.id, TarotContext.WORK))
    assert opening.small_action == previous
    assert opening.everyday_scene == action_copy.ACTION_SCENES[("viet_ra", "work")]


def _meaning_resource(card_id: str, topic: TarotContext) -> str:
    from app.domains.tarot.engine import _CardMeaning
    from app.domains.tarot.knowledge import card_by_id

    return _CardMeaning.for_context(card_by_id(card_id), topic).resource


def test_a_frame_without_an_action_renders_as_before() -> None:
    reading = _render(None, TarotContext.WORK, TarotSpreadMap.THREE_UNBLOCK)
    step = reading.positions[-1]
    assert step.everyday_scene == roles.scene_without_label(
        card_scene(step.card.id, TarotContext.WORK)
    )
    assert step.small_action not in set(action_copy.ACTION_STEPS.values())


def test_roast_keeps_its_lead_in_before_the_action_step() -> None:
    reading = _render(
        TarotAction.TU_CHOI, TarotContext.WORK, TarotSpreadMap.THREE_UNBLOCK, voice=TarotVoice.ROAST
    )
    step = reading.positions[-1].small_action or ""
    assert _shows_step(step, action_copy.ACTION_STEPS[("tu_choi", "next")])
    assert step != action_copy.ACTION_STEPS[("tu_choi", "next")]


@pytest.mark.parametrize("voice", list(TarotVoice))
def test_every_action_topic_and_map_passes_the_gates(voice: TarotVoice) -> None:
    """Every action x topic x spread map renders through all reading gates (role_fit,
    stance_consistent, no_decision_or_prediction and the plain-language review); cards that
    lean "open" give the action's own step."""

    for action, topic, spread_map in itertools.product(TarotAction, TarotContext, TarotSpreadMap):
        reading = _render(action, topic, spread_map, voice=voice)
        step = reading.positions[-1]
        assert reading.stance is not None
        assert reading.stance.level is TarotStanceLevel.LEAN_TRY
        expected = action_copy.action_step(action, step.key, topic)
        if expected is not None:
            assert _shows_step(step.small_action or "", expected)
        # The question names no partner: partner-only rows give way to the general row.
        assert step.everyday_scene == action_copy.action_scene(action, topic, partner=False)


# ---------------------------------------------------------------- whole-output composition (r47)


def test_preparation_steps_cover_every_action_but_self_care_and_follow_c5() -> None:
    self_care = {a.value for a in stance.SELF_CARE_ACTIONS}
    assert set(action_copy.PREP_STEPS) == (
        {a.value for a in TarotAction} - self_care | {action_copy.CHOICE_STEP}
    )
    executing = set(action_copy.ACTION_STEPS.values()) | set(
        action_copy.ACTION_OPENINGS_BY_TOPIC.values()
    )
    markers = tuple(stance.MARKERS.values())
    prep = list(action_copy.PREP_STEPS.values())
    assert len(set(prep)) == len(prep)
    for key, step in action_copy.PREP_STEPS.items():
        text = step.casefold()
        assert step not in executing, key
        assert len(step.split()) <= 25, key
        assert not step.startswith("Mở lời"), key
        assert not _FORCE.search(text) and not _PONDER.search(text), key
        assert not any(m in text for m in markers), key
        assert not any(f in text for f in BANNED_CORE_FRAGMENTS + OPAQUE_CORE_FRAGMENTS), key


def test_the_send_question_gets_a_preparation_step_in_every_voice() -> None:
    """Codex r47 finding 1: "cân nhắc thêm trước khi gửi đi" never sits beside "bấm gửi", and the
    Roast lead-in never says "làm liền" under "Khoan đạp ga"."""

    question = "Mình có nên gửi bản thảo này đi không?"
    for voice in TarotVoice:
        reading = _intake(question, TarotContext.WORK, ("major-hermit",), voice)
        assert reading.stance is not None
        assert reading.stance.level is TarotStanceLevel.CONSIDER
        assert reading.stance.action is TarotAction.GUI_DI
        (focus,) = reading.positions
        step = focus.small_action or ""
        assert "bấm gửi" not in step and not step.startswith(tuple(URGING)), voice
        assert _shows_step(step, action_copy.PREP_STEPS["gui_di"]), voice
        assert focus.everyday_scene == action_copy.ACTION_SCENES[("gui_di", "work")]
    # The same question with an "open" card keeps the sending step.
    leaning = _intake(question, TarotContext.WORK, ("major-sun",))
    assert leaning.stance is not None and leaning.stance.level is TarotStanceLevel.LEAN_TRY
    assert leaning.positions[0].small_action == action_copy.ACTION_STEPS[("gui_di", "focus")]


@pytest.mark.parametrize("voice", list(TarotVoice))
def test_the_step_agrees_with_the_stance_for_every_action_form_and_map(voice: TarotVoice) -> None:
    """Complete outputs across stance levels and forms: cautious, unclear and "when" readings
    prepare the action (self-care keeps its own step); an unsettled choice names neither option;
    no reading whose cards ask for care uses a lead-in that urges acting now."""

    self_care = stance.SELF_CARE_ACTIONS
    forms = (TarotQuestionForm.YES_NO, TarotQuestionForm.TIMING, TarotQuestionForm.CHOICE)
    for action, spread_map, form in itertools.product(TarotAction, TarotSpreadMap, forms):
        for topic in (TarotContext.GENERAL, TarotContext.RELATIONSHIPS, TarotContext.ENERGY):
            reading = _render(action, topic, spread_map, voice=voice, cards=HOLD_CARDS, form=form)
            step = reading.positions[-1]
            text = step.small_action or ""
            level = reading.stance.level if reading.stance is not None else None
            if form is TarotQuestionForm.CHOICE:
                assert level in {TarotStanceLevel.CLARIFY_CHOICE, TarotStanceLevel.UNCLEAR}
                expected = action_copy.PREP_STEPS[action_copy.CHOICE_STEP]
                assert step.everyday_scene == roles.scene_without_label(
                    card_scene(step.card.id, topic)
                )
            elif action in self_care:
                assert level is not TarotStanceLevel.CONSIDER
                expected = action_copy.action_step(action, step.key, topic) or ""
            else:
                assert form is TarotQuestionForm.TIMING or level is TarotStanceLevel.CONSIDER
                expected = action_copy.PREP_STEPS[action.value]
            assert _shows_step(text, expected), (action, spread_map, form, topic)
            assert not text.startswith(tuple(URGING)), (action, spread_map, form, topic)


def test_a_choice_the_cards_settle_gets_the_chosen_option_step() -> None:
    question = "Mình nên nhắn lại hay chờ thêm?"
    assessment = ENGINE.assess_question(question, TarotContext.RELATIONSHIPS)
    assert assessment.frame is not None
    assert stance.split_choice(question, asked_clause=True) == (
        TarotAction.NHAN_LAI,
        TarotAction.CHO_THEM,
    )
    # option_a holds, option_b is open: the cards choose "chờ thêm".
    cards = ("major-sun", "major-hermit", "major-star", "cups-9", "pentacles-8")
    reading = ENGINE.render(
        card_ids=cards,
        spread=TarotSpread.FIVE_CARD,
        spread_map=TarotSpreadMap.FIVE_CHOICE,
        context=TarotContext.RELATIONSHIPS,
        question=question,
        voice=TarotVoice.STRAIGHT_WARM,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )
    assert reading.stance is not None and reading.stance.action is TarotAction.CHO_THEM
    step = reading.positions[-1]
    assert step.small_action == action_copy.action_step(
        TarotAction.CHO_THEM, step.key, TarotContext.RELATIONSHIPS
    )
    assert step.everyday_scene == action_copy.ACTION_SCENES[("cho_them", "relationships")]


def test_partner_rows_are_exactly_the_scenes_that_presume_a_partner() -> None:
    marked = {
        key
        for key, scene in action_copy.ACTION_SCENES.items()
        if PARTNER_MARKERS.search(scene.casefold())
    }
    # Reviewed by hand: a marker word that is not about a partner (a new group of friends,
    # after-work appointments), and a date without a marker word (two weeks of evening texts and
    # a photo of a new café).
    not_partner = {("ra_ngoai", "relationships"), ("dat_ranh_gioi", "energy")}
    assert action_copy.PARTNER_SCENES == (marked - not_partner) | {("hen_gap", "relationships")}
    for key, opening in action_copy.ACTION_OPENINGS_BY_TOPIC.items():
        text = opening.casefold()
        assert not PARTNER_MARKERS.search(text) and not EVENT_MARKERS.search(text), key


def test_names_partner_reads_closed_words_only() -> None:
    assert question_frame.names_partner("Mình có nên nhắn lại cho người yêu không?")
    assert question_frame.names_partner("Có nên hẹn hò lại với người cũ?")
    assert question_frame.names_partner("Mình có nên xin lỗi chồng không?")
    assert not question_frame.names_partner("Mình có nên nhắn lại cho mẹ không?")
    assert not question_frame.names_partner("Mình có nên nhắn lại cho bạn thân không?")


@pytest.mark.parametrize(
    ("who", "partner"),
    [("mẹ", False), ("bạn thân", False), ("anh trai", False), ("người yêu", True)],
)
def test_reply_questions_about_family_friends_and_partners(who: str, partner: bool) -> None:
    """Codex r47 finding 2, through intake and rendering: replying after an argument never
    invents an outing, and a partner scene shows only when the question names a partner."""

    question = f"Mình có nên nhắn lại cho {who} sau lần cãi nhau không?"
    assessment = ENGINE.assess_question(question, TarotContext.RELATIONSHIPS)
    assert assessment.frame is not None
    assert (assessment.frame.topic, assessment.frame.action) == (
        TarotContext.RELATIONSHIPS,
        TarotAction.NHAN_LAI,
    )
    for cards in (CARDS, HOLD_CARDS):
        for voice in TarotVoice:
            reading = _intake(question, TarotContext.RELATIONSHIPS, cards, voice)
            assert reading.spread_map is TarotSpreadMap.FIVE_CONVERSATION
            step = reading.positions[-1]
            text = f"{step.everyday_scene} {step.small_action}".casefold()
            assert not EVENT_MARKERS.search((step.small_action or "").casefold()), (who, voice)
            assert bool(PARTNER_MARKERS.search(text)) is partner, (who, voice)
            expected_scene = ("nhan_lai", "relationships" if partner else "general")
            assert step.everyday_scene == action_copy.ACTION_SCENES[expected_scene]
            if cards is CARDS:
                assert _shows_step(
                    step.small_action or "",
                    action_copy.ACTION_OPENINGS_BY_TOPIC[("nhan_lai", "relationships")],
                )
            else:
                assert _shows_step(step.small_action or "", action_copy.PREP_STEPS["nhan_lai"])


# ---------------------------------------------------------------- stored readings stay frozen


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[Database]:
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'tarot-action-copy.db'}")
    await db.initialize()
    try:
        yield db
    finally:
        await db.dispose()


async def _guest(db: Database) -> UUID:
    guest_id, now = uuid4(), datetime.now(UTC)
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id, token_hash=guest_id.bytes * 2, csrf_hash=b"c" * 32, state="active",
                onboarding_status="birth_pending", created_at=now, last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )  # fmt: skip
    return guest_id


async def test_a_drawn_reading_keeps_its_text_when_the_copy_changes(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = TarotSessionService(
        database.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"t" * 32)),
        SecretHasher(b"h" * 32),
    )
    guest = await _guest(database)
    view = await service.start(
        guest_id=guest, context=TarotContext.RELATIONSHIPS,
        question="Mình có nên xin lỗi người yêu sau lần cãi nhau tối qua không?",
        spread=TarotSpread.ONE_CARD, voice=TarotVoice.PLAYFUL_GROUNDED, origin=TarotOrigin.DIRECT,
        idempotency_key="tarot-action-copy-frozen-000001",
    )  # fmt: skip
    view = await service.select_card(
        guest_id=guest, session_id=view.id, fan_index=7, expected_version=view.version
    )
    assert view.reading is not None
    drawn = view.reading
    assert (
        drawn.positions[0].everyday_scene
        == (action_copy.ACTION_SCENES[("xin_loi", "relationships")])
    )
    edited = {key: f"{text} (đã sửa)" for key, text in action_copy.ACTION_SCENES.items()}
    monkeypatch.setattr(action_copy, "ACTION_SCENES", edited)
    reopened = await service.get(guest, view.id)
    assert reopened.reading == drawn
    # Not vacuous: rendering the same draw again now gives the edited scene.
    redrawn = ENGINE.render(
        card_ids=tuple(position.card.id for position in drawn.positions),
        spread=TarotSpread.ONE_CARD,
        spread_map=drawn.spread_map,
        context=TarotContext.RELATIONSHIPS,
        question=drawn.question,
        voice=drawn.voice,
        question_intent=drawn.question_intent,
        frame=ENGINE.assess_question(drawn.question, TarotContext.RELATIONSHIPS).frame,
    )
    assert redrawn.positions[0].everyday_scene.endswith("(đã sửa)")


FIXTURE = Path(__file__).parent / "fixtures" / "tarot-reading-v7-xin-loi.json"


async def test_a_literal_v7_reading_is_served_unchanged(database: Database) -> None:
    """A reading persisted under renderer v7 (rendered at 010b27e, the workbook's root bug) is
    returned byte for byte; the current renderer would show the apology scene instead."""

    stored = json.loads(FIXTURE.read_text())
    assert stored["reading"]["provenance"]["renderer_version"] == "tarot-renderer-v7"
    service = TarotSessionService(
        database.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"t" * 32)),
        SecretHasher(b"h" * 32),
    )
    guest = await _guest(database)
    view = await service.start(
        guest_id=guest, context=TarotContext.RELATIONSHIPS,
        question=stored["reading"]["question"],
        spread=TarotSpread.ONE_CARD, voice=TarotVoice.PLAYFUL_GROUNDED, origin=TarotOrigin.DIRECT,
        idempotency_key="tarot-action-copy-v7-fixture-1",
    )  # fmt: skip
    view = await service.select_card(
        guest_id=guest, session_id=view.id, fan_index=7, expected_version=view.version
    )
    async with database.sessions() as session, session.begin():
        row = await session.get(TarotSessionRow, view.id)
        assert row is not None
        payload = service._decrypt(row)
        payload["reading"] = stored["reading"]
        row.payload_ciphertext = service._encrypt(row.id, payload)
    reopened = await service.get(guest, view.id)
    assert reopened.reading is not None
    assert reopened.reading.model_dump(mode="json") == stored["reading"]
    (old,) = reopened.reading.positions
    assert old.everyday_scene.startswith("Có lần bạn muốn rủ người mới quen")
    current = _intake(stored["reading"]["question"], TarotContext.RELATIONSHIPS, ("major-fool",))
    assert current.positions[0].everyday_scene != old.everyday_scene
