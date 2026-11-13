"""#176 item 1: the composer's spacing and trailing-punctuation rules are linear and unchanged.

Each legacy pattern is kept here only as the oracle. Text is synthetic.
"""

from __future__ import annotations

import random
import re
import time
import unicodedata

import pytest

from app.domains.grammar.composer import (
    _SPACE_BEFORE_PUNCT,
    _TRAILING,
    dedupe_key,
    normalize,
    value_identity,
)

LEGACY_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.!?;:…])")
LEGACY_TRAILING = re.compile(r"[\s.!?…,;:]+$")
LIMIT_SECONDS = 0.25

CASES = [
    "",
    " ",
    "Hôm nay",
    "Hôm nay , bạn thấy sao ?",
    "a  ,b",
    "a \t\n, b",
    " ,đầu câu",
    "a ,,b . . .",
    "Câu kết thúc…",
    "Câu kết thúc ... ",
    "nghỉ một chút ; rồi tiếp : nhé !",
    "a\u00a0,b\u2003.",
    "a\x1c,b",
    "chữ\n",
    "chỉ có chữ",
    " " * 40,
    "." * 40,
    " ." * 20 + "x",
    "Ừ, ổn mà.   ",
]


@pytest.mark.parametrize("text", CASES)
def test_space_before_punct_keeps_the_legacy_result(text: str) -> None:
    assert _SPACE_BEFORE_PUNCT.sub(r"\1", text) == LEGACY_SPACE_BEFORE_PUNCT.sub(r"\1", text)


@pytest.mark.parametrize("text", CASES)
def test_trailing_keeps_the_legacy_result(text: str) -> None:
    assert _TRAILING.sub("", text) == LEGACY_TRAILING.sub("", text)


def _legacy_normalize(text: str) -> str:
    text = " ".join(unicodedata.normalize("NFC", text).split())
    text = LEGACY_SPACE_BEFORE_PUNCT.sub(r"\1", text)
    return text[:1].upper() + text[1:]


def _legacy_dedupe_key(text: str) -> str:
    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return LEGACY_TRAILING.sub("", folded)


@pytest.mark.parametrize("text", CASES)
def test_public_helpers_keep_the_legacy_result(text: str) -> None:
    assert normalize(text) == _legacy_normalize(text)
    assert dedupe_key(text) == _legacy_dedupe_key(text)
    assert value_identity(text) == _legacy_dedupe_key(_legacy_normalize(text))


def test_patterns_agree_with_the_legacy_patterns_on_random_text() -> None:
    rng = random.Random(20261103)  # noqa: S311 - seeded fuzz, not a secret
    alphabet = " \t\n\u00a0\u2003,.!?;:…aĐư"
    for _ in range(20_000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))
        assert _SPACE_BEFORE_PUNCT.sub(r"\1", text) == LEGACY_SPACE_BEFORE_PUNCT.sub(r"\1", text)
        assert _TRAILING.sub("", text) == LEGACY_TRAILING.sub("", text)


@pytest.mark.parametrize("text", [" " * 50_000 + "a", "\u2003" * 50_000 + "đ", "a " * 25_000 + "b"])
def test_space_before_punct_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    assert time.perf_counter() - started < LIMIT_SECONDS


@pytest.mark.parametrize("text", ["." * 50_000 + "a", "…" * 50_000 + "ư", ". " * 25_000 + "a"])
def test_trailing_is_fast_on_long_adversarial_text(text: str) -> None:
    started = time.perf_counter()
    _TRAILING.sub("", text)
    assert time.perf_counter() - started < LIMIT_SECONDS
