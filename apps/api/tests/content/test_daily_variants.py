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
from app.domains.content_rewrite.gates import (
    _ACTION_VERBS,
    _ASTRO_TERMS,
    _OPAQUE_FILLER,
    _SCENE_MARKERS,
    _fold,
    _words,
)
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
from app.domains.readings.daily_psychology import (
    _ARENA_LEADS,
    current_scene_lead,
    lead_scene,
    split_scene_lead,
)
from app.domains.readings.daily_rotation import axis_slot
from app.domains.readings.gates import scene_contains_advice
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS

PARTS = {"headline": "headlines", "scene": "scenes", "action": "advice"}
ID = re.compile(r"^daily\.(?P<part>[a-z]+)\.(?P<issue>[a-z-]+)\.\d{2}$")
# Bundles (owner 10.11): daily.bundle.<issue>.<nn>.<part>; each part gets the variant checks.
BUNDLE_ID = re.compile(r"^daily\.bundle\.(?P<issue>[a-z-]+)\.\d{2}\.(?P<part>[a-z]+)$")
ISSUES = {issue.key: issue for issue in daily_psychology.DAILY_ISSUES}
REGISTRY = load_registry()
DAILY = {key: entry for key, entry in REGISTRY.items() if key.startswith("daily.")}


def _match(key: str) -> re.Match[str] | None:
    return BUNDLE_ID.match(key) or ID.match(key)


def _part_keys(daily: dict[str, Any], part: str) -> list[str]:
    return sorted(k for k in daily if (m := _match(k)) is not None and m["part"] == part)


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


def _check_well_formed(daily: dict[str, Any]) -> None:
    assert registry_problems(daily) == []
    for key, entry in daily.items():
        match = _match(key)
        assert match, key
        assert match["part"] in PARTS and match["issue"] in ISSUES, key
        assert entry.category == "reading"
        if entry.status == "approved":
            assert entry.digest == copy_digest(entry.text)


def test_registry_daily_entries_are_well_formed() -> None:
    assert DAILY
    _check_well_formed(DAILY)


@pytest.mark.parametrize("key", sorted(DAILY))
def test_variant_passes_clarity_hard_zero(key: str) -> None:
    _check_clarity(key, DAILY[key].text)


def _check_clarity(key: str, text: str) -> None:
    assert len(sentences(text)) == 1
    assert syllables(text) <= MAX_SENTENCE_SYLLABLES
    assert not is_past_event_claim(text)
    assert not any(count_safety(rule, text) for rule in SAFETY)
    assert count_jargon(text) == count_meta_talk(text) == count_placeholders(text) == 0
    assert english_words(text) == ()
    match = _match(key)
    if match and match["part"] == "scene":
        longest = max(syllables(scene) for issue in ISSUES.values() for scene in issue.scenes)
        assert syllables(text) <= longest


def test_variants_are_new_wording() -> None:
    _check_new_wording(DAILY)


def _check_new_wording(daily: dict[str, Any]) -> None:
    for key, entry in daily.items():
        match = _match(key)
        assert match
        issue = ISSUES[match["issue"]]
        if entry.status == "pending":
            assert entry.text not in getattr(issue, PARTS[match["part"]]), key
    texts = [entry.text for entry in daily.values()]
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


@pytest.mark.parametrize("key", _part_keys(DAILY, "action"))
def test_action_variant_passes_card_gates(key: str) -> None:
    _check_action(key, DAILY[key].text)


def _check_action(key: str, text: str) -> None:
    # Same verb and anchor rules meaning_gate applies to an assembled card (#288).
    match = _match(key)
    assert match
    folded = _fold(text)
    assert any(folded.startswith(_fold(verb)) for verb in _ACTION_VERBS), key
    assert any(_fold(a) in folded for a in ISSUES[match["issue"]].action_anchors), key


@pytest.mark.parametrize("key", _part_keys(DAILY, "scene"))
def test_scene_variant_carries_its_issue_anchor(key: str) -> None:
    _check_scene_anchor(key, DAILY[key].text)


def _check_scene_anchor(key: str, text: str) -> None:
    # meaning_gate rejects a card whose scene drifts from its issue's scene anchors.
    match = _match(key)
    assert match
    folded = _fold(text)
    assert any(_fold(a) in folded for a in ISSUES[match["issue"]].scene_anchors), key


# Per-field Daily gates (#288 follow-up). Every number and word list below is read from
# content_rewrite/gates.py (evaluate_daily_rewrite) or readings/gates.py
# (scene_contains_advice); nothing here sets a new threshold.
_OPAQUE = (*_OPAQUE_FILLER, *BANNED_CORE_FRAGMENTS, *OPAQUE_CORE_FRAGMENTS)
_CERTAINTY = ("chac chan", "nhat dinh", "se luon", "luon luon")
# A served scene carries one arena lead ("Với người kia, khi …"); the gate sees the led text.
_LEADS = tuple(daily_psychology._ARENA_LEADS.values())

# Known exceptions: registry copy that fails a field gate today. Test-only PR, so the copy
# is not rewritten here; these go to the Codex copy batch and leave this list once fixed.
# All are pending, so none is served. strict=True makes a fixed entry fail until removed.
_KNOWN_FIELD_GATE_EXCEPTIONS: dict[str, str] = {}


def _field_params(part: str) -> list[Any]:
    return [
        pytest.param(
            key,
            marks=pytest.mark.xfail(reason=_KNOWN_FIELD_GATE_EXCEPTIONS[key], strict=True),
        )
        if key in _KNOWN_FIELD_GATE_EXCEPTIONS
        else key
        for key in _part_keys(DAILY, part)
    ]


def test_known_field_gate_exceptions_are_pending_registry_entries() -> None:
    for key in _KNOWN_FIELD_GATE_EXCEPTIONS:
        assert key in DAILY and DAILY[key].status == "pending", key


def _shared_failures(text: str) -> list[str]:
    folded = _fold(text)
    failures: list[str] = []
    if any(_fold(term) in folded for term in _ASTRO_TERMS):
        failures.append("daily_astro_term")
    if any(_fold(term) in folded for term in _OPAQUE):
        failures.append("daily_opaque_filler")
    if scene_contains_advice(text):
        failures.append("scene_contains_advice")
    return failures


@pytest.mark.parametrize("key", _field_params("headline"))
def test_headline_variant_passes_title_gates(key: str) -> None:
    _check_headline(key, DAILY[key].text)


def _check_headline(key: str, text: str) -> None:
    failures = _shared_failures(text)
    if not 3 <= _words(text) <= 11:
        failures.append("daily_title_budget")
    assert failures == [], (key, failures)


@pytest.mark.parametrize("key", _field_params("scene"))
def test_scene_variant_passes_scene_gates(key: str) -> None:
    _check_scene(key, DAILY[key].text)


def _check_scene(key: str, text: str) -> None:
    failures = _shared_failures(text)
    for led in (text, *(daily_psychology.lead_scene(lead, text) for lead in _LEADS)):
        if not 8 <= _words(led) <= 40:
            failures.append("daily_scene_budget")
        if any(_words(s) > 28 for s in re.split(r"[.!?]+", led) if s.strip()):
            failures.append("daily_dense_sentence")
        folded = _fold(led)
        if re.search(r"(?:^|[.!?]\s+)(?:hay|thu|nen|dung)\s", folded):
            failures.append("daily_advice_in_scene")
        if any(term in folded for term in _CERTAINTY):
            failures.append("daily_unwarranted_certainty")
        if not any(_fold(marker) in folded for marker in _SCENE_MARKERS):
            failures.append("daily_unobservable_scene")
    assert list(dict.fromkeys(failures)) == [], (key, failures)


def test_every_headline_fits_the_home_title_budget() -> None:
    """Same counter as the daily_title_budget gate; pending headlines included."""
    over = {
        key: _words(entry.text)
        for key, entry in DAILY.items()
        if key in _part_keys(DAILY, "headline") and not 3 <= _words(entry.text) <= 11
    }
    assert not over, over


@pytest.mark.parametrize("lead", sorted(_ARENA_LEADS.values()))
def test_any_scene_opening_composes_with_every_arena_lead(lead: str) -> None:
    arena = next(key for key, value in _ARENA_LEADS.items() if value == lead)
    khi = "Khi bạn nhận thêm việc, lịch tối nay kín dần."
    other = "Bạn nhận thêm việc rồi thấy lịch tối nay kín dần."
    spliced = lead_scene(lead, khi)
    assert spliced == f"{lead} khi bạn nhận thêm việc, lịch tối nay kín dần."
    assert split_scene_lead(spliced) == (arena, khi)
    colon = lead_scene(lead, other)
    assert colon == f"{lead.rstrip(',')}: {other}"
    assert split_scene_lead(colon) == (arena, other)
    assert current_scene_lead(spliced) == lead
    assert current_scene_lead(colon) == f"{lead.rstrip(',')}:"
    for key in _part_keys(DAILY, "scene"):
        text = DAILY[key].text
        assert split_scene_lead(lead_scene(lead, text)) == (arena, text)


_PART_CHECKS = {
    "headline": (_check_headline,),
    "scene": (_check_scene, _check_scene_anchor),
    "action": (_check_action,),
}


def test_synthetic_pending_bundle_gets_every_variant_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = ISSUES["missing-context"]
    texts = {
        "headline": issue.headlines[0],
        "scene": issue.scenes[0],
        "action": issue.advice[0],
    }
    entries = [
        _entry(f"daily.bundle.missing-context.01.{part}", text, approved=False)
        for part, text in texts.items()
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    daily = dict(registry)
    _check_well_formed(daily)
    checked: list[tuple[str, str]] = []
    for part, checks in _PART_CHECKS.items():
        (key,) = _part_keys(daily, part)
        assert key == f"daily.bundle.missing-context.01.{part}"
        _check_clarity(key, daily[key].text)
        for check in checks:
            check(key, daily[key].text)
            checked.append((part, check.__name__))
    assert {part for part, _ in checked} == set(PARTS)

    # Existing pool sentences pass the gates; a bad bundle action line is rejected.
    with pytest.raises(AssertionError):
        _check_action("daily.bundle.missing-context.01.action", "Một câu không có động từ mở.")
    _use(monkeypatch, *entries)
    assert copy_approval.approved_bundles("missing-context") == ()
