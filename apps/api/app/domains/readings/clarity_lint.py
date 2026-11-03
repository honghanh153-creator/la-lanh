"""Plain-language lint for rendered readings (layer A of the content clarity gate).

Spec: ``docs/research/2026-11-01-content-clarity-gate.md`` section 3, "Lớp A". Every rule reads
only the text a user sees in the body of a reading (no evidence, receipts, factor codes or UI
labels) and returns a count, so a release review can keep a per-surface baseline and fail when a
count rises (ratchet). Thresholds are provisional, like the spec says.

Text is normalised before any rule runs (NFC, no-break spaces as spaces, full-width ASCII as
ASCII, zero-width and bidi controls removed), so look-alike characters cannot hide a match.

Out of scope here (reported as TODO by the release review): A9 first-screen length, A13 Daily
follows the day, A15 facts match the engine.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

RULES: dict[str, str] = {
    "A1": "thuật ngữ đứng trơ",
    "A2": "nhãn tự đặt",
    "A3": "ẩn dụ máy (> 2/bài)",
    "A4": "nói về bài/app",
    "A5": "cặp câu gần trùng",
    "A6": "câu lặp > 20% số bài",
    "A7": "rào đón (> 0.3/câu)",
    "A8": "câu > 25 âm tiết",
    "A10": "tiếng Anh",
    "A11": "placeholder",
    "A14": "khẳng định việc đã xảy ra",
    "A16": "chữ nhà/cung/chủ tinh/góc",
}
TODO_RULES: dict[str, str] = {
    "A1+": "thuật ngữ được giải thích ở câu đó hoặc câu sau thì không tính",
    "A7+": "câu kiểu disclaimer trong thân bài",
    "A9": "độ dài màn đầu",
    "A13": "Daily bám đúng ngày (30 ngày)",
    "A15": "dữ kiện trong câu chữ khớp engine",
}

ENGINE_METAPHOR_ALLOWANCE = 2  # A3: at most two per reading
HEDGES_PER_SENTENCE = 0.3  # A7
MAX_SENTENCE_SYLLABLES = 25  # A8
NEAR_DUPLICATE_MIN_SYLLABLES = 6  # A5
NEAR_DUPLICATE_OVERLAP = 0.5  # A5: shared bigrams over the smaller sentence's bigrams
SHARED_SENTENCE_SHARE = 0.2  # A6
SHARED_SENTENCE_MIN_SYLLABLES = 4  # A6 ignores very short fragments


def _terms(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)


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
# by the hard-zero rule H1; look-alike spaces become a plain space; full-width ASCII becomes ASCII.
_ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff\u00ad\u180e"
_BIDI_CONTROLS = "\u200e\u200f\u061c\u202a-\u202e\u2066-\u2069"
HIDDEN_CHARACTERS = re.compile(f"[{_ZERO_WIDTH}{_BIDI_CONTROLS}]")
_LOOKALIKE_SPACES = re.compile("[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")
_FULL_WIDTH_ASCII = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}

# Closing quotes (straight, curly, guillemet) or a bracket after the end mark.
_SENTENCE_SPLIT = re.compile("(?<=[.!?\u2026])[\"\u201d'\u2019\u00bb)]*\\s+|\n+")
# Quotes (straight, curly, guillemets), brackets, dashes (- en em) and the middle dot.
_EDGE_PUNCTUATION = " \t.!?\u2026\"\u201c\u201d'\u2018\u2019\u00ab\u00bb()[]:;,-\u2013\u2014\u00b7"


@dataclass(frozen=True)
class ClarityDocument:
    """One rendered reading as a user sees it: body text by section, nothing else."""

    surface: str
    sample_id: str
    sections: tuple[tuple[str, str], ...]
    variant: str = "default"


@dataclass(frozen=True)
class SurfaceReport:
    surface: str
    samples: int
    variants: dict[str, int]
    rules: dict[str, int]
    readings_flagged: dict[str, int] = field(default_factory=dict)

    def as_baseline(self) -> dict[str, Any]:
        return {
            "samples": self.samples,
            "variants": dict(sorted(self.variants.items())),
            "rules": {rule: self.rules.get(rule, 0) for rule in RULES},
        }


def normalize_text(text: str) -> str:
    """NFC, plain spaces, ASCII for full-width letters, no zero-width or bidi controls."""

    text = HIDDEN_CHARACTERS.sub("", text.translate(_FULL_WIDTH_ASCII))
    return unicodedata.normalize("NFC", _LOOKALIKE_SPACES.sub(" ", text))


def normalize_document(document: ClarityDocument) -> ClarityDocument:
    return ClarityDocument(
        surface=document.surface,
        sample_id=document.sample_id,
        sections=tuple((name, normalize_text(text)) for name, text in document.sections),
        variant=document.variant,
    )


def sentences(text: str) -> tuple[str, ...]:
    return tuple(
        part.strip() for part in _SENTENCE_SPLIT.split(text) if part.strip(_EDGE_PUNCTUATION)
    )


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


def near_duplicate_pairs(items: Iterable[str]) -> int:
    """A5. Pairs of sentences (>= 6 syllables) sharing >= 50% of the smaller one's bigrams."""

    grams = [
        _bigrams(sentence)
        for sentence in items
        if syllables(sentence) >= NEAR_DUPLICATE_MIN_SYLLABLES
    ]
    pairs = 0
    for index, first in enumerate(grams):
        for second in grams[index + 1 :]:
            if first and second:
                shared = len(first & second) / min(len(first), len(second))
                pairs += shared >= NEAR_DUPLICATE_OVERLAP
    return pairs


def excess_engine_metaphors(text: str) -> int:
    return max(0, count_engine_metaphors(text) - ENGINE_METAPHOR_ALLOWANCE)


def excess_hedges(text: str, sentence_count: int) -> int:
    allowed = math.floor(HEDGES_PER_SENTENCE * sentence_count + 1e-9)
    return max(0, count_hedges(text) - allowed)


def document_sentences(document: ClarityDocument) -> tuple[str, ...]:
    return tuple(sentence for _, text in document.sections for sentence in sentences(text))


def lint_document(document: ClarityDocument) -> dict[str, int]:
    """Per-reading counts for every rule except A6, which needs the whole surface."""

    document = normalize_document(document)
    body = "\n".join(text for _, text in document.sections)
    items = document_sentences(document)
    return {
        "A1": count_jargon(body),
        "A2": count_coined_labels(body),
        "A3": excess_engine_metaphors(body),
        "A4": count_meta_talk(body),
        "A5": near_duplicate_pairs(items),
        "A7": excess_hedges(body, len(items)),
        "A8": count_long_sentences(items),
        "A10": len(english_words(body)),
        "A11": count_placeholders(body),
        "A14": count_past_action_claims(items),
        "A16": count_house_sign_aspect_words(body),
    }


def _sentence_key(sentence: str) -> str:
    folded = " ".join(sentence.casefold().split()).strip(_EDGE_PUNCTUATION)
    return re.sub(r"\d+", "#", folded)


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
                for sentence in document_sentences(document)
                if syllables(sentence) >= SHARED_SENTENCE_MIN_SYLLABLES
            }
        )
    limit = SHARED_SENTENCE_SHARE * total
    return tuple(sorted(key for key, seen in frequency.items() if seen > limit))


def lint_surface(surface: str, documents: Iterable[ClarityDocument]) -> SurfaceReport:
    docs = tuple(
        normalize_document(document) for document in documents if document.surface == surface
    )
    totals: Counter[str] = Counter()
    flagged: Counter[str] = Counter()
    for document in docs:
        for rule, value in lint_document(document).items():
            totals[rule] += value
            flagged[rule] += value > 0
    shared = shared_sentences(docs)
    totals["A6"] = len(shared)
    flagged["A6"] = sum(
        any(_sentence_key(sentence) in shared for sentence in document_sentences(document))
        for document in docs
    )
    return SurfaceReport(
        surface=surface,
        samples=len(docs),
        variants=dict(Counter(document.variant for document in docs)),
        rules={rule: totals.get(rule, 0) for rule in RULES},
        readings_flagged={rule: flagged.get(rule, 0) for rule in RULES},
    )


def ratchet_regressions(
    current: Mapping[str, SurfaceReport],
    baseline: Mapping[str, Any],
    *,
    minimum_samples: Mapping[str, int],
) -> tuple[str, ...]:
    """Problems that block a release: a count above baseline, or lost coverage.

    A rule or surface missing from the baseline has a baseline of 0, so new rules start as hard
    blocks. Counts below baseline never fail; lock them in with ``--update-baseline``.
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
        expected_rules: Mapping[str, Any] = surfaces.get(surface, {}).get("rules", {})
        for rule, value in report.rules.items():
            allowed = int(expected_rules.get(rule, 0))
            if value > allowed:
                problems.append(
                    f"{surface}: {rule} {RULES[rule]} rose to {value} (baseline {allowed})"
                )
    return tuple(problems)


def baseline_document(reports: Mapping[str, SurfaceReport]) -> dict[str, Any]:
    return {
        "spec": "docs/research/2026-11-01-content-clarity-gate.md#lớp-a",
        "note": (
            "Counts only go down. Rewrite with `python -m scripts.review_content_release "
            "--update-baseline` after an intended change, and explain it in the PR."
        ),
        "surfaces": {surface: reports[surface].as_baseline() for surface in sorted(reports)},
    }
