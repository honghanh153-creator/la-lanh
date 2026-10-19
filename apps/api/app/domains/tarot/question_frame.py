"""Deterministic understanding of a Tarot question (US-20 AC01-AC06, B2-1).

``QuestionFrame`` holds closed labels only: a form, a scored topic and an optional action label
from the owner-approved table of 30 (decision A6). It is computed once when a session starts,
stored inside the session's AES-GCM payload, and replayed when the reading is rendered. It is
never logged, never returned by the API and never sent to a provider. No text from the question
ever leaves this module; matched words are only used to pick a label.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum

from app.domains.tarot.models import (
    QUESTION_FRAME_VERSION,
    QUESTION_RULES_VERSION,
    QuestionFrame,
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotVoice,
)

__all__ = [
    "QUESTION_FRAME_VERSION",
    "QUESTION_RULES_VERSION",
    "QuestionFrame",
    "TarotAction",
    "TarotQuestionForm",
    "TimingOwner",
    "asks_own_timing",
    "classify_form",
    "frame_question",
    "is_vague",
    "match_action",
    "readiness_headline",
    "score_topic",
    "timing_owner",
]


def fold(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _has(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


# ---------------------------------------------------------------- form (AC01)

_TIMING = ("bao giờ", "khi nào", "lúc nào", "thời điểm nào", "bao lâu nữa")
_WHY = ("vì sao", "tại sao", "sao mình lại", "lý do gì")
_HOW = ("làm thế nào", "làm sao", "thế nào", "cách nào", "bằng cách nào")
_CHOICE_START = re.compile(r"^(?:mình\s+|tôi\s+)?(?:nên|giữa)\b")


def classify_form(question: str) -> TarotQuestionForm:
    text = fold(question)
    if any(_has(text, phrase) for phrase in _TIMING):
        return TarotQuestionForm.TIMING
    if any(_has(text, phrase) for phrase in _WHY):
        return TarotQuestionForm.WHY
    if _has(text, "giữa") and _has(text, "và"):
        # "Giữa A và B, cách nào ...?" compares two options even when phrased as "how".
        return TarotQuestionForm.CHOICE
    if any(_has(text, phrase) for phrase in _HOW):
        return TarotQuestionForm.HOW
    ends_with_khong = re.search(r"\bkhông\s*[?!.…]*$", text) is not None
    if (ends_with_khong and _has(text, "có")) or (ends_with_khong and _has(text, "nên")):
        # "Có nên A hay B không?" asks whether to do A: a yes/no question.
        return TarotQuestionForm.YES_NO
    if _has(text, "hay") or _has(text, "hoặc"):
        return TarotQuestionForm.CHOICE
    if _CHOICE_START.search(text) and _has(text, "chọn"):
        return TarotQuestionForm.CHOICE
    if ends_with_khong:
        return TarotQuestionForm.YES_NO
    return TarotQuestionForm.OPEN


_FIRST_PERSON = ("mình", "tôi", "em", "tớ", "tui")
_THIRD_PERSON_MARKERS = ("ấy", "kia", "đó", "ta")  # "em ấy", "mình kia" name someone else
# Words that may sit between the timing phrase and the clause's subject:
# "Khi nào [thì] [là] [lúc] [phù hợp] [để] mình ...".
_TIMING_FILLERS = (
    "thì",
    "là",
    "lúc",
    "thời điểm",
    "phù hợp",
    "thích hợp",
    "hợp lý",
    "tốt nhất",
    "đúng",
    "để",
    "nhất",
)
_TIMING_PHRASE = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(p) for p in _TIMING) + r")(?!\w)")


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text)


# Modals and manner words between the subject and the action ("mình [nên|có thể] nhắn ...").
_MODALS = (
    "có thể",
    "có nên",
    "nên",
    "cần",
    "phải",
    "định",
    "muốn",
    "nên thử",
    "thử",
    "chủ động",
    "thật sự",
    "bắt buộc",
)
_MODALS_SHORTEST_FIRST = tuple(sorted(_MODALS, key=lambda m: len(m.split())))
# A predicate that is an outcome or event, not an action the reader takes: "mình có người
# yêu", "mình sẽ ...", "mình được nhận", "mình hết buồn". These are predictions.
_OUTCOME_PREDICATES = ("có", "sẽ", "được", "bị", "hết", "khỏi", "trúng", "đậu", "thành công")
# The own-action exception needs a positively identified action; a predicate outside this list
# ("Khi nào mình giàu?", "Khi nào mình nên?") is unresolved and asks for clarification.
_ACTION_VERBS = (
    "nhắn",
    "nói",
    "hỏi",
    "trả lời",
    "gọi",
    "gửi",
    "viết",
    "ghi",
    "kể",
    "chia sẻ",
    "mở lời",
    "xin",
    "đề xuất",
    "đề nghị",
    "góp ý",
    "từ chối",
    "nhận",
    "đồng ý",
    "hẹn",
    "gặp",
    "rủ",
    "mời",
    "bắt đầu",
    "dừng",
    "ngừng",
    "nghỉ",
    "ngủ",
    "đi",
    "về",
    "ở lại",
    "chuyển",
    "đổi",
    "tìm",
    "học",
    "tập",
    "luyện",
    "làm",
    "thử",
    "dọn",
    "sắp xếp",
    "đặt",
    "lên kế hoạch",
    "chuẩn bị",
    "dành",
    "đăng ký",
    "nộp",
    "ứng tuyển",
    "tắt",
    "giảm",
    "bỏ",
    "buông",
    "tha thứ",
    "xin lỗi",
    "cảm ơn",
    "kết thúc",
    "chia tay",
    "quay lại",
    "liên lạc",
    "thăm",
    "chăm",
    "đọc",
    "nghe",
    "mua",
    "bán",
    "dời",
    "hoãn",
    "đặt lịch",
    "chốt",
    "quyết định",
    "chọn",
    "giữ",
    "nhờ",
    "giúp",
    "tặng",
    "thưởng",
    "khen",
    "đi chơi",
    "ra ngoài",
    "nấu",
    "tập trung",
    "thử lại",
    "làm lại",
    "bớt",
    "tự thưởng",
    "tự khen",
    "tạm ngừng",
    "tạm dừng",
    "tạm nghỉ",
)
# Reporting prefixes that only introduce the question: "Mình muốn biết khi nào ...",
# "Cho mình hỏi bạn khi nào ...", "Mình muốn hỏi sếp xem bao giờ ...". Recognised by their
# whole shape: [speaker words] reporting verb [addressee] [tail]. The timed clause is then the
# one after the timing phrase.
_REPORTING_VERBS = ("biết", "hỏi", "thắc mắc", "tự hỏi", "phân vân", "băn khoăn")
_REPORTING_LEAD = (*_FIRST_PERSON, "cho", "xin", "muốn", "cần", "đang", "rất", "chỉ", "được")
_ADDRESSEES = (
    "bạn",
    "sếp",
    "chị",
    "anh",
    "em",
    "cô",
    "thầy",
    "mẹ",
    "bố",
    "ba",
    "lá",
    "cậu",
    "mọi người",
    "mn",
    "ad",
)
_REPORTING_TAIL = ("là", "rằng", "xem", "thử", "giúp", "với", "nhé", "ạ")
# A subordinate clause after a trailing timing phrase: "Mình nên nhắn lại khi nào để kịp?".
# Only true subordinators: "thì" (and similar bridges) is a timing filler that can precede the
# timed subject itself ("... khi nào thì họ nên ..."), so it never proves subordination.
_SUBORDINATORS = ("để", "cho kịp", "trước khi", "sau khi", "nếu")
# Sentence-final particles: "Mình nên hỏi sếp khi nào nhỉ?" still ends with the timing phrase.
_FINAL_PARTICLES = ("nhỉ", "vậy", "thế", "ạ", "nhé", "đây", "ta", "nha", "hả", "hở")


class TimingOwner(StrEnum):
    OWN = "own"  # the reader's own action: reframed as readiness
    OTHER = "other"  # another person, an event or an outcome: a prediction, refused
    UNCLEAR = "unclear"  # no identified subject or action: ask for clarification


def _skip(tokens: list[str], phrases: tuple[str, ...]) -> list[str]:
    changed = True
    while changed and tokens:
        changed = False
        for phrase in sorted(phrases, key=lambda p: -len(p.split())):
            parts = phrase.split()
            if tokens[: len(parts)] == parts:
                tokens = tokens[len(parts) :]
                changed = True
                break
    return tokens


def _starts_with(tokens: list[str], phrases: tuple[str, ...]) -> bool:
    return any(tokens[: len(p.split())] == p.split() for p in phrases)


def _clause_owner(tokens: list[str]) -> TimingOwner:
    """Owner of one clause: subject first, then a positively identified predicate."""

    if not tokens:
        return TimingOwner.UNCLEAR
    if tokens[0] in _FIRST_PERSON:
        if len(tokens) > 1 and tokens[1] in _THIRD_PERSON_MARKERS:
            return TimingOwner.OTHER  # "em ấy", "mình kia": someone else
        rest = tokens[1:]
    elif tokens[0] == "nên" or tokens[:2] == ["có", "nên"]:
        rest = tokens  # "Bao giờ thì nên ...": the reader is the one advised
    else:
        return TimingOwner.OTHER  # "họ", "sếp", "dự án", ...
    predicate = rest
    while predicate:
        # An action is recognised before a modal is stripped, so "thử lại" stays an action.
        if _starts_with(predicate, _ACTION_VERBS):
            return TimingOwner.OWN
        if _starts_with(predicate, _OUTCOME_PREDICATES) and not _starts_with(
            predicate, ("có thể", "có nên")
        ):
            return TimingOwner.OTHER
        modal = next((m for m in _MODALS_SHORTEST_FIRST if _starts_with(predicate, (m,))), None)
        if modal is None:
            break
        predicate = predicate[len(modal.split()) :]  # one modal at a time, shortest first
    return TimingOwner.UNCLEAR  # empty ("Khi nào mình nên?") or unresolved ("... mình giàu?")


def _is_reporting_prefix(tokens: list[str]) -> bool:
    """``tokens`` (before the timing phrase) are exactly an introductory question: speaker
    words, one reporting verb, an optional addressee (at most two words), optional tail."""

    rest = list(tokens)
    while rest and rest[-1] in _REPORTING_TAIL:
        rest.pop()
    for verb in sorted(_REPORTING_VERBS, key=lambda v: -len(v.split())):
        parts = verb.split()
        for start in range(len(rest) - len(parts) + 1):
            if rest[start : start + len(parts)] != parts:
                continue
            lead, addressee = rest[:start], rest[start + len(parts) :]
            if all(word in _REPORTING_LEAD for word in lead) and (
                not addressee or " ".join(addressee) in _ADDRESSEES
            ):
                return True
    return False


def _mentions_reporting(tokens: list[str]) -> bool:
    return any(
        tokens[i : i + len(v.split())] == v.split()
        for v in _REPORTING_VERBS
        for i in range(len(tokens))
    )


def _strip_final_particles(tokens: list[str]) -> list[str]:
    rest = list(tokens)
    while rest and rest[-1] in _FINAL_PARTICLES:
        rest.pop()
    return rest


def timing_owner(question: str) -> TimingOwner:
    """Who acts in the clause being timed, for the readiness reframe (US-20 AC05).

    - Timing phrase first ("Khi nào mình nhắn lại ...", "Khi nào là lúc phù hợp để mình ..."):
      the clause right after it.
    - After a reporting prefix ("Mình muốn biết khi nào họ ...", "Cho mình hỏi khi nào mình
      ..."): also the clause after the phrase; the prefix asks, it is not timed.
    - Otherwise ("Mình nên nghỉ việc khi nào?", "Dự án nên xong khi nào để mình nghỉ?"): the
      clause that opens the sentence; what follows the phrase is subordinate.
    """

    text = fold(question)
    match = _TIMING_PHRASE.search(text)
    if match is None:
        return TimingOwner.UNCLEAR
    before = _tokens(text[: match.start()])
    after_raw = _strip_final_particles(_tokens(text[match.end() :]))
    after = _skip(after_raw, _TIMING_FILLERS)
    if not before:
        return _clause_owner(after)  # "Khi nào mình ...": the clause after the phrase
    if not after_raw:
        return _clause_owner(before)  # "Mình nên hỏi sếp khi nào?": a trailing time modifier
    if _is_reporting_prefix(before):
        return _clause_owner(after)  # "Mình muốn hỏi bạn khi nào họ ...": a timed complement
    if _starts_with(after_raw, _SUBORDINATORS):
        if _mentions_reporting(before):
            # "Mình muốn hỏi thêm khi nào để ...": the opening clause may be an introduction,
            # so which clause is timed is not established.
            return TimingOwner.UNCLEAR
        return _clause_owner(before)  # "Mình nên nhắn lại khi nào để kịp?"
    # Any other shape: the relation between the clauses is not established, so never infer
    # the reader's own action. An explicit other subject after the phrase is still refused.
    return TimingOwner.OTHER if _clause_owner(after) is TimingOwner.OTHER else TimingOwner.UNCLEAR


def asks_own_timing(question: str) -> bool:
    return timing_owner(question) is TimingOwner.OWN


# ---------------------------------------------------------------- topic (AC02)

# Several weighted signals per topic; the explicitly chosen topic adds a prior. "hỏi" alone is
# deliberately not a communication signal: asking a manager about a deadline is about work.
_TOPIC_SIGNALS: dict[TarotContext, tuple[str, ...]] = {
    TarotContext.RELATIONSHIPS: (
        "người yêu",
        "bạn thân",
        "gia đình",
        "người thân",
        "bạn bè",
        "hai người",
        "mối quan hệ",
        "nhóm bạn",
        "tình bạn",
        "tình cảm",
        "bạn cũ",
        "hẹn hò",
        "bố mẹ",
        "anh chị em",
    ),
    TarotContext.WORK: (
        "sếp",
        "công việc",
        "dự án",
        "đồng nghiệp",
        "cuộc họp",
        "buổi họp",
        "hạn chót",
        "báo cáo",
        "quy trình",
        "tăng ca",
        "nơi làm việc",
        "chỗ làm",
        "công ty",
        "giờ làm",
        "nghỉ việc",
        "kỹ năng",
        "vị trí mới",
        "quản lý",
        "bản kế hoạch",
        "cơ hội mới",
    ),
    TarotContext.COMMUNICATION: (
        "nói chuyện",
        "nhắn tin",
        "tin nhắn",
        "mở lời",
        "diễn đạt",
        "lắng nghe",
        "email",
        "gọi điện",
        "nói thẳng",
        "im lặng",
        "trò chuyện",
        "góp ý",
        "nói rõ",
        "trả lời",
    ),
    TarotContext.ENERGY: (
        "mệt",
        "kiệt sức",
        "năng lượng",
        "nạp lại",
        "ngủ",
        "buổi chiều",
        "tập thể dục",
        "lấy lại sức",
        "quá sức",
        "nghỉ ngơi",
        "sức",
    ),
    TarotContext.SELF_CARE: (
        "chăm mình",
        "chăm sóc bản thân",
        "bản thân",
        "tự khen",
        "tự trách",
        "an ủi",
        "cho mình",
        "chỉ cho mình",
        "thư giãn",
        "sở thích",
        "tự thưởng",
    ),
}
_CHOSEN_TOPIC_PRIOR = 1.5


def score_topic(question: str, chosen: TarotContext) -> TarotContext:
    text = fold(question)
    scores = {
        topic: float(sum(1 for signal in signals if _has(text, signal)))
        for topic, signals in _TOPIC_SIGNALS.items()
    }
    scores[TarotContext.GENERAL] = 0.0
    scores[chosen] = scores.get(chosen, 0.0) + _CHOSEN_TOPIC_PRIOR
    best = max(scores.values())
    # Ties go to the topic the reader chose, then to a stable enum order.
    if scores[chosen] == best:
        return chosen
    return next(topic for topic in TarotContext if scores.get(topic) == best)


# ---------------------------------------------------------------- action (closed labels)

_ACTION_SIGNALS: tuple[tuple[TarotAction, tuple[str, ...]], ...] = (
    (TarotAction.XIN_GOP_Y, ("xin góp ý", "hỏi ý kiến", "xin ý kiến")),
    (TarotAction.XIN_LOI, ("xin lỗi",)),
    (TarotAction.TU_CHOI, ("từ chối", "nói không")),
    (TarotAction.NHAN_LOI, ("nhận lời", "nhận thêm", "đồng ý", "nhận việc")),
    (TarotAction.DAT_RANH_GIOI, ("ranh giới", "giữ khoảng cách", "giới hạn")),
    (TarotAction.DOI_VIEC, ("nghỉ việc", "đổi việc", "chuyển việc", "cơ hội mới", "vị trí mới")),
    (TarotAction.KET_THUC, ("kết thúc", "chấm dứt", "chia tay")),
    (TarotAction.THU_LAI, ("thử lại", "làm lại")),
    (TarotAction.HOI_LAI, ("hỏi lại", "hỏi thẳng", "hỏi riêng")),
    (TarotAction.NHAN_LAI, ("nhắn lại", "nhắn hỏi", "trả lời tin nhắn", "nhắn cho", "nhắn tin")),
    (TarotAction.HEN_GAP, ("hẹn gặp", "gặp trực tiếp", "gặp lại", "rủ")),
    (TarotAction.GUI_DI, ("gửi",)),
    (TarotAction.CHIA_SE, ("chia sẻ", "kể với", "tâm sự")),
    (TarotAction.NOI_RA, ("nói ra", "nói thật", "nói rõ", "nói thẳng", "nói chuyện", "kể")),
    (TarotAction.GOP_Y, ("góp ý",)),
    (TarotAction.DE_XUAT, ("đề xuất", "đề nghị")),
    (TarotAction.NHO_GIUP, ("nhờ", "làm chung")),
    (TarotAction.HOC_THEM, ("học",)),
    (TarotAction.TAP_TRUNG, ("tập trung",)),
    (TarotAction.SAP_XEP_LAI, ("sắp xếp", "dời", "lịch")),
    (TarotAction.DON_DEP, ("dọn",)),
    (TarotAction.RA_NGOAI, ("ra ngoài", "đi dạo", "đi chơi", "đổi gió")),
    (TarotAction.O_NHA, ("ở nhà",)),
    (TarotAction.NGHI_NGOI, ("nghỉ ngơi", "nghỉ", "ngủ sớm", "đi ngủ", "thư giãn")),
    (TarotAction.TU_THUONG, ("tự khen", "tự thưởng")),
    (TarotAction.VIET_RA, ("viết", "ghi lại", "ghi ra")),
    (TarotAction.DOI_THOI_QUEN, ("thói quen", "tắt thông báo", "giảm bớt", "bớt lướt")),
    (TarotAction.DUNG_LAI, ("dừng", "bỏ dở", "ngừng")),
    (TarotAction.CHO_THEM, ("chờ", "đợi", "bình tĩnh", "thêm thời gian")),
    (TarotAction.BAT_DAU, ("bắt đầu", "thử", "đăng ký")),
)
# A signal is negated when its own clause puts a negator right before it, optionally through
# auxiliaries: "không xin lỗi", "không cần phải xin lỗi", "chưa muốn phải nghỉ". "Không biết
# có nên xin lỗi" is not a negation of the action ("biết" is not an auxiliary).
_NEGATORS = r"(?:không|chưa|chẳng|chả|đừng|khỏi|thôi)"
_AUXILIARIES = r"(?:muốn|cần|phải|định|nên|có|thể|được|dám|hề|còn|cố|bao giờ|tính)"
_NEGATED = re.compile(rf"(?<!\w){_NEGATORS}(?:\s+{_AUXILIARIES})*\s+$")
_CLAUSE_BREAK = re.compile(r"[,;.!?…]|(?<!\w)(?:nhưng|mà|hay|hoặc|rồi|thì)(?!\w)")


def _negated(text: str, start: int) -> bool:
    """Is the signal starting at ``start`` negated inside its own clause?"""

    breaks = [m.end() for m in _CLAUSE_BREAK.finditer(text, 0, start)]
    clause = text[breaks[-1] if breaks else 0 : start]
    return _NEGATED.search(clause) is not None


def match_action(question: str) -> TarotAction | None:
    """The best-supported closed label among affirmed actions.

    Negated matches are removed first, then the longest signal wins, then table order; with no
    affirmed match the label is ``None`` rather than a guess.
    """

    text = fold(question)
    best: tuple[int, int, TarotAction] | None = None
    for order, (label, signals) in enumerate(_ACTION_SIGNALS):
        for signal in signals:
            for match in re.finditer(rf"(?<!\w){re.escape(signal)}(?!\w)", text):
                if _negated(text, match.start()):
                    continue
                candidate = (len(signal), -order, label)
                if best is None or candidate[:2] > best[:2]:
                    best = candidate
    return best[2] if best else None


def frame_question(question: str, chosen: TarotContext) -> QuestionFrame:
    return QuestionFrame(
        form=classify_form(question),
        topic=score_topic(question, chosen),
        action=match_action(question),
    )


# ---------------------------------------------------------------- vague questions (AC04, A7)

# A question word marks a situation being asked about ("vì sao mình hay ...", "phần nào ...").
_QUESTION_WORDS = (
    "vì sao",
    "tại sao",
    "làm sao",
    "thế nào",
    "gì",
    "nào",
    "không",
    "chưa",
    "nên",
    "hay",
    "bao giờ",
    "khi nào",
    "sao",
    "đâu",
    "ai",
    "bao nhiêu",
    "chứ",
    "nhỉ",
    "sẽ",
)
_SITUATION_WORDS = (
    "nên",
    "có",
    "làm",
    "nói",
    "nhắn",
    "hỏi",
    "gửi",
    "chọn",
    "đi",
    "ở",
    "nghỉ",
    "ngủ",
    "bắt đầu",
    "dừng",
    "thử",
    "học",
    "giữ",
    "đổi",
    "chuyển",
    "gặp",
    "dọn",
    "viết",
    "đọc",
    "nghe",
    "đặt",
    "chuẩn bị",
    "nhận",
    "từ chối",
    "xin",
    "trả lời",
    "giúp",
    "thấy",
    "cần",
    "muốn",
    "bỏ",
    "kể",
    "mời",
    "dành",
    "tập trung",
    "lắng nghe",
    "chia",
    "buông",
    "cản",
    "giảm",
    "tắt",
    "dời",
    "gọi",
    "hẹn",
    "rủ",
    "tập",
    "sắp xếp",
    "chăm",
    "lo",
    "sợ",
    "ngại",
    "quên",
    "thay đổi",
)


def is_vague(question: str) -> bool:
    """Owner decision A7: fewer than 3 words, or neither a question word nor a verb.

    "Tình yêu và công việc" is a topic, not a question; "Vì sao mình hay im lặng trong các
    cuộc họp?" asks about a situation even without a listed verb.
    """

    text = fold(re.sub(r"[?!.…,;:]", " ", question))
    if len(text.split()) < 3:
        return True
    return not any(_has(text, word) for word in (*_QUESTION_WORDS, *_SITUATION_WORDS))


# ---------------------------------------------------------------- readiness reframe (AC05)

READINESS_HEADLINE: dict[bool, str] = {
    False: "Chưa cần đoán thời điểm; hãy xem điều cần sẵn sàng trước.",
    True: "Lịch thì Lá chịu, nhưng điều cần sẵn sàng thì soi được.",
}
READINESS_NOTE = (
    "Lá Hỏi không đoán ngày giờ. Bài này chỉ ra điều cần sẵn sàng trước khi bạn làm việc này."
)


def readiness_headline(voice: TarotVoice) -> str:
    return READINESS_HEADLINE[voice is TarotVoice.ROAST]
