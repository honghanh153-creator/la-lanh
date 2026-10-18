"""Closed, locally authored interpretation context. No user prose leaves this module."""

import re
from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from app.domains.tarot.models import TarotContext, TarotReading, TarotReadingPosition

MEANING_BRIEF_VERSION = "tarot-meaning-brief-v2"


@dataclass(frozen=True)
class QuestionGoal:
    key: str
    meaning: str
    reflection: str
    keywords: tuple[str, ...]
    topics: tuple[TarotContext, ...]


_RELATIONSHIPS = (TarotContext.RELATIONSHIPS, TarotContext.COMMUNICATION)
_WORK = (TarotContext.WORK, TarotContext.COMMUNICATION)
_GOALS = (
    QuestionGoal(
        "apology",
        "Khi muốn xin lỗi, nói rõ việc mình đã làm trước khi giải thích lý do.",
        "Bạn muốn nhận lỗi về việc gì, và có thể sửa bằng hành động nào?",
        ("xin lỗi", "lỡ hẹn"),
        _RELATIONSHIPS,
    ),
    QuestionGoal(
        "meeting",
        "Khi muốn chốt lịch gặp, đưa một thời gian cụ thể để cả hai cùng chọn.",
        "Bạn có thể đề nghị lịch gặp nào mà cả hai đều sắp xếp được?",
        ("thời gian gặp", "lịch gặp", "hẹn gặp"),
        _RELATIONSHIPS,
    ),
    QuestionGoal(
        "shared_care",
        "Khi muốn được quan tâm hơn, nói một việc cụ thể thay vì chờ người kia tự hiểu.",
        "Việc quan tâm nào bạn muốn cả hai cùng làm, thay vì chỉ một phía?",
        ("quan tâm", "chăm sóc", "một phía"),
        (TarotContext.RELATIONSHIPS,),
    ),
    QuestionGoal(
        "task_handoff",
        "Khi chia việc, cần thống nhất ai làm phần nào và khi nào bàn giao.",
        "Phần việc nào cần có người phụ trách và thời hạn rõ?",
        ("chia việc", "phân công", "phần việc", "bàn giao"),
        _WORK,
    ),
    QuestionGoal(
        "recognition",
        "Khi muốn được ghi nhận, nêu kết quả mình đã làm và điều mình mong được đánh giá lại.",
        "Kết quả nào bạn có thể đưa ra để nói rõ công sức của mình?",
        ("ghi nhận", "đánh giá"),
        _WORK,
    ),
    QuestionGoal(
        "workload",
        "Khi được giao thêm việc, nói rõ việc nào cần giảm hoặc dời hạn.",
        "Nếu nhận việc mới, bạn cần dời hoặc bỏ bớt việc nào?",
        ("nhận thêm", "quá nhiều việc", "quá tải"),
        (TarotContext.WORK, TarotContext.ENERGY),
    ),
    QuestionGoal(
        "rest",
        "Khi cần nghỉ, chọn một khoảng có thể dừng việc thay vì chờ mọi thứ xong hết.",
        "Bạn có thể dành khoảng nào để nghỉ mà không tự thêm một nhiệm vụ mới?",
        ("nghỉ", "mệt", "ngủ"),
        (TarotContext.ENERGY, TarotContext.SELF_CARE),
    ),
    QuestionGoal(
        "disagreement",
        "Khi bất đồng, nói đúng việc đang khác ý thay vì kết luận về tính cách của nhau.",
        "Hai bên đang khác ý ở việc nào, và đã hiểu đúng ý nhau chưa?",
        ("bất đồng", "cãi", "khác ý"),
        (*_RELATIONSHIPS, TarotContext.WORK),
    ),
)
_DEFAULT_GOAL = QuestionGoal(
    "general",
    "Bài đọc giữ đúng chủ đề bạn đã chọn; không tự đoán thêm chuyện chưa được kể.",
    "Trong chuyện bạn đang hỏi, điều gì cần được nói rõ trước?",
    (),
    (),
)


def goal_by_key(key: str) -> QuestionGoal:
    """A closed goal by its catalog key (provenance resolver, US-20 AC06)."""

    if key == _DEFAULT_GOAL.key:
        return _DEFAULT_GOAL
    return next(goal for goal in _GOALS if goal.key == key)


GOAL_KEYS = frozenset({_DEFAULT_GOAL.key, *(goal.key for goal in _GOALS)})


def question_goals(question: str, context: TarotContext) -> tuple[QuestionGoal, ...]:
    text = " ".join(question.casefold().split())
    # Only closed authored values are returned, never matched text, names or identities.
    matched = tuple(
        goal
        for goal in _GOALS
        if context in goal.topics
        and any(keyword in text for keyword in goal.keywords)
        and not any(
            re.search(r"\b(?:không|chưa) (?:muốn|cần)\s+" + re.escape(keyword), text)
            for keyword in goal.keywords
        )
    )
    return matched or (_DEFAULT_GOAL,)


# Purpose constrains advice, not the user's feelings or the other person's response.
# These are examples of controllable actions, never facts inferred from the question.
_GOAL_ACTIONS: dict[str, tuple[str, str, str]] = {
    "apology": (
        "Mở lời: “Mình xin lỗi về việc mình đã làm. Mình muốn nghe bạn nói.”",
        "Bỏ câu “nhưng tại…” khỏi lời xin lỗi; nghe hết phản hồi trước khi giải thích.",
        "Nói một việc bạn sẽ sửa và thời điểm làm; đừng yêu cầu họ tha thứ ngay.",
    ),
    "meeting": (
        "Thử đề nghị hai khung giờ bạn thật sự có thể gặp.",
        "Hỏi họ có sắp xếp được không; chưa trả lời không có nghĩa là đã đồng ý.",
        "Chọn ngày, giờ và địa điểm sau khi cả hai xác nhận.",
    ),
    "shared_care": (
        "Nói một việc quan tâm bạn muốn nhận, như hỏi han hoặc dành thời gian gặp.",
        "Hỏi điều đó có phù hợp với họ không, thay vì đợi họ tự đoán.",
        "Thử thống nhất một việc cả hai có thể làm; không nhận hết phần chăm sóc.",
    ),
    "task_handoff": (
        "Viết rõ từng phần việc và người phụ trách.",
        "Hỏi lại phần nào còn chưa rõ trước khi coi việc phân công là xong.",
        "Thử thống nhất thời hạn và cách báo khi một phần việc bị chậm.",
    ),
    "recognition": (
        "Chọn một kết quả cụ thể để nói rõ phần công sức bạn đã đóng góp.",
        "Hỏi tiêu chí đánh giá là gì, thay vì đoán người khác không coi trọng mình.",
        "Thử đề nghị một cuộc trao đổi về kết quả và điều bạn mong được ghi nhận.",
    ),
    "workload": (
        "Viết các việc đang làm cùng thời hạn của từng việc.",
        "Nói rõ việc nào sẽ chậm nếu nhận thêm; đừng hứa xong hết khi chưa tính thời gian.",
        "Thử đề nghị giảm một đầu việc hoặc dời một thời hạn trước khi nhận thêm.",
    ),
    "rest": (
        "Chọn một khoảng nghỉ bạn có thể giữ hôm nay.",
        "Bỏ một việc không cần làm ngay khỏi khoảng nghỉ đó.",
        "Giữ khoảng nghỉ đã chọn; không cần đợi làm xong mọi thứ mới nghỉ.",
    ),
    "disagreement": (
        "Nói đúng một việc hai bên đang khác ý, không nhận xét tính cách của nhau.",
        "Nhắc lại ý của họ và hỏi xem bạn đã hiểu đúng chưa.",
        "Thử đề nghị một cách xử lý cho việc đang bàn; nếu quá căng, hẹn lúc nói tiếp.",
    ),
}


# Goal actions by position (US-20 AC06 provenance; pinned by the fallback approval since
# 2026-10-18). Text unchanged from production release 836222282dfc; only moved out of goal_action
# so the approval fingerprints it.
_GOAL_FEELING_ACTION = (
    "Viết một câu về cảm xúc của bạn khi chuyện đó xảy ra, không kết luận về ý của người kia."
)
_GOAL_NEED_ACTIONS: dict[str, str] = {
    "apology": ("Nói rõ bạn muốn sửa điều gì sau lời xin lỗi, không yêu cầu họ tha thứ ngay."),
    "meeting": "Nói rõ thời gian bạn có thể dành cho buổi gặp, thay vì hứa rồi đổi lịch.",
    "shared_care": "Chọn một việc quan tâm cụ thể bạn mong cả hai cùng làm.",
    "task_handoff": "Nói rõ thông tin bạn còn thiếu để làm xong phần việc của mình.",
    "recognition": (
        "Nói rõ bạn muốn được góp ý về kết quả nào, không yêu cầu đánh giá chung về con người."
    ),
    "workload": "Chọn việc cần ưu tiên nhất, rồi nói rõ vì sao việc đó cần làm trước.",
    "rest": (
        "Nói rõ điều bạn cần trong lúc nghỉ: yên tĩnh, ngủ thêm hoặc không phải trả lời ngay."
    ),
    "disagreement": (
        "Nói rõ điều bạn muốn giải quyết trong cuộc trao đổi này, chỉ chọn một việc trước."
    ),
}
_GOAL_AGENCY_ACTIONS: dict[str, str] = {
    "apology": "Chọn một lỗi bạn có thể tự sửa, kể cả khi họ chưa sẵn sàng nói chuyện.",
    "meeting": "Giữ một khung giờ phù hợp với lịch của bạn; chỉ chốt khi cả hai xác nhận.",
    "shared_care": "Nói việc bạn có thể làm và việc bạn chưa thể nhận, không tự ôm hết.",
    "task_handoff": ("Chọn phần việc bạn tự làm được, rồi báo rõ phần đang cần người khác hỗ trợ."),
    "recognition": (
        "Ghi lại kết quả và phần việc mình đã làm để trao đổi, thay vì chỉ chờ được khen."
    ),
    "workload": ("Chọn một đầu việc có thể dời, rồi hỏi lại người phụ trách về thứ tự ưu tiên."),
    "rest": "Tắt một thông báo không cần trả lời ngay trong khoảng nghỉ bạn đã chọn.",
    "disagreement": (
        "Giữ cuộc trao đổi ở một việc cụ thể; nếu bắt đầu xúc phạm, dừng và hẹn nói tiếp."
    ),
}
_GOAL_BOUNDARY_ACTIONS: dict[str, str] = {
    "apology": ("Không hứa một việc bạn chưa làm được chỉ để cuộc nói chuyện kết thúc nhanh."),
    "meeting": "Nói rõ giờ bạn cần về trước khi chốt buổi gặp.",
    "shared_care": (
        "Nói một việc bạn chưa thể nhận trong tuần này, rồi nghe xem họ có sắp xếp được không."
    ),
    "task_handoff": "Nói rõ phần nào chưa thể bàn giao và điều còn cần để hoàn thành.",
    "recognition": (
        "Giữ cuộc trao đổi ở kết quả công việc, không biến nó thành việc xin họ thích mình."
    ),
    "workload": "Nói rõ bạn chưa thể nhận thêm nếu các thời hạn hiện tại không được đổi.",
    "rest": "Báo rằng bạn sẽ trả lời sau giờ nghỉ, thay vì vừa nghỉ vừa canh tin nhắn.",
    "disagreement": ("Nói rõ bạn sẵn sàng nghe góp ý về việc đang bàn, không nhận lời xúc phạm."),
}
_STAGE_ONE_POSITIONS = frozenset({"missed", "assumption", "habit", "cost"})
_STAGE_TWO_POSITIONS = frozenset(
    {"next", "agency", "alternative", "boundary", "opening", "criterion", "tradeoff"}
)


def goal_action(goal: QuestionGoal, position_key: str) -> str | None:
    actions = _GOAL_ACTIONS.get(goal.key)
    if actions is None:
        return None
    if position_key == "feeling":
        return _GOAL_FEELING_ACTION
    if position_key in {"need", "payoff"}:
        return _GOAL_NEED_ACTIONS[goal.key]
    if position_key == "agency":
        return _GOAL_AGENCY_ACTIONS[goal.key]
    if position_key == "boundary":
        return _GOAL_BOUNDARY_ACTIONS[goal.key]
    if position_key in _STAGE_ONE_POSITIONS:
        stage = 1
    elif position_key in _STAGE_TWO_POSITIONS:
        stage = 2
    else:
        stage = 0
    return actions[stage]


@dataclass(frozen=True)
class CardLink:
    key: str
    topic: TarotContext
    sources: tuple[tuple[str, str], tuple[str, str]]
    meaning: str


# Deliberately small editorial rules, bound to both card identity AND position.
# A different order or topic does not inherit a fabricated combined meaning.
_LINKS = (
    CardLink(
        "express_then_ask",
        TarotContext.RELATIONSHIPS,
        (("cups-king", "clear"), ("wands-3", "missed")),
        "Đừng chờ họ tự hiểu: nói cảm xúc mà không cố tỏ ra ổn, rồi hỏi rõ bước tiếp theo.",
    ),
    CardLink(
        "hope_and_disappointment",
        TarotContext.RELATIONSHIPS,
        (("major-star", "clear"), ("cups-5", "missed")),
        "Bạn có thể muốn thử lại mà vẫn còn buồn. "
        "Nói cả điều mong thay đổi lẫn việc làm bạn thất vọng.",
    ),
    CardLink(
        "care_and_reciprocity",
        TarotContext.RELATIONSHIPS,
        (("cups-queen", "clear"), ("pentacles-6", "next")),
        "Quan tâm không có nghĩa là làm hết. "
        "Hai phía cần nói rõ mình có thể cho và muốn nhận điều gì.",
    ),
)


def card_links(
    positions: tuple[TarotReadingPosition, ...],
    context: TarotContext,
) -> list[dict[str, JsonValue]]:
    return links_for({(position.card.id, position.key) for position in positions}, context)


def links_for(available: set[tuple[str, str]], context: TarotContext) -> list[dict[str, JsonValue]]:
    """Authored links whose (card, position) pairs are all present in this draw."""

    return [
        {
            "key": link.key,
            "kind": "ordered_interpretation",
            "source_positions": [key for _, key in link.sources],
            "meaning": link.meaning,
        }
        for link in _LINKS
        if link.topic is context and set(link.sources) <= available
    ]


BRIEF_LIMITS = (
    "Examples are hypothetical, not observed events.",
    "Cards cannot establish another person's thoughts or predict events.",
    "No facts beyond the supplied card meanings and locally recognised goals.",
)


def meaning_brief_for(reading: TarotReading) -> dict[str, JsonValue]:
    """Brief v2: sessions without a QuestionFrame (framed readings use provenance.framed_brief)."""

    goals = question_goals(reading.question, reading.context)
    return {
        "version": MEANING_BRIEF_VERSION,
        "topic": reading.context.value,
        "intent": reading.question_intent.value,
        "goals": cast(JsonValue, [{"key": goal.key, "meaning": goal.meaning} for goal in goals]),
        "local_summary": reading.summary,
        "links": cast(JsonValue, card_links(reading.positions, reading.context)),
        "limits": list(BRIEF_LIMITS),
    }
