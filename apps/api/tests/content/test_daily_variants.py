"""Daily v2 variants: pending ones never join the rotated pool (owner decision 06.11.2026)."""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import (
    copy_digest,
    load_registry,
    parse_registry,
    registry_problems,
)
from app.domains.content_rewrite.gates import _ACTION_VERBS, _fold
from app.domains.readings import daily_psychology
from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    MAX_SENTENCE_SYLLABLES,
    count_jargon,
    count_meta_talk,
    count_placeholders,
    count_safety,
    english_words,
    is_past_event_claim,
    sentences,
    syllables,
)
from app.domains.readings.daily_rotation import axis_slot

PARTS = {"headline": "headlines", "scene": "scenes", "action": "advice"}
ID = re.compile(r"^daily\.(?P<part>[a-z]+)\.(?P<issue>[a-z-]+)\.\d{2}$")
ISSUES = {issue.key: issue for issue in daily_psychology.DAILY_ISSUES}
REGISTRY = load_registry()
DAILY = {key: entry for key, entry in REGISTRY.items() if key.startswith("daily.")}
SAFETY = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))


def _use(monkeypatch: pytest.MonkeyPatch, *entries: dict[str, Any]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": list(entries)})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _entry(entry_id: str, text: str, *, approved: bool) -> dict[str, Any]:
    entry: dict[str, Any] = {"id": entry_id, "category": "reading", "text": text}
    if approved:
        return {
            **entry,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-07",
            "digest": copy_digest(text),
        }
    return {**entry, "status": "pending"}


def test_registry_daily_entries_are_well_formed() -> None:
    assert DAILY
    assert registry_problems(DAILY) == []
    for key, entry in DAILY.items():
        match = ID.match(key)
        assert match, key
        assert match["part"] in PARTS and match["issue"] in ISSUES, key
        assert entry.category == "reading"
        if entry.status == "approved":
            assert entry.digest == copy_digest(entry.text)


@pytest.mark.parametrize("key", sorted(DAILY))
def test_variant_passes_clarity_hard_zero(key: str) -> None:
    text = DAILY[key].text
    assert len(sentences(text)) == 1
    assert syllables(text) <= MAX_SENTENCE_SYLLABLES
    assert not is_past_event_claim(text)
    assert not any(count_safety(rule, text) for rule in SAFETY)
    assert count_jargon(text) == count_meta_talk(text) == count_placeholders(text) == 0
    assert english_words(text) == ()
    if key.startswith("daily.scene."):
        # The arena lead ("Với người kia, khi …") needs every scene to open with "Khi".
        assert text.startswith("Khi ")
        longest = max(syllables(scene) for issue in ISSUES.values() for scene in issue.scenes)
        assert syllables(text) <= longest


def test_variants_are_new_wording() -> None:
    for key, entry in DAILY.items():
        match = ID.match(key)
        assert match
        issue = ISSUES[match["issue"]]
        if entry.status == "pending":
            assert entry.text not in getattr(issue, PARTS[match["part"]]), key
    texts = [entry.text for entry in DAILY.values()]
    assert len(texts) == len(set(texts))


@pytest.mark.parametrize("part", sorted(PARTS))
def test_pending_variant_never_joins_the_pool(monkeypatch: pytest.MonkeyPatch, part: str) -> None:
    issue = ISSUES["missing-context"]
    text = "Câu thử nghiệm đang chờ duyệt."
    _use(monkeypatch, _entry(f"daily.{part}.missing-context.01", text, approved=False))
    expanded = daily_psychology._expand_daily_issue(issue)
    assert text not in getattr(expanded, PARTS[part])
    assert expanded == issue


@pytest.mark.parametrize("part", sorted(PARTS))
def test_approved_variant_joins_the_rotation(monkeypatch: pytest.MonkeyPatch, part: str) -> None:
    issue = ISSUES["missing-context"]
    text = "Câu thử nghiệm đã được duyệt."
    _use(
        monkeypatch,
        _entry(f"daily.{part}.missing-context.01", text, approved=True),
        _entry(f"daily.{part}.missing-context.02", "Câu khác chưa duyệt.", approved=False),
        _entry(f"daily.{part}.changed-plan.01", "Câu của tình huống khác.", approved=True),
    )
    pool = getattr(daily_psychology._expand_daily_issue(issue), PARTS[part])
    assert pool[-1] == text
    assert len(pool) == len(getattr(issue, PARTS[part])) + 1
    assert "Câu khác chưa duyệt." not in pool and "Câu của tình huống khác." not in pool
    served = {pool[axis_slot("seed-a", part, len(pool), day)] for day in range(len(pool))}
    assert text in served


def test_real_registry_serves_no_pending_daily_text() -> None:
    pending = {entry.text for entry in DAILY.values() if entry.status != "approved"}
    for issue in daily_psychology.DAILY_ISSUES:
        for field in PARTS.values():
            assert not pending & set(getattr(issue, field))


@pytest.mark.parametrize("key", sorted(k for k in DAILY if k.startswith("daily.action.")))
def test_action_variant_passes_card_gates(key: str) -> None:
    # Same verb and anchor rules meaning_gate applies to an assembled card (#288).
    match = ID.match(key)
    assert match
    folded = _fold(DAILY[key].text)
    assert any(folded.startswith(_fold(verb)) for verb in _ACTION_VERBS), key
    assert any(_fold(a) in folded for a in ISSUES[match["issue"]].action_anchors), key


@pytest.mark.parametrize("key", sorted(k for k in DAILY if k.startswith("daily.scene.")))
def test_scene_variant_carries_its_issue_anchor(key: str) -> None:
    # meaning_gate rejects a card whose scene drifts from its issue's scene anchors.
    match = ID.match(key)
    assert match
    folded = _fold(DAILY[key].text)
    assert any(_fold(a) in folded for a in ISSUES[match["issue"]].scene_anchors), key
