"""#176 item 1: the Hợp gu sentence identity drops trailing punctuation in linear time.

The legacy pattern is kept here only as the oracle. Text is synthetic.
"""

from __future__ import annotations

import random
import re
import time
import unicodedata

import pytest

from app.domains.radar.readable import _TRAILING, normalize

LEGACY_TRAILING = re.compile(r"[\s.!?…,;:]+$")
LIMIT_SECONDS = 0.25

CASES = [
    "",
    "   ",
    "Hai bạn hợp nhau.",
    "Hai bạn hợp nhau ... !",
    "Có lúc lệch nhịp; vẫn ổn:",
    "Câu này… còn tiếp",
    "Thử\u00a0khoảng\u2003trắng lạ .",
    "!?" * 20,
    ". " * 20 + "kết",
    "ĐIỀU TRÔI CHẢY,",
]


@pytest.mark.parametrize("text", CASES)
def test_trailing_keeps_the_legacy_result(text: str) -> None:
    assert _TRAILING.sub("", text) == LEGACY_TRAILING.sub("", text)
    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    assert normalize(text) == LEGACY_TRAILING.sub("", folded)


def test_trailing_agrees_with_the_legacy_pattern_on_random_text() -> None:
    rng = random.Random(20261103)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = " \t\n\u00a0.!?…,;:aợ"
    for _ in range(20_000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
        assert _TRAILING.sub("", text) == LEGACY_TRAILING.sub("", text)


@pytest.mark.parametrize(
    "text", ["." * 50_000 + "a", "…" * 50_000 + "ợ", ", " * 25_000 + "a", "!" * 50_000]
)
def test_normalize_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    normalize(text)
    assert time.perf_counter() - started < LIMIT_SECONDS
