"""Lighter Daily action (#627): the copy pool and which sentence a card offers. Synthetic ids."""

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
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import (
    LIGHTER_ACTION_PREFIX,
    LIGHTER_CATALOG,
    lighter_action_for,
    lighter_action_projection,
    within_five_minutes,
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


def _one_slot_catalog(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    """A catalog whose only slot is ``text``, approved: only the runtime guards can refuse it."""

    monkeypatch.setattr(
        lighter_action, "LIGHTER_CATALOG", ((f"{LIGHTER_ACTION_PREFIX}01", copy_digest(text)),)
    )
    _use(monkeypatch, _entry(1, text, approved=True))


def test_overlong_approved_sentence_is_left_out(monkeypatch: pytest.MonkeyPatch) -> None:
    _one_slot_catalog(monkeypatch, "Uống một cốc nước rồi ngồi yên.")
    assert lighter_action_for(REVISIONS[0]) is not None
    _one_slot_catalog(monkeypatch, "Nghỉ " * LIGHTER_ACTION_MAX_CHARS)
    assert lighter_action_for(REVISIONS[0]) is None


def test_catalog_is_exactly_the_checked_in_sentences() -> None:
    """Editing, adding or dropping a sentence must be a deliberate catalog change.

    A sentence that was never released may be edited with its digest updated here. After a
    release, add a new id under a new catalog version instead (see ``lighter_action``).
    """

    assert dict(LIGHTER_CATALOG) == {key: copy_digest(entry.text) for key, entry in POOL.items()}
    assert len(dict(LIGHTER_CATALOG)) == len(LIGHTER_CATALOG)


@pytest.mark.parametrize("key", sorted(POOL))
def test_lighter_action_names_at_most_five_minutes(key: str) -> None:
    """The rubric's "within 5 minutes", checked apart from the API's constant weight."""

    assert within_five_minutes(POOL[key].text)


@pytest.mark.parametrize(
    "text",
    [
        "Tắt điện thoại mười phút rồi nằm nghỉ.",
        "Tắm nước ấm rồi nằm nghỉ mười lăm phút.",
        "Nằm nghỉ hai mươi phút.",
        "Nằm nghỉ 10 phút.",
        "Nằm nghỉ sáu phút.",
        "Nằm nghỉ năm phút rưỡi.",
        "Nằm nghỉ vài phút.",
        "Nằm nghỉ nửa tiếng.",
        "Đi bộ một giờ.",
    ],
)
def test_longer_or_unclear_durations_are_not_light(
    text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert not within_five_minutes(text)
    # Even approved and in the catalog, such a sentence is never served as light.
    _one_slot_catalog(monkeypatch, text)
    assert lighter_action_for(REVISIONS[0]) is None


@pytest.mark.parametrize(
    "text",
    [
        "Nằm nghỉ năm phút.",
        "Nghe tiếng mưa một phút.",
        "Nằm nghỉ bốn phút rưỡi.",
        "Nằm nghỉ 5 phút.",
        "Mở cửa sổ và đứng thở chậm.",
    ],
)
def test_short_durations_are_light(text: str) -> None:
    assert within_five_minutes(text)


# --- Frozen offer (review of #634): what a card offers never moves once it was shown. ---

CARD = NAMESPACE
EXTRA = "Rót một cốc nước và uống chậm."


def _approved_pool() -> list[dict[str, Any]]:
    return [_entry(i, entry.text, approved=True) for i, entry in enumerate(POOL.values(), start=1)]


def test_offer_does_not_move_when_another_sentence_is_approved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _approve_checked_in_pool(monkeypatch)
    before = lighter_action_projection(CARD, keepable=True)
    assert before is not None and before.experiment is not None

    _use(monkeypatch, *_approved_pool(), _entry(len(POOL) + 1, EXTRA, approved=True))
    after = lighter_action_projection(CARD, keepable=True)
    assert after == before


def test_offer_is_one_fixed_sentence_or_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    _approve_checked_in_pool(monkeypatch)
    offered = lighter_action_for(CARD)
    assert offered is not None
    own = next(entry for entry in _approved_pool() if entry["text"] == offered)
    others = [entry for entry in _approved_pool() if entry["text"] != offered]

    # Its own sentence alone is enough; the rest of the pool does not matter.
    _use(monkeypatch, own)
    assert lighter_action_for(CARD) == offered
    # Without its own sentence the card offers nothing, never a neighbour's sentence.
    _use(monkeypatch, *others)
    assert lighter_action_for(CARD) is None
    # An edited sentence is not offered until the catalog names the new text.
    edited = dict(own, text=offered + " Rồi thở.", digest=copy_digest(offered + " Rồi thở."))
    _use(monkeypatch, *others, edited)
    assert lighter_action_for(CARD) is None
