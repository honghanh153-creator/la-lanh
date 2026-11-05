"""C2d: 30-day anti-repeat for Daily content pieces (synthetic keys and dates only)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domains.readings.daily_rotation import ANTI_REPEAT_WINDOW_DAYS, pick_avoiding_recent

START = date(2026, 3, 1)


def _simulate(pool: list[tuple[str, float]], seed: str, days: int) -> list[str]:
    recent: dict[str, date] = {}
    picks: list[str] = []
    for offset in range(days):
        today = START + timedelta(days=offset)
        key = pick_avoiding_recent(pool, recent, today, seed)
        recent[key] = today
        picks.append(key)
    return picks


def test_regression_recent_piece_is_not_picked_again_when_equal_alternative_exists() -> None:
    pool = [("piece-a", 1.0), ("piece-b", 1.0)]
    today = START
    first = pick_avoiding_recent(pool, {}, today, "seed-x")
    other = "piece-b" if first == "piece-a" else "piece-a"
    shown = {first: today - timedelta(days=29)}
    assert pick_avoiding_recent(pool, shown, today, "seed-x") == other


def test_window_expires_after_thirty_days() -> None:
    pool = [("piece-a", 1.0), ("piece-b", 1.0)]
    first = pick_avoiding_recent(pool, {}, START, "seed-x")
    shown = {first: START - timedelta(days=ANTI_REPEAT_WINDOW_DAYS)}
    assert pick_avoiding_recent(pool, shown, START, "seed-x") == first


def test_never_trades_relevance_for_novelty() -> None:
    pool = [("best", 2.0), ("weaker", 1.0)]
    assert pick_avoiding_recent(pool, {"best": START}, START, "s") == "best"


def test_fallback_picks_least_recent_and_is_deterministic() -> None:
    pool = [("a", 1.0), ("b", 1.0), ("c", 1.0)]
    shown = {"a": START - timedelta(days=3), "b": START - timedelta(days=9), "c": START}
    assert pick_avoiding_recent(pool, shown, START, "s") == "b"
    assert pick_avoiding_recent(pool, shown, START, "s") == "b"


def test_rejects_empty_pool() -> None:
    with pytest.raises(ValueError):
        pick_avoiding_recent([], {}, START, "s")


@pytest.mark.parametrize("seed", [f"synthetic-seed-{n}" for n in range(12)])
def test_property_no_repeat_within_window_when_pool_is_large(seed: str) -> None:
    pool = [(f"piece-{n:02d}", 1.0) for n in range(ANTI_REPEAT_WINDOW_DAYS + 5)]
    pool.append(("off-tier", 0.5))
    picks = _simulate(pool, seed, 200)
    assert "off-tier" not in picks
    last: dict[str, int] = {}
    for offset, key in enumerate(picks):
        if key in last:
            assert offset - last[key] >= ANTI_REPEAT_WINDOW_DAYS
        last[key] = offset
    assert picks == _simulate(pool, seed, 200)


@pytest.mark.parametrize("size", [1, 2, 5, 17])
def test_property_small_pool_cycles_evenly(size: int) -> None:
    pool = [(f"piece-{n:02d}", 1.0) for n in range(size)]
    picks = _simulate(pool, "synthetic", 120)
    for offset in range(size, len(picks)):
        assert picks[offset] == picks[offset - size]
    assert len(set(picks[:size])) == size
