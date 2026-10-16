"""Lời của Lá: the companion's lines, reviewed as part of the content matrix.

Lá (the sprout companion) greets, waits and reacts. It never changes the meaning of a
reading, predicts events, claims to know the reader, or speaks for another person.

Two voices, like the Daily card: ``direct`` (plain, warm Vietnamese, the default) and
``roast`` ("Cà khịa", owner-approved style 2026-10-11): one light tease of the behaviour in
the reading, never of the person, always with a way out. Lines tied to a Daily issue also
carry a ``meaning`` brief: it is the only thing Luna receives when it rewrites the line, so
the rewrite keeps the point without copying the authored sentence.

The web client renders the static lines (greetings, loading, mood reactions) from
``apps/web/src/shared/ui/la/laCatalog.generated.ts``; regenerate it with
``python -m scripts.export_companion_catalog`` after changing anything here. A test fails
when the generated file drifts.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace

from app.domains.mood.models import MoodValue
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS

COMPANION_VOICE_VERSION = "la-companion-v1"

# Words per line. The bubble sits next to the card on a phone; a longer line competes
# with the reading instead of nudging the reader to act on it.
DIRECT_MAX_WORDS = 14
ROAST_MAX_WORDS = 16
MIN_WORDS = 3


@dataclass(frozen=True)
class CompanionLine:
    direct: str
    roast: str


@dataclass(frozen=True)
class CompanionIssueLine:
    """What Lá says right after a Daily card about one issue.

    ``anchors`` are the words that carry the nudge (one must appear, never negated) and
    ``contrary`` the phrasings that would push the opposite way; the rewrite gate applies
    both to Luna's line and to the authored one, so a line cannot contradict its card.
    """

    meaning: str
    line: CompanionLine
    anchors: tuple[str, ...] = ()
    contrary: tuple[str, ...] = ()


DAY_PARTS = ("morning", "noon", "afternoon", "evening", "late")

COMPANION_ISSUE_LINES: dict[str, CompanionIssueLine] = {
    "missing-context": CompanionIssueLine(
        "Hỏi lại phần chưa rõ thay vì tự đoán ý tin nhắn.",
        CompanionLine(
            "Hỏi lại một câu thôi, đỡ hơn đoán cả buổi.",
            "Thám tử tin nhắn ơi, hỏi thẳng một câu cho nhanh án.",
        ),
    ),
    "too-many-open-loops": CompanionIssueLine(
        "Khuyến khích làm xong một việc trước khi mở việc mới.",
        CompanionLine(
            "Xong một việc trước đã, việc kia vẫn chờ được.",
            "Đóng bớt tab trong đầu đi, một việc thôi là đủ.",
        ),
    ),
    "changed-plan": CompanionIssueLine(
        "Nhắc chốt lại giờ hẹn mới trước khi xếp lại cả ngày.",
        CompanionLine(
            "Chốt giờ mới trước, rồi hẵng xếp lại cả ngày.",
            "Lịch đổi một chỗ thôi, đừng vội xây lại cả ngày.",
        ),
    ),
    "comparison-loop": CompanionIssueLine(
        "Kéo chú ý về tiến triển của chính mình.",
        CompanionLine(
            "Nhìn lại việc bạn đã xong hôm nay trước nhé.",
            "Lướt thành tích người ta đủ rồi, xem của mình chút đi.",
        ),
    ),
    "automatic-caretaking": CompanionIssueLine(
        "Xem sức mình trước khi nhận giúp người khác.",
        CompanionLine(
            "Giúp được bao nhiêu thì nói bấy nhiêu, vậy là đủ.",
            "Siêu anh hùng cũng cần sạc pin. Nhận vừa sức thôi.",
        ),
    ),
    "decision-fatigue": CompanionIssueLine(
        "Thu hẹp lựa chọn khi đang mệt.",
        CompanionLine(
            "Bớt lựa chọn đi một chút, chọn sẽ nhẹ hơn.",
            "Mười phương án thì chọn tới mai. Gạch bớt đi nào.",
        ),
    ),
    "perfect-before-start": CompanionIssueLine(
        "Khuyến khích gửi bản nháp đã đủ ý thay vì sửa mãi.",
        CompanionLine(
            "Bản nháp đủ ý rồi đó. Gửi đi để được góp ý.",
            "Sửa tới chữ thứ một trăm rồi. Bấm gửi đi nào.",
        ),
    ),
    "group-pressure": CompanionIssueLine(
        "Hỏi lại chỗ chưa hiểu dù cả nhóm đã chốt.",
        CompanionLine(
            "Một câu hỏi bây giờ đỡ phải làm lại sau này.",
            "Gật cho êm rồi lát tự mò một mình à? Hỏi luôn đi.",
        ),
    ),
    "avoid-small-conflict": CompanionIssueLine(
        "Ủng hộ nói thật điều mình không nhận được.",
        CompanionLine(
            "Từ chối nhẹ nhàng vẫn là từ chối. Bạn làm được.",
            "Chữ được bật ra nhanh ghê. Lần này thử nói thật xem.",
        ),
    ),
    "defend-old-choice": CompanionIssueLine(
        "Xem kết quả thật trước khi bỏ thêm công.",
        CompanionLine(
            "Xem kết quả trước đã, rồi hẵng quyết đi tiếp hay đổi.",
            "Tiếc công thì hiểu, nhưng đừng đổ thêm công vào chỗ chưa ổn.",
        ),
    ),
    "capacity-before-agreement": CompanionIssueLine(
        "Xem lịch trước khi nhận thêm việc.",
        CompanionLine(
            "Mở lịch ra xem trước, rồi hẵng nhận lời.",
            "Lịch kín mít mà vẫn muốn ôm thêm? Xem lịch cái đã.",
        ),
    ),
    "quick-reply": CompanionIssueLine(
        "Đọc hết tin nhắn rồi mới trả lời.",
        CompanionLine(
            "Đọc hết tin rồi hẵng trả lời, chậm vài giây thôi.",
            "Ngón tay nhanh hơn não rồi kìa. Đọc hết đã nha.",
        ),
    ),
    "repair-reply": CompanionIssueLine(
        "Khuyến khích sửa cách nói sau một câu trả lời vội.",
        CompanionLine(
            "Lỡ gắt một câu thì nói lại một câu. Vậy là ổn.",
            "Gửi rồi mới thấy gắt hả? Nhắn lại cho dịu, chưa muộn đâu.",
        ),
    ),
    "specific-feedback": CompanionIssueLine(
        "Khuyến khích hỏi góp ý cho đúng một phần cụ thể.",
        CompanionLine(
            "Hỏi đúng một chỗ, bạn sẽ nhận góp ý đúng chỗ.",
            "Hỏi thấy sao thì nhận về cũng được thôi. Hỏi cụ thể đi.",
        ),
    ),
    "name-the-need": CompanionIssueLine(
        "Khuyến khích nói rõ một việc cụ thể cần được giúp.",
        CompanionLine(
            "Nói rõ một việc cần giúp, người kia mới giúp đúng được.",
            "Than mệt thì được an ủi, nói cần gì mới được giúp.",
        ),
    ),
}

_NUDGES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "missing-context": (("hỏi",), ("đoán",)),
    "too-many-open-loops": (("một việc", "xong"), ("mở thêm việc", "làm hết một lúc")),
    "changed-plan": (("chốt", "giờ mới", "xác nhận"), ("đổi hết", "xếp lại ngay")),
    "comparison-loop": (("đã xong", "đã làm", "của mình"), ("so với người ta",)),
    "automatic-caretaking": (("nói", "sức"), ("nhận hết", "ôm hết")),
    "decision-fatigue": (("bớt", "gạch", "lựa chọn"), ("thêm lựa chọn", "xem hết")),
    "perfect-before-start": (("gửi",), ("sửa thêm", "sửa cho xong")),
    "group-pressure": (("hỏi",), ("cứ gật", "gật cho xong")),
    "avoid-small-conflict": (("từ chối", "nói thật", "nói rõ", "không nhận"), ("cứ nhận",)),
    "defend-old-choice": (("kết quả", "kiểm tra"), ("cứ làm tiếp", "làm tiếp cách cũ")),
    "capacity-before-agreement": (("lịch",), ("cứ nhận", "nhận luôn")),
    "quick-reply": (("đọc",), ("trả lời ngay", "rep luôn")),
    "repair-reply": (("nói lại", "nhắn lại", "sửa"), ("cãi tiếp", "im luôn")),
    "specific-feedback": (("hỏi", "một chỗ", "một phần", "cụ thể"), ("hỏi chung chung",)),
    "name-the-need": (("nói rõ", "cần giúp", "cần gì"), ("than tiếp", "giữ trong lòng")),
}
COMPANION_ISSUE_LINES = {
    key: replace(entry, anchors=_NUDGES[key][0], contrary=_NUDGES[key][1])
    for key, entry in COMPANION_ISSUE_LINES.items()
}

# Shown when a Daily card has no authored issue (legacy or unmatched wording).
COMPANION_FALLBACK = CompanionIssueLine(
    "Thử việc nhỏ trong note thay vì chỉ đọc xong rồi thôi.",
    CompanionLine(
        "Đọc xong rồi thì thử một việc nhỏ nhé.",
        "Đọc xong nhớ thử. Đừng chỉ gật đầu cho đẹp.",
    ),
    anchors=("thử",),
    contrary=("bỏ qua việc", "khỏi làm"),
)

COMPANION_GREETINGS: dict[str, CompanionLine] = {
    "morning": CompanionLine(
        "Chào buổi sáng. Lá để sẵn note hôm nay cho bạn rồi.",
        "Dậy rồi đó hả? Note hôm nay Lá để sẵn, đọc trước khi lướt TikTok nha.",
    ),
    "noon": CompanionLine(
        "Giữa ngày rồi. Ghé Lá một chút nhé.",
        "Giữa trưa rồi, ăn gì chưa? Ăn xong ghé đọc note nha.",
    ),
    "afternoon": CompanionLine(
        "Chiều rồi. Xem nhanh điều đáng để ý hôm nay?",
        "Chiều rồi mà việc sáng còn dang dở hả? Đọc note rồi làm tiếp.",
    ),
    "evening": CompanionLine(
        "Tối rồi. Ngồi xuống với Lá một nhịp.",
        "Tối rồi. Ngồi xuống, kể Lá nghe hôm nay ai làm bạn cạn pin.",
    ),
    "late": CompanionLine(
        "Khuya rồi đó. Đọc nhẹ thôi rồi đi ngủ nhé.",
        "Khuya vậy còn thức? Đọc nhanh rồi cất điện thoại, mai còn làm người.",
    ),
}

COMPANION_LOADING: tuple[CompanionLine, ...] = (
    CompanionLine("Lá đang dò sóng…", "Đợi xíu, Lá đang soi bạn…"),
    CompanionLine("Lá đang lật trang lá số…", "Lá đang gõ… đừng giục nha."),
    CompanionLine("Lá đang gom ánh sao…", "Lá đang lục lại hồ sơ drama của bạn…"),
)

COMPANION_MOOD_REACTIONS: dict[MoodValue, CompanionLine] = {
    MoodValue.RUC: CompanionLine(
        "Bạn đang nhiều năng lượng. Nhớ để dành một chút cho mình.",
        "Năng lượng max ghê. Nhớ chừa pin cho tối nay, đừng đốt hết lúc 10 giờ sáng.",
    ),
    MoodValue.CHILL: CompanionLine(
        "Nhịp này đẹp đấy. Không cần đẩy mọi thứ đi nhanh hơn.",
        "Chill quá ha. Giữ nhịp này, đừng để group chat kéo bạn vào drama.",
    ),
    MoodValue.DUOI: CompanionLine(
        "Hôm nay bớt một việc cũng là chăm mình.",
        "Pin 3% mà còn gồng. Bớt một việc đi, thế giới không sập đâu.",
    ),
    MoodValue.CANG: CompanionLine(
        "Thở chậm một nhịp trước khi trả lời điều quan trọng.",
        "Vai đang gồng tới tai rồi kìa. Thở ra một hơi rồi hẵng rep tin nhắn.",
    ),
    MoodValue.LAC_TROI: CompanionLine(
        "Chưa cần hiểu hết. Chỉ cần tìm một điểm để quay về.",
        "Đang trôi giữa vũ trụ hả? Neo lại một việc nhỏ trước đã.",
    ),
}

# Direct only by design: it is an invitation, not a reaction to the reader.
COMPANION_MOOD_NUDGE = "Hôm nay bạn đang ở mood nào? Chạm để kể Lá nghe."

# Greetings and mood reactions predate the matrix (owner-approved 2026-10-11) and are
# allowed to run longer than the note bubble; they still pass the forbidden checks.
STATIC_MAX_WORDS = 18

# Lá never claims knowledge, fate or another person's mind.
COMPANION_FORBIDDEN_FRAGMENTS = (
    "vũ trụ thì thầm",
    "tín hiệu vũ trụ",
    "số phận",
    "định mệnh",
    "lá biết hết",
    "chắc chắn sẽ",
    "nhất định sẽ",
    "người kia nghĩ",
    "họ đang nghĩ",
    "họ muốn",
)

_WORD = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)


def word_count(value: str) -> int:
    return len(_WORD.findall(unicodedata.normalize("NFC", value)))


def _all_lines() -> tuple[tuple[str, str, int], ...]:
    """(label, text, word limit) for every authored line."""

    rows: list[tuple[str, str, int]] = []
    for key, entry in (*COMPANION_ISSUE_LINES.items(), ("fallback", COMPANION_FALLBACK)):
        rows.append((f"{key}.direct", entry.line.direct, DIRECT_MAX_WORDS))
        rows.append((f"{key}.roast", entry.line.roast, ROAST_MAX_WORDS))
    for part, line in COMPANION_GREETINGS.items():
        rows.append((f"greeting.{part}.direct", line.direct, STATIC_MAX_WORDS))
        rows.append((f"greeting.{part}.roast", line.roast, STATIC_MAX_WORDS))
    for index, line in enumerate(COMPANION_LOADING):
        rows.append((f"loading.{index}.direct", line.direct, STATIC_MAX_WORDS))
        rows.append((f"loading.{index}.roast", line.roast, STATIC_MAX_WORDS))
    for mood, line in COMPANION_MOOD_REACTIONS.items():
        rows.append((f"mood.{mood.value}.direct", line.direct, STATIC_MAX_WORDS))
        rows.append((f"mood.{mood.value}.roast", line.roast, STATIC_MAX_WORDS))
    rows.append(("mood_nudge", COMPANION_MOOD_NUDGE, STATIC_MAX_WORDS))
    return tuple(rows)


_NEGATORS = ("đừng", "không", "khỏi", "chẳng", "chả", "chớ", "miễn", "bỏ qua", "chưa cần")
# "X thay vì / hơn là Y": whatever follows the marker is the rejected alternative.
_INSTEAD_OF = ("thay vì", "hơn là", "còn hơn")
# Predicates that wave an action away ("hỏi lại chỉ mất thời gian", "đoán làm gì cho mệt").
_DISMISSALS = (
    "mất thời gian",
    "phí thời gian",
    "mất công",
    "phí công",
    "vô ích",
    "vô nghĩa",
    "thừa",
    "không cần",
    "chẳng cần",
    "chả cần",
    "khỏi cần",
    "làm gì",
    "không đáng",
    "rườm rà",
    "cho mệt",
)
# Negation never carries across a clause marker ("Không rõ thì hỏi lại", "Đừng đoán mà hỏi");
# a dismissal covers the whole punctuation segment ("Hỏi lại thì phí công lắm").
_SEGMENT_BREAK = re.compile(r"[,.;:!?…\n]+")
_CLAUSE_BREAK = re.compile(r"\b(?:mà|nhưng|rồi|thì|hãy)\b", re.IGNORECASE)


def _tokens(value: str) -> list[str]:
    return [token.casefold() for token in _WORD.findall(unicodedata.normalize("NFC", value))]


def _clauses(text: str) -> list[tuple[list[str], list[str]]]:
    """(clause tokens, enclosing segment tokens) for every clause of ``text``."""

    clauses: list[tuple[list[str], list[str]]] = []
    for segment in _SEGMENT_BREAK.split(unicodedata.normalize("NFC", text)):
        segment_tokens = _tokens(segment)
        for part in _CLAUSE_BREAK.split(segment):
            if tokens := _tokens(part):
                clauses.append((tokens, segment_tokens))
    return clauses


def _find(tokens: list[str], phrase: str) -> list[int]:
    target = _tokens(phrase)
    width = len(target)
    return [i for i in range(len(tokens) - width + 1) if tokens[i : i + width] == target]


def _rejected(clause: list[str], segment: list[str], index: int, phrase: str) -> bool:
    """True when the anchor ``phrase`` at ``clause[index]`` is negated, set aside or waved away.

    Deliberately broad: any negation earlier in the clause or any dismissal in the segment
    rejects the anchor. A wrongly rejected line only falls back to the authored one.
    """

    if _tokens(phrase)[0] in _NEGATORS:  # the anchor is itself a refusal ("không nhận")
        before_markers: tuple[str, ...] = _INSTEAD_OF
    else:
        before_markers = (*_NEGATORS, *_INSTEAD_OF)
    before = clause[:index]
    if any(_find(before, marker) for marker in before_markers):
        return True
    for dismissal in _DISMISSALS:
        for start in _find(segment, dismissal):
            # "không mất thời gian" / "chẳng thừa" flip the dismissal back.
            negated = start > 0 and segment[start - 1] in ("không", "chẳng", "chả")
            if not negated or dismissal.startswith(("không", "chẳng", "chả", "khỏi")):
                return True
    return False


# A contrary action is set aside only by a marker aimed at it: right before it, past these
# adverbs ("đừng cứ đoán", "thay vì tự đoán", "đỡ hơn đoán"). "thôi" is not one: "thôi cứ
# đoán" urges the action.
_CONTRARY_GOVERNORS = (
    *_NEGATORS,
    *_INSTEAD_OF,
    "hơn",
    "không cần",
    "chẳng cần",
    "chả cần",
    "khỏi cần",
    "không nên",
    "chẳng nên",
    "đừng nên",
)
_ACTION_ADVERBS = ("cứ", "tự", "có", "phải", "ngồi", "đi")
# ...or by a dismissal right after it ("đoán làm gì cho mệt"), at most two words away. The gap
# must not push the action or negate the dismissal ("cứ đoán cho nhanh khỏi mất thời gian",
# "cứ đoán không mất công", "đoán có làm gì đâu" all stay contrary).
_CONTRARY_DISMISSALS = (
    "làm gì",
    "làm chi",
    "để làm gì",
    "vô ích",
    "mất thời gian",
    "phí thời gian",
    "mất công",
    "phí công",
    "cho mệt",
    "không đáng",
)
_DISMISSAL_BLOCKERS = (
    *_NEGATORS,
    "chưa",
    "có",
    "cho",
    "nhanh",
    "luôn",
    "đi",
    "đỡ",
    "để",
    "nhé",
    "ngay",
)
_DISMISSAL_REACH = 2


def _contrary_set_aside(clause: list[str], index: int, phrase: str) -> bool:
    """True only when a negation or dismissal targets the contrary ``phrase`` itself.

    A negation of some other action ("không chờ trả lời, cứ đoán"), a double negation
    ("không phải không đoán", "không gì hơn đoán") or a negated dismissal does not count;
    when the scope is unclear the phrase stays contrary and the line is rejected.
    """

    start = index
    while start > 0 and clause[start - 1] in _ACTION_ADVERBS:
        start -= 1
    for marker in _CONTRARY_GOVERNORS:
        width = len(_tokens(marker))
        if start >= width and clause[start - width : start] == _tokens(marker):
            # Any negation before the governor makes the scope a double negation or unclear.
            return not any(_find(clause[: start - width], negator) for negator in _NEGATORS)
    end = index + len(_tokens(phrase))
    for dismissal in _CONTRARY_DISMISSALS:
        for at in _find(clause, dismissal):
            if not 0 <= at - end <= _DISMISSAL_REACH:
                continue
            gap = clause[end:at]
            after = clause[at + len(_tokens(dismissal)) :]
            blocked = any(_find(gap, word) for word in _DISMISSAL_BLOCKERS)
            if not blocked and "đâu" not in after:
                return True
    return False


def nudge_failures(text: str, entry: CompanionIssueLine) -> list[str]:
    """Why ``text`` does not carry ``entry``'s nudge (empty when it does).

    Works clause by clause: an anchor counts only when no negation or "thay vì/hơn là" in
    its clause and no dismissive predicate in its sentence segment rejects it; a contrary
    phrase counts unless a negation or dismissal aimed at that very action sets it aside
    (scope unclear means contrary). Matching keeps Vietnamese diacritics on
    purpose: folded "dung" would confuse "đừng" (don't) with "đúng" (right).
    """

    failures: list[str] = []
    found = False
    for clause, segment in _clauses(text):
        for anchor in entry.anchors:
            for index in _find(clause, anchor):
                found = True
                if _rejected(clause, segment, index, anchor):
                    failures.append("negated_nudge")
        for phrase in entry.contrary:
            if any(
                not _contrary_set_aside(clause, index, phrase) for index in _find(clause, phrase)
            ):
                failures.append("contrary_nudge")
    if not found:
        failures.append("missing_nudge")
    return list(dict.fromkeys(failures))


def validate_companion_catalog() -> list[str]:
    failures: list[str] = []
    issue_keys = {issue.key for issue in DAILY_ISSUES}
    if set(COMPANION_ISSUE_LINES) != issue_keys:
        missing = sorted(issue_keys - set(COMPANION_ISSUE_LINES))
        extra = sorted(set(COMPANION_ISSUE_LINES) - issue_keys)
        failures.append(
            f"companion issue lines must match Daily issues (missing={missing}, extra={extra})"
        )
    if set(COMPANION_GREETINGS) != set(DAY_PARTS):
        failures.append("companion greetings must cover every day part")
    if set(COMPANION_MOOD_REACTIONS) != set(MoodValue):
        failures.append("companion mood reactions must cover every mood")
    lines = _all_lines()
    texts = [text for _, text, _ in lines]
    if len(texts) != len(set(texts)):
        failures.append("companion lines must be distinct")
    forbidden = tuple(
        fragment.casefold() for fragment in (*COMPANION_FORBIDDEN_FRAGMENTS, *BANNED_CORE_FRAGMENTS)
    )
    for label, text, limit in lines:
        count = word_count(text)
        if not MIN_WORDS <= count <= limit:
            failures.append(f"{label} has {count} words (limit {MIN_WORDS}-{limit})")
        folded = text.casefold()
        if any(fragment in folded for fragment in forbidden):
            failures.append(f"{label} uses a forbidden fragment")
    for key, entry in (*COMPANION_ISSUE_LINES.items(), ("fallback", COMPANION_FALLBACK)):
        if entry.line.direct == entry.line.roast:
            failures.append(f"{key} roast must differ from direct")
        if not entry.meaning.strip():
            failures.append(f"{key} needs a meaning brief for Luna")
        if not entry.anchors:
            failures.append(f"{key} needs nudge anchors")
        for problem in nudge_failures(entry.line.direct, entry):
            failures.append(f"{key}.direct {problem}")
    return failures


_failures = validate_companion_catalog()
if _failures:
    raise ValueError("; ".join(_failures))

_DIRECT_TO_ROAST: dict[str, str] = {
    entry.line.direct: entry.line.roast
    for entry in (*COMPANION_ISSUE_LINES.values(), COMPANION_FALLBACK)
}


def companion_issue_entry(mechanism_key: str | None) -> CompanionIssueLine:
    """The entry for a Daily blueprint mechanism (``psychology:<issue>``), or the fallback."""

    if mechanism_key and mechanism_key.startswith("psychology:"):
        entry = COMPANION_ISSUE_LINES.get(mechanism_key.removeprefix("psychology:"))
        if entry is not None:
            return entry
    return COMPANION_FALLBACK


def roast_companion_line(direct: str) -> str:
    """Roast wording for an authored direct line; any other text passes through."""

    return _DIRECT_TO_ROAST.get(direct, direct)


def companion_metrics() -> dict[str, int]:
    return {
        "companion_issue_lines": len(COMPANION_ISSUE_LINES),
        "companion_mood_reactions": len(COMPANION_MOOD_REACTIONS),
        "companion_greetings": len(COMPANION_GREETINGS),
    }
