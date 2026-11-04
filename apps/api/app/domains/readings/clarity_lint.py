"""Plain-language lint for rendered readings (layer A of the content clarity gate).

Spec: ``docs/research/2026-11-01-content-clarity-gate.md`` section 3, "Lớp A". Every rule reads
only the text a user sees in the body of a reading (no evidence, receipts, factor codes or UI
labels) and returns a count plus the keys of the violating sentences (short hashes), so a release
review can keep a per-surface baseline and fail when a count rises or a new violating sentence
appears (ratchet). Thresholds are provisional, like the spec says.

Hard-zero rules are never ratcheted: any hit fails unless its exact key is an approved exception.
They are the class-A safety rules S1-S9 (health, death/accident, money, law, certainty, blame,
crisis, predicted life events, assumed circumstances; gap register GT-17, GT-24, HM-4), H1
(hidden characters, GT-11), the rules the spec always called blocking, A4 (talk about the reading),
A11 (placeholders) and A14 (past events stated as fact) (GT-1), and the measured rules added in C1-3
(GT-10): A9 first-screen length, A13 Daily follows the day (30 consecutive days per persona with a
birth time) and A15 astrology facts in the text match the engine's facts for that reading.

Text is normalised before any rule runs (NFC, no-break spaces as spaces, full-width ASCII as
ASCII, zero-width and bidi controls removed), so look-alike characters cannot hide a match. Safety
phrases also match across line breaks, which stay sentence breaks for every other rule.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from itertools import pairwise
from typing import Any

# Ratcheted rules: a count may only go down and no new violating sentence may appear.
RULES: dict[str, str] = {
    "A1": "thuật ngữ đứng trơ",
    "A2": "nhãn tự đặt",
    "A3": "ẩn dụ máy (> 2/bài)",
    "A5": "cặp câu gần trùng",
    "A6": "câu lặp > 20% số bài",
    "A7": "rào đón (> 0.3/câu)",
    "A8": "câu > 25 âm tiết",
    "A10": "tiếng Anh",
    "A16": "chữ nhà/cung/chủ tinh/góc",
}
TODO_RULES: dict[str, str] = {
    "A1+": "thuật ngữ được giải thích ở câu đó hoặc câu sau thì không tính",
    "A7+": "câu kiểu disclaimer trong thân bài",
}

ENGINE_METAPHOR_ALLOWANCE = 2  # A3: at most two per reading
HEDGES_PER_SENTENCE = 0.3  # A7
MAX_SENTENCE_SYLLABLES = 25  # A8
NEAR_DUPLICATE_MIN_SYLLABLES = 6  # A5
NEAR_DUPLICATE_OVERLAP = 0.5  # A5: shared bigrams over the smaller sentence's bigrams
SHARED_SENTENCE_SHARE = 0.2  # A6
SHARED_SENTENCE_MIN_SYLLABLES = 4  # A6 ignores very short fragments
KEY_LENGTH = 10  # hex digits of a violation key (40 bits)
# Hard-zero rules: the blocking layer-A rules (GT-1, GT-10), class-A safety (GT-17, GT-24, HM-4)
# and hidden characters (GT-11). They are never ratcheted: any hit on any surface fails, unless
# its exact key is an approved exception.
HARD_ZERO_RULES: dict[str, str] = {
    "A4": "nói về bài/app",
    "A9": "màn đầu quá dài",
    "A11": "placeholder",
    "A13": "Daily không bám ngày",
    "A14": "khẳng định việc đã xảy ra",
    "A15": "dữ kiện lệch engine",
    "S1": "sức khỏe, chẩn đoán",
    "S2": "chết, tai nạn",
    "S3": "khuyên tiền, vay, vàng, đầu tư",
    "S4": "pháp lý, hợp đồng",
    "S5": "chắc chắn, định mệnh",
    "S6": "đổ lỗi cho người đọc",
    "S7": "ngôn ngữ khủng hoảng",
    "S8": "đoán sự kiện đời người",
    "S9": "giả định hoàn cảnh người đọc",
    "H1": "ký tự ẩn (zero-width, bidi)",
}
# A9: syllables on the first screen, before the reader opens anything (spec section 3).
FIRST_SCREEN_LIMITS: dict[str, int] = {"daily": 150, "radar": 400, "kham_pha": 300}
TAROT_FIRST_SCREEN_LIMITS: dict[int, int] = {1: 120, 3: 250, 5: 400}
# A13: a fast factor is a transit of one of these bodies (or the Moon's own sign or house).
FAST_BODIES = frozenset({"sun", "moon", "mercury", "venus", "mars"})
DAILY_FOLLOW_DAYS = 30
DAILY_REASON_WINDOW = 7
DAILY_REASON_MAX_DAYS = 3


def _terms(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)


def _phrases(*patterns: str) -> re.Pattern[str]:
    """Like ``_terms``, but every space in a pattern matches any run of whitespace, line breaks
    included. The safety rules use it, so a line break (LF, CRLF, U+2028, U+2029…) inside
    "không muốn sống" cannot hide the phrase. No pattern may put a space in a character class."""

    return _terms(*(pattern.replace(" ", r"\s+") for pattern in patterns))


# "Nhà Bảy", "nhà thứ bảy": a house named with a number word. Capitalised number words always
# count; lower-case ones only from "bốn" up, and not before a unit ("về nhà bảy giờ"), because
# "nhà một mình", "nhà hai bên" and "nhà ba mẹ" are everyday Vietnamese.
_HOUSE_NUMBER_WORD = (
    r"\bnhà (?:(?-i:Một|Hai|Ba|Bốn|Năm|Sáu|Bảy|Tám|Chín|Mười)"
    r"|(?:bốn|sáu|bảy|tám|chín|mười(?: một| hai)?)"
    r"(?!\s+(?:giờ|tiếng|phút|ngày|tuần|tháng|năm|người|lần|bữa|đứa|cái|chiếc|căn|tầng|mét)\b))\b"
)

# A1. Astrology and engine terms a first-time reader does not know. Orb and degrees belong to the
# evidence layer ("Vì sao Lá đọc vậy?"), never to the body. English planet names are A10.
JARGON = _terms(
    r"\bgóc chiếu\b",
    r"\bgóc vuông\b",
    r"\bvuông góc\b",
    r"\b(?:góc )?đồng vị\b",
    r"\bđồng cung\b",
    r"\bđối đỉnh\b",
    r"\blục hợp\b",
    r"\btam hợp\b",
    r"\bnghịch hành\b",
    r"\bđi lùi\b",
    r"\bgiao hội\b",
    r"\bxung chiếu\b",
    r"\btrùng tụ\b",
    r"\bchủ tinh\b",
    r"\bcung mọc\b",
    r"\bthiên đỉnh\b",
    r"\bnhà \d+\b",
    r"\bnhà thứ\b",
    _HOUSE_NUMBER_WORD,
    r"\bgóc \d+",
    r"\bcomposite\b",
    r"\bsynastry\b",
    r"\boverlay\b",
    r"\bnakshatra\b",
    r"\bpada\b",
    r"\bdrishti\b",
    r"\bđiểm thế hệ\b",
    r"\btropical\b",
    r"\bsidereal\b",
    r"\borb\b",
    r"\d+(?:[.,]\d+)?\s*(?:°|độ\b)",
)
# A2. Labels the product coined; UI headings are not body text and are not measured.
COINED_LABELS = _terms(
    r"\bbắt sóng\b",
    r"\blực cấn\b",
    r"\bdễ phối hợp\b",
    r"\blớp kỹ thuật\b",
    r"\btrạm bắt sóng\b",
    r"\bbản đồ lá\b",
)
# A16. House, ascendant/midheaven, ruler and aspect words in the body of a reading. They belong to
# the evidence layer; the body says what they mean for the reader instead (gap register GT-10).
HOUSE_SIGN_ASPECT = _terms(
    r"\bnhà \d+",
    r"\bnhà thứ\b",
    _HOUSE_NUMBER_WORD,
    r"\bcung mọc\b",
    r"\bchủ tinh\b",
    r"\bthiên đỉnh\b",
    r"\bgóc \d+",
    r"\bgóc chiếu\b",
    r"\bgóc vuông\b",
    r"\bvuông góc\b",
    r"\blục hợp\b",
    r"\btam hợp\b",
    r"\bđối đỉnh\b",
    r"\bgiao hội\b",
    r"\bxung chiếu\b",
    r"\btrùng tụ\b",
    r"\bđồng cung\b",
    r"\bđi lùi\b",
    r"\bnghịch hành\b",
)
# A3. Engine metaphors that need decoding. "sóng" alone so "lệch sóng" counts once.
ENGINE_METAPHORS = _terms(
    r"\bnhịp\b",
    r"\btín hiệu\b",
    r"\bchạm vào\b",
    r"\bđiểm chạm\b",
    r"\blớp\b",
    r"\bvùng\b",
    r"\bkích hoạt\b",
    r"\blực kéo\b",
    r"(?<!bắt )\bsóng\b",
    r"\bnăng lượng\b",
    r"\bđường phối hợp\b",
    r"\bđiều tiết\b",
    r"\bkéo-ngược\b",
)
# A4. Text about the reading, the app or the method instead of the reader's life.
META_TALK = _terms(
    r"\bphần dưới\b",
    r"\bmở phần\b",
    r"\bradar giữ\b",
    r"\bđây không phải tín hiệu\b",
    r"\bý chính của lá\b",
    r"\bví dụ\s*:",
    r"\bkhông nói bạn là gì\b",
    r"\bsuy từ chart\b",
    r"\bchart có thể\b",
    r"\bbài đọc\b",
    r"\bkhông phải bằng chứng\b",
)
# A7. Hedges; the gate allows 0.3 per sentence.
HEDGES = _terms(
    r"\bcó thể\b",
    r"\bdễ\b",
    r"\bchưa chắc\b",
    r"\bkhông phải\b",
    r"\bđôi lúc\b",
    r"\bcó lẽ\b",
)
# A11. Waiting copy and template leftovers: "{name}", "{{ name }}", "%s", "%(name)s", "<name>",
# "[TÊN]", and values a template prints when data is missing. Code words are case-sensitive.
PLACEHOLDERS = re.compile(
    r"(?i:chưa sẵn sàng|đang cập nhật|lorem ipsum)"
    r"|\bTODO\b|\bFIXME\b|\bTBD\b|\bXXX\b"
    r"|\{\{[^{}]*\}\}|\{[A-Za-z_][A-Za-z0-9_.]*\}|\$\{[^{}]*\}"
    r"|%(?:\([A-Za-z_]\w*\))?[sdif](?![^\W\d_])"
    r"|<[^<>\s][^<>]*>"
    r"|\[[^\[\]]*[A-Z][^\[\]]*\]"
    r"|\b(?:None|undefined|null|NaN|nil)\b"
)
# A14. An event stated as already done, without a condition word in the sentence: "vừa" with an
# action verb ("tin nhắn vừa gửi"), a person who "đã/mới" did it ("bạn đã cãi"), or a past time
# ("hôm qua", "sáng nay", "lúc nãy") the reader may not have lived. "lúc nãy"/"khi nãy" are past
# times, not conditions. "đã/mới" without a person is mostly a relative clause ("lời đã nói",
# "cần thời gian mới nói ra") and is not counted, except the original "đã gửi".
_PAST_VERBS = (
    "gửi|nói|nhắn|gặp|cãi|nhận|hứa|đăng|gọi|hỏi|trả lời|xin lỗi|chia tay|hủy|ký|đọc|nghe|quên"
    "|viết|bỏ|từ chối|đồng ý|mua|tiêu|bấm|chặn|xóa|hẹn|khóc|giận|mất"
)
_PEOPLE = "bạn|mình|người kia|người ấy|anh ấy|cô ấy|em ấy|họ|sếp|cả hai|hai bạn|hai người|người yêu"
PAST_ACTION = _terms(
    rf"\bvừa (?:{_PAST_VERBS})\b",
    rf"\b(?:{_PEOPLE}) (?:vừa |cũng |lại )?(?:đã|mới) (?:{_PAST_VERBS})\b",
    r"\bđã gửi\b",
    r"\brồi mới thấy\b",
)
PAST_TIME = _terms(
    r"\bhôm qua\b",
    r"\btối qua\b",
    r"\bđêm qua\b",
    r"\bsáng nay\b",
    r"\btrưa nay\b",
    r"\b(?:lúc|khi|ban|hồi) nãy\b",
    r"\bhồi sáng\b",
    r"\bhôm trước\b",
    r"\b(?:tuần|tháng) trước\b",
    r"\bnăm ngoái\b",
    r"\bvừa rồi\b",
    r"\bmới đây\b",
)
CONDITION_WORDS = _terms(r"\bnếu\b", r"\bkhi\b(?! nãy)", r"\blúc\b(?! nãy)", r"\bgiả sử\b")
_VUA = re.compile(r"\bvừa\b", re.IGNORECASE)

# A10. A word written only in ASCII letters is foreign unless it has the shape of one unaccented
# Vietnamese syllable (initial + rhyme). Vietnamese has no f, j, w or z, and no "st", "ck" or
# "nd" clusters, so "healing", "detox", "ghost" or "mindset" never fit. Loanwords that happen to
# fit ("sun", "moon", "plan"…) are listed. Product names are allowed; "Vibe" only as the
# capitalised product label.
_VIETNAMESE_SYLLABLE = re.compile(
    r"(?:ngh|ng|gh|gi|kh|nh|ph|qu|th|tr|ch|[bcdghklmnprstvx])?"
    r"(?:(?:oa|oe|uy|oo|[aeiouy])(?:ch|nh|ng|[cmnpt])|(?:uye|ye|ie|uo|ua)(?:ng|[cmnptiu])"
    r"|oai|oao|oay|oeo|uya|uyu|eo|ia|iu|ua|ui|oa|oe|uy|[ao][iouy]|[aeiouy])"
)
ENGLISH_LOANWORDS = frozenset(
    {
        "healing",
        "detox",
        "ghost",
        "toxic",
        "ascendant",
        "vibe",
        "inbox",
        "drama",
        "trend",
        "mindset",
        "transit",
        "retrograde",
        "ok",
        "okay",
        "sorry",
        "hot",
        "top",
        "team",
        "sale",
        "app",
        "like",
        "share",
        "post",
        "chart",
        "pattern",
        "mood",
        "crush",
        "flirt",
        "check",
        "test",
        "mini",
        "node",
        "true",
        "orb",
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "saturn",
        "uranus",
        "pluto",
        "neptune",
        "chiron",
        "composite",
        "overlay",
        "synastry",
        "deadline",
        "online",
        "offline",
        "spam",
        "story",
        "list",
        "plan",
        "space",
        "match",
        "date",
        "cute",
        "chill",
        "stress",
    }
)
ENGLISH_ALLOWLIST = frozenset({"radar", "luna", "zalo"})
PRODUCT_LABELS = frozenset({"Vibe", "VIBE"})
_FOREIGN_LETTERS = re.compile(r"[fjwz]")
_ASCII_WORD = re.compile(r"[a-z]+")

# Normalisation (gap register GT-11). Hidden characters are removed before linting and reported
# by the hard-zero rule H1; every run of spaces, tabs or look-alike spaces becomes one plain space,
# so a multiword pattern cannot be dodged with "không  muốn" or "không\tmuốn"; line breaks become
# one "\n" each (they still end a sentence); full-width ASCII becomes ASCII.
_ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff\u00ad\u180e"
_BIDI_CONTROLS = "\u200e\u200f\u061c\u202a-\u202e\u2066-\u2069"
HIDDEN_CHARACTERS = re.compile(f"[{_ZERO_WIDTH}{_BIDI_CONTROLS}]")
_LOOKALIKE_SPACES = re.compile("[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")
_LINE_BREAKS = re.compile("\r\n?|[\x0b\x0c\x85\u2028\u2029]")
# Any Unicode whitespace except the line feed: tab, NBSP, the look-alike spaces above and so on.
_HORIZONTAL_WHITESPACE = re.compile(r"[^\S\n]+")
_FULL_WIDTH_ASCII = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}

# Class-A safety (hard zero). A reading never diagnoses, predicts death or accidents, advises on
# money or law, states fate as certain, blames the reader, or uses crisis language. Sources: WHO
# safe messaging on suicide (2023), the gate spec, gap register GT-17/GT-24.
SAFETY_RULES: dict[str, re.Pattern[str]] = {
    "S1": _phrases(
        r"\bchẩn đoán\b",
        r"\btrầm cảm\b",
        r"\brối loạn (?:lo âu|ăn uống|lưỡng cực|giấc ngủ|tâm thần|nhân cách)\b",
        r"\bbệnh\b",
        r"\bung thư\b",
        r"\bkhối u\b",
        r"\btiểu đường\b",
        r"\bhuyết áp\b",
        r"\bđột quỵ\b",
        r"\b(?:không cần|khỏi|đừng) (?:đi )?khám\b",
        r"\b(?:uống|bỏ|ngưng|ngừng|tự mua|đổi) thuốc\b",
        r"\bnhịn ăn\b",
        r"\bthải độc\b",
        r"\bdetox\b",
        r"\bđau (?:đầu|bụng|ngực|lưng|dạ dày|tim|nửa đầu)\b",
        r"\bmang thai\b",
        r"\bsảy thai\b",
        r"\bvô sinh\b",
        r"\bphẫu thuật\b",
        r"\bchữa (?:khỏi|bệnh)\b",
    ),
    "S2": _phrases(
        r"\bchết\b",
        r"\btử vong\b",
        r"\bqua đời\b",
        r"\bmất mạng\b",
        r"\btai nạn\b",
        r"\btai ương\b",
        r"\btai họa\b",
        r"\bthảm họa\b",
        r"\bđổ máu\b",
        r"\bgặp (?:nạn|họa)\b",
        r"\bđừng ra (?:khỏi nhà|đường)\b",
    ),
    "S3": _phrases(
        r"\bvay\b",
        r"\b(?:mua|bán|giữ|tích trữ) vàng\b",
        r"\bxuống tiền\b",
        r"\bđầu tư (?:vào )?(?:tiền|vàng|cổ phiếu|chứng khoán|crypto|coin|tiền ảo|đất|bất động sản"
        r"|căn hộ|nhà)\b",
        r"\bcổ phiếu\b",
        r"\bchứng khoán\b",
        r"\bcrypto\b",
        r"\btiền (?:ảo|mã hóa|điện tử)\b",
        r"\bbất động sản\b",
        r"\b(?:lô đề|xổ số|cá cược|cá độ|đánh bạc|cờ bạc)\b",
        r"\blãi suất\b",
        r"\bchốt (?:lời|lỗ|căn)\b",
        r"\b(?:ngày|giờ) (?:đẹp|tốt|hợp) để (?:mua|bán|đầu tư|ký|vay)\b",
    ),
    "S4": _phrases(
        r"\bhợp đồng\b",
        r"\bly hôn\b",
        r"\b(?:thắng|thua|khởi|đi) kiện\b",
        r"\bkiện tụng\b",
        r"\bra tòa\b",
        r"\btòa án\b",
        r"\bluật sư\b",
        r"\btranh chấp (?:đất|tài sản|thừa kế)\b",
        r"\bthừa kế\b",
    ),
    "S5": _phrases(
        r"\bchắc chắn sẽ\b",
        r"\bnhất định sẽ\b",
        r"\bkhông thể tránh\b",
        r"\bkhông tránh khỏi\b",
        r"\bđịnh mệnh\b",
        r"\bsố phận\b",
        r"\bsố mệnh\b",
        r"\bvận hạn\b",
        r"\bnghiệp chướng\b",
        r"\bngày xui\b",
        r"\bxui xẻo\b",
        r"\bsẽ (?:đổ vỡ|tan vỡ|thất bại|chia tay|mất việc|gặp may|gặp xui|trúng|phát tài"
        r"|được tăng lương|thăng chức)\b",
        r"\b(?:khó|không thể) (?:mà )?cứu vãn\b",
        r"\b(?:sao \w+|vũ trụ|ông trời) (?:đang |sẽ )?(?:trừng phạt|phạt)\b",
    ),
    "S6": _phrases(
        r"\blỗi (?:là )?(?:ở|tại|do|của) bạn\b",
        r"\btại bạn\b",
        r"\bbạn (?:lúc nào cũng|luôn luôn|toàn) (?:làm hỏng|làm sai|phá hỏng|thất bại)\b",
        r"\bbạn (?:thật |quá |rất |đúng là )?(?:vô dụng|tệ hại|ngu ngốc|đáng trách|ích kỷ)\b",
        r"\bbạn lười (?:kinh khủng|quá|thế)\b",
        r"\bchẳng trách\b",
        r"\bđáng đời\b",
        r"\btự chuốc\b",
    ),
    "S7": _phrases(
        r"\bbiến mất\b",
        r"\bkhông cần ai\b",
        r"\bkhông muốn sống\b",
        r"\bkhông muốn tồn tại\b",
        r"\btự tử\b",
        r"\btự sát\b",
        r"\btự (?:làm )?hại\b",
        r"\btự làm đau\b",
        r"\bkết liễu\b",
        r"\b(?:kết thúc|chấm dứt) (?:tất cả|mọi thứ|cuộc đời|cuộc sống)\b",
        r"\bbuông xuôi\b",
        r"\b(?:mọi thứ|cuộc sống|sống) (?:đều |thật |cũng )?vô nghĩa\b",
        r"\bkhông ai cần bạn\b",
        r"\bđừng tin (?:ai|bất kỳ ai)\b",
        r"\bcắt đứt (?:với )?(?:mọi người|tất cả)\b",
    ),
    # S8 (HM-4). No source lets one transit foretell a life event, and Lá does not forecast them
    # (Daily v2 plan 1.1): pregnancy, marriage, a breakup, losing a job, illness, the death of a
    # loved one. Pregnancy and fertility are sensitive health data (HM-5) and are never raised,
    # not even as a condition. "chuyện con cái" as one door of a broad sentence stays allowed.
    "S8": _phrases(
        # pregnancy and fertility
        r"\b(?:có|mang|dính) (?:bầu|thai)\b",
        r"\b(?:bụng|bà|mẹ) bầu\b",
        r"\bthụ (?:thai|tinh)\b",
        r"\bthai (?:kỳ|nhi|sản)\b",
        r"\bsinh (?:con|em bé|bé|nở)\b",
        r"\b(?:có|đón) (?:em bé|thêm (?:con|bé|một bé|thành viên))\b",
        r"\b(?:sẽ|sắp) có (?:con|tin vui)\b",
        r"\blên chức (?:bố|mẹ|ba|cha|ông|bà)\b",
        r"\bhiếm muộn\b",
        # marriage
        r"\bkết hôn\b",
        r"\b(?:lấy|cưới) (?:chồng|vợ)\b",
        r"\b(?:cầu|đính) hôn\b",
        r"\bvề chung (?:một )?nhà\b",
        r"\b(?:sẽ|sắp|chuẩn bị|tính chuyện|đến lúc|tới lúc) (?:làm )?(?:đám )?cưới\b",
        r"\bđám cưới của (?:bạn|hai bạn|hai người)\b",
        # a breakup
        r"\b(?:sẽ|sắp|dễ|có thể|nguy cơ|đến lúc|tới lúc|chuẩn bị|đứng trước) (?:phải )?chia tay\b",
        r"\bchia tay (?:với )?(?:người yêu|người ấy|nửa kia|bạn trai|bạn gái|anh ấy|cô ấy"
        r"|chồng|vợ)\b",
        r"\b(?:hai bạn|hai người|cả hai) (?:sẽ |sắp |dễ )?chia tay\b",
        r"\bđường ai nấy đi\b",
        r"\bly thân\b",
        r"\bngoại tình\b",
        r"\b(?:tình cảm|mối quan hệ|chuyện tình|cuộc tình|hôn nhân) (?:này |của bạn )?"
        r"(?:sẽ |sắp |dễ |có thể )?(?:tan vỡ|đổ vỡ|rạn nứt|kết thúc|chấm dứt)\b",
        r"\b(?:sẽ|sắp) bị (?:đá|bỏ|bỏ rơi|phản bội|cắm sừng)\b",
        r"\bbị cắm sừng\b",
        # losing a job
        r"\bmất (?:việc|chức|ghế|chỗ làm|công việc)\b",
        r"\bthất nghiệp\b",
        r"\bsa thải\b",
        r"\bđuổi việc\b",
        r"\bcho (?:bạn )?nghỉ việc\b",
        r"\bcắt giảm (?:nhân sự|biên chế|người)\b",
        r"\bgiáng chức\b",
        r"\bphá sản\b",
        r"\b(?:sẽ|sắp) (?:phải )?nghỉ việc\b",
        # illness
        r"\b(?:bị|đổ|ngã|lăn ra|phát) ốm\b",
        r"\bốm (?:nặng|đau|liệt)\b",
        r"\b(?:nhập|nằm|vào|ra) viện\b(?! (?:bảo tàng|nghiên cứu|hàn lâm|dưỡng lão))",
        r"\bcấp cứu\b",
        r"\b(?:phải|bị) mổ\b",
        r"\bchấn thương\b",
        r"\bsốt (?:cao|xuất huyết)\b",
        r"\bcảm cúm\b",
        r"\bsức kh(?:ỏe|oẻ) (?:của bạn )?(?:sẽ |sắp |đang |dễ )?"
        r"(?:suy|giảm sút|đi xuống|xấu đi|có vấn đề)\b",
        # the death of a loved one
        r"\bmất (?:đi )?(?:người thân|người thương|người nhà|bố|mẹ|cha|vợ|chồng|ông"
        r"|bà nội|bà ngoại)\b",
        r"\bngười thân (?:sẽ |sắp |có thể |dễ )?(?:mất|ra đi|qua đời|không còn|đau ốm|bệnh)\b",
        r"\b(?:để|chịu|đám|có) tang\b",
        r"\btang (?:lễ|sự|thương)\b",
        r"\bđám ma\b",
        r"\btừ trần\b",
        r"\bkhuất núi\b",
        r"\bra đi mãi mãi\b",
        r"\bmồ côi\b",
        r"\bgóa (?:chồng|vợ|bụa)\b",
        r"\bâm dương cách biệt\b",
        r"\bmất mát (?:người thân|lớn trong gia đình)\b",
        # other life events foretold
        r"\b(?:sẽ|sắp) (?:gặp|tìm thấy|tìm được|có) (?:người yêu|nửa kia|chân ái|ý trung nhân"
        r"|người định mệnh|tình yêu mới|người ấy)\b",
        r"\b(?:sẽ|sắp) (?:chuyển nhà|chuyển việc|đổi việc|ra nước ngoài|định cư)\b",
    ),
}

# S9 (HM-4). Lá never assumes the reader's circumstances: single or partnered, has children or
# not, gender (plan 1.1 personas, rule N-7). A door that names the circumstance as one
# possibility ("Nếu bạn đang độc thân, …", "Nếu bạn có con nhỏ, đón con sớm") is not an
# assumption: a match is exempt when a door word before it opens a condition (up to the next
# clause break or "thì") that contains the match or names the same kind of circumstance; the
# condition's scope runs through the consequent. A condition about something else ("Nếu chiều
# nay rảnh thì đón con sớm") does not exempt it.
_CIRCUMSTANCE_KINDS: tuple[tuple[str, re.Pattern[str], re.Pattern[str]], ...] = (
    (
        "single",
        _terms(
            r"\bbạn (?:đang |vẫn |còn |hiện )?(?:độc thân|ế|lẻ bóng|một mình chưa có ai)\b",
            r"\b(?:độc thân|ế|lẻ bóng) như bạn\b",
            r"\bchưa có (?:người yêu|bồ|nửa kia|ai để yêu)\b",
            r"\bbạn chưa (?:lập gia đình|kết hôn|có gia đình|có con)\b",
        ),
        _terms(r"\b(?:độc thân|ế|lẻ bóng|một mình|chưa có ai|người yêu|bồ|nửa kia)\b"),
    ),
    (
        "partnered",
        _terms(
            r"\b(?:người yêu|bạn trai|bạn gái|nửa kia|người ấy|vợ|chồng|người thương|crush)"
            r" của bạn\b"
            r"(?! (?:ấy|bè|thân))",
            r"\b(?:ông|bà) xã\b",
            r"\bvợ chồng (?:bạn|nhà bạn|hai bạn)\b",
            r"\b(?:nhà|mẹ|bố|ba) (?:chồng|vợ)\b",
            r"\bgia đình nhỏ của bạn\b",
        ),
        _terms(
            r"\b(?:người yêu|bạn trai|bạn gái|nửa kia|người ấy|vợ|chồng|người thương|crush"
            r"|gia đình|kết hôn|lập gia đình|có đôi|hẹn hò)\b"
        ),
    ),
    (
        "children",
        _terms(
            r"\b(?:con|các con|con cái|con nhỏ|bé|nhóc|các bé) (?:của|nhà) bạn\b"
            r"(?! (?:ấy|bè|thân))",
            r"\bcon bạn\b(?! (?:ấy|bè|thân|học|cùng))",
            r"\b(?:đón|đưa) (?:con|bé|các con)\b",
            r"\b(?:dỗ|ru|chăm|nuôi|tắm cho) (?:con|bé|các con)\b",
            r"\bcho (?:con|bé) (?:bú|ăn|ngủ)\b",
            r"\bbạn (?:là|đang làm) (?:bố|mẹ|cha|ba|cha mẹ|bố mẹ|phụ huynh)\b",
            r"\b(?:bố mẹ|cha mẹ|phụ huynh|mẹ bỉm|bỉm sữa) như bạn\b",
            r"\bmẹ bỉm\b",
        ),
        _terms(
            r"\b(?:có|nuôi|chăm|nhà có) (?:con|bé|các con|con nhỏ)\b",
            r"\b(?:con cái|con nhỏ|phụ huynh|làm cha mẹ|làm bố mẹ|làm mẹ|làm bố|làm cha)\b",
            r"\bbạn (?:là|đang làm) (?:bố|mẹ|cha|ba|cha mẹ|bố mẹ|phụ huynh)\b",
        ),
    ),
    (
        "gender",
        _terms(
            r"\bbạn là (?:một )?"
            r"(?:phụ nữ|đàn ông|đàn bà|con gái|con trai|cô gái|chàng trai|nam|nữ)\b",
            r"\b(?:phụ nữ|đàn ông|con gái|con trai|cô gái|chàng trai|nàng|chàng) như bạn\b",
            r"\bphái (?:đẹp|mạnh|yếu)\b",
            r"\bchị em (?:mình|phụ nữ|ta)\b",
            r"\b(?:các|mấy) (?:nàng|chàng)\b",
            r"\b(?:nàng|chàng|anh|chị|cô) ơi\b",
            r"\bđấng mày râu\b",
            r"\b(?:cô nàng|chàng trai|anh chàng|quý cô|quý ông)"
            r" (?:Bạch Dương|Kim Ngưu|Song Tử|Cự Giải"
            r"|Sư Tử|Xử Nữ|Thiên Bình|Bọ Cạp|Thiên Yết|Nhân Mã|Ma Kết|Bảo Bình|Song Ngư)\b",
        ),
        _terms(r"\b(?:phụ nữ|đàn ông|đàn bà|con gái|con trai|cô gái|chàng trai|nam|nữ|giới)\b"),
    ),
)
ASSUMED_CIRCUMSTANCES = re.compile(
    "|".join(f"(?:{pattern.pattern})" for _, pattern, _ in _CIRCUMSTANCE_KINDS), re.IGNORECASE
)
_DOOR_WORDS = re.compile(r"\b(?:nếu|giả sử|trường hợp|với ai|ai đang|người đang)\b", re.IGNORECASE)
_CONDITION_END = re.compile(r"[,;:]|\bthì\b", re.IGNORECASE)


def _conditions(sentence: str) -> list[tuple[int, int]]:
    """(start, end) of every condition a door word opens: up to the next clause break or "thì"."""

    found = []
    for door in _DOOR_WORDS.finditer(sentence):
        end = _CONDITION_END.search(sentence, door.end())
        found.append((door.start(), end.start() if end else len(sentence)))
    return found


# A condition opens the door only when it says the reader (or "ai/người" the door names) has the
# circumstance: the words between the door and the topic may only be "bạn" and plain verbs of
# being or having. "Nếu bạn chưa có con", "Nếu bạn làm việc với phụ huynh" do not open it.
_AFFIRMING_GAP = re.compile(
    r"\s*(?:bạn\s+)?(?:(?:đã|đang|vẫn|cũng|hiện|là|có|vừa)\s+)*", re.IGNORECASE
)
_NEGATION = re.compile(r"\b(?:chưa|không|chẳng|chả|đâu có|không phải)\b", re.IGNORECASE)


def _affirms(sentence: str, door_end: int, end: int, topic: re.Pattern[str]) -> bool:
    if _NEGATION.search(sentence, door_end, end):
        return False
    return any(
        _AFFIRMING_GAP.fullmatch(sentence, door_end, match.start())
        for match in topic.finditer(sentence, door_end, end)
    )


def assumes_circumstances(sentence: str) -> bool:
    """S9. True when the sentence takes a circumstance of the reader for granted. A circumstance
    after a door word is fine only when that condition affirms the reader has it."""

    doors = [
        (door.end(), end)
        for door, (_, end) in zip(
            _DOOR_WORDS.finditer(sentence), _conditions(sentence), strict=True
        )
    ]
    for _, pattern, topic in _CIRCUMSTANCE_KINDS:
        for match in pattern.finditer(sentence):
            if not any(
                door_end <= match.end() and _affirms(sentence, door_end, end, topic)
                for door_end, end in doors
            ):
                return True
    return False


# Closing quotes (straight, curly, guillemet) or a bracket after the end mark.
_SENTENCE_SPLIT = re.compile("(?<=[.!?\u2026])[\"\u201d'\u2019\u00bb)]*\\s+|\n+")
# Quotes (straight, curly, guillemets), brackets, dashes (- en em) and the middle dot.
_EDGE_PUNCTUATION = " \t.!?\u2026\"\u201c\u201d'\u2018\u2019\u00ab\u00bb()[]:;,-\u2013\u2014\u00b7"


@dataclass(frozen=True)
class AstroFacts:
    """What the engine computed for one reading (A15), in engine ids, never prose.

    ``placements`` are (body, sign) pairs, ``houses`` (body, house number). ``contacts`` are the
    natal aspects and ``transits`` the transit-to-natal contacts, both (first body, second body,
    aspect kind, phase): a natal aspect is listed in both orders; a transit lists the transit body
    first and the natal body second. Phase is ``approaching``, ``exact`` or ``separating``. A
    claim about today's sky is checked against ``transits`` only.
    """

    placements: frozenset[tuple[str, str]] = frozenset()
    houses: frozenset[tuple[str, int]] = frozenset()
    contacts: frozenset[tuple[str, str, str, str]] = frozenset()
    transits: frozenset[tuple[str, str, str, str]] = frozenset()


@dataclass(frozen=True)
class ClarityDocument:
    """One rendered reading as a user sees it: body text by section, nothing else.

    ``first_screen`` names the sections shown before the reader opens anything, with the A9
    syllable limit for this reading. ``facts`` are the engine's facts for A15; a reading without a
    chart (Tarot) has none, and A15 does not apply to it.
    """

    surface: str
    sample_id: str
    sections: tuple[tuple[str, str], ...]
    variant: str = "default"
    first_screen: tuple[str, ...] = ()
    first_screen_limit: int | None = None
    facts: AstroFacts | None = None


@dataclass(frozen=True)
class DailyDay:
    """One rendered Daily note in a 30-day run for one persona with a birth time (A13).

    ``reason`` is a stable id of why this note was chosen (a transit's bodies and aspect, or the
    natal rule when no transit is used), ``sky_bodies`` the transit bodies the note uses; the
    Moon's own sign or house counts as ``moon``.
    """

    persona: str
    day: str
    headline: str
    reason: str
    sky_bodies: tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfaceReport:
    surface: str
    samples: int
    variants: dict[str, int]
    rules: dict[str, int]
    readings_flagged: dict[str, int] = field(default_factory=dict)
    keys: dict[str, tuple[str, ...]] = field(default_factory=dict)
    hard_zero: dict[str, int] = field(default_factory=dict)

    def as_baseline(self) -> dict[str, Any]:
        return {
            "samples": self.samples,
            "variants": dict(sorted(self.variants.items())),
            "rules": {rule: self.rules.get(rule, 0) for rule in RULES},
            "keys": {rule: list(self.keys.get(rule, ())) for rule in RULES},
        }


def normalize_text(text: str) -> str:
    """NFC, one plain space per run of other whitespace, line feeds for line breaks, ASCII for
    full-width letters, no zero-width or bidi controls."""

    text = HIDDEN_CHARACTERS.sub("", text.translate(_FULL_WIDTH_ASCII))
    text = _LINE_BREAKS.sub("\n", _LOOKALIKE_SPACES.sub(" ", text))
    return unicodedata.normalize("NFC", _HORIZONTAL_WHITESPACE.sub(" ", text))


def normalize_document(document: ClarityDocument) -> ClarityDocument:
    return replace(
        document,
        sections=tuple((name, normalize_text(text)) for name, text in document.sections),
    )


def sentence_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Start and end offsets of each sentence in ``text`` (what ``sentences`` returns)."""

    spans: list[tuple[int, int]] = []
    start = 0
    for end, resume in (
        *((match.start(), match.end()) for match in _SENTENCE_SPLIT.finditer(text)),
        (len(text), len(text)),
    ):
        part = text[start:end]
        if part.strip(_EDGE_PUNCTUATION):
            spans.append((start + len(part) - len(part.lstrip()), start + len(part.rstrip())))
        start = resume
    return tuple(spans)


def sentences(text: str) -> tuple[str, ...]:
    return tuple(text[start:end] for start, end in sentence_spans(text))


def syllables(sentence: str) -> int:
    """Vietnamese is written one syllable per space-separated token."""

    return sum(1 for token in sentence.split() if re.search(r"\w", token))


def _count(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text))


def count_jargon(text: str) -> int:
    """A1. Every occurrence counts for now.

    TODO(A1+): do not count a term whose plain meaning and effect on the reader ("bạn" with a
    behaviour verb) follow in the same or the next sentence (CDC item 7).
    """

    return _count(JARGON, text)


def count_coined_labels(text: str) -> int:
    return _count(COINED_LABELS, text)


def count_engine_metaphors(text: str) -> int:
    return _count(ENGINE_METAPHORS, text)


def count_meta_talk(text: str) -> int:
    return _count(META_TALK, text)


def count_hedges(text: str) -> int:
    return _count(HEDGES, text)


def count_placeholders(text: str) -> int:
    return _count(PLACEHOLDERS, text)


def count_house_sign_aspect_words(text: str) -> int:
    return _count(HOUSE_SIGN_ASPECT, text)


def english_words(text: str) -> tuple[str, ...]:
    words: list[str] = []
    for token in re.findall(r"[^\W\d_]+", text):
        word = token.casefold()
        if not _ASCII_WORD.fullmatch(word) or word in ENGLISH_ALLOWLIST or len(word) < 2:
            continue
        if token in PRODUCT_LABELS:
            continue
        if (
            _FOREIGN_LETTERS.search(word)
            or word in ENGLISH_LOANWORDS
            or not _VIETNAMESE_SYLLABLE.fullmatch(word)
        ):
            words.append(word)
    return tuple(words)


def count_long_sentences(items: Iterable[str]) -> int:
    return sum(syllables(sentence) > MAX_SENTENCE_SYLLABLES for sentence in items)


def is_past_event_claim(sentence: str) -> bool:
    """A14. "vừa … vừa …" is "both … and …", not "just did"."""

    if CONDITION_WORDS.search(sentence):
        return False
    if PAST_TIME.search(sentence):
        return True
    correlative = len(_VUA.findall(sentence)) > 1
    return any(
        not (correlative and match.group(0).casefold().startswith("vừa"))
        for match in PAST_ACTION.finditer(sentence)
    )


def count_past_action_claims(items: Iterable[str]) -> int:
    return sum(is_past_event_claim(sentence) for sentence in items)


def _bigrams(sentence: str) -> set[tuple[str, str]]:
    tokens = re.findall(r"\w+", sentence.casefold())
    return set(pairwise(tokens))


def near_duplicate_sentence_pairs(items: Iterable[str]) -> tuple[tuple[str, str], ...]:
    """A5. Pairs of sentences (>= 6 syllables) sharing >= 50% of the smaller one's bigrams."""

    grams = [
        (sentence, _bigrams(sentence))
        for sentence in items
        if syllables(sentence) >= NEAR_DUPLICATE_MIN_SYLLABLES
    ]
    pairs: list[tuple[str, str]] = []
    for index, (first_text, first) in enumerate(grams):
        for second_text, second in grams[index + 1 :]:
            if first and second:
                shared = len(first & second) / min(len(first), len(second))
                if shared >= NEAR_DUPLICATE_OVERLAP:
                    pairs.append((first_text, second_text))
    return tuple(pairs)


def near_duplicate_pairs(items: Iterable[str]) -> int:
    return len(near_duplicate_sentence_pairs(items))


def excess_engine_metaphors(text: str) -> int:
    return max(0, count_engine_metaphors(text) - ENGINE_METAPHOR_ALLOWANCE)


def excess_hedges(text: str, sentence_count: int) -> int:
    allowed = math.floor(HEDGES_PER_SENTENCE * sentence_count + 1e-9)
    return max(0, count_hedges(text) - allowed)


def document_sentences(document: ClarityDocument) -> tuple[str, ...]:
    return tuple(sentence for _, text in document.sections for sentence in sentences(text))


# Fixed headings (Radar section and scene titles) repeat across readings by design, so A6 skips
# sections whose name ends with this suffix; every other rule still lints them.
TITLE_SECTION_SUFFIX = "_title"


def a6_sentences(document: ClarityDocument) -> tuple[str, ...]:
    """Sentences A6 compares across a surface: every section except fixed titles."""

    return tuple(
        sentence
        for name, text in document.sections
        if not name.endswith(TITLE_SECTION_SUFFIX)
        for sentence in sentences(text)
    )


def _sentence_key(sentence: str) -> str:
    folded = " ".join(sentence.casefold().split()).strip(_EDGE_PUNCTUATION)
    return re.sub(r"\d+", "#", folded)


def _digest(normalised: str) -> str:
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:KEY_LENGTH]


def sentence_key(sentence: str) -> str:
    """Short, stable id of a normalised sentence; the baseline stores ids, never prose."""

    return _digest(_sentence_key(sentence))


def _pair_key(first: str, second: str) -> str:
    return _digest("\x1f".join(sorted((_sentence_key(first), _sentence_key(second)))))


# Sentence-level rules: a sentence that matches is a violation key for the rule. The safety rules
# are keyed by ``safety_keys`` instead, because their phrases may cross a line break.
_SENTENCE_RULES: dict[str, Callable[[str], bool]] = {
    "A1": lambda sentence: bool(JARGON.search(sentence)),
    "A2": lambda sentence: bool(COINED_LABELS.search(sentence)),
    "A4": lambda sentence: bool(META_TALK.search(sentence)),
    "A8": lambda sentence: syllables(sentence) > MAX_SENTENCE_SYLLABLES,
    "A10": lambda sentence: bool(english_words(sentence)),
    "A11": lambda sentence: bool(PLACEHOLDERS.search(sentence)),
    "A14": is_past_event_claim,
    "A16": lambda sentence: bool(HOUSE_SIGN_ASPECT.search(sentence)),
    # S9 is sentence-level (no single phrase), so it is keyed here, not by ``safety_keys``.
    "S9": assumes_circumstances,
}
# Every safety rule, in order: pattern rules plus the sentence-level S9.
SAFETY_RULE_IDS: tuple[str, ...] = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))


def count_hidden_characters(document: ClarityDocument) -> int:
    """H1. Sections that carry a zero-width or bidi control character (before normalisation)."""

    return sum(bool(HIDDEN_CHARACTERS.search(text)) for _, text in document.sections)


def count_safety(rule: str, text: str) -> int:
    if rule == "S9":
        return sum(assumes_circumstances(sentence) for sentence in sentences(text))
    return _count(SAFETY_RULES[rule], text)


def first_screen_limit(surface: str, *, cards: int = 0) -> int | None:
    """A9 limit in syllables: by surface, and by spread size for Tarot."""

    if surface == "tarot":
        return TAROT_FIRST_SCREEN_LIMITS.get(cards)
    return FIRST_SCREEN_LIMITS.get(surface)


def first_screen_syllables(document: ClarityDocument) -> int:
    shown = set(document.first_screen)
    return sum(syllables(text) for name, text in document.sections if name in shown)


def first_screen_overflow(document: ClarityDocument) -> str | None:
    """A9. The key of the first screen when it is longer than its limit, else ``None``."""

    if document.first_screen_limit is None or not document.first_screen:
        return None
    if first_screen_syllables(document) <= document.first_screen_limit:
        return None
    shown = set(document.first_screen)
    return _digest(
        "\x1e".join(_sentence_key(text) for name, text in document.sections if name in shown)
    )


# A15 vocabulary: the names the renderers write, mapped to engine ids. Names are matched
# case-sensitively ("mặt trời" in an everyday sentence is not the planet) and both tone spellings
# are accepted ("Thủy"/"Thuỷ", "Hỏa"/"Hoả").
_BODY_NAMES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Mặt Trời", ("sun",)),
    ("Mặt Trăng", ("moon",)),
    ("Sao Th(?:ủy|uỷ)", ("mercury",)),
    ("Sao Kim", ("venus",)),
    ("Sao H(?:ỏa|oả)", ("mars",)),
    ("Sao Mộc", ("jupiter",)),
    ("Sao Thổ", ("saturn",)),
    ("(?:Sao )?Thiên Vương", ("uranus",)),
    ("(?:Sao )?Hải Vương", ("neptune",)),
    ("(?:Sao )?Diêm Vương", ("pluto",)),
    ("Nút Bắc", ("true_node", "mean_node")),
    ("Nút Nam", ("south_node",)),
    ("Chiron", ("chiron",)),
    ("[Cc]ung Mọc", ("ascendant",)),
)
_SIGN_NAMES: tuple[tuple[str, str], ...] = (
    ("Bạch Dương", "aries"),
    ("Kim Ngưu", "taurus"),
    ("Song Tử", "gemini"),
    ("Cự Giải", "cancer"),
    ("Sư Tử", "leo"),
    ("Xử Nữ", "virgo"),
    ("Thiên Bình", "libra"),
    ("Bọ Cạp|Thiên Yết|Hổ Cáp", "scorpio"),
    ("Nhân Mã", "sagittarius"),
    ("Ma Kết", "capricorn"),
    ("Bảo Bình", "aquarius"),
    ("Song Ngư", "pisces"),
)
_BODY_PATTERN = re.compile(
    "|".join(f"(?P<b{index}>\\b(?:{name})\\b)" for index, (name, _) in enumerate(_BODY_NAMES))
)
_SIGN_PATTERN = re.compile(
    "|".join(f"(?P<s{index}>\\b(?:{name})\\b)" for index, (name, _) in enumerate(_SIGN_NAMES))
)
_HOUSE_WORDS = {
    "một": 1,
    "nhất": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "tư": 4,
    "năm": 5,
    "sáu": 6,
    "bảy": 7,
    "tám": 8,
    "chín": 9,
    "mười": 10,
    "mười một": 11,
    "mười hai": 12,
}
_HOUSE_MENTION = re.compile(
    r"\b[Nn]hà (?:thứ )?(?P<digits>\d{1,2})\b"
    r"|\b[Nn]hà thứ (?P<word>mười một|mười hai|mười|một|nhất|hai|ba|bốn|tư|năm|sáu|bảy|tám|chín)\b"
    r"|\bNhà (?P<title>Mười Một|Mười Hai|Mười|Một|Hai|Ba|Bốn|Năm|Sáu|Bảy|Tám|Chín)\b"
)
# Aspect words, from the most specific; a sentence names an aspect only with two bodies in it.
_ASPECT_WORDS: tuple[tuple[re.Pattern[str], frozenset[str]], ...] = (
    (_terms(r"\blục hợp\b"), frozenset({"sextile"})),
    (_terms(r"\btam hợp\b"), frozenset({"trine"})),
    (_terms(r"\bvuông góc\b", r"\bgóc vuông\b"), frozenset({"square"})),
    (_terms(r"\bđối đỉnh\b", r"\bxung chiếu\b"), frozenset({"opposition"})),
    (
        _terms(r"\bđi sát\b", r"\bđồng cung\b", r"\bgiao hội\b", r"\btrùng tụ\b", r"\bhội tụ\b"),
        frozenset({"conjunction"}),
    ),
    (_terms(r"\bhỗ trợ\b", r"\bgóc thuận\b", r"\bnâng đỡ\b"), frozenset({"sextile", "trine"})),
    (_terms(r"\bgóc căng\b", r"\bcăng với\b"), frozenset({"square", "opposition"})),
)
_PHASE_WORDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (_terms(r"\bđang (?:tiến|tới|đến) gần\b", r"\bsắp (?:chính xác|chạm|khớp)\b"), "approaching"),
    (_terms(r"\bđang (?:rời|tách)(?: xa| ra)?\b", r"\bđã qua điểm\b"), "separating"),
    (_terms(r"\bchính xác\b", r"\bđúng góc\b"), "exact"),
)


@dataclass(frozen=True)
class _Mention:
    start: int
    end: int
    ids: tuple[str, ...]


def _bodies(sentence: str) -> list[_Mention]:
    found = []
    for match in _BODY_PATTERN.finditer(sentence):
        index = int(str(match.lastgroup)[1:])
        found.append(_Mention(match.start(), match.end(), _BODY_NAMES[index][1]))
    return found


def _signs(sentence: str) -> list[tuple[int, str]]:
    return [
        (match.start(), _SIGN_NAMES[int(str(match.lastgroup)[1:])][1])
        for match in _SIGN_PATTERN.finditer(sentence)
    ]


def _houses(sentence: str) -> list[tuple[int, int]]:
    found = []
    for match in _HOUSE_MENTION.finditer(sentence):
        value = match.group("digits") or match.group("word") or match.group("title")
        number = int(value) if value.isdigit() else _HOUSE_WORDS[value.casefold()]
        found.append((match.start(), number))
    return found


# A sentence about the current sky claims a transit, not a natal aspect.
_TRANSIT_TIME = _terms(
    r"\b(?:hôm|sáng|trưa|chiều|tối|đêm|tuần|tháng|năm) nay\b",
    r"\blúc này\b",
    r"\bbây giờ\b",
    r"\bdạo này\b",
    r"\bnhững ngày (?:này|tới)\b",
    r"\bhiện tại\b",
)


@dataclass(frozen=True)
class _AspectClaim:
    first: _Mention
    second: _Mention
    kinds: frozenset[str]


def _aspect_claims(sentence: str, bodies: Sequence[_Mention]) -> list[_AspectClaim]:
    """Every aspect named in the sentence, each with its own two bodies: the body after the
    aspect word, and the nearest body before it that is not the previous claim's second body
    ("Sao Kim tam hợp Sao Hỏa và đối đỉnh Sao Mộc" is Kim-Hỏa and Kim-Mộc). With no body after
    the word, the two bodies before it ("Sao Kim và Sao Hỏa tam hợp")."""

    words: list[tuple[int, int, frozenset[str]]] = []
    for pattern, kinds in _ASPECT_WORDS:
        for match in pattern.finditer(sentence):
            if not any(start < match.end() and match.start() < end for start, end, _ in words):
                words.append((match.start(), match.end(), kinds))
    claims: list[_AspectClaim] = []
    previous: _Mention | None = None
    for start, end, kinds in sorted(words, key=lambda word: word[0]):
        before = [mention for mention in bodies if mention.end <= start]
        after = [mention for mention in bodies if mention.start >= end]
        if after:
            firsts = [mention for mention in before if mention is not previous] or before
            if not firsts:
                continue
            claim = _AspectClaim(firsts[-1], after[0], kinds)
        elif len(before) >= 2:
            claim = _AspectClaim(before[-2], before[-1], kinds)
        else:
            continue
        claims.append(claim)
        previous = claim.second
    return claims


def _phase(text: str) -> str | None:
    return next((phase for pattern, phase in _PHASE_WORDS if pattern.search(text)), None)


_CLAUSE_BREAK = re.compile(r"[,;:]")
_CLAUSE_JOIN = re.compile(r"\b(?:và|nhưng|còn)\b", re.IGNORECASE)


def _claim_windows(sentence: str, claims: Sequence[_AspectClaim]) -> list[tuple[int, int]]:
    """The stretch of the sentence each claim owns. Between two claims the text after the first
    claim's second body is cut at the last clause break (comma, semicolon, colon) before the next
    claim's second body; with none, where the next claim's own first body starts; with that body
    shared, at the last "và/nhưng/còn". So phase words before or after a claim's bodies stay in
    that claim's clause."""

    if not claims:
        return []
    cuts: list[int] = []
    for current, following in pairwise(claims):
        gap_start = current.second.end
        gap_end = max(gap_start, following.second.start)
        breaks = [m.end() for m in _CLAUSE_BREAK.finditer(sentence, gap_start, gap_end)]
        if not breaks and gap_start <= following.first.start < gap_end:
            breaks = [following.first.start]
        if not breaks:
            breaks = [m.start() for m in _CLAUSE_JOIN.finditer(sentence, gap_start, gap_end)]
        cuts.append(breaks[-1] if breaks else gap_end)
    starts = [0, *cuts]
    ends = [*cuts, len(sentence)]
    return list(zip(starts, ends, strict=True))


def _claim_phases(sentence: str, claims: Sequence[_AspectClaim]) -> list[str | None]:
    """The phase each claim states: the phase words inside that claim's own clause, before or
    after its bodies ("Sao Kim đang rời xa góc tam hợp với Sao Hỏa, Mặt Trăng đang tiến gần …")."""

    return [_phase(sentence[start:end]) for start, end in _claim_windows(sentence, claims)]


def _owner(
    position: int, bodies: Sequence[_Mention], subject: tuple[str, ...] | None
) -> tuple[str, ...] | None:
    before = [mention for mention in bodies if mention.end <= position]
    return before[-1].ids if before else subject


def _sentence_fact_errors(
    sentence: str, facts: AstroFacts, subject: tuple[str, ...] | None
) -> tuple[bool, tuple[str, ...] | None]:
    """Whether every checkable fact in the sentence is in ``facts``, and the subject body the next
    sentence of the same section inherits."""

    bodies = _bodies(sentence)
    ok = True
    today = _TRANSIT_TIME.search(sentence) is not None
    claims = _aspect_claims(sentence, bodies)
    for claim, phase in zip(claims, _claim_phases(sentence, claims), strict=True):
        first, second = claim.first, claim.second
        directed = sentence[second.end :].lstrip().startswith("của bạn")
        transit = directed or today
        pool = facts.transits if transit else facts.contacts | facts.transits
        if not any(
            kind in claim.kinds
            and (phase is None or phase == contact_phase)
            and (
                (a in first.ids and b in second.ids)
                or (not directed and a in second.ids and b in first.ids)
            )
            for a, b, kind, contact_phase in pool
        ):
            ok = False
    for position, sign in _signs(sentence):
        owner = _owner(position, bodies, subject)
        if owner is not None and not any((body, sign) in facts.placements for body in owner):
            ok = False
    for position, number in _houses(sentence):
        owner = _owner(position, bodies, subject)
        if owner is not None and not any((body, number) in facts.houses for body in owner):
            ok = False
    return ok, (bodies[-1].ids if bodies else subject)


def _section_group(name: str) -> str:
    """Sections of one claim share a suffix ("summary_sun-sign", "meaning_sun-sign")."""

    return name.split("_", 1)[1] if "_" in name else name


def astro_fact_errors(document: ClarityDocument) -> tuple[str, ...]:
    """A15. Sentences that name a placement, house or aspect the engine did not compute for this
    reading. A sign or house with no body in the sentence belongs to the last body named earlier
    in the same claim; one with no body at all cannot be checked and is skipped."""

    facts = document.facts
    if facts is None:
        return ()
    errors: list[str] = []
    group: str | None = None
    subject: tuple[str, ...] | None = None
    for name, text in document.sections:
        if _section_group(name) != group:
            group, subject = _section_group(name), None
        for sentence in sentences(text):
            ok, subject = _sentence_fact_errors(sentence, facts, subject)
            if not ok:
                errors.append(sentence)
    return tuple(errors)


def daily_follow_findings(days: Iterable[DailyDay]) -> tuple[int, frozenset[str]]:
    """A13 over 30-day runs: (a) every day uses a fast factor, (b) no reason on more than 3 of any
    7 consecutive days, (c) no headline repeated, and every run covers 30 consecutive days.
    Returns the violation count (days without a fast factor, crowded reasons, repeated
    headlines) and one key per persona and failed check (hashes only), so a check that starts
    failing for another persona is a new key."""

    runs: dict[str, list[DailyDay]] = defaultdict(list)
    for day in days:
        runs[day.persona].append(day)
    count = 0
    keys: set[str] = set()
    for persona, run in sorted(runs.items()):
        run.sort(key=lambda item: item.day)
        dates = [_iso_day(item.day) for item in run]
        consecutive = all((later - earlier).days == 1 for earlier, later in pairwise(dates))
        if len(run) < DAILY_FOLLOW_DAYS or not consecutive:
            count += 1
            keys.add(_digest(f"A13:coverage:{persona}"))
        slow = sum(not FAST_BODIES.intersection(item.sky_bodies) for item in run)
        if slow:
            count += slow
            keys.add(_digest(f"A13:fast:{persona}"))
        crowded: set[str] = set()
        for start in range(max(0, len(run) - DAILY_REASON_WINDOW + 1)):
            window = Counter(item.reason for item in run[start : start + DAILY_REASON_WINDOW])
            crowded |= {reason for reason, seen in window.items() if seen > DAILY_REASON_MAX_DAYS}
        if crowded:
            count += len(crowded)
            keys.add(_digest(f"A13:reason:{persona}"))
        headlines = Counter(_sentence_key(normalize_text(item.headline)) for item in run)
        repeats = sum(seen - 1 for seen in headlines.values())
        if repeats:
            count += repeats
            keys.add(_digest(f"A13:headline:{persona}"))
    return count, frozenset(keys)


def _iso_day(value: str) -> date:
    return date.fromisoformat(value)


def safety_keys(rule: str, text: str) -> frozenset[str]:
    """Keys of the sentences a safety phrase touches. A phrase split by a line break touches two
    "sentences"; its key is the key of both read as one, which is the one-line sentence's key
    when the only break was inside the phrase."""

    spans = sentence_spans(text)
    keys: set[str] = set()
    for match in SAFETY_RULES[rule].finditer(text):
        touched = [span for span in spans if span[0] < match.end() and match.start() < span[1]]
        found = text[touched[0][0] : touched[-1][1]] if touched else match.group(0)
        keys.add(sentence_key(found))
    return frozenset(keys)


def _document_findings(
    document: ClarityDocument,
) -> tuple[dict[str, int], dict[str, frozenset[str]]]:
    hidden = {
        sentence_key(normalize_text(text))
        for _, text in document.sections
        if HIDDEN_CHARACTERS.search(text)
    }
    document = normalize_document(document)
    body = "\n".join(text for _, text in document.sections)
    items = document_sentences(document)
    pairs = near_duplicate_sentence_pairs(items)
    overflow = first_screen_overflow(document)
    fact_errors = astro_fact_errors(document)
    counts = {
        "A1": count_jargon(body),
        "A2": count_coined_labels(body),
        "A3": excess_engine_metaphors(body),
        "A4": count_meta_talk(body),
        "A5": len(pairs),
        "A7": excess_hedges(body, len(items)),
        "A8": count_long_sentences(items),
        "A9": int(overflow is not None),
        "A10": len(english_words(body)),
        "A11": count_placeholders(body),
        "A14": count_past_action_claims(items),
        "A15": len(fact_errors),
        "A16": count_house_sign_aspect_words(body),
        **{rule: count_safety(rule, body) for rule in SAFETY_RULE_IDS},
        "H1": len(hidden),
    }
    keys: dict[str, set[str]] = {rule: set() for rule in counts}
    keys["H1"] = hidden
    keys["A9"] = {overflow} if overflow is not None else set()
    keys["A15"] = {sentence_key(sentence) for sentence in fact_errors}
    for sentence in items:
        for rule, matches in _SENTENCE_RULES.items():
            if matches(sentence):
                keys[rule].add(sentence_key(sentence))
        # A3 and A7 are per reading: once a reading is over its allowance, every sentence that
        # carries a metaphor or a hedge is part of the violation.
        if counts["A3"] and ENGINE_METAPHORS.search(sentence):
            keys["A3"].add(sentence_key(sentence))
        if counts["A7"] and HEDGES.search(sentence):
            keys["A7"].add(sentence_key(sentence))
    keys["A5"] = {_pair_key(first, second) for first, second in pairs}
    for rule in SAFETY_RULES:
        keys[rule] = set(safety_keys(rule, body))
    return counts, {rule: frozenset(found) for rule, found in keys.items()}


def lint_document(document: ClarityDocument) -> dict[str, int]:
    """Per-reading counts for every rule except A6 and A13, which need the whole surface,
    including the hard-zero rules."""

    return _document_findings(document)[0]


def lint_document_keys(document: ClarityDocument) -> dict[str, frozenset[str]]:
    """Per-reading violation keys (short hashes of normalised sentences or sentence pairs)."""

    return _document_findings(document)[1]


def shared_sentences(documents: Iterable[ClarityDocument]) -> tuple[str, ...]:
    """A6. Sentences found in more than 20% of a surface's readings (disclaimers are not body
    text, so they never reach this rule)."""

    frequency: Counter[str] = Counter()
    total = 0
    for document in documents:
        total += 1
        frequency.update(
            {
                _sentence_key(sentence)
                for sentence in a6_sentences(normalize_document(document))
                if syllables(sentence) >= SHARED_SENTENCE_MIN_SYLLABLES
            }
        )
    limit = SHARED_SENTENCE_SHARE * total
    return tuple(sorted(key for key, seen in frequency.items() if seen > limit))


def lint_surface(
    surface: str,
    documents: Iterable[ClarityDocument],
    *,
    days: Iterable[DailyDay] = (),
) -> SurfaceReport:
    """Every rule over one surface; ``days`` are the 30-day Daily runs A13 reads."""

    raw = tuple(document for document in documents if document.surface == surface)
    docs = tuple(normalize_document(document) for document in raw)
    totals: Counter[str] = Counter()
    flagged: Counter[str] = Counter()
    keys: dict[str, set[str]] = {rule: set() for rule in (*RULES, *HARD_ZERO_RULES)}
    for document in raw:
        counts, found = _document_findings(document)
        for rule, value in counts.items():
            totals[rule] += value
            flagged[rule] += value > 0
            keys[rule] |= found[rule]
    shared = shared_sentences(docs)
    totals["A6"] = len(shared)
    keys["A6"] = {_digest(key) for key in shared}
    flagged["A6"] = sum(
        any(_sentence_key(sentence) in shared for sentence in a6_sentences(document))
        for document in docs
    )
    totals["A13"], found_days = daily_follow_findings(days)
    keys["A13"] = set(found_days)
    return SurfaceReport(
        surface=surface,
        samples=len(docs),
        variants=dict(Counter(document.variant for document in docs)),
        rules={rule: totals.get(rule, 0) for rule in RULES},
        readings_flagged={rule: flagged.get(rule, 0) for rule in RULES},
        keys={rule: tuple(sorted(keys[rule])) for rule in (*RULES, *HARD_ZERO_RULES)},
        hard_zero={rule: totals.get(rule, 0) for rule in HARD_ZERO_RULES},
    )


def hard_zero_violations(
    current: Mapping[str, SurfaceReport], exceptions: Iterable[RatchetException] = ()
) -> tuple[str, ...]:
    """Class-A safety and hidden characters: every hit fails, on every surface, unless its exact
    sentence key is listed for that rule and surface in an approved exception."""

    tolerated: dict[tuple[str, str], set[str]] = {}
    for entry in exceptions:
        if entry.rule in HARD_ZERO_RULES:
            tolerated.setdefault((entry.surface, entry.rule), set()).update(entry.keys)
    problems: list[str] = []
    for surface, report in sorted(current.items()):
        for rule, name in HARD_ZERO_RULES.items():
            found = set(report.keys.get(rule, ()))
            if report.hard_zero.get(rule, 0) and not found:
                found = {"(no key)"}
            new_keys = sorted(found - tolerated.get((surface, rule), set()))
            if new_keys:
                problems.append(
                    f"{surface}: {rule} {name} is a hard zero: {len(new_keys)} sentence(s) "
                    f"({_preview(new_keys)})"
                )
    return tuple(problems)


def ratchet_regressions(
    current: Mapping[str, SurfaceReport],
    baseline: Mapping[str, Any],
    *,
    minimum_samples: Mapping[str, int],
) -> tuple[str, ...]:
    """Problems that block a release: a count above baseline, a violating sentence the baseline
    does not know (gap register GT-3: a fix elsewhere cannot hide it), or lost coverage.

    A rule or surface missing from the baseline has a baseline of 0 and no keys, so new rules
    start as hard blocks. Counts below baseline never fail; lock them in with
    ``--update-baseline``.
    """

    problems: list[str] = []
    surfaces: Mapping[str, Any] = baseline.get("surfaces", {})
    for surface in sorted(set(surfaces) | set(minimum_samples)):
        report = current.get(surface)
        expected: Mapping[str, Any] = surfaces.get(surface, {})
        if report is None:
            problems.append(f"{surface}: surface is no longer reviewed")
            continue
        floor = max(int(expected.get("samples", 0)), minimum_samples.get(surface, 0))
        if report.samples < floor:
            problems.append(f"{surface}: {report.samples} samples, needs at least {floor}")
        for variant, count in dict(expected.get("variants", {})).items():
            if report.variants.get(variant, 0) < int(count):
                problems.append(
                    f"{surface}: variant {variant} has {report.variants.get(variant, 0)} "
                    f"samples, baseline {count}"
                )
    for surface, report in sorted(current.items()):
        expected_surface: Mapping[str, Any] = surfaces.get(surface, {})
        expected_rules: Mapping[str, Any] = expected_surface.get("rules", {})
        expected_keys: Mapping[str, Any] = expected_surface.get("keys", {})
        for rule, value in report.rules.items():
            allowed = int(expected_rules.get(rule, 0))
            if value > allowed:
                problems.append(
                    f"{surface}: {rule} {RULES[rule]} rose to {value} (baseline {allowed})"
                )
            new_keys = sorted(set(report.keys.get(rule, ())) - set(expected_keys.get(rule, ())))
            if new_keys:
                problems.append(
                    f"{surface}: {rule} {RULES[rule]}: {len(new_keys)} new violating "
                    f"sentence(s) not in the baseline ({_preview(new_keys)})"
                )
    return tuple(problems)


def _preview(keys: Sequence[str], limit: int = 5) -> str:
    return ", ".join(keys[:limit]) + (f", +{len(keys) - limit} more" if len(keys) > limit else "")


def baseline_document(reports: Mapping[str, SurfaceReport]) -> dict[str, Any]:
    return {
        "spec": "docs/research/2026-11-01-content-clarity-gate.md#lớp-a",
        "note": (
            "Counts only go down and no new violating sentence may appear; the PR is compared "
            "with this file on its base branch. Rewrite with `python -m "
            "scripts.review_content_release --update-baseline` after an intended change; a "
            "rise needs an owner-approved entry in content_clarity_exceptions.json. Keys are "
            "short hashes of normalised sentences, never prose."
        ),
        "surfaces": {surface: reports[surface].as_baseline() for surface in sorted(reports)},
    }


def dump_baseline(document: Mapping[str, Any]) -> str:
    """JSON with one line per key list, so the file stays small and diffs stay readable."""

    compact = copy.deepcopy(dict(document))
    placeholders: dict[str, str] = {}
    for surface, entry in compact.get("surfaces", {}).items():
        for rule, keys in entry.get("keys", {}).items():
            token = f"@@keys:{surface}:{rule}@@"
            placeholders[json.dumps(token)] = json.dumps(list(keys), separators=(",", ":"))
            entry["keys"][rule] = token
    text = json.dumps(compact, ensure_ascii=False, indent=2)
    for token, value in placeholders.items():
        text = text.replace(token, value)
    return text + "\n"


@dataclass(frozen=True)
class RatchetException:
    """An owner-approved rise for one rule on one surface (``content_clarity_exceptions.json``).

    For a ratcheted rule the PR's own baseline is used for that rule and surface. ``keys`` is
    only used by hard-zero rules, which accept nothing but the listed sentence keys.
    """

    rule: str
    surface: str
    reason: str
    approver: str
    keys: tuple[str, ...] = ()


def parse_exceptions(
    document: Mapping[str, Any], *, surfaces: Iterable[str]
) -> tuple[tuple[RatchetException, ...], tuple[str, ...]]:
    known_surfaces = set(surfaces)
    entries: list[RatchetException] = []
    problems: list[str] = []
    for index, raw in enumerate(document.get("exceptions", ())):
        where = f"exceptions[{index}]"
        if not isinstance(raw, Mapping):
            problems.append(f"{where}: must be an object")
            continue
        fields = {name: str(raw.get(name, "")).strip() for name in _EXCEPTION_FIELDS}
        missing = [name for name, value in fields.items() if not value]
        if missing:
            problems.append(f"{where}: missing {', '.join(missing)}")
            continue
        if fields["rule"] not in RULES and fields["rule"] not in HARD_ZERO_RULES:
            problems.append(f"{where}: unknown rule {fields['rule']}")
            continue
        if fields["surface"] not in known_surfaces:
            problems.append(f"{where}: unknown surface {fields['surface']}")
            continue
        keys = tuple(str(key) for key in raw.get("keys", ()))
        if fields["rule"] in HARD_ZERO_RULES and not keys:
            problems.append(f"{where}: a hard-zero rule needs the exact sentence keys")
            continue
        entries.append(RatchetException(keys=keys, **fields))
    return tuple(entries), tuple(problems)


_EXCEPTION_FIELDS = ("rule", "surface", "reason", "approver")


def _ratchet_exceptions(exceptions: Iterable[RatchetException]) -> set[tuple[str, str]]:
    return {(entry.surface, entry.rule) for entry in exceptions if entry.rule in RULES}


def baseline_raises(
    base: Mapping[str, Any],
    head: Mapping[str, Any],
    exceptions: Iterable[RatchetException] = (),
) -> tuple[str, ...]:
    """GT-2. A PR may not raise its own baseline: a higher count or a new key than the base
    branch's file fails unless an owner-approved exception names that rule and surface."""

    allowed = _ratchet_exceptions(exceptions)
    base_surfaces: Mapping[str, Any] = base.get("surfaces", {})
    problems: list[str] = []
    for surface, entry in sorted(dict(head.get("surfaces", {})).items()):
        before: Mapping[str, Any] = base_surfaces.get(surface, {})
        for rule in RULES:
            if (surface, rule) in allowed:
                continue
            old = int(before.get("rules", {}).get(rule, 0))
            new = int(entry.get("rules", {}).get(rule, 0))
            if new > old:
                problems.append(
                    f"{surface}: baseline file raises {rule} from {old} to {new} "
                    "without an exception"
                )
            added = sorted(
                set(entry.get("keys", {}).get(rule, ())) - set(before.get("keys", {}).get(rule, ()))
            )
            if added:
                problems.append(
                    f"{surface}: baseline file adds {len(added)} {rule} key(s) "
                    f"without an exception ({_preview(added)})"
                )
    return tuple(problems)


def effective_baseline(
    base: Mapping[str, Any],
    head: Mapping[str, Any],
    exceptions: Iterable[RatchetException] = (),
) -> dict[str, Any]:
    """The base branch's baseline, except for excepted rule/surface pairs, which use the PR's."""

    merged: dict[str, Any] = copy.deepcopy(dict(base))
    surfaces: dict[str, Any] = merged.setdefault("surfaces", {})
    head_surfaces: Mapping[str, Any] = head.get("surfaces", {})
    for surface, rule in sorted(_ratchet_exceptions(exceptions)):
        source: Mapping[str, Any] = head_surfaces.get(surface, {})
        target = surfaces.setdefault(
            surface,
            {
                "samples": source.get("samples", 0),
                "variants": dict(source.get("variants", {})),
            },
        )
        target.setdefault("rules", {})[rule] = int(source.get("rules", {}).get(rule, 0))
        target.setdefault("keys", {})[rule] = list(source.get("keys", {}).get(rule, ()))
    return merged
