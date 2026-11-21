"""Daily topic anti-repeat per person, without stored history (plan 2026-11-21).

Spec: ``docs/plans/2026-11-21-daily-topic-anti-repeat.md`` (proposed US-21 AC05).

Daily used to pick its situation (topic, ``issue_key``) from the day's top 3 by ``day_index mod 3``,
so a reader met the same three topics in a three-day loop (81% of days repeated a topic seen in the
previous six, 20.11 release, 1000 personas). This module chooses instead from up to
``TOPIC_POOL_SIZE`` eligible situations, ranked best first, by three tiers:

1. not shown in the previous ``TOPIC_WINDOW_DAYS - 1`` days and not of a theme shown in the previous
   ``THEME_WINDOW_DAYS - 1`` days;
2. not shown in the previous ``TOPIC_WINDOW_DAYS - 1`` days;
3. the one shown longest ago.

Inside a tier the better-ranked situation wins, so novelty never skips a stronger situation that is
also fresh. "Shown" is what this same choice gave on earlier days, recomputed by the caller from the
chart, each day's transits and the reader's seed (owner decision 21.10.2026: no stored history).
To keep that bounded, days are cut into ``SCHEDULE_BLOCK_DAYS`` blocks at a per-reader phase; the
caller recomputes the block from its first day (``schedule``), with the previous block (computed
without history of its own) as the history at the block start.

Pure functions only: no I/O, no clock, no ``random``, nothing stored.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256

TOPIC_POOL_SIZE = 6
TOPIC_WINDOW_DAYS = 7
THEME_WINDOW_DAYS = 3
SCHEDULE_BLOCK_DAYS = 7

# One theme per Daily issue: situations of one theme read alike on consecutive days. A code, not
# copy; tests require every issue in the catalog to have exactly one.
ISSUE_THEMES: Mapping[str, str] = {
    "too-many-open-loops": "overload",
    "decision-fatigue": "overload",
    "capacity-before-agreement": "overload",
    "automatic-caretaking": "overload",
    "quick-reply": "reply",
    "repair-reply": "reply",
    "specific-feedback": "reply",
    "missing-context": "reply",
    "avoid-small-conflict": "friction",
    "group-pressure": "friction",
    "defend-old-choice": "friction",
    "changed-plan": "friction",
    "comparison-loop": "self-judgment",
    "perfect-before-start": "self-judgment",
    "name-the-need": "needs",
}

_BLOCK_LABEL = "daily-topic-block/v1"


def block_start(seed: str, index: int) -> int:
    """First day index of the schedule block holding day ``index`` for this reader.

    The phase comes from the reader's rotation seed, so readers do not all start a block on the
    same day; it reveals nothing about the chart (the seed holds no birth data)."""

    if index < 0:
        raise ValueError("day_index must not be negative")
    phase = int.from_bytes(sha256(f"{seed}\x1f{_BLOCK_LABEL}".encode()).digest()[:8], "big")
    return index - (index - phase % SCHEDULE_BLOCK_DAYS) % SCHEDULE_BLOCK_DAYS


def pick_topic(
    pool: Sequence[str],
    history: Sequence[str | None],
    themes: Mapping[str, str] = ISSUE_THEMES,
) -> int:
    """Index in ``pool`` (ranked best first) of the day's topic, given ``history`` (one entry per
    earlier day, oldest first, yesterday last; ``None`` = nothing known for that day)."""

    if not pool:
        raise ValueError("a topic needs a non-empty pool")
    candidates = list(pool[:TOPIC_POOL_SIZE])
    recent_topics = list(history[-(TOPIC_WINDOW_DAYS - 1) :])
    recent_themes = {themes.get(key) for key in history[-(THEME_WINDOW_DAYS - 1) :] if key}

    def last_seen(key: str) -> int:
        """Days ago the topic was last shown inside the window; 0 = not inside it."""

        for age, shown in enumerate(reversed(recent_topics), start=1):
            if shown == key:
                return age
        return 0

    fresh = [i for i, key in enumerate(candidates) if not last_seen(key)]
    for i in fresh:
        if themes.get(candidates[i]) not in recent_themes:
            return i
    if fresh:
        return fresh[0]
    # Every candidate was shown inside the window: the one shown longest ago, better rank first.
    return max(range(len(candidates)), key=lambda i: (last_seen(candidates[i]), -i))


def schedule(
    pools: Sequence[Sequence[str]],
    prior: Sequence[str | None] = (),
    themes: Mapping[str, str] = ISSUE_THEMES,
) -> list[str | None]:
    """Topics for consecutive days, each chosen with ``pick_topic`` against ``prior`` (the days
    before the first pool, oldest first) and the days already scheduled. An empty pool gives
    ``None`` for that day (no situation; the caller keeps its fallback)."""

    history: list[str | None] = list(prior)
    chosen: list[str | None] = []
    for pool in pools:
        key = pool[pick_topic(pool, history, themes)] if pool else None
        chosen.append(key)
        history.append(key)
    return chosen
