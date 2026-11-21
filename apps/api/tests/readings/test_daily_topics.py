"""Daily topic anti-repeat (plan 2026-11-21, proposed US-21 AC05): pure choice and schedule."""

from __future__ import annotations

from itertools import pairwise

import pytest

from app.domains.readings import daily_topics
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.daily_topics import (
    ISSUE_THEMES,
    SCHEDULE_BLOCK_DAYS,
    TOPIC_POOL_SIZE,
    TOPIC_WINDOW_DAYS,
    block_start,
    pick_topic,
    rotation_order,
    schedule,
)

# Six issues of four themes, ranked best first.
POOL = (
    "too-many-open-loops",  # overload
    "decision-fatigue",  # overload
    "quick-reply",  # reply
    "avoid-small-conflict",  # friction
    "comparison-loop",  # self-judgment
    "repair-reply",  # reply
)


def _repeats_within(days: list[str | None], window: int) -> int:
    return sum(
        1
        for i, key in enumerate(days)
        if key is not None and key in days[max(0, i - window + 1) : i]
    )


def test_every_catalog_issue_has_exactly_one_theme() -> None:
    assert set(ISSUE_THEMES) == {issue.key for issue in DAILY_ISSUES}
    assert all(theme and theme.isascii() for theme in ISSUE_THEMES.values())


def test_the_best_ranked_fresh_topic_of_a_new_theme_wins() -> None:
    assert pick_topic(POOL, []) == 0
    # Yesterday was overload: the next fresh topic of another theme, not decision-fatigue.
    assert pick_topic(POOL, ["too-many-open-loops"]) == 2


def test_a_theme_is_only_avoided_while_a_fresh_topic_of_another_theme_exists() -> None:
    pool = ("too-many-open-loops", "decision-fatigue")
    assert pick_topic(pool, ["too-many-open-loops"]) == 1


def test_a_stable_pool_shows_every_topic_before_one_comes_back() -> None:
    days = schedule([POOL] * 28)
    assert len(set(days[:6])) == 6
    # With six topics and a seven-day window, a repeat can only be the one shown longest ago.
    for i in range(6, 28):
        assert days[i] == days[i - 6]
    # No topic twice within six days; no theme on two days in a row while another exists.
    assert _repeats_within(days, 6) == 0
    themes = [ISSUE_THEMES[key] for key in days if key]
    assert all(a != b for a, b in pairwise(themes))


def test_the_old_three_topic_pool_still_rotates() -> None:
    days = schedule([POOL[:3]] * 9)
    assert all(days[i] != days[i + 1] for i in range(8))
    assert len(set(days[:3])) == 3


def test_a_one_topic_pool_stays_and_an_empty_pool_gives_none() -> None:
    assert schedule([("name-the-need",)] * 3) == ["name-the-need"] * 3
    assert schedule([(), POOL]) == [None, "too-many-open-loops"]
    with pytest.raises(ValueError):
        pick_topic((), [])


def test_only_the_top_of_the_pool_is_eligible() -> None:
    long_pool = (*POOL, "name-the-need", "group-pressure")
    days = schedule([long_pool] * 14)
    assert set(days) <= set(long_pool[:TOPIC_POOL_SIZE])


def test_history_outside_the_window_is_forgotten() -> None:
    old = ["quick-reply"] + [None] * (TOPIC_WINDOW_DAYS - 1)
    assert pick_topic(("quick-reply", "decision-fatigue"), old) == 0


def test_prior_days_count_as_history() -> None:
    assert schedule([POOL], prior=["too-many-open-loops"]) == ["quick-reply"]


def test_a_changing_pool_still_prefers_topics_not_seen_this_week() -> None:
    pools = [POOL[i % 3 : i % 3 + 4] for i in range(14)]
    days = schedule(pools)
    assert _repeats_within(days, 3) == 0


def test_the_schedule_is_deterministic_and_pure() -> None:
    pools = [POOL[: 3 + i % 4] for i in range(20)]
    assert schedule(pools) == schedule(pools)


def test_block_start_is_a_per_reader_phase_and_never_after_the_day() -> None:
    for index in range(SCHEDULE_BLOCK_DAYS, 70):
        start = block_start("seed-a", index)
        assert 0 <= index - start < SCHEDULE_BLOCK_DAYS
        assert block_start("seed-a", start) == start
    starts = {block_start(f"seed-{n}", 30) for n in range(40)}
    assert len(starts) > 1
    with pytest.raises(ValueError):
        block_start("seed-a", -1)


def test_the_module_has_no_clock_or_random() -> None:
    source = daily_topics.__loader__.get_source(daily_topics.__name__) or ""  # type: ignore[union-attr]
    assert "import random" not in source and "datetime" not in source


@pytest.mark.parametrize("size", [2, 3, 4, 6])
def test_a_steady_pool_keeps_its_rotation_across_block_boundaries(size: int) -> None:
    """Codex P2 on #841: each block restarts with an empty history, yet a pool that stays the
    same rotates without a break at the boundary, because the block length is a multiple of it."""

    pool = POOL[:size]
    block = schedule([pool] * SCHEDULE_BLOCK_DAYS)
    days = block * 4  # four blocks, each recomputed from an empty history
    assert all(days[i] == days[i - size] for i in range(size, len(days)))
    assert _repeats_within(days, size) == 0


def test_rotation_order_is_a_per_reader_permutation_with_themes_apart() -> None:
    order = rotation_order("seed-a", POOL)
    assert sorted(order) == sorted(POOL)
    assert order == rotation_order("seed-a", POOL)
    assert any(rotation_order(f"seed-{n}", POOL) != order for n in range(10))
    themes = [ISSUE_THEMES[key] for key in order]
    assert all(a != b for a, b in pairwise(themes))
