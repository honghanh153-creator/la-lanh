"""Per-sentence gates run at build time on every composed combination (spec §3 step 3).

They reuse the text-level rules of the live reading gates, so a sentence in an allowlist has
passed the same anti-influence, editorial, privacy and banned-phrase rules as served copy,
plus the part-specific meaning rules. Whole-reading ``evaluate_candidate`` stays the runtime
safety net (spec §5); it is not run here because it needs a plan and a full candidate.
"""

from __future__ import annotations

import unicodedata

from app.domains.grammar.models import Frame, Surface
from app.domains.readings.companion import companion_issue_entry, nudge_failures
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.gates import (
    ANTI_INFLUENCE_GATE_VERSION,
    EDITORIAL_GATE_VERSION,
    MEANING_GATE_VERSION,
    PRIVACY_GATE_VERSION,
    anti_influence_failures,
    editorial_failures,
    has_observable_action,
    privacy_failures,
    scene_contains_advice,
)
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS

GRAMMAR_GATE_VERSION = "grammar-sentence-gate-v1"
GATE_VERSION = "+".join(
    (
        GRAMMAR_GATE_VERSION,
        ANTI_INFLUENCE_GATE_VERSION,
        EDITORIAL_GATE_VERSION,
        MEANING_GATE_VERSION,
        PRIVACY_GATE_VERSION,
    )
)
_ISSUES = {issue.key: issue for issue in DAILY_ISSUES}


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def sentence_failures(frame: Frame, sentence: str) -> list[str]:
    """Reasons ``sentence`` may not enter ``frame``'s allowlist (empty when it may)."""

    failures = [code.value for code in anti_influence_failures(sentence)]
    failures += [code.value for code in editorial_failures((sentence,))]
    failures += [code.value for code in privacy_failures(sentence)]
    folded = _fold(sentence)
    if any(fragment in folded for fragment in BANNED_CORE_FRAGMENTS):
        failures.append("banned_core_fragment")
    if frame.part in {"headline", "scene"} and scene_contains_advice(sentence):
        failures.append("scene_contains_advice")
    if frame.part == "advice":
        if not has_observable_action(sentence):
            failures.append("action_not_observable")
        issue = _ISSUES.get(frame.meaning_key) if frame.surface is Surface.DAILY else None
        if issue is not None and not any(_fold(a) in folded for a in issue.action_anchors):
            failures.append("meaning_anchor_missing")
    if frame.part == "companion":
        failures += nudge_failures(
            sentence, companion_issue_entry(f"psychology:{frame.meaning_key}")
        )
    return failures
