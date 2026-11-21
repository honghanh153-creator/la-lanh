""" "Hai bạn tuần này" (Hợp gu AL1 direction C, second half; off by default).

A pair the invited person chose to keep (their own box on the link page, owner AR1) gets a short
weekly card on the sender's Hôm nay: one easy thing, one thing that may snag, one thing to try.
It is computed from the current sky against both people's date-only
charts (the same reduction as a date-only reading): this week's Sun, Mercury, Venus and Mars at
midweek noon in Vietnam, against each person's Sun, Mercury, Venus and Mars. No event is
predicted and no date is named; the same pair and week always give the same card.

Keeping a pair stores the invited person's birth date (encrypted) beyond the result. That
is new personal-data collection, so it sits behind ``radar_weekly_pairs`` and the owner's
approval of its sentences (``privacy.radar.weekly.*``), and every pair is deletable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, CalculationConfig, NatalChart
from app.domains.content.copy_approval import approved_copy

WEEKLY_VERSION = "radar-weekly-v1"
VIETNAM = ZoneInfo("Asia/Ho_Chi_Minh")
TRANSITING = (BodyName.SUN, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS)
# Natal point → the theme a weekly contact to it speaks about.
POINT_THEMES = {
    BodyName.MERCURY: "communication",
    BodyName.VENUS: "attraction",
    BodyName.MARS: "pace",
    BodyName.SUN: "visibility",
}
THEMES = tuple(POINT_THEMES.values())
EASY_ANGLES = (0.0, 60.0, 120.0)
WATCH_ANGLES = (90.0, 180.0)
ORB = 3.0
# "recipient-optin" is B's own box on the link page (owner AR1, 21.11.2026), the only way a pair
# is kept. "privacy-page" is the /privacy line (owner AV1, 21.11.2026; replaced the AQ1 line
# written for the sender); "home-note" sits under the card on Hôm nay.
PRIVACY_KEYS = ("privacy-page", "home-note", "recipient-optin")


@dataclass(frozen=True)
class WeeklyCard:
    week_of: date
    easy: str | None
    watch: str | None
    try_line: str | None
    quiet: str | None


def week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def _midweek(monday: date) -> datetime:
    return datetime.combine(monday + timedelta(days=2), time(12), tzinfo=VIETNAM).astimezone(UTC)


def _separation(a: float, b: float) -> float:
    gap = abs(a - b) % 360.0
    return 360.0 - gap if gap > 180.0 else gap


def weekly_hits(
    engine: NatalChartEngine, charts: tuple[NatalChart, NatalChart], monday: date
) -> dict[str, tuple[str, float]]:
    """Best (tone, orb) per theme this week, tone "easy" or "watch"; closest contact wins."""

    sky = {
        body.body: body.longitude
        for body in engine.transiting_positions(
            _midweek(monday), CalculationConfig.western_recommended()
        )
        if body.body in TRANSITING
    }
    best: dict[str, tuple[str, float]] = {}
    for chart in charts:
        for natal in chart.bodies:
            theme = POINT_THEMES.get(natal.body)
            if theme is None:
                continue
            for longitude in sky.values():
                gap = _separation(longitude, natal.longitude)
                for tone, angles in (("easy", EASY_ANGLES), ("watch", WATCH_ANGLES)):
                    for angle in angles:
                        orb = abs(gap - angle)
                        if orb <= ORB and (theme not in best or orb < best[theme][1]):
                            best[theme] = (tone, orb)
    return best


def card_for(hits: dict[str, tuple[str, float]], monday: date) -> WeeklyCard | None:
    """The approved card for these hits, or None while any line it needs is pending."""

    easy = min(
        ((orb, theme) for theme, (tone, orb) in hits.items() if tone == "easy"), default=None
    )
    watch = min(
        ((orb, theme) for theme, (tone, orb) in hits.items() if tone == "watch"), default=None
    )
    if easy is None and watch is None:
        quiet = approved_copy("radar.weekly.quiet")
        return None if quiet is None else WeeklyCard(monday, None, None, None, quiet)
    lines = {
        "easy": approved_copy(f"radar.weekly.easy.{easy[1]}") if easy else None,
        "watch": approved_copy(f"radar.weekly.watch.{watch[1]}") if watch else None,
        "try": approved_copy(f"radar.weekly.try.{(watch or easy)[1]}"),  # type: ignore[index]
    }
    if (easy and lines["easy"] is None) or (watch and lines["watch"] is None) or not lines["try"]:
        return None
    return WeeklyCard(monday, lines["easy"], lines["watch"], lines["try"], None)


def weekly_sentences() -> dict[str, str] | None:
    """The owner-approved opt-in sentences, or None while any is pending."""

    found: dict[str, str] = {}
    for key in PRIVACY_KEYS:
        text = approved_copy(f"privacy.radar.weekly.{key}")
        if text is None:
            return None
        found[key] = text
    return found


def registry_ids() -> list[str]:
    ids = [f"radar.weekly.{part}.{theme}" for part in ("easy", "watch", "try") for theme in THEMES]
    return [*ids, "radar.weekly.quiet", *(f"privacy.radar.weekly.{key}" for key in PRIVACY_KEYS)]
