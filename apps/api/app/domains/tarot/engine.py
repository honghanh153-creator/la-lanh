from __future__ import annotations

import re
from dataclasses import dataclass

from app.domains.readings.review_agent import OPAQUE_CORE_FRAGMENTS
from app.domains.tarot.knowledge import (
    KNOWLEDGE_VERSION,
    card_by_id,
    minor_scene,
    source_ids_for_concepts,
)
from app.domains.tarot.models import (
    TarotCard,
    TarotContext,
    TarotQuestionAssessment,
    TarotQuestionIntent,
    TarotReading,
    TarotReadingPosition,
    TarotReadingProvenance,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)


class TarotContentRejected(ValueError):
    pass


@dataclass(frozen=True)
class _ContextLens:
    focus: str
    scene: str
    action_frame: str


_CONTEXTS: dict[TarotContext, _ContextLens] = {
    TarotContext.GENERAL: _ContextLens(
        "điều đang chiếm nhiều chú ý nhất nhưng chưa được gọi đúng tên",
        "lúc bạn mở điện thoại, đổi lịch hoặc chuẩn bị trả lời một việc "
        "và nhận ra mình đang chần chừ",
        "chọn một tình huống thật trong 24 giờ tới để đối chiếu",
    ),
    TarotContext.RELATIONSHIPS: _ContextLens(
        "phần mình có thể nói rõ thay vì đoán hộ người kia",
        "khi một tin nhắn đến chậm, một câu trả lời ngắn hơn thường lệ "
        "hoặc hai người né đúng chủ đề cần nói",
        "đổi một phép thử ngầm thành một câu hỏi có thể trả lời thẳng",
    ),
    TarotContext.WORK: _ContextLens(
        "điều đang lấy công sức nhưng chưa có tiêu chí hoàn thành rõ",
        "khi lịch họp dày lên, việc mới được đẩy sang "
        "hoặc bạn sắp nhận thêm phần không ai đứng tên",
        "chốt một ưu tiên, một người chịu trách nhiệm hoặc một mốc dừng",
    ),
    TarotContext.COMMUNICATION: _ContextLens(
        "câu chính cần được nói trước phần giải thích",
        "khi bạn soạn rồi xóa một tin nhắn, nói vòng để giữ hòa khí "
        "hoặc nghe một câu theo hai nghĩa khác nhau",
        "viết câu chính trong một dòng rồi mới thêm bối cảnh",
    ),
    TarotContext.ENERGY: _ContextLens(
        "việc nào đang tiêu hao nhiều hơn giá trị nó trả lại",
        "khi cơ thể đã mệt nhưng đầu vẫn mở thêm việc, "
        "hoặc bạn thấy bực với một yêu cầu vốn rất nhỏ",
        "bỏ bớt một việc gây nhiễu trước khi thêm giải pháp",
    ),
    TarotContext.SELF_CARE: _ContextLens(
        "nhu cầu thật nằm dưới phản xạ phải tỏ ra ổn",
        "khi bạn trì hoãn ăn, ngủ, nghỉ hoặc một cuộc hẹn với chính mình "
        "vì nghĩ phải xong hết mới được dừng",
        "đặt một việc chăm mình vào lịch như một cam kết thật",
    ),
}

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
_CERTAINTY = re.compile(r"\b(?:chắc chắn|bao giờ|khi nào|có quay lại|sẽ xảy ra)\b", re.IGNORECASE)
_HIGH_STAKES = re.compile(
    r"\b(?:bệnh|thuốc|mang thai|tự tử|kiện|pháp lý|đầu tư|cổ phiếu|vay tiền|chẩn đoán)\b",
    re.IGNORECASE,
)
_ABSTRACT_FILLER = (
    "tín hiệu vũ trụ",
    "mọi thứ xảy ra đều có lý do",
    "hãy tin vào hành trình",
    "năng lượng đang dịch chuyển",
)

_INTENT_FOCUS: dict[TarotQuestionIntent, str] = {
    TarotQuestionIntent.CLARITY: "phân biệt điều đã biết với phần đang tự điền vào",
    TarotQuestionIntent.BOUNDARY: "nhìn chỗ cần một giới hạn rõ mà không biến nó thành trừng phạt",
    TarotQuestionIntent.NEXT_STEP: "thu nhỏ quyết định thành một bước còn có thể quan sát và đổi ý",
    TarotQuestionIntent.COMMUNICATION: "đưa câu cần nói ra trước lớp giải thích và suy đoán",
    TarotQuestionIntent.SELF_CHECK: "gọi đúng cảm xúc, nhu cầu và phần trách nhiệm thuộc về mình",
}

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
        normalized = " ".join(question.strip().split())
        if len(normalized) < 8:
            return TarotQuestionAssessment(
                accepted=False,
                normalized_question=normalized,
                explanation=(
                    "Câu hỏi cần thêm một tình huống cụ thể để bài đọc không thành lời chung chung."
                ),
                suggested_reframe="Trong chuyện này, mình cần nhìn rõ điều gì trước?",
            )
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
        if _CERTAINTY.search(normalized):
            return TarotQuestionAssessment(
                accepted=False,
                normalized_question=normalized,
                explanation=(
                    "Câu hỏi đang tìm một kết luận chắc chắn; bài sẽ hữu ích hơn "
                    "khi neo vào điều bạn có thể quan sát."
                ),
                suggested_reframe="Mình nên quan sát điều gì trước khi quyết định bước tiếp theo?",
            )
        return TarotQuestionAssessment(
            accepted=True,
            normalized_question=normalized,
            intent=self._classify_intent(normalized, context),
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
    ) -> TarotReading:
        assessment = self.assess_question(question, context)
        if not assessment.accepted:
            raise TarotContentRejected("question must pass reflection boundary")
        intent = question_intent or assessment.intent
        if intent is None:
            raise TarotContentRejected("question intent is required")
        resolved_map = spread_map or self.choose_spread_map(
            spread, intent, assessment.normalized_question
        )
        positions = _POSITIONS[resolved_map]
        if len(card_ids) != len(positions) or len(set(card_ids)) != len(card_ids):
            raise TarotContentRejected("card count must match spread and be unique")
        lens = _CONTEXTS[context]
        rendered: list[TarotReadingPosition] = []
        for index, ((key, label), card_id) in enumerate(zip(positions, card_ids, strict=True)):
            try:
                card = card_by_id(card_id)
            except KeyError as exc:
                raise TarotContentRejected("unknown card") from exc
            meaning = self._meaning(card, key, lens, intent, voice)
            scene = self._scene(card, lens, index)
            reflection = self._reflection(key, context)
            action = self._action(card.resource, lens.action_frame, voice, key)
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
        title_card = rendered[0].card
        reading = TarotReading(
            headline=_INTENT_HEADLINES[intent],
            summary=self._summary(title_card),
            question=assessment.normalized_question,
            question_intent=intent,
            context=context,
            spread=spread,
            spread_map=resolved_map,
            voice=voice,
            positions=tuple(rendered),
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
                source_ids=self._reading_sources(tuple(position.card for position in rendered)),
            ),
        )
        self.validate(reading)
        return reading

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
    def _summary(card: TarotCard) -> str:
        tension, secondary = _tension_parts(card.tension)
        text = (
            f"Lá đầu tiên là {card.title_vi}. Ý chính của lá: {card.core}. "
            f"Điểm cần kiểm tra là bạn có đang {tension} hay không."
        )
        if secondary is not None:
            text += f" Bạn cũng có thể {secondary}."
        return text

    @staticmethod
    def _meaning(
        card: TarotCard,
        position_key: str,
        lens: _ContextLens,
        intent: TarotQuestionIntent,
        voice: TarotVoice,
    ) -> str:
        tension, secondary_tension = _tension_parts(card.tension)
        secondary_copy = (
            f" Bạn cũng có thể {secondary_tension}." if secondary_tension is not None else ""
        )
        resource = _resource_step(card.resource)
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
            text = (
                f"Một cách đáp lại phù hợp hơn là {resource}. "
                "Vị trí này nói về nhu cầu của bạn, không đoán suy nghĩ người khác."
            )
        elif position_key in {
            "agency",
            "alternative",
            "boundary",
            "criterion",
            "opening",
            "tradeoff",
        }:
            text = f"Điều bạn làm được lúc này: {resource}. Mục tiêu là {_INTENT_FOCUS[intent]}."
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
        elif position_key == "next":
            text = f"Bước tiếp theo: {resource}. Làm một lần rồi xem kết quả trước khi đi tiếp."
        else:
            text = (
                f"Ý chính của lá: {card.core}. "
                f"Điều cần coi chừng là lúc bạn {tension}.{secondary_copy}"
            )
        if voice is TarotVoice.GENTLE_SPECIFIC:
            text += " Chưa cần kết luận ngay; hãy kiểm tra bằng chuyện thật trước."
        return text

    @staticmethod
    def _scene(card: TarotCard, lens: _ContextLens, index: int) -> str:
        card_scene = minor_scene(card)
        tension, secondary_tension = _tension_parts(card.tension)
        secondary_copy = (
            f" Bạn cũng có thể {secondary_tension}." if secondary_tension is not None else ""
        )
        if index == 0:
            scene = f"Tình huống để kiểm tra: {lens.scene}."
            if card_scene is not None and card_scene != lens.scene:
                scene += f" Một chi tiết khác: {card_scene}."
            return scene
        variants = (
            (
                f"Dấu hiệu cụ thể là khi bạn {tension}.{secondary_copy} "
                "Hãy tìm một lần việc này đã thật sự xảy ra."
            ),
            (
                f"Nhớ lại lần gần nhất bạn {tension}.{secondary_copy} "
                "Sau đó xem điều gì xảy ra tiếp theo."
            ),
            f"Trong một việc gần đây, kiểm tra xem bạn có {tension} không.{secondary_copy}",
            (
                f"Nếu không nhớ được lần nào gần đây mình {tension}, "
                f"lá này có thể không hợp tình huống.{secondary_copy}"
            ),
        )
        return variants[(index - 1) % len(variants)]

    @staticmethod
    def _reflection(position_key: str, context: TarotContext) -> str:
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
    def _action(resource: str, frame: str, voice: TarotVoice, position_key: str = "focus") -> str:
        prefix = "Thử nhé:" if voice is TarotVoice.PLAYFUL_GROUNDED else "Một việc nhỏ:"
        resource = _resource_step(resource)
        if position_key in {"focus", "clear", "facts", "trigger"}:
            action = f"viết hai dòng: điều đã xảy ra và điều mình đang đoán. Sau đó {resource}"
        elif position_key in {"missed", "assumption", "habit", "cost"}:
            action = (
                "chọn một điều đang đoán và tìm cách hỏi hoặc kiểm tra trực tiếp. "
                f"Tiếp theo, {resource}"
            )
        elif position_key in {"option_a", "option_b", "tradeoff", "criterion"}:
            action = f"viết một điều được và một điều phải đánh đổi. Sau đó {resource}"
        elif position_key in {"need", "feeling", "payoff"}:
            action = f"viết một câu bắt đầu bằng “Mình cần…”. Tiếp theo, {resource}"
        elif position_key == "next":
            action = (
                f"làm đúng một việc trong hôm nay. {_sentence_start(resource)}. "
                "Chờ phản hồi thật rồi mới đi tiếp"
            )
        else:
            action = f"{frame}. Tiếp theo, {resource}"
        return f"{prefix} {action}."

    @staticmethod
    def _gate(reading: TarotReading) -> None:
        text = " ".join(
            [reading.headline, reading.summary, reading.closing_prompt, reading.disclaimer]
            + [
                value
                for position in reading.positions
                for value in (
                    position.meaning_here,
                    position.everyday_scene,
                    position.reflection_question,
                    position.small_action,
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
                position.small_action,
            )
        ):
            raise TarotContentRejected("reading contains an empty semantic block")

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
