"""Mood-shaped actions (#701): a "slow" action for Căng and a "clear" one for Lạc trôi, per issue.

Coverage, copy quality and the frozen catalog. The sentences are pending; serving them is a
later step (API, then web). Synthetic data only.
"""

from __future__ import annotations

import pytest

from app.domains.content.copy_approval import copy_digest, load_registry
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
    ISSUE_LIGHT_PREFIX,
    MOOD_ACTION_CATALOG,
    MOOD_ACTION_PREFIXES,
    mood_slots,
    mood_store_gaps,
    within_ten_minutes,
)
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS

ISSUE_KEYS = tuple(issue.key for issue in DAILY_ISSUES)
REGISTRY = load_registry()
POOL = {
    key: entry
    for key, entry in REGISTRY.items()
    if key.startswith(tuple(MOOD_ACTION_PREFIXES.values()))
}
SAFETY = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))
# A wait tied to a later moment has no bound: after a meal can be hours away (#877 review).
OPEN_ENDED_WAITS = (
    "sau bữa",
    "tối nay",
    "ngày mai",
    "sáng mai",
    "cuối tuần",
    "lúc khác",
    "khi rảnh",
    "khi nào",
)


def test_every_daily_issue_has_a_slow_and_a_clear_action_with_a_picture_group() -> None:
    assert set(MOOD_ACTION_CATALOG) == {"slow", "clear"}
    assert mood_store_gaps(ISSUE_KEYS) == []
    for kind in MOOD_ACTION_CATALOG:
        assert set(MOOD_ACTION_CATALOG[kind]) == set(ISSUE_KEYS)


def test_coverage_goes_red_for_a_missing_issue_or_picture_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = ISSUE_KEYS[0]
    slow = {key: slots for key, slots in MOOD_ACTION_CATALOG["slow"].items() if key != issue}
    monkeypatch.setattr(
        lighter_action, "MOOD_ACTION_CATALOG", {**MOOD_ACTION_CATALOG, "slow": slow}
    )
    assert mood_store_gaps(ISSUE_KEYS) == [f"slow {issue}: no action"]

    number, digest, _shape = MOOD_ACTION_CATALOG["clear"][issue][0]
    clear = {**MOOD_ACTION_CATALOG["clear"], issue: ((number, digest, "sleep"),)}
    monkeypatch.setattr(
        lighter_action, "MOOD_ACTION_CATALOG", {**MOOD_ACTION_CATALOG, "clear": clear}
    )
    assert mood_store_gaps(ISSUE_KEYS) == [
        f"lighter.clear.{issue}.{number}: picture group must be one of the six"
    ]

    extra = {**MOOD_ACTION_CATALOG["slow"], "no-such-issue": ()}
    monkeypatch.setattr(
        lighter_action, "MOOD_ACTION_CATALOG", {**MOOD_ACTION_CATALOG, "slow": extra}
    )
    assert mood_store_gaps(ISSUE_KEYS) == ["slow no-such-issue: not a Daily issue"]


def test_catalog_is_exactly_the_checked_in_pending_sentences() -> None:
    """Editing, adding or dropping a sentence must be a deliberate catalog change."""

    catalog = {
        entry_id: digest
        for kind in MOOD_ACTION_CATALOG
        for issue in ISSUE_KEYS
        for entry_id, digest, _shape in mood_slots(kind, issue)
    }
    assert catalog == {key: copy_digest(entry.text) for key, entry in POOL.items()}
    assert {entry.status for entry in POOL.values()} == {"pending"}
    assert {entry.category for entry in POOL.values()} == {"reading"}
    light = {entry.text for key, entry in REGISTRY.items() if key.startswith(ISSUE_LIGHT_PREFIX)}
    texts = [entry.text for entry in POOL.values()]
    assert len(set(texts)) == len(texts) and not set(texts) & light
    shapes = {
        shape
        for kind in MOOD_ACTION_CATALOG.values()
        for slots in kind.values()
        for _n, _d, shape in slots
    }
    assert shapes <= set(ACTION_SHAPES)


@pytest.mark.parametrize("key", sorted(POOL))
def test_mood_action_is_plain_short_concrete_and_within_ten_minutes(key: str) -> None:
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
    assert within_ten_minutes(text)
    assert not any(wait in folded for wait in OPEN_ENDED_WAITS)
    # No health or diagnosis words: a mood is a vibe, never a medical signal (US-04 AC10).
    assert not any(word in folded for word in ("bệnh", "trầm cảm", "lo âu", "chẩn đoán", "thuốc"))


@pytest.mark.parametrize(
    ("text", "ok"),
    [
        ("Đợi năm phút rồi mới gửi.", True),
        ("Đợi sáu phút rồi mới gửi.", True),
        ("Đợi chín phút rồi mới gửi.", True),
        ("Đợi chín phút rưỡi rồi mới gửi.", True),
        ("Đợi mười phút rồi mới gửi.", True),
        ("Đợi 10 phút rồi mới gửi.", True),
        ("Đợi mười phút rưỡi rồi mới gửi.", False),
        ("Đợi 11 phút rồi mới gửi.", False),
        ("Đợi mười một phút rồi mới gửi.", False),
        ("Đợi mười lăm phút rồi mới gửi.", False),
        ("Đợi hai mươi phút rồi mới gửi.", False),
        ("Đợi vài phút rồi mới gửi.", False),
        ("Đợi một hai phút rồi mới gửi.", False),
        ("Nghỉ một giờ rồi quay lại.", False),
        ("Viết ra một việc duy nhất.", True),
    ],
)
def test_within_ten_minutes(text: str, ok: bool) -> None:
    assert within_ten_minutes(text) is ok
