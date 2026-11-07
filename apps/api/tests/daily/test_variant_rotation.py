"""Daily v2 C2d (stateless HMAC variants) and N-6 (⚠ at most once in any 7 days).

Synthetic readers and a fake key only.
"""

from __future__ import annotations

import ast
import logging
from collections import Counter
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path
from uuid import UUID

import pytest

from app.domains.daily import variant_rotation
from app.domains.daily.variant_rotation import (
    SENSITIVE_BLOCK_DAYS,
    SENSITIVE_JITTER_DAYS,
    SENSITIVE_WINDOW_DAYS,
    daily_trend_tags,
    daily_variant,
    limit_sensitive,
    reader_seed,
    sensitive_day_open,
    variant_slot,
)
from app.domains.readings.daily_rotation import (
    _shuffled,
    daily_variety_seed,
    day_index,
    derive_variety_key,
)
from app.domains.readings.house_meanings import (
    HOUSE_MEANINGS,
    MeaningSource,
    SourcedMeaning,
    display_order,
)

KEY = derive_variety_key(b"fake-test-secret-not-a-real-key")
OTHER_KEY = derive_variety_key(b"another-fake-test-secret")
READERS = tuple(UUID(int=0x40000000_0000_4000_8000_000000000000 + i) for i in range(600))
READER = READERS[0]
START = date(2026, 11, 2)
YEAR = tuple(START + timedelta(days=i) for i in range(365))
SLOT = "moon:trine:venus:body"

# Every house's display-safe order (⚠ meanings included), as a trend tag would carry it.
ALL_TAGS = tuple(display_order(house, daily=False) for house in range(1, 13))
HOUSE_5 = display_order(5, daily=True)


def _sensitive_count(tags: tuple[tuple[SourcedMeaning, ...], ...]) -> int:
    return sum(meaning.sensitive for tag in tags for meaning in tag)


# --- C2d: variants -------------------------------------------------------------------------


def test_variant_is_deterministic_per_reader_day_and_key() -> None:
    first = [daily_variant(KEY, reader, SLOT, 10, day) for reader in READERS[:50] for day in YEAR]
    again = [daily_variant(KEY, reader, SLOT, 10, day) for reader in READERS[:50] for day in YEAR]
    assert first == again
    assert all(0 <= value < 10 for value in first)


def test_readers_spread_across_variants() -> None:
    n = 10
    for day in (START, START + timedelta(days=17), START + timedelta(days=200)):
        counts = Counter(daily_variant(KEY, reader, SLOT, n, day) for reader in READERS)
        assert set(counts) == set(range(n))
        expected = len(READERS) / n
        # Binomial(600, 0.1): sd ~7.3; +-35 is far outside chance for a fair spread.
        assert all(abs(count - expected) <= 35 for count in counts.values()), counts


def test_one_reader_sees_every_variant_once_per_cycle_and_never_twice_in_a_row() -> None:
    n = 10
    for reader in READERS[:40]:
        values = [daily_variant(KEY, reader, SLOT, n, day) for day in YEAR]
        assert all(left != right for left, right in pairwise(values))
        start = day_index(YEAR[0])
        first_full_cycle = (-start) % n
        for cycle_start in range(first_full_cycle, len(values) - n + 1, n):
            assert sorted(values[cycle_start : cycle_start + n]) == list(range(n))


def test_cycle_boundary_collision_keeps_both_cycles_unique() -> None:
    """#302: when a new cycle's raw shuffle opens with yesterday's variant, the boundary rule
    swaps its first two positions. A swap keeps the cycle a permutation; "take the next
    element" would show that element again the following day."""

    forced = []
    for n in (3, 5, 10):
        for reader in READERS[:200]:
            seed = reader_seed(KEY, reader)
            for cycle in range(1, 40):
                if _shuffled(seed, f"c2d:{SLOT}", cycle, n)[0] == _shuffled(
                    seed, f"c2d:{SLOT}", cycle - 1, n
                )[-1]:
                    forced.append((n, seed, cycle))
    assert len(forced) >= 30, "the collision case must actually be exercised"
    for n, seed, cycle in forced:
        prev_last, first, second = (
            variant_slot(seed, SLOT, n, cycle * n + offset) for offset in (-1, 0, 1)
        )
        assert prev_last != first
        assert first != second
        new_cycle = [variant_slot(seed, SLOT, n, cycle * n + day) for day in range(n)]
        assert sorted(new_cycle) == list(range(n))
        old_cycle = [variant_slot(seed, SLOT, n, (cycle - 1) * n + day) for day in range(n)]
        assert sorted(old_cycle) == list(range(n))


def test_slots_rotate_independently() -> None:
    a = [daily_variant(KEY, READER, "moon:trine:venus:body", 10, day) for day in YEAR]
    b = [daily_variant(KEY, READER, "moon:square:mars:body", 10, day) for day in YEAR]
    assert a != b


def test_changing_the_key_changes_the_assignment() -> None:
    day = START + timedelta(days=3)
    same = sum(
        daily_variant(KEY, reader, SLOT, 10, day) == daily_variant(OTHER_KEY, reader, SLOT, 10, day)
        for reader in READERS
    )
    # About 1 in 10 agree by chance; a key that did not matter would agree on all 600.
    assert same < len(READERS) * 0.2
    assert reader_seed(KEY, READER) != reader_seed(OTHER_KEY, READER)


def test_seed_is_separate_from_the_b3_daily_seed_and_holds_no_date() -> None:
    seed = reader_seed(KEY, READER)
    assert len(seed) == 32
    assert int(seed, 16) >= 0
    assert seed != daily_variety_seed(KEY, READER, "daily-v2-variants-v1")
    assert len({reader_seed(KEY, reader) for reader in READERS}) == len(READERS)


@pytest.mark.parametrize("bad_key", [b"", b"short", bytes(31)])
def test_a_missing_or_short_key_fails_closed(bad_key: bytes) -> None:
    with pytest.raises(ValueError, match="selection key"):
        reader_seed(bad_key, READER)


def test_bad_inputs_are_rejected() -> None:
    seed = reader_seed(KEY, READER)
    with pytest.raises(ValueError):
        variant_slot(seed, "", 3, 0)
    with pytest.raises(ValueError):
        variant_slot(seed, SLOT, 0, 0)
    with pytest.raises(ValueError):
        daily_variant(KEY, READER, SLOT, 3, date(2025, 12, 31))
    with pytest.raises(ValueError):
        sensitive_day_open(seed, -1)


# --- N-6: ⚠ at most once in any rolling 7 days ----------------------------------------------


def test_open_days_are_a_rolling_window_apart_for_every_reader() -> None:
    assert SENSITIVE_BLOCK_DAYS - SENSITIVE_JITTER_DAYS >= SENSITIVE_WINDOW_DAYS
    for reader in READERS:
        seed = reader_seed(KEY, reader)
        open_days = [i for i in range(0, 800) if sensitive_day_open(seed, i)]
        gaps = [right - left for left, right in pairwise(open_days)]
        assert min(gaps) >= SENSITIVE_WINDOW_DAYS
        assert max(gaps) <= SENSITIVE_BLOCK_DAYS + SENSITIVE_JITTER_DAYS


def test_sensitive_meaning_appears_at_most_once_in_any_seven_days() -> None:
    for reader in READERS[:200]:
        shown = [_sensitive_count(daily_trend_tags(KEY, reader, day, ALL_TAGS)) for day in YEAR]
        assert all(count <= 1 for count in shown)
        for start in range(len(shown) - SENSITIVE_WINDOW_DAYS + 1):
            assert sum(shown[start : start + SENSITIVE_WINDOW_DAYS]) <= 1
        # The cap rotates ⚠ meanings in; it does not delete them for good.
        assert sum(shown) >= len(YEAR) // (SENSITIVE_BLOCK_DAYS + SENSITIVE_JITTER_DAYS) - 1


def test_readers_get_sensitive_days_on_different_days_and_topics_rotate() -> None:
    for offset in range(SENSITIVE_BLOCK_DAYS * 2):
        day = START + timedelta(days=offset)
        open_today = sum(
            _sensitive_count(daily_trend_tags(KEY, reader, day, (HOUSE_5,))) for reader in READERS
        )
        # About one reader in nine on every calendar day; never everyone, never no one.
        assert len(READERS) * 0.05 < open_today < len(READERS) * 0.2, (day, open_today)
    picked = Counter(
        meaning.key
        for day in YEAR
        for tag in daily_trend_tags(KEY, READER, day, ALL_TAGS)
        for meaning in tag
        if meaning.sensitive
    )
    assert len(picked) >= 3


def test_kept_sensitive_meaning_never_leads_never_stands_alone_never_banned() -> None:
    for reader in READERS[:100]:
        for day in YEAR[:60]:
            for tag in daily_trend_tags(KEY, reader, day, ALL_TAGS):
                assert tag, "a tag keeps its non-⚠ lead"
                assert not tag[0].sensitive
                assert all(meaning.daily_allowed for meaning in tag)


def test_a_tag_that_would_open_with_a_sensitive_meaning_offers_no_candidate() -> None:
    sensitive = SourcedMeaning("synthetic_sensitive", "x", MeaningSource.CLASSICAL, sensitive=True)
    plain = SourcedMeaning("synthetic_plain", "y", MeaningSource.CLASSICAL)
    seed = reader_seed(KEY, READER)
    open_day = next(i for i in range(SENSITIVE_BLOCK_DAYS) if sensitive_day_open(seed, i))
    assert limit_sensitive(seed, open_day, ((sensitive, plain),)) == ((plain,),)
    assert limit_sensitive(seed, open_day, ((sensitive,),)) == ((),)
    assert limit_sensitive(seed, open_day, ((plain, sensitive),)) == ((plain, sensitive),)
    closed_day = open_day + 1
    assert limit_sensitive(seed, closed_day, ((plain, sensitive),)) == ((plain,),)


def test_non_sensitive_meanings_are_untouched_and_order_is_kept() -> None:
    seed = reader_seed(KEY, READER)
    for index in range(40):
        for before, after in zip(ALL_TAGS, limit_sensitive(seed, index, ALL_TAGS), strict=True):
            plain = tuple(m for m in before if not m.sensitive)
            assert tuple(m for m in after if not m.sensitive) == plain
            assert list(after) == [m for m in before if m in after]


def test_changing_the_key_moves_the_sensitive_days() -> None:
    moved = 0
    for reader in READERS[:100]:
        a = [sensitive_day_open(reader_seed(KEY, reader), i) for i in range(90)]
        b = [sensitive_day_open(reader_seed(OTHER_KEY, reader), i) for i in range(90)]
        moved += a != b
    assert moved > 80


# --- nothing persisted, nothing logged ------------------------------------------------------


def test_nothing_is_persisted_or_logged(caplog: pytest.LogCaptureFixture) -> None:
    module_state = {
        name: repr(value)
        for name, value in vars(variant_rotation).items()
        if not name.startswith("__") and not callable(value)
    }
    with caplog.at_level(logging.DEBUG):
        for day in YEAR[:30]:
            daily_variant(KEY, READER, SLOT, 10, day)
            daily_trend_tags(KEY, READER, day, ALL_TAGS)
    assert caplog.records == []
    after = {
        name: repr(value)
        for name, value in vars(variant_rotation).items()
        if not name.startswith("__") and not callable(value)
    }
    assert after == module_state
    # Same answer from a fresh computation: there is no hidden history.
    assert daily_variant(KEY, READER, SLOT, 10, YEAR[0]) == variant_slot(
        reader_seed(KEY, READER), SLOT, 10, day_index(YEAR[0])
    )


def test_module_has_no_io_storage_logging_or_clock() -> None:
    source = Path(variant_rotation.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported <= {"__future__", "hmac", "collections", "datetime", "hashlib", "uuid", "app"}
    from_app = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app")
    }
    assert from_app == {
        "app.domains.readings.daily_rotation",
        "app.domains.readings.house_meanings",
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert not names & {"open", "print", "logging", "logger", "lru_cache", "cache", "now"}
    assert "functools" not in source


def test_house_table_still_has_sensitive_meanings_to_cap() -> None:
    assert any(m.sensitive and m.daily_allowed for tag in HOUSE_MEANINGS.values() for m in tag)
