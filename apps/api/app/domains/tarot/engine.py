from __future__ import annotations

import re
from dataclasses import dataclass

from app.domains.readings.review_agent import (
    OPAQUE_CORE_FRAGMENTS,
    ContentReviewAgent,
    ReviewSample,
)
from app.domains.tarot import question_frame, roles, stance
from app.domains.tarot.context_readings import CONTEXT_READINGS, CONTEXT_SCENES
from app.domains.tarot.examples import example_for
from app.domains.tarot.knowledge import (
    KNOWLEDGE_VERSION,
    card_by_id,
    source_ids_for_concepts,
)
from app.domains.tarot.meaning_brief import card_links, goal_action, question_goals
from app.domains.tarot.models import (
    QUESTION_RULES_VERSION,
    QuestionFrame,
    TarotCard,
    TarotContext,
    TarotQuestionAssessment,
    TarotQuestionForm,
    TarotQuestionIntent,
    TarotReading,
    TarotReadingPosition,
    TarotReadingProvenance,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.quality import prose_is_safe
from app.domains.tarot.relationship_readings import RELATIONSHIP_READINGS
from app.domains.tarot.voice import (
    SUMMARY_OPENERS,
    action_frame,
    effective_voice,
    meaning_tail,
    roast_headline,
)


class TarotContentRejected(ValueError):
    pass


TAROT_RENDERER_VERSION = "tarot-renderer-v6"
# B2-2: role_fit and no_decision_or_prediction join the gates for framed (B2-1+) readings.
TAROT_GATE_VERSION = "tarot-gates-v5"


@dataclass(frozen=True)
class _CardMeaning:
    core: str
    tension: str
    resource: str

    @classmethod
    def for_context(cls, card: TarotCard, context: TarotContext) -> _CardMeaning:
        if context is TarotContext.RELATIONSHIPS:
            try:
                return cls(*RELATIONSHIP_READINGS[card.id])
            except KeyError as exc:
                raise TarotContentRejected("missing relationship meaning") from exc
        if context.value in CONTEXT_READINGS:
            try:
                return cls(*CONTEXT_READINGS[context.value][card.id])
            except KeyError as exc:
                raise TarotContentRejected("missing contextual meaning") from exc
        return cls(card.core, card.tension, card.resource)


_POSITIONS: dict[TarotSpreadMap, tuple[tuple[str, str], ...]] = {
    TarotSpreadMap.ONE_FOCUS: (("focus", "Điều đáng nhìn lúc này"),),
    TarotSpreadMap.THREE_UNBLOCK: (
        ("clear", "Điều đã rõ"),
        ("missed", "Điều dễ bỏ sót"),
        ("next", "Một bước nhỏ có thể thử"),
    ),
    TarotSpreadMap.FIVE_CLARITY: (
        ("facts", "Điều đã có dữ kiện"),
        ("assumption", "Phần mình đang tự điền"),
        ("need", "Nhu cầu thật phía dưới"),
        ("agency", "Phần mình chọn được"),
        ("next", "Một bước để kiểm chứng"),
    ),
    TarotSpreadMap.FIVE_LOOP: (
        ("trigger", "Điều thường châm ngòi"),
        ("habit", "Phản xạ quen thuộc"),
        ("payoff", "Điều phản xạ này giúp ngay lúc đó"),
        ("cost", "Cái giá về sau"),
        ("alternative", "Một phản ứng khác để thử"),
    ),
    TarotSpreadMap.FIVE_CHOICE: (
        ("need", "Điều mình không muốn đánh đổi"),
        ("option_a", "Hướng A: điều được và cái giá"),
        ("option_b", "Hướng B: điều được và cái giá"),
        ("tradeoff", "Khác biệt thật sự giữa hai hướng"),
        ("criterion", "Tiêu chí để tự chốt"),
    ),
    TarotSpreadMap.FIVE_CONVERSATION: (
        ("facts", "Điều đã thật sự xảy ra"),
        ("feeling", "Cảm xúc của mình"),
        ("need", "Điều mình cần"),
        ("boundary", "Ranh giới cần rõ"),
        ("opening", "Cách mở lời"),
    ),
}

_CHOICE_SHAPE = re.compile(
    r"\b(?:giữa|hay là|nên chọn|lựa chọn|phương án|ở lại|rời đi)\b",
    re.IGNORECASE,
)
_LOOP_SHAPE = re.compile(r"\b(?:lặp lại|lần nào cũng|cứ mỗi|vòng lặp|quen thuộc)\b", re.IGNORECASE)
_CONVERSATION_SHAPE = re.compile(
    r"\b(?:nói chuyện|mở lời|nhắn|trả lời|hỏi thẳng|xin lỗi|ranh giới)\b",
    re.IGNORECASE,
)

_THIRD_PARTY = re.compile(
    r"\b(?:người ấy|họ|anh ấy|cô ấy|crush)\b.{0,28}\b(?:nghĩ|yêu|thích|muốn|định|có)\b",
    re.IGNORECASE,
)
# "Khi nào / bao giờ" about one's own action is reframed as readiness (US-20 AC05, B2-1);
# a timing question about an event or another person is still a prediction (see assess).
_CERTAINTY = re.compile(r"\b(?:chắc chắn|có quay lại|sẽ xảy ra)\b", re.IGNORECASE)
# The certainty rule of tarot-question-rules-v1, kept verbatim so a session accepted under v1
# renders under v1 (US-20 AC17). Do not edit: it defines what earlier sessions were promised.
_CERTAINTY_V1 = re.compile(
    r"\b(?:chắc chắn|bao giờ|khi nào|có quay lại|sẽ xảy ra)\b", re.IGNORECASE
)
_LEGACY_RULES_VERSION = "tarot-question-rules-v1"
_HIGH_STAKES = re.compile(
    r"\b(?:bệnh|thuốc|mang thai|tự tử|kiện|pháp lý|đầu tư|cổ phiếu|vay tiền|chẩn đoán)\b",
    re.IGNORECASE,
)


def _position_views(
    positions: tuple[TarotReadingPosition, ...], context: TarotContext
) -> list[stance.PositionView]:
    views = []
    for position in positions:
        meaning = _CardMeaning.for_context(position.card, context)
        views.append(
            stance.PositionView(
                key=position.key,
                label=position.label,
                card_id=position.card.id,
                title=position.card.title_vi,
                core=meaning.core,
                tension=_tension_parts(meaning.tension)[0],
                resource=_resource_step(meaning.resource),
            )
        )
    return views


def _authored_by_engine(reading: TarotReading) -> str:
    """Reading prose minus the reviewed catalog text it quotes. A card's pitfall may name a
    feared prediction ("coi ... là chuyện chắc sẽ xảy ra") and an example scene may describe a
    choice someone faced ("bạn phải chọn ...") without the reading deciding or predicting."""

    text = " ".join(
        [reading.headline, reading.summary, reading.closing_prompt]
        + [
            value
            for position in reading.positions
            for value in (
                position.meaning_here,
                position.reflection_question,
                position.small_action or "",
            )
        ]
    )
    for position in reading.positions:
        meaning = _CardMeaning.for_context(position.card, reading.context)
        for quoted in (meaning.core, meaning.tension, meaning.resource):
            text = text.replace(quoted, " ")
    return text.lower()


_ABSTRACT_FILLER = (
    "tín hiệu vũ trụ",
    "mọi thứ xảy ra đều có lý do",
    "hãy tin vào hành trình",
    "năng lượng đang dịch chuyển",
    "khả năng dẫn dắt và chịu trách nhiệm khi xử lý",
    "một việc cần thêm người hoặc nguồn lực phối hợp",
    "sự điều chỉnh để dòng trao đổi cân hơn",
)

_INTENT_HEADLINES: dict[TarotQuestionIntent, str] = {
    TarotQuestionIntent.CLARITY: "Trước hết, tách điều đã xảy ra khỏi điều bạn đang đoán.",
    TarotQuestionIntent.BOUNDARY: "Nói rõ giới hạn trước khi cố làm vừa lòng tất cả.",
    TarotQuestionIntent.NEXT_STEP: "Chọn một bước nhỏ để thử, chưa cần chốt cả câu chuyện.",
    TarotQuestionIntent.COMMUNICATION: "Nói câu chính trước; phần giải thích để sau.",
    TarotQuestionIntent.SELF_CHECK: "Gọi đúng điều bạn đang cảm và điều bạn đang cần.",
}


def _tension_parts(value: str) -> tuple[str, str | None]:
    first, separator, second = value.partition("; đồng thời dễ ")
    return first, second if separator else None


def _resource_step(value: str) -> str:
    return value.partition(", rồi ")[0]


def _sentence_start(value: str) -> str:
    return value[:1].upper() + value[1:]


class TarotReadingEngine:
    @staticmethod
    def positions_for(spread_map: TarotSpreadMap) -> tuple[tuple[str, str], ...]:
        return _POSITIONS[spread_map]

    def assess_question(self, question: str, context: TarotContext) -> TarotQuestionAssessment:
        """Intake rules, in order: too short or vague -> high stakes -> another person's mind
        -> certainty (US-20 AC03). Accepted questions get their ``QuestionFrame`` once here."""

        normalized = " ".join(question.strip().split())
        if len(normalized) < 8 or question_frame.is_vague(normalized):
            return self._clarify(normalized)
        boundary = self._boundary_rejection(normalized)
        if boundary is not None:
            return boundary
        return TarotQuestionAssessment(
            accepted=True,
            normalized_question=normalized,
            intent=self._classify_intent(normalized, context),
            frame=question_frame.frame_question(normalized, context),
            rules_version=QUESTION_RULES_VERSION,
        )

    def _boundary_rejection(
        self, normalized: str, rules_version: str = QUESTION_RULES_VERSION
    ) -> TarotQuestionAssessment | None:
        """Safety boundary of ``rules_version``, shared by intake and rendering.

        Vagueness is an intake-only rule. Rendering applies the rules the session was accepted
        under, so a v1 session (no stored frame) is never refused by a rule added later.
        """

        if _HIGH_STAKES.search(normalized):
            return TarotQuestionAssessment(
                accepted=False,
                normalized_question=normalized,
                explanation=(
                    "Tarot không thay thế dữ kiện hay chuyên gia trong chuyện sức khỏe, "
                    "pháp lý hoặc tiền bạc. Mình có thể đổi sang câu hỏi về cách bạn "
                    "chuẩn bị cho một cuộc trao đổi an toàn hơn."
                ),
                suggested_reframe=(
                    "Mình cần chuẩn bị câu hỏi và dữ kiện nào trước khi tìm người có chuyên môn?"
                ),
            )
        if _THIRD_PARTY.search(normalized):
            return TarotQuestionAssessment(
                accepted=False,
                normalized_question=normalized,
                explanation=(
                    "Lá Hỏi không đoán đầu người khác; mình đổi trọng tâm về phần mình "
                    "có thể quan sát và hỏi thẳng."
                ),
                suggested_reframe="Trong kết nối này, phần mình cần nhìn rõ hoặc hỏi thẳng là gì?",
            )
        if rules_version == _LEGACY_RULES_VERSION:
            refused = _CERTAINTY_V1.search(normalized) is not None
        else:
            refused = _CERTAINTY.search(normalized) is not None
            if not refused and question_frame.classify_form(normalized) is TarotQuestionForm.TIMING:
                owner = question_frame.timing_owner(normalized)
                if owner is question_frame.TimingOwner.UNCLEAR:
                    # No identified own action ("Khi nào mình nên?", "Khi nào mình giàu?"):
                    # ask what the reader wants to do instead of guessing either way.
                    return self._clarify(normalized)
                refused = owner is question_frame.TimingOwner.OTHER
        if refused:
            return TarotQuestionAssessment(
                accepted=False,
                normalized_question=normalized,
                rules_version=QUESTION_RULES_VERSION,
                explanation=(
                    "Câu hỏi đang tìm một kết luận chắc chắn; bài sẽ hữu ích hơn "
                    "khi neo vào điều bạn có thể quan sát."
                ),
                suggested_reframe="Mình nên quan sát điều gì trước khi quyết định bước tiếp theo?",
            )
        return None

    @staticmethod
    def _clarify(normalized: str) -> TarotQuestionAssessment:
        return TarotQuestionAssessment(
            accepted=False,
            normalized_question=normalized,
            rules_version=QUESTION_RULES_VERSION,
            explanation=(
                "Câu hỏi cần thêm một tình huống cụ thể để bài đọc không thành lời chung chung."
            ),
            suggested_reframe="Trong chuyện này, mình cần nhìn rõ điều gì trước?",
        )

    def render(
        self,
        *,
        card_ids: tuple[str, ...],
        spread: TarotSpread,
        spread_map: TarotSpreadMap | None = None,
        context: TarotContext,
        question: str,
        voice: TarotVoice,
        question_intent: TarotQuestionIntent | None = None,
        frame: QuestionFrame | None = None,
    ) -> TarotReading:
        """Render once. ``frame`` is the session's stored QuestionFrame (None for sessions
        started before B2-1, which render exactly as before); it is never recomputed here."""

        normalized = " ".join(question.strip().split())
        rules = QUESTION_RULES_VERSION if frame is not None else _LEGACY_RULES_VERSION
        if len(normalized) < 8 or self._boundary_rejection(normalized, rules) is not None:
            raise TarotContentRejected("question must pass reflection boundary")
        intent = question_intent or self._classify_intent(normalized, context)
        assessment = TarotQuestionAssessment(
            accepted=True, normalized_question=normalized, intent=intent, frame=frame
        )
        # Sensitive questions never get the roast frame, whatever was requested.
        voice = effective_voice(voice, assessment.normalized_question)
        roast = voice is TarotVoice.ROAST
        resolved_map = spread_map or self.choose_spread_map(
            spread, intent, assessment.normalized_question
        )
        positions = _POSITIONS[resolved_map]
        if len(card_ids) != len(positions) or len(set(card_ids)) != len(card_ids):
            raise TarotContentRejected("card count must match spread and be unique")
        rendered: list[TarotReadingPosition] = []
        meanings: list[_CardMeaning] = []
        goals = question_goals(assessment.normalized_question, context)
        used_tails: set[str] = set()
        for index, ((key, label), card_id) in enumerate(zip(positions, card_ids, strict=True)):
            try:
                card = card_by_id(card_id)
            except KeyError as exc:
                raise TarotContentRejected("unknown card") from exc
            contextual_meaning = _CardMeaning.for_context(card, context)
            goal = goals[index % len(goals)]
            purposeful_action = goal_action(goal, key)
            meanings.append(contextual_meaning)
            if frame is not None:
                # B2-2: sessions with a stored QuestionFrame read each position by its role.
                rendered.append(
                    self._role_position(
                        key=key,
                        label=label,
                        card=card,
                        meaning=contextual_meaning,
                        context=context,
                        voice=voice,
                        index=index,
                        goal_step=purposeful_action,
                        reflection=(
                            goal.reflection
                            if goal.key != "general" and index == 0
                            else self._reflection(key, context, intent)
                        ),
                        used_tails=used_tails,
                    )
                )
                continue
            meaning = self._meaning(contextual_meaning, key, voice)
            tail = meaning_tail(key, context) if roast else None
            if tail is not None and tail not in used_tails:
                # One playful tail per reading; a repeated tail would read as filler.
                used_tails.add(tail)
                meaning = f"{meaning} {tail}"
            scene = (
                CONTEXT_SCENES[context.value][card.id]
                if context.value in CONTEXT_SCENES
                else example_for(card.id, context.value)
            )
            reflection = (
                goal.reflection
                if goal.key != "general" and index == 0
                else self._reflection(key, context, intent)
            )
            if roast:
                # Same instruction as the default voice; only the playful lead-in differs.
                step = purposeful_action or (
                    f"{_sentence_start(_resource_step(contextual_meaning.resource))}."
                )
                action = f"{action_frame(index, context)} {step}"
            else:
                action = purposeful_action or self._action(contextual_meaning.resource, voice)
            rendered.append(
                TarotReadingPosition(
                    key=key,
                    label=label,
                    card=card,
                    meaning_here=meaning,
                    everyday_scene=scene,
                    reflection_question=reflection,
                    small_action=action,
                )
            )
        reading_stance = None
        reserve = (
            len(question_frame.READINESS_NOTE.split())
            if frame is not None and frame.form is TarotQuestionForm.TIMING
            else 0
        )
        if frame is not None:
            # B2-3: lean, a summary that links the roles, and a dynamic headline (AC08-AC11).
            views = _position_views(tuple(rendered), context)
            reading_stance = stance.stance_for(
                frame.form, frame.action, assessment.normalized_question, frame.topic, views
            )
            lead = tuple(goal.meaning for goal in goals if goal.key != "general")
            summary = stance.linked_summary(views, lead, reserve)
        else:
            summary = self._summary(
                tuple(rendered), tuple(meanings), context, assessment.normalized_question
            )
        if roast:
            opener = SUMMARY_OPENERS[context]
            # The opener is optional framing; it never displaces a selected card.
            if len(f"{opener} {summary}".split()) + reserve <= 180:
                summary = f"{opener} {summary}"
        headline = roast_headline(intent, context) if roast else _INTENT_HEADLINES[intent]
        if frame is not None and frame.form is TarotQuestionForm.TIMING:
            # AC05: answer "when" as what to have ready first, and say why there is no date.
            headline = question_frame.readiness_headline(voice)
            summary = f"{question_frame.READINESS_NOTE} {summary}"
        if frame is not None and not roast:
            # AC11: a headline from form + lean (or action/topic) + the focal card. The Roast
            # headline stays until its own frames exist (AC19, B2-4).
            focal = next((view for view in views if roles.ROLES[view.key].step), views[-1])
            others = [view for view in views if view is not focal]
            second = next(
                (v for v in others if roles.ROLES[v.key].field is roles.RoleField.TENSION),
                others[0] if others else None,
            )
            headline = stance.dynamic_headline(
                frame.form, reading_stance, frame.action, frame.topic, focal, second
            )
        reading = TarotReading(
            headline=headline,
            summary=summary,
            question=assessment.normalized_question,
            question_intent=intent,
            context=context,
            spread=spread,
            spread_map=resolved_map,
            voice=voice,
            positions=tuple(rendered),
            stance=reading_stance,
            closing_prompt=(
                "Đừng cố nhớ hết cả bài. Chọn một điều đúng với chuyện thật và một việc "
                "bạn có thể làm trong 24 giờ tới."
            ),
            disclaimer=(
                "Bài Tarot là một góc tự soi từ lá bạn đã chọn, không phải dự đoán "
                "chắc chắn hay lời thay cho quyết định của bạn."
            ),
            provenance=TarotReadingProvenance(
                knowledge_version=KNOWLEDGE_VERSION,
                renderer_version=TAROT_RENDERER_VERSION,
                # Legacy sessions keep their v4 provenance byte for byte (AC17).
                gate_version=TAROT_GATE_VERSION if frame is not None else "tarot-gates-v4",
                question_rules_version=rules,
                source_ids=self._reading_sources(tuple(position.card for position in rendered)),
            ),
        )
        self.validate(reading)
        return reading

    @staticmethod
    def _role_position(
        *,
        key: str,
        label: str,
        card: TarotCard,
        meaning: _CardMeaning,
        context: TarotContext,
        voice: TarotVoice,
        index: int,
        goal_step: str | None,
        reflection: str,
        used_tails: set[str],
    ) -> TarotReadingPosition:
        """One position read by its role (US-20 AC07, AC12): the role's card field and frame,
        a scene without a duplicate "Ví dụ:" label, and an action only on a step role."""

        tension, _ = _tension_parts(meaning.tension)
        text = roles.meaning_for(
            key, core=meaning.core, tension=tension, resource=_resource_step(meaning.resource)
        )
        if voice is TarotVoice.GENTLE_SPECIFIC:
            text += " Chưa cần kết luận ngay; hãy kiểm tra bằng chuyện thật trước."
        if voice is TarotVoice.ROAST:
            tail = meaning_tail(key, context)
            if tail not in used_tails:
                used_tails.add(tail)  # one playful tail per reading
                text = f"{text} {tail}"
        scene = (
            CONTEXT_SCENES[context.value][card.id]
            if context.value in CONTEXT_SCENES
            else example_for(card.id, context.value)
        )
        action: str | None = None
        if key in roles.STEP_ROLES:
            step = goal_step or roles.action_for(meaning.resource)
            action = f"{action_frame(index, context)} {step}" if voice is TarotVoice.ROAST else step
        return TarotReadingPosition(
            key=key,
            label=label,
            card=card,
            meaning_here=text,
            everyday_scene=roles.scene_without_label(scene),
            reflection_question=reflection,
            small_action=action,
        )

    @staticmethod
    def validate(reading: TarotReading) -> None:
        TarotReadingEngine._gate(reading)

    @staticmethod
    def choose_spread_map(
        spread: TarotSpread,
        intent: TarotQuestionIntent,
        question: str,
    ) -> TarotSpreadMap:
        if spread is TarotSpread.ONE_CARD:
            return TarotSpreadMap.ONE_FOCUS
        if spread is TarotSpread.THREE_CARD:
            return TarotSpreadMap.THREE_UNBLOCK
        if _CHOICE_SHAPE.search(question):
            return TarotSpreadMap.FIVE_CHOICE
        if _LOOP_SHAPE.search(question):
            return TarotSpreadMap.FIVE_LOOP
        if intent in {
            TarotQuestionIntent.COMMUNICATION,
            TarotQuestionIntent.BOUNDARY,
        } or _CONVERSATION_SHAPE.search(question):
            return TarotSpreadMap.FIVE_CONVERSATION
        return TarotSpreadMap.FIVE_CLARITY

    @staticmethod
    def _summary(
        positions: tuple[TarotReadingPosition, ...],
        meanings: tuple[_CardMeaning, ...],
        context: TarotContext,
        question: str,
    ) -> str:
        goals = tuple(goal for goal in question_goals(question, context) if goal.key != "general")
        per_card = " ".join(
            f"{position.card.title_vi}: "
            + (
                f"{_sentence_start(meaning.core if goals else _resource_step(meaning.resource))}."
                if position.key in {"next", "agency", "alternative", "boundary", "opening"}
                else f"Dễ vướng ở việc {_tension_parts(meaning.tension)[0]}."
                if position.key in {"missed", "assumption", "habit", "cost"}
                else f"{_sentence_start(meaning.core)}."
            )
            for position, meaning in zip(positions, meanings, strict=True)
        )
        # Keep every selected card. Optional links/goals must fit as whole
        # sentences; a long accepted question must not lose its entire reading.
        summary_parts = [per_card]
        for link in card_links(positions, context):
            meaning = str(link["meaning"])
            if len(" ".join([*summary_parts, meaning]).split()) <= 180:
                summary_parts.append(meaning)
        goal_copy: list[str] = []
        # The summary answers one main thread. Secondary goals remain available
        # in the position/context brief, not a stack of generic advice up front.
        for goal in goals[:1]:
            if len(" ".join([*goal_copy, goal.meaning, *summary_parts]).split()) <= 180:
                goal_copy.append(goal.meaning)
        return " ".join([*goal_copy, *summary_parts])

    @staticmethod
    def _meaning(
        card: _CardMeaning,
        position_key: str,
        voice: TarotVoice,
    ) -> str:
        tension, secondary_tension = _tension_parts(card.tension)
        secondary_copy = (
            f" Bạn cũng có thể {secondary_tension}." if secondary_tension is not None else ""
        )
        if position_key in {"facts", "trigger"}:
            text = (
                f"Ý nghĩa của lá ở vị trí này: {card.core}. Chỉ giữ điều đã thật sự "
                "được nói, làm hoặc thống nhất."
            )
        elif position_key in {"assumption", "habit"}:
            text = (
                f"Kiểm tra xem bạn có đang {tension} hay không.{secondary_copy} "
                "Đây chưa phải sự thật cho tới khi có dữ kiện."
            )
        elif position_key in {"need", "feeling", "payoff"}:
            text = f"Điều cần nhận ra ở đây: {card.core}. Chỗ dễ vướng: {tension}."
        elif position_key in {
            "agency",
            "alternative",
            "boundary",
            "criterion",
            "opening",
            "tradeoff",
            "next",
        }:
            text = f"Ý chính: {card.core}. Chỗ dễ vướng: {tension}.{secondary_copy}"
        elif position_key == "cost":
            text = (
                f"Nếu cứ tiếp tục như cũ, bạn dễ {tension}.{secondary_copy} "
                "Hãy xác định điều cần giới hạn hoặc chuẩn bị trước."
            )
        elif position_key in {"option_a", "option_b"}:
            text = (
                f"Điểm có ích của hướng này: {card.core}. Đổi lại, bạn cần tính tới "
                f"khả năng {tension}.{secondary_copy}"
            )
        elif position_key == "missed":
            text = (
                f"Bạn dễ bỏ sót việc mình đang {tension}.{secondary_copy} "
                "Kiểm tra điều này trong chuyện thật trước khi kết luận."
            )
        else:
            text = (
                f"Ý chính của lá: {card.core}. "
                f"Điều cần coi chừng là lúc bạn {tension}.{secondary_copy}"
            )
        if voice is TarotVoice.GENTLE_SPECIFIC:
            text += " Chưa cần kết luận ngay; hãy kiểm tra bằng chuyện thật trước."
        return text

    @staticmethod
    def _reflection(position_key: str, context: TarotContext, intent: TarotQuestionIntent) -> str:
        # Ask about the spread role, not a motive inferred from a broad intent.
        questions = {
            "trigger": "Lúc nào bạn bắt đầu phản ứng như vậy, và chuyện gì vừa xảy ra?",
            "habit": "Ngay sau chuyện đó, bạn thường làm gì mà chưa kịp nghĩ?",
            "payoff": "Cách phản ứng này giúp bạn giải quyết điều gì ngay lúc đó?",
            "cost": "Sau đó, việc gì vẫn chưa được giải quyết hoặc làm bạn mệt thêm?",
            "alternative": "Nếu gặp lại chuyện đó, bạn có thể thử phản ứng khác ở bước nào?",
            "feeling": "Bạn thấy buồn, bực, lo hay nhẹ nhõm khi nhớ lại chuyện này?",
            "need": "Bạn muốn điều gì được nói rõ hoặc thay đổi trong chuyện này?",
            "agency": "Trong chuyện này, phần nào bạn có thể tự quyết mà không cần họ đồng ý?",
            "boundary": "Bạn chưa thể nhận lời việc gì, và có thể nói giới hạn đó thế nào?",
            "opening": "Bạn sẽ mở lời bằng câu nào để người nghe biết đúng chuyện đang bàn?",
            "option_a": "Nếu chọn hướng A, bạn được gì và cần chuẩn bị cho điều gì?",
            "option_b": "Nếu chọn hướng B, bạn được gì và cần chuẩn bị cho điều gì?",
            "tradeoff": "Hai hướng khác nhau ở điều gì bạn thật sự coi trọng?",
            "criterion": "Bạn sẽ dùng tiêu chí nào để chọn, thay vì đổi ý theo người vừa nói?",
            "next": "Bạn có thể làm việc nhỏ nào trước, rồi xem phản hồi thực tế ra sao?",
        }
        if position_key in questions:
            return questions[position_key]
        if intent is TarotQuestionIntent.COMMUNICATION and position_key in {"focus", "clear"}:
            return "Bạn muốn nói câu nào trước, và cần người nghe hiểu đúng điều gì?"
        relationship_tail = (
            " mà không đoán hộ người kia" if context is TarotContext.RELATIONSHIPS else ""
        )
        if position_key in {"focus", "clear", "facts", "trigger"}:
            return (
                "Trong chuyện này, điều gì đã được nói hoặc làm mà bạn có thể kiểm tra"
                f"{relationship_tail}?"
            )
        if position_key in {"missed", "assumption", "habit", "cost"}:
            return f"Điều nào là dữ kiện, điều nào đang do bạn tự nối thêm{relationship_tail}?"
        if position_key in {"option_a", "option_b", "tradeoff", "criterion"}:
            return "Nếu chọn hướng này, bạn được gì và phải chấp nhận điều gì?"
        if position_key in {"need", "feeling", "payoff"}:
            return "Bạn cần điều gì để có thể nói hoặc quyết định rõ hơn?"
        return "Việc nhỏ nào nằm hoàn toàn trong quyền quyết định của bạn?"

    @staticmethod
    def _action(resource: str, voice: TarotVoice) -> str:
        prefix = "Thử nhé:" if voice is TarotVoice.PLAYFUL_GROUNDED else "Một việc nhỏ:"
        resource = _resource_step(resource)
        # The card's authored resource is already an actionable sentence. Do not
        # attach a worksheet task or context-wide instruction to every card.
        return f"{prefix} {_sentence_start(resource)}."

    @staticmethod
    def _gate(reading: TarotReading) -> None:
        if not prose_is_safe(reading):
            raise TarotContentRejected("unsupported or unsafe prose claim")
        expected_positions = _POSITIONS[reading.spread_map]
        expected_count = {
            TarotSpread.ONE_CARD: 1,
            TarotSpread.THREE_CARD: 3,
            TarotSpread.FIVE_CARD: 5,
        }[reading.spread]
        if (
            len(reading.positions) != expected_count
            or tuple((position.key, position.label) for position in reading.positions)
            != expected_positions
            or len({position.card.id for position in reading.positions}) != len(reading.positions)
        ):
            raise TarotContentRejected("reading does not match its selected spread")
        for position in reading.positions:
            try:
                known_card = card_by_id(position.card.id)
            except KeyError as exc:
                raise TarotContentRejected("reading contains an unknown card") from exc
            if position.card != known_card:
                raise TarotContentRejected("reading changes the selected card facts")
        if len(reading.headline.split()) > 18 or len(reading.summary.split()) > 180:
            raise TarotContentRejected("reading headline or summary exceeds scan budget")
        framed = reading.provenance.question_rules_version == QUESTION_RULES_VERSION
        if framed:
            views = _position_views(reading.positions, reading.context)
            # Gate summary_links_cards replaces "names every card" (US-20 AC10).
            if not stance.summary_links(reading.summary, views):
                raise TarotContentRejected("summary does not link every role")
            TarotReadingEngine._stance_consistent(reading, views)
        elif any(position.card.title_vi not in reading.summary for position in reading.positions):
            raise TarotContentRejected("summary omits a selected card")
        text = " ".join(
            [reading.headline, reading.summary, reading.closing_prompt, reading.disclaimer]
            + [
                value
                for position in reading.positions
                for value in (
                    position.meaning_here,
                    position.everyday_scene,
                    position.reflection_question,
                    position.small_action or "",
                )
            ]
        ).lower()
        if any(phrase in text for phrase in _ABSTRACT_FILLER):
            raise TarotContentRejected("abstract filler failed content gate")
        if any(phrase in text for phrase in OPAQUE_CORE_FRAGMENTS):
            raise TarotContentRejected("opaque copy failed content gate")
        if any(
            not value.strip()
            for position in reading.positions
            for value in (
                position.meaning_here,
                position.everyday_scene,
                position.reflection_question,
            )
        ):
            raise TarotContentRejected("reading contains an empty semantic block")
        if framed:
            TarotReadingEngine._role_fit(reading)
            authored = _authored_by_engine(reading)
            if any(re.search(pattern, authored) for pattern in roles.DECISION_OR_PREDICTION):
                raise TarotContentRejected("reading decides or predicts for the reader")
        elif any(not (position.small_action or "").strip() for position in reading.positions):
            raise TarotContentRejected("reading contains an empty semantic block")
        sections = [("headline", reading.headline), ("summary", reading.summary)]
        sections.append(("closing", reading.closing_prompt))
        for index, position in enumerate(reading.positions):
            sections.extend(
                (
                    (f"meaning_{index}", position.meaning_here),
                    (f"scene_{index}", position.everyday_scene),
                    (f"reflection_{index}", position.reflection_question),
                )
            )
            if position.small_action:
                sections.append((f"action_{index}", position.small_action))
        result = ContentReviewAgent().review(
            (
                ReviewSample(
                    persona_id="tarot-runtime",
                    surface="tarot",
                    sections=tuple(sections),
                    disclaimer=reading.disclaimer,
                    provenance_ids=reading.provenance.source_ids,
                    evidence_validated=True,
                ),
            )
        )
        if not result.passed:
            raise TarotContentRejected("reading failed plain-language content review")

    @staticmethod
    def _stance_consistent(reading: TarotReading, views: list[stance.PositionView]) -> None:
        """Gate stance_consistent (US-20 AC09): the stored lean is what the cards give, the
        headline says it (default voices), and no prose states another level."""

        current = reading.stance
        others = set(stance.MARKERS.values())
        if current is not None:
            expected = stance.recompute(current, views)
            if (expected.level, expected.action) != (current.level, current.action):
                raise TarotContentRejected("stance does not match the cards")
            if expected.conclusion != current.conclusion:
                raise TarotContentRejected("stance does not match the cards")
            marker = stance.MARKERS[current.level]
            others.discard(marker)
            if reading.voice is not TarotVoice.ROAST and marker not in reading.headline.lower():
                raise TarotContentRejected("headline does not state the stance")
        prose = f"{reading.headline} {reading.summary}".lower()
        if any(other in prose for other in others):
            raise TarotContentRejected("prose states a different stance")

    @staticmethod
    def _role_fit(reading: TarotReading) -> None:
        """Gate ``role_fit`` (US-20 AC07, AC12): each position reads its role's card field, only
        step roles carry an action, and retired prefixes are gone."""

        for position in reading.positions:
            role = roles.ROLES.get(position.key)
            if role is None:
                raise TarotContentRejected("position has no role")
            meaning = _CardMeaning.for_context(position.card, reading.context)
            tension, _ = _tension_parts(meaning.tension)
            body = position.meaning_here
            expected = {
                roles.RoleField.CORE: (meaning.core,),
                roles.RoleField.TENSION: (tension,),
                roles.RoleField.OPTION: (meaning.core, tension),
                roles.RoleField.RESOURCE: (),
            }[role.field]
            if any(part not in body for part in expected):
                raise TarotContentRejected("position does not read its role's field")
            if role.field is roles.RoleField.RESOURCE and not role.step:
                if _resource_step(meaning.resource) not in body:
                    raise TarotContentRejected("position does not read its role's field")
            if role.step != bool(position.small_action and position.small_action.strip()):
                raise TarotContentRejected("small action outside a step role, or missing")
            prose = " ".join(
                (position.meaning_here, position.everyday_scene, position.small_action or "")
            ).casefold()
            if any(prefix in prose for prefix in roles.RETIRED_PREFIXES):
                raise TarotContentRejected("retired filler prefix in a role reading")

    @staticmethod
    def _classify_intent(question: str, context: TarotContext) -> TarotQuestionIntent:
        lowered = question.casefold()
        if any(word in lowered for word in ("ranh giới", "từ chối", "giới hạn", "nhận thêm")):
            return TarotQuestionIntent.BOUNDARY
        if any(word in lowered for word in ("nhắn", "nói", "hỏi", "giao tiếp", "trả lời")):
            return TarotQuestionIntent.COMMUNICATION
        if any(word in lowered for word in ("bước", "làm gì", "tiếp theo", "thử gì")):
            return TarotQuestionIntent.NEXT_STEP
        if any(word in lowered for word in ("cảm thấy", "nhu cầu", "phản ứng", "bản thân")):
            return TarotQuestionIntent.SELF_CHECK
        if context in {TarotContext.ENERGY, TarotContext.SELF_CARE}:
            return TarotQuestionIntent.SELF_CHECK
        return TarotQuestionIntent.CLARITY

    @staticmethod
    def _reading_sources(cards: tuple[TarotCard, ...]) -> tuple[str, ...]:
        concepts = {
            "position-discipline",
            "self-reflection",
            "non-determinism",
            "story-coherence",
            "plain-spoken-reading",
            "present-focus",
            *(concept for card in cards for concept in card.source_concept_ids),
        }
        return source_ids_for_concepts(tuple(sorted(concepts)))
