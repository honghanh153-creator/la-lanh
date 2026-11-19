"""Light actions per Daily issue (#699): coverage, copy quality, frozen offer. Synthetic ids."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid5

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import lighter_action
from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    MAX_SENTENCE_SYLLABLES,
    count_jargon,
    count_meta_talk,
    count_placeholders,
    count_safety,
    english_words,
    sentences,
    syllables,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import (
    ACTION_SHAPES,
    ISSUE_LIGHT_CATALOG,
    ISSUE_LIGHT_PREFIX,
    LIGHTER_ACTION_PREFIX,
    issue_key_of,
    light_slots,
    light_store_gaps,
    lighter_action_for,
    lighter_action_projection,
    within_five_minutes,
)
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS
from scripts.persona_metrics import light_by_rule

NAMESPACE = UUID("00000000-0000-4000-8000-000000000699")
REVISIONS = tuple(uuid5(NAMESPACE, f"simulated-day-{day}") for day in range(120))
ISSUE_KEYS = tuple(issue.key for issue in DAILY_ISSUES)
REGISTRY = load_registry()
POOL = {key: entry for key, entry in REGISTRY.items() if key.startswith(ISSUE_LIGHT_PREFIX)}
GENERAL = {key: entry for key, entry in REGISTRY.items() if key.startswith(LIGHTER_ACTION_PREFIX)}
SAFETY = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))


def _entry(entry_id: str, text: str, *, approved: bool) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": entry_id,
        "category": "reading",
        "text": text,
        "status": "pending",
    }
    if approved:
        entry.update(
            status="approved", approver="codex", date="2026-11-19", digest=copy_digest(text)
        )
    return entry


def _use(monkeypatch: pytest.MonkeyPatch, *entries: dict[str, Any]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": list(entries)})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _pool(*, approved: bool, general: bool = True) -> list[dict[str, Any]]:
    source = {**POOL, **GENERAL} if general else POOL
    return [_entry(key, entry.text, approved=approved) for key, entry in source.items()]


def _mechanism(issue_key: str) -> str:
    return f"psychology:{issue_key}"


# --- AC2, AC3: every Daily issue has a light action, each with a picture group. ---


def test_every_daily_issue_has_a_light_action_with_a_picture_group() -> None:
    assert light_store_gaps(ISSUE_KEYS) == []
    assert set(ISSUE_LIGHT_CATALOG) == set(ISSUE_KEYS)


def test_coverage_goes_red_for_a_missing_issue_or_picture_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = ISSUE_KEYS[0]
    without = {key: slots for key, slots in ISSUE_LIGHT_CATALOG.items() if key != issue}
    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", without)
    assert light_store_gaps(ISSUE_KEYS) == [f"{issue}: no light action"]

    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", {**without, issue: ()})
    assert light_store_gaps(ISSUE_KEYS) == [f"{issue}: no light action"]

    number, digest, _shape = ISSUE_LIGHT_CATALOG[issue][0]
    for shape in ("", "sleep"):
        untagged = {**without, issue: ((number, digest, shape),)}
        monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", untagged)
        assert light_store_gaps(ISSUE_KEYS) == [
            f"{ISSUE_LIGHT_PREFIX}{issue}.{number}: picture group must be one of the six"
        ]

    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", {**without, "no-such-issue": ()})
    assert f"{issue}: no light action" in light_store_gaps(ISSUE_KEYS)
    assert "no-such-issue: not a Daily issue" in light_store_gaps(ISSUE_KEYS)


def test_catalog_is_exactly_the_checked_in_sentences() -> None:
    """Editing, adding or dropping a sentence must be a deliberate catalog change."""

    catalog = {
        entry_id: digest
        for issue in ISSUE_LIGHT_CATALOG
        for entry_id, digest, _shape in light_slots(issue)
    }
    assert catalog == {key: copy_digest(entry.text) for key, entry in POOL.items()}
    assert len({entry.text for entry in (*POOL.values(), *GENERAL.values())}) == len(POOL) + len(
        GENERAL
    )
    assert {entry.category for entry in POOL.values()} == {"reading"}
    assert len(ACTION_SHAPES) == len(set(ACTION_SHAPES)) == 6


@pytest.mark.parametrize("key", sorted(POOL))
def test_issue_light_action_is_plain_short_and_light(key: str) -> None:
    text = POOL[key].text
    assert len(text) <= LIGHTER_ACTION_MAX_CHARS
    assert len(sentences(text)) == 1
    assert syllables(text) <= MAX_SENTENCE_SYLLABLES
    assert not any(count_safety(rule, text) for rule in SAFETY)
    assert count_jargon(text) == count_meta_talk(text) == count_placeholders(text) == 0
    assert english_words(text) == ()
    folded = text.casefold()
    assert not any(part in folded for part in (*BANNED_CORE_FRAGMENTS, *OPAQUE_CORE_FRAGMENTS))
    assert has_observable_action(text)
    # The measuring rule of the persona run (qa/personas/judge-rubric.md): light, within 5 minutes.
    assert light_by_rule(text)
    assert within_five_minutes(text)


# --- Runtime: a card offers a light action of its own issue, one fixed sentence or nothing. ---


@pytest.mark.parametrize("issue", ISSUE_KEYS)
def test_card_offers_a_light_action_written_for_its_own_issue(
    issue: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, *_pool(approved=True))
    own = {REGISTRY[entry_id].text for entry_id, _digest, _shape in light_slots(issue)}
    offered = {lighter_action_for(revision, _mechanism(issue)) for revision in REVISIONS}
    # Every card gets one, only from its own issue, and the issue's sentences all get used.
    assert offered == own


def test_pending_issue_copy_is_never_offered_and_the_general_list_does_not_fill_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    general = [_entry(key, entry.text, approved=True) for key, entry in GENERAL.items()]
    _use(monkeypatch, *general, *_pool(approved=False, general=False))
    for issue in ISSUE_KEYS:
        for revision in REVISIONS[:10]:
            assert lighter_action_for(revision, _mechanism(issue)) is None
            assert (
                lighter_action_projection(revision, keepable=True, mechanism_key=_mechanism(issue))
                is None
            )


def test_checked_in_registry_offers_only_approved_issue_copy() -> None:
    for issue in ISSUE_KEYS:
        approved = {
            REGISTRY[entry_id].text
            for entry_id, _digest, _shape in light_slots(issue)
            if REGISTRY[entry_id].servable
        }
        for revision in REVISIONS[:20]:
            action = lighter_action_for(revision, _mechanism(issue))
            assert action is None or action in approved


def test_a_card_without_a_known_issue_keeps_the_general_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _use(monkeypatch, *_pool(approved=True))
    general = {entry.text for entry in GENERAL.values()}
    for mechanism in (None, "", "psychology:no-such-issue", "aura:quick-reply", "quick-reply"):
        assert issue_key_of(mechanism) is None
        for revision in REVISIONS[:20]:
            offered = lighter_action_for(revision, mechanism)
            assert offered == lighter_action_for(revision) and offered in general


def test_issue_offer_is_one_fixed_sentence_or_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    issue, card = "quick-reply", REVISIONS[0]
    _use(monkeypatch, *_pool(approved=True))
    offered = lighter_action_for(card, _mechanism(issue))
    assert offered is not None
    own = next(entry for entry in _pool(approved=True) if entry["text"] == offered)
    others = [entry for entry in _pool(approved=True) if entry["text"] != offered]

    # Its own sentence alone is enough; nothing else in the registry matters.
    _use(monkeypatch, own)
    assert lighter_action_for(card, _mechanism(issue)) == offered
    # Without it the card offers nothing: not a neighbour, not a sentence of the general list.
    _use(monkeypatch, *others)
    assert lighter_action_for(card, _mechanism(issue)) is None
    # A sentence approved later, even under this issue's prefix, does not move the offer.
    later = _entry(
        f"{ISSUE_LIGHT_PREFIX}{issue}.99", "Rót một cốc nước và uống chậm.", approved=True
    )
    _use(monkeypatch, own, *others, later)
    assert lighter_action_for(card, _mechanism(issue)) == offered
    # An edited sentence is not offered until the catalog names the new text.
    edited = dict(own, text=offered + " Rồi thở.", digest=copy_digest(offered + " Rồi thở."))
    _use(monkeypatch, *others, edited)
    assert lighter_action_for(card, _mechanism(issue)) is None


def test_issue_offer_is_keepable_under_its_own_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, *_pool(approved=True))
    mechanism = _mechanism("decision-fatigue")
    first = lighter_action_projection(REVISIONS[1], keepable=True, mechanism_key=mechanism)
    again = lighter_action_projection(REVISIONS[1], keepable=True, mechanism_key=mechanism)
    assert first is not None and first == again
    assert first.weight == "light"
    assert first.experiment is not None and first.experiment.action == first.action
    plain = lighter_action_projection(REVISIONS[1], keepable=False, mechanism_key=mechanism)
    assert plain is not None and plain.experiment is None and plain.action == first.action
