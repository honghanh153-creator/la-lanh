"""Lighter Daily action (#627): the copy pool and which sentence a card offers. Synthetic ids."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid5

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
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
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import (
    LIGHTER_ACTION_PREFIX,
    lighter_action_for,
    lighter_action_projection,
)
from app.domains.readings.models import (
    LIGHTER_ACTION_MAX_CHARS,
    canonical_experiment_action_key,
)
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS
from scripts.persona_metrics import is_light, light_by_rule

NAMESPACE = UUID("00000000-0000-4000-8000-000000000627")
REVISIONS = tuple(uuid5(NAMESPACE, f"simulated-day-{day}") for day in range(290))
POOL = {
    key: entry for key, entry in load_registry().items() if key.startswith(LIGHTER_ACTION_PREFIX)
}
SAFETY = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))


def _entry(number: int, text: str, *, approved: bool) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": f"{LIGHTER_ACTION_PREFIX}{number:02d}",
        "category": "reading",
        "text": text,
        "status": "pending",
    }
    if approved:
        entry.update(
            status="approved", approver="codex", date="2026-11-17", digest=copy_digest(text)
        )
    return entry


def _use(monkeypatch: pytest.MonkeyPatch, *entries: dict[str, Any]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": list(entries)})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _approve_checked_in_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(
        monkeypatch,
        *(_entry(i, entry.text, approved=True) for i, entry in enumerate(POOL.values(), start=1)),
    )


def test_pool_is_large_enough_and_reading_copy() -> None:
    assert len(POOL) >= 10
    assert {entry.category for entry in POOL.values()} == {"reading"}
    assert len({entry.text for entry in POOL.values()}) == len(POOL)


@pytest.mark.parametrize("key", sorted(POOL))
def test_lighter_action_is_plain_short_and_light(key: str) -> None:
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
    # The measuring rule the persona run falls back to (qa/personas/judge-rubric.md).
    assert light_by_rule(text)


def test_mood_low_day_gets_a_light_action_on_at_least_90_percent_of_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#627 AC2, API half: every simulated card offers a lighter action marked light."""

    _approve_checked_in_pool(monkeypatch)
    offers = [lighter_action_projection(revision, keepable=True) for revision in REVISIONS]
    light = [
        offer
        for offer in offers
        if offer is not None and is_light(offer.action, {}, offer.weight) == (True, "api")
    ]
    assert len(light) / len(REVISIONS) >= 0.9
    # The pool rotates instead of repeating one sentence.
    assert len({offer.action for offer in light}) >= 8


def test_pending_lighter_copy_is_never_offered(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _entry(1, "Uống một cốc nước rồi ngồi yên.", approved=False))
    assert all(lighter_action_for(revision) is None for revision in REVISIONS[:20])
    assert lighter_action_projection(REVISIONS[0], keepable=True) is None


def test_checked_in_registry_offers_only_approved_lighter_copy() -> None:
    approved = {entry.text for entry in POOL.values() if entry.servable}
    for revision in REVISIONS[:50]:
        action = lighter_action_for(revision)
        assert action is None if not approved else action in approved


def test_offer_is_stable_per_card_and_keyed_to_it(monkeypatch: pytest.MonkeyPatch) -> None:
    _approve_checked_in_pool(monkeypatch)
    first = lighter_action_projection(REVISIONS[0], keepable=True)
    assert first is not None and first == lighter_action_projection(REVISIONS[0], keepable=True)
    assert first.experiment is not None
    assert first.experiment.action == first.action
    assert first.experiment.action_key == canonical_experiment_action_key(
        REVISIONS[0], first.action
    )
    not_keepable = lighter_action_projection(REVISIONS[0], keepable=False)
    assert not_keepable is not None and not_keepable.experiment is None


def test_overlong_approved_sentence_is_left_out(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _entry(1, "Nghỉ " * LIGHTER_ACTION_MAX_CHARS, approved=True))
    assert lighter_action_for(REVISIONS[0]) is None
