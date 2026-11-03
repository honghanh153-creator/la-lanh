"""#176 item 1: the quote and e-mail checks of the reading gates are linear and unchanged.

Each legacy pattern is kept here only as the oracle. Text is synthetic.
"""

from __future__ import annotations

import random
import re
import time

import pytest

from app.domains.readings.gates import (
    _PRIVACY_EMAIL,
    _fold,
    _quoted_spans,
    _without_safe_examples,
    privacy_failures,
)
from app.domains.readings.models import GateFailureCode

LEGACY_QUOTE = re.compile('["\u201c\u2018\u00ab]([^"\u201d\u2019\u00bb]+)["\u201d\u2019\u00bb]')
LEGACY_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
LIMIT_SECONDS = 0.25


def _legacy_without_safe_examples(folded: str) -> str:
    pieces: list[str] = []
    cursor = 0
    for match in LEGACY_QUOTE.finditer(folded):
        prefix = folded[max(0, match.start() - 45) : match.start()]
        if re.search(r"(?:vi du|cum tu|cau can tranh|khong nen noi|tranh noi)\s*:?\s*$", prefix):
            pieces.append(folded[cursor : match.start()])
            cursor = match.end()
    pieces.append(folded[cursor:])
    return " ".join(pieces)


QUOTE_CASES = [
    "",
    "không có dấu ngoặc nào",
    '"a"',
    '""',
    '"""',
    '""a"',
    "\u201c\u201d",
    "\u201chôm nay\u201d",
    "\u201c\u201c\u201cnhiều mở\u201d",
    "\u00abmột\u00bb và \u2018hai\u2019",
    'ví dụ: "hãy làm ngay" thì nên tránh',
    'cụm từ "chắc chắn" và tránh nói \u201cđịnh mệnh\u201d nhé',
    "\u201c" * 40,
    '"' * 41,
    "mở \u201c mà không đóng",
    "\u201d\u2019\u00bb chỉ có dấu đóng",
]


@pytest.mark.parametrize("text", QUOTE_CASES)
def test_quoted_spans_match_the_legacy_regex(text: str) -> None:
    assert _quoted_spans(text) == [match.span() for match in LEGACY_QUOTE.finditer(text)]


@pytest.mark.parametrize("text", QUOTE_CASES)
def test_safe_example_removal_is_unchanged(text: str) -> None:
    assert _without_safe_examples(text) == _legacy_without_safe_examples(_fold(text))


def test_quoted_spans_agree_with_the_legacy_regex_on_random_text() -> None:
    rng = random.Random(20261103)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = 'a ạ"\u201c\u2018\u00ab\u201d\u2019\u00bbđ:'
    for _ in range(20_000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 30)))
        assert _quoted_spans(text) == [m.span() for m in LEGACY_QUOTE.finditer(text)], text


EMAIL_CASES = [
    "",
    "a@b.co",
    "hỏi về a@b.co nhé",
    "A.B+C@X-Y.VN",
    ".a@b.co",
    "+-+@a.bc",
    "%@a.bc",
    "x.@y.zz",
    "a_b@c.de",
    "_@c.de",
    "@b.co",
    "a@b.c",
    "a@b.cd1",
    "đ@ư.vn",
    "đa@b.co",
    "đ.a@b.co",
    "đ+@b.co",
    "\u212a@b.co",
    "\u017f.@b.co",
    "chưa có địa chỉ nào cả",
    "a+" * 20 + "@b.co",
]


@pytest.mark.parametrize("text", EMAIL_CASES)
def test_email_pattern_keeps_the_legacy_result(text: str) -> None:
    assert bool(_PRIVACY_EMAIL.search(text)) is bool(LEGACY_EMAIL.search(text))


def test_email_pattern_agrees_with_the_legacy_pattern_on_random_text() -> None:
    rng = random.Random(20261103)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = "aZ9_.%+-@ đK\u212a\u017f\u0131"
    for _ in range(20_000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
        assert bool(_PRIVACY_EMAIL.search(text)) is bool(LEGACY_EMAIL.search(text)), text


@pytest.mark.parametrize("text", ["liên hệ a.b@c.vn", "Gửi về A_B@C.COM nhé"])
def test_privacy_gate_still_refuses_an_email(text: str) -> None:
    assert privacy_failures(text) == [GateFailureCode.PRIVACY_PERSONAL_DATA]


@pytest.mark.parametrize("text", ["", "không có liên hệ nào", "@" * 40, "a+" * 40])
def test_privacy_gate_still_passes_text_without_an_email(text: str) -> None:
    assert privacy_failures(text) == []


@pytest.mark.parametrize(
    "text", ["a+" * 25_000, "a" * 50_000, "+" * 50_000, "a@" + "a." * 25_000, "_." * 25_000]
)
def test_privacy_gate_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    privacy_failures(text)
    assert time.perf_counter() - started < LIMIT_SECONDS


@pytest.mark.parametrize(
    "text", ["\u201c" * 50_000, '"' * 50_001, "\u00ab" + "a" * 50_000, "\u201ca" * 25_000]
)
def test_safe_example_removal_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    _without_safe_examples(text)
    assert time.perf_counter() - started < LIMIT_SECONDS
