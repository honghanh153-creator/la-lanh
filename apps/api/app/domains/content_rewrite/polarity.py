"""Shared polarity tripwire for rewrite merge gates (Tarot, Radar)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

NEGATION = re.compile(r"\b(?:khong can|khong nen|khong muon|chang can|dung|bo qua)\b")


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


def negates_source_claim(source: str, rewritten: str, tokens: Callable[[str], set[str]]) -> bool:
    """Conservative polarity tripwire, not a semantic-entailment proof.

    Reject a new negated clause sharing anchors with a source assertion. Preserve
    existing cautionary negations. Uncertain paraphrases fall back to the local reading.
    """
    source_clauses = [clause for clause in re.split(r"[.!?;:]", source) if clause.strip()]
    positive = [tokens(c) for c in source_clauses if not NEGATION.search(fold(c))]
    negative = [tokens(c) for c in source_clauses if NEGATION.search(fold(c))]
    for clause in re.split(r"[.!?;:]", rewritten):
        if not NEGATION.search(fold(clause)):
            continue
        anchors_found = tokens(clause)
        if any(len(anchors_found & anchors) >= 2 for anchors in positive) and not any(
            len(anchors_found & anchors) >= 2 for anchors in negative
        ):
            return True
    return False
