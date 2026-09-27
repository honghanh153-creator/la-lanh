from __future__ import annotations

import re
from dataclasses import dataclass

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
        "bỏ bớt một nhịp gây nhiễu trước khi thêm giải pháp",
    ),
    TarotContext.SELF_CARE: _ContextLens(
        "nhu cầu thật nằm dưới phản xạ phải tỏ ra ổn",
        "khi bạn trì hoãn ăn, ngủ, nghỉ hoặc một cuộc hẹn với chính mình "
        "vì nghĩ phải xong hết mới được dừng",
        "đặt một việc chăm mình vào lịch như một cam kết thật",
    ),
}

_POSITIONS: dict[TarotSpread, tuple[tuple[str, str], ...]] = {
    TarotSpread.ONE_CARD: (("focus", "Điều đáng nhìn lúc này"),),
    TarotSpread.THREE_CARD: (
        ("clear", "Điều đã rõ"),
        ("missed", "Điều dễ bỏ sót"),
        ("next", "Một bước nhỏ có thể thử"),
    ),
}

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


class TarotReadingEngine:
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
        positions = _POSITIONS[spread]
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
            reflection = self._reflection(card.resource, key, context)
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
            headline=self._headline(title_card.title_vi, context, voice),
            summary=(
                f"Câu hỏi của bạn đang chạm vào {lens.focus}. "
                f"{title_card.title_vi} mở một góc để soi lại chuyện này "
                "bằng dữ kiện đời thật, không chốt hộ bạn."
            ),
            question=assessment.normalized_question,
            question_intent=intent,
            context=context,
            spread=spread,
            voice=voice,
            positions=tuple(rendered),
            closing_prompt=(
                "Đọc xong, giữ lại câu nào giúp bạn gọi đúng chuyện đang xảy ra; "
                "phần không khớp có thể bỏ qua."
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
        self._gate(reading)
        return reading

    @staticmethod
    def _meaning(
        card: TarotCard,
        position_key: str,
        lens: _ContextLens,
        intent: TarotQuestionIntent,
        voice: TarotVoice,
    ) -> str:
        if position_key == "missed":
            text = (
                f"Điểm dễ bỏ sót: {card.tension}. "
                f"Hãy kiểm tra nó ở {lens.focus}, nhất là khi mục tiêu là {_INTENT_FOCUS[intent]}."
            )
        elif position_key == "next":
            text = (
                f"Bước nhỏ lá này gợi ra: {card.resource}. "
                f"Dùng nó để {_INTENT_FOCUS[intent]}, không phải để chốt cả câu chuyện "
                "trong một lần."
            )
        else:
            text = (
                f"Điều đã có thể gọi tên: {card.core}. "
                f"Trong chuyện này, hãy đối chiếu nó với {lens.focus}; "
                f"mục tiêu là {_INTENT_FOCUS[intent]}."
            )
        if voice is TarotVoice.GENTLE_SPECIFIC:
            text += " Chưa cần kết luận ngay; chỉ cần gọi đúng phần đang có thật."
        return text

    @staticmethod
    def _scene(card: TarotCard, lens: _ContextLens, index: int) -> str:
        card_scene = minor_scene(card)
        if card_scene:
            return f"Ngoài đời, nó có thể lộ ra qua {card_scene}; cụ thể hơn là {lens.scene}."
        variants = (
            f"Ngoài đời, hãy để ý {lens.scene}. "
            "Đây là lúc chủ đề của lá dễ lộ qua hành động thật nhất.",
            f"Một cảnh đáng nhìn là {lens.scene}. "
            "Phản xạ đầu tiên của bạn ở đó nói nhiều hơn một kết luận đẹp.",
            f"Nó có thể xuất hiện {lens.scene}. "
            "So điều bạn nghĩ với điều đã thực sự được nói hoặc làm.",
        )
        return variants[index % len(variants)]

    @staticmethod
    def _reflection(resource: str, position_key: str, context: TarotContext) -> str:
        relationship_tail = (
            " mà không đoán hộ người kia" if context is TarotContext.RELATIONSHIPS else ""
        )
        if position_key in {"focus", "clear"}:
            return (
                f"Nếu thử cách “{resource}”, chi tiết nào trong những gì đã thật sự xảy ra "
                f"sẽ ủng hộ hoặc làm yếu đi cảm nhận hiện tại{relationship_tail}?"
            )
        if position_key == "missed":
            return (
                f"Khi nghĩ tới cách “{resource}”, nhu cầu hoặc giới hạn nào vẫn đang bị để ngoài "
                f"cuộc nói chuyện vì bạn ngại câu trả lời{relationship_tail}?"
            )
        return f"Nếu thử cách “{resource}”, bạn sẽ có thêm dữ kiện gì mà vẫn giữ quyền đổi ý?"

    @staticmethod
    def _action(resource: str, frame: str, voice: TarotVoice, position_key: str = "focus") -> str:
        prefix = "Thử nhé:" if voice is TarotVoice.PLAYFUL_GROUNDED else "Một việc nhỏ:"
        if position_key in {"focus", "clear"}:
            action = f"viết hai dòng — điều đã xảy ra và phần mình đang đoán; sau đó {resource}"
        elif position_key == "missed":
            action = (
                f"gọi tên một nhu cầu hoặc giới hạn chưa được nói; trước khi phản ứng, {resource}"
            )
        else:
            action = f"{frame}; tiếp theo {resource}"
        return f"{prefix} {action}. Nếu không hợp tình huống thật, dừng ở bước quan sát."

    @staticmethod
    def _headline(card_title: str, context: TarotContext, voice: TarotVoice) -> str:
        context_label = {
            TarotContext.GENERAL: "chuyện đang chiếm đầu",
            TarotContext.RELATIONSHIPS: "kết nối này",
            TarotContext.WORK: "nhịp công việc",
            TarotContext.COMMUNICATION: "cuộc nói chuyện",
            TarotContext.ENERGY: "mức năng lượng hiện tại",
            TarotContext.SELF_CARE: "nhu cầu của bạn",
        }[context]
        if voice is TarotVoice.PLAYFUL_GROUNDED:
            variants = (
                f"{card_title} vừa kéo một chi tiết của {context_label} ra khỏi vùng mờ.",
                f"{card_title} đang nhắc đúng chỗ {context_label} bị khựng.",
                f"{card_title} không chốt hộ bạn; lá này soi vào {context_label}.",
            )
            return variants[sum(ord(character) for character in card_title) % len(variants)]
        return f"{card_title} kéo ánh nhìn về {context_label}."

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
            *(concept for card in cards for concept in card.source_concept_ids),
        }
        return source_ids_for_concepts(tuple(sorted(concepts)))
