"""Read a typed month question into closed labels only: a topic and a question kind.

The text is read in memory and dropped. Nothing here logs, stores or returns it, and no answer
ever quotes it: the answer is built from the topic, the kind and the chart. The same text always
gives the same labels.

Kinds (the answer never says yes or no and never names a date for the event):

- ``outcome``: "có qua không", "có đủ tiền không", "sẽ ... không" → what raises your chances.
- ``timing``: "bao giờ", "khi nào", "tuần nào" → what you can do from now.
- ``should``: "có nên" → Lá does not choose for you.
- ``other_mind``: what someone else feels or thinks → what you can do on your side.
- ``how``: "làm sao", "nói sao", "nên làm gì" and anything else → the plain answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.domains.month_answer.facts import Topic
from app.domains.safety.crisis import fold, normalize

QUESTION_MIN_CHARS = 8
QUESTION_MAX_CHARS = 280


class QuestionKind(StrEnum):
    HOW = "how"
    OUTCOME = "outcome"
    TIMING = "timing"
    SHOULD = "should"
    OTHER_MIND = "other_mind"


@dataclass(frozen=True, slots=True)
class QuestionLabels:
    topic: Topic | None  # None: the text names no topic; the person picks one
    kind: QuestionKind


def _words(*items: str) -> re.Pattern[str]:
    return re.compile(r"\b(?:" + "|".join(items) + r")\b")


# Keywords are written with accents. Text typed with accents is matched on the accented copy, so
# "thì" is not "thi" and "lo" (worry) is not "lỗ" (loss); text typed without any accent is matched
# on the folded copy. Each hit adds one point; the most points wins, ties go to the order below.
_TOPIC_KEYWORDS: tuple[tuple[Topic, tuple[str, ...]], ...] = (
    (
        Topic.STUDY,
        (
            "học",
            "ôn thi",
            "thi",
            "môn",
            "bài tập",
            "đồ án",
            "khóa luận",
            "luận văn",
            "điểm",
            "học bổng",
            "trường",
            "lớp",
            "thầy",
            "giảng viên",
            "kỳ thi",
            "học kỳ",
            "tiết",
            "bài thi",
            "nộp bài",
            "tiếng anh",
            "tiếng trung",
            "ra trường",
            "thực tập",
            "ôn",
            "bài",
            "nộp",
            "tác phẩm",
            "ngành",
            "lập trình",
            "bạn nhóm",
            "chuyển ngành",
            "năm hai",
            "năm nhất",
            "cuối kỳ",
        ),
    ),
    (
        Topic.MONEY,
        (
            "tiền",
            "lương",
            "nợ",
            "chi tiêu",
            "tiết kiệm",
            "để dành",
            "giá",
            "nhập hàng",
            "lỗ",
            "lãi",
            "tiền trọ",
            "tiền nhà",
            "hóa đơn",
            "vay",
            "trả nợ",
            "bán hàng",
            "đơn hàng",
            "hàng tồn",
            "xả hàng",
            "tăng lương",
            "thu nhập",
            "công nợ",
            "tiền ăn",
            "mua",
            "bom hàng",
            "đơn",
            "nhập",
            "bán",
            "tiệm",
            "món",
            "chi",
            "tiệc",
            "kênh bán",
            "mẫu mới",
            "dự toán",
            "tiêu",
        ),
    ),
    (
        Topic.WORK,
        (
            "việc",
            "công việc",
            "sếp",
            "công ty",
            "ca",
            "tăng ca",
            "hợp đồng",
            "phỏng vấn",
            "deadline",
            "dự án",
            "khách",
            "đồng nghiệp",
            "báo cáo",
            "chốt",
            "nghỉ việc",
            "đổi việc",
            "nhảy việc",
            "trưởng phòng",
            "quản lý",
            "văn phòng",
            "hồ sơ",
            "kho",
            "livestream",
            "giao hàng",
            "chiến dịch",
            "thử việc",
            "chủ tiệm",
            "quán",
            "chỗ làm",
            "làm thêm",
            "chỉ tiêu",
            "khách sạn",
            "ca đêm",
        ),
    ),
    (
        Topic.LOVE,
        (
            "người yêu",
            "bạn gái",
            "bạn trai",
            "người cũ",
            "crush",
            "yêu",
            "hẹn hò",
            "chồng",
            "vợ",
            "cưới",
            "duyên",
            "yêu xa",
            "chia tay",
            "tình cảm",
            "người ấy",
            "anh ấy",
            "cô ấy",
            "người hợp",
        ),
    ),
    (
        Topic.FAMILY,
        (
            "bố",
            "mẹ",
            "ba",
            "má",
            "bố mẹ",
            "ba mẹ",
            "con",
            "con trai",
            "con gái",
            "anh trai",
            "chị gái",
            "em trai",
            "em gái",
            "gia đình",
            "ông",
            "bà nội",
            "bà ngoại",
            "cháu",
            "về quê",
            "về nhà",
            "nhà mình",
            "cả nhà",
            "anh chị em",
            "con cháu",
            "bà",
            "bé",
            "tết",
        ),
    ),
    (
        Topic.MIND,
        (
            "mệt",
            "buồn",
            "lo",
            "lo lắng",
            "ngủ",
            "mất ngủ",
            "stress",
            "áp lực",
            "nhớ nhà",
            "một mình",
            "bực",
            "chán",
            "nghỉ ngơi",
            "căng",
            "đuối",
            "khóc",
            "cô đơn",
            "tự ti",
            "bình tĩnh",
            "nguôi",
            "nghĩ nhiều",
            "chưa đủ tốt",
            "sức khỏe tinh thần",
            "ấm ức",
            "mất lòng",
            "nói nặng",
            "nhớ",
            "bạn cùng phòng",
            "bạn bè",
            "đi chơi",
        ),
    ),
)
_TOPIC_PATTERNS: tuple[tuple[Topic, re.Pattern[str], re.Pattern[str]], ...] = tuple(
    (topic, _words(*words), _words(*(fold(word) for word in words)))
    for topic, words in _TOPIC_KEYWORDS
)

_OTHER = (
    r"(?:bo|me|ba|ma|bo me|ba me|anh ay|co ay|nguoi ay|ho|ban gai|ban trai|chong|vo|sep|"
    r"nguoi yeu|nguoi cu|ban cung phong|ban nhom|con|anh trai|chi gai|ong|crush)"
)
_OTHER_MIND = re.compile(
    rf"\b{_OTHER} (?:co )?(?:that su |con |dang |se )?"
    r"(?:buon|gian|thich|nho|yeu|nghi|thuong|ghet|chan|hieu|chap nhan|tha thu|quay lai)\b"
)
_TIMING = _words(
    "bao gio",
    "khi nao",
    "luc nao",
    "tuan nao",
    "hom nao",
    "ngay nao",
    "thang nao",
    "chung nao",
    "bao lau",
    "may gio",
)
_SHOULD = _words("co nen", "nen hay khong", "hay la", "hay khong nen")
_HOW = _words(
    "lam sao",
    "lam the nao",
    "the nao",
    "nhu the nao",
    "noi sao",
    "noi gi",
    "nen lam gi",
    "lam gi",
    "cach nao",
    "cach gi",
    "ra sao",
    "sao cho",
    "chuan bi gi",
    "chu y gi",
)
_OUTCOME = re.compile(
    r"\b(?:co|se|lieu)\b.*\b(?:khong|ko|k|hong|chua)\b\s*[.?]*$"
    r"|\b(?:co (?:qua|dau|duoc|kip|du|on|thanh|giu|bi|tro lai|quay lai)|se (?:ra sao|the nao))\b"
)


def read_question(text: str) -> QuestionLabels:
    accented, folded = normalize(text[:QUESTION_MAX_CHARS])
    clean_accented = accented.replace(" . ", " ").strip(" .")
    clean = folded.replace(" . ", " ").strip(" .")
    typed_accents = clean_accented != clean
    return QuestionLabels(topic=_topic(clean_accented, typed_accents), kind=_kind(clean))


def _topic(text: str, typed_accents: bool) -> Topic | None:
    best: tuple[int, int] | None = None
    chosen: Topic | None = None
    for rank, (topic, accented, folded) in enumerate(_TOPIC_PATTERNS):
        hits = len((accented if typed_accents else folded).findall(text))
        if hits and (best is None or (hits, -rank) > best):
            best, chosen = (hits, -rank), topic
    return chosen


def _kind(folded: str) -> QuestionKind:
    if _OTHER_MIND.search(folded):
        return QuestionKind.OTHER_MIND
    if _TIMING.search(folded):
        return QuestionKind.TIMING
    if _SHOULD.search(folded):
        return QuestionKind.SHOULD
    if _HOW.search(folded):
        return QuestionKind.HOW
    if _OUTCOME.search(folded):
        return QuestionKind.OUTCOME
    return QuestionKind.HOW
