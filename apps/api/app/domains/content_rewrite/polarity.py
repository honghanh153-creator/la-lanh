"""Shared polarity tripwire for rewrite merge gates (Tarot, Radar)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

NEGATION = re.compile(r"\b(?:khong can|khong nen|khong muon|chang can|dung|bo qua)\b")

# Folded negation markers and common connectives. Sharing only these with a source caution is
# not shared claim content, so they never earn the caution exemption.
NON_CLAIM_TOKENS = frozenset(
    {
        "khong", "chang", "dung", "muon", "cung", "nhung", "nhieu", "nhat", "rang", "hoac",
        "thay", "nhau", "phai", "luon", "khac", "them",
    }
)  # fmt: skip


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


def negates_source_claim(
    source: str,
    rewritten: str,
    tokens: Callable[[str], set[str]],
    *,
    caution_tokens: Callable[[str], set[str]] | None = None,
) -> bool:
    """Conservative polarity tripwire, not a semantic-entailment proof.

    Reject a new negated clause sharing anchors with a source assertion. Preserve
    existing cautionary negations. Uncertain paraphrases fall back to the local reading.

    Without `caution_tokens` (Tarot) a clause sharing two anchors with any source caution is
    preserved. With `caution_tokens` (Radar) the exemption is bound to the negated assertion:
    see `_restates_caution`.
    """
    source_clauses = [clause for clause in re.split(r"[.!?;:]", source) if clause.strip()]
    positive_clauses = [c for c in source_clauses if not NEGATION.search(fold(c))]
    caution_clauses = [c for c in source_clauses if NEGATION.search(fold(c))]
    positive = [tokens(c) for c in positive_clauses]
    negative = [tokens(c) for c in caution_clauses]
    for clause in re.split(r"[.!?;:]", rewritten):
        if not NEGATION.search(fold(clause)):
            continue
        anchors_found = tokens(clause)
        if not any(len(anchors_found & anchors) >= 2 for anchors in positive):
            continue
        if caution_tokens is None:
            if not any(len(anchors_found & anchors) >= 2 for anchors in negative):
                return True
        elif not _restates_caution(clause, positive_clauses, caution_clauses, caution_tokens):
            return True
    return False


def _restates_caution(
    clause: str,
    positive_clauses: list[str],
    caution_clauses: list[str],
    claim_tokens: Callable[[str], set[str]],
) -> bool:
    """Every negated assertion in the clause restates a source caution, and only that.

    The negated assertion is the comma segment holding the negation marker, so an introduction
    before a comma cannot lend it the caution's words. A segment with fewer than two claim
    tokens ("không cần cố quá nhiều") names its subject elsewhere, so the whole clause is used.
    The scope must share two claim tokens with one caution and hold no claim token that only a
    positive source clause has: positive claim content in a negated assertion is a reversal.
    """
    cautions = [claim_tokens(c) for c in caution_clauses]
    caution_union = set().union(*cautions)
    positive_only = set().union(*(claim_tokens(c) for c in positive_clauses)) - caution_union
    whole = claim_tokens(clause)
    segments = [seg for seg in clause.split(",") if NEGATION.search(fold(seg))] or [clause]
    for segment in segments:
        scope = claim_tokens(segment)
        if len(scope) < 2:
            scope = whole
        if scope & positive_only or not any(len(scope & caution) >= 2 for caution in cautions):
            return False
    return True
