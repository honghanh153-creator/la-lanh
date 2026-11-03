"""#176 item 1 remainder: the offline measurement scripts drop trailing punctuation in linear time.

The legacy pattern is kept here only as the oracle. Text is synthetic.
"""

from __future__ import annotations

import random
import re
import time

import pytest

from scripts import audit_tarot_knowledge, variety_baseline

LEGACY_TRAILING = re.compile(r"[\s.!?…,;:]+$")
LIMIT_SECONDS = 0.25
PATTERNS = {
    "variety_baseline": variety_baseline._TRAILING,
    "audit_tarot_knowledge": audit_tarot_knowledge._TRAILING,
}

CASES = [
    "",
    "   ",
    "Hỏi lại một câu thôi.",
    "Đọc hết đã nha ... !",
    "Có lúc chậm lại; vẫn ổn:",
    "Câu này… còn tiếp",
    "Thử\u00a0khoảng\u2003trắng lạ .",
    "!?" * 20,
    ". " * 20 + "kết",
]


@pytest.mark.parametrize("name", PATTERNS)
@pytest.mark.parametrize("text", CASES)
def test_trailing_keeps_the_legacy_result(name: str, text: str) -> None:
    assert PATTERNS[name].sub("", text) == LEGACY_TRAILING.sub("", text)


@pytest.mark.parametrize("name", PATTERNS)
def test_trailing_agrees_with_the_legacy_pattern_on_random_text(name: str) -> None:
    rng = random.Random(20261103)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = " \t\n\u00a0.!?…,;:aợ"
    for _ in range(20_000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
        assert PATTERNS[name].sub("", text) == LEGACY_TRAILING.sub("", text)


@pytest.mark.parametrize(
    "text",
    ["." * 50_000 + "a", "…" * 50_000 + "ợ", "!" * 50_000],
    ids=["dots-then-letter", "ellipses-then-letter", "only-bangs"],
)
def test_normalizers_are_fast_on_long_adversarial_text(text: str) -> None:
    for normalize in (variety_baseline.normalize, audit_tarot_knowledge._normalize):
        started = time.perf_counter()
        normalize(text)
        assert time.perf_counter() - started < LIMIT_SECONDS
