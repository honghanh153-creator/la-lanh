"""Every Daily action has a size and a picture group (#699 AC2, AC3). Synthetic ids only."""

from __future__ import annotations

from collections import Counter

import pytest

from app.domains.content.copy_approval import copy_digest, load_registry
from app.domains.readings import action_tags, lighter_action
from app.domains.readings.action_tags import (
    ActionTag,
    normal_issue_of,
    normal_tags,
    store_gaps,
    tag_of,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.lighter_action import ACTION_SHAPES, ISSUE_LIGHT_CATALOG, light_slots

ISSUE_KEYS = tuple(issue.key for issue in DAILY_ISSUES)
DIGESTS = {key: copy_digest(entry.text) for key, entry in load_registry().items()}
NORMAL = {key: digest for key, digest in DIGESTS.items() if normal_issue_of(key) is not None}


def _with_tags(monkeypatch: pytest.MonkeyPatch, tags: dict[str, tuple[str, str]]) -> None:
    monkeypatch.setattr(action_tags, "normal_tags", lambda: tags)


def test_every_daily_issue_has_a_light_and_a_normal_action_all_tagged() -> None:
    assert store_gaps(ISSUE_KEYS, DIGESTS) == []
    assert set(normal_tags()) == set(NORMAL)
    for issue in ISSUE_KEYS:
        assert light_slots(issue)
        assert any(normal_issue_of(key) == issue for key in NORMAL)


def test_only_action_sentences_count_as_normal_actions() -> None:
    assert normal_issue_of("daily.action.quick-reply.01") == "quick-reply"
    assert normal_issue_of("daily.bundle.quick-reply.02.action") == "quick-reply"
    for other in (
        "daily.bundle.quick-reply.02.scene",
        "daily.bundle.quick-reply.02.headline",
        "daily.scene.quick-reply.01",
        "lighter.issue.quick-reply.01",
        "daily.action.quick-reply",
    ):
        assert normal_issue_of(other) is None


def test_a_tag_gives_size_and_picture_group_for_both_kinds() -> None:
    normal_id = sorted(NORMAL)[0]
    assert tag_of(normal_id, ISSUE_KEYS) == ActionTag("normal", normal_tags()[normal_id][1])
    light_id, _digest, shape = light_slots(ISSUE_KEYS[0])[0]
    assert tag_of(light_id, ISSUE_KEYS) == ActionTag("light", shape)
    assert tag_of("daily.scene.quick-reply.01", ISSUE_KEYS) is None
    for entry_id in NORMAL:
        tag = tag_of(entry_id, ISSUE_KEYS)
        assert tag is not None and tag.weight == "normal" and tag.shape in ACTION_SHAPES


def test_goes_red_for_an_issue_without_a_normal_action() -> None:
    issue = ISSUE_KEYS[0]
    without = {key: digest for key, digest in DIGESTS.items() if normal_issue_of(key) != issue}
    gaps = store_gaps(ISSUE_KEYS, without)
    assert f"{issue}: no normal action" in gaps
    # Its tags now point at nothing, and that is named too.
    assert all(gap == f"{issue}: no normal action" or "tagged but not in" in gap for gap in gaps)


def test_goes_red_for_an_issue_without_a_light_action(monkeypatch: pytest.MonkeyPatch) -> None:
    issue = ISSUE_KEYS[0]
    without = {key: slots for key, slots in ISSUE_LIGHT_CATALOG.items() if key != issue}
    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", without)
    assert store_gaps(ISSUE_KEYS, DIGESTS) == [f"{issue}: no light action"]


def test_goes_red_for_a_normal_action_without_a_valid_picture_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = dict(normal_tags())
    entry_id = sorted(tags)[0]
    digest, _shape = tags[entry_id]

    _with_tags(monkeypatch, {key: tag for key, tag in tags.items() if key != entry_id})
    assert store_gaps(ISSUE_KEYS, DIGESTS) == [f"{entry_id}: no picture group"]

    for shape in ("", "sleep"):
        _with_tags(monkeypatch, {**tags, entry_id: (digest, shape)})
        assert store_gaps(ISSUE_KEYS, DIGESTS) == [
            f"{entry_id}: picture group must be one of the six"
        ]


def test_goes_red_when_a_sentence_is_reworded_added_or_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry_id = sorted(NORMAL)[0]
    reworded = {**DIGESTS, entry_id: copy_digest("Uống một cốc nước rồi mới trả lời.")}
    assert store_gaps(ISSUE_KEYS, reworded) == [
        f"{entry_id}: reworded, check its picture group again"
    ]

    new_id = "daily.action.quick-reply.9999"
    added = {**DIGESTS, new_id: copy_digest("Ghi ra một việc cần làm trước.")}
    assert store_gaps(ISSUE_KEYS, added) == [f"{new_id}: no picture group"]

    stray = "daily.action.no-such-issue.01"
    assert f"{stray}: not a Daily issue" in store_gaps(ISSUE_KEYS, {**DIGESTS, stray: "0" * 64})

    gone = "daily.action.quick-reply.9998"
    _with_tags(monkeypatch, {**normal_tags(), gone: ("0" * 64, "rest")})
    assert store_gaps(ISSUE_KEYS, DIGESTS) == [f"{gone}: tagged but not in the copy store"]


def test_tag_file_is_sorted_and_names_each_sentence_once() -> None:
    raw = action_tags.TAGS_PATH.read_text(encoding="utf-8")
    keys = [line.split('"')[1] for line in raw.splitlines() if line.startswith(' "daily.')]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys)) == len(NORMAL)
    counts = Counter(shape for _digest, shape in normal_tags().values())
    assert set(counts) <= set(ACTION_SHAPES)
