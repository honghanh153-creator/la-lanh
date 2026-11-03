"""Select the day's sky factors for the Daily v2 note (pure, additive engine layer).

The current Daily note ranks one transit by exactness and natal weight at a single instant, so a
slow contact that stays in orb for months wins day after day. This module selects instead from
what changes *within the user's day*:

* the day is the Vietnam civil day (``Asia/Ho_Chi_Minh``), sampled every 30 minutes;
* tiers follow the contact's measured length, not only the planet (AS-7): ``today`` holds
  transiting-Moon contacts and fast contacts that perfect today, ``days`` fast contacts that
  last at most ``DAYS_TIER_MAX_DAYS``, ``weeks`` longer fast contacts (a slow or stationary
  Mercury…Mars), and ``trend`` Jupiter and slower bodies (incl. Chiron and the nodes) plus any
  fast contact longer than ``WEEKS_TIER_MAX_DAYS``;
* picks are ranked by a documented weighted score (``score_contact``), at most two Moon picks
  and one slow pick a day, and one sky event touching two aspected natal points is one factor;
* each contact carries its timing: ``time_kind``, the in-orb window and the tight 1° peak window
  inside the day, and a closest moment only when the closest approach really falls inside it;
* trend contacts carry their whole in-orb window across retrograde passes (C2c), with the orb at
  each closest date and a weight; generational outer-to-outer contacts are dropped.

It returns geometry and labels only (no copy, no persistence, no logging) and is deterministic
for a chart and date. Nothing in the request path calls it yet; the Daily service and planner
wiring come later.

Precision (``ContactEligibility``, AS-1/PL-14). A non-exact birth time still gets personal
factors, but only those that hold over the whole uncertain birth interval:

* ``exact_time``: every natal body as a point; natal house of the transiting Moon is read.
* ``approximate_time``: the chart is calculated at the window's stored midpoint and the five
  narrow-window midpoints (03, 08, 12, 15, 19 h) lie within ``APPROXIMATE_HALF_WIDTH_DAYS`` of
  their window's edges. Natal Sun…Pluto and the natal Moon are bounded over that interval with
  ``NatalChartEngine.longitude_domains`` and a contact counts only while its worst-case orb
  (``orb_bounds``) is inside the limit; the natal Moon gets ``NATAL_MOON_WINDOW_EXTRA_ORB`` on
  top because it spreads ~3° over the window.
* ``approximate_night``: the "Đêm" window, stored at 23:00 on the entered date. Before the
  "Rạng sáng 00-06h" option (PL-37) it read "sau 22h" and people born after midnight picked it
  too, so a stored night record can be anywhere on that civil date. It is read like
  ``date_only`` (no natal Moon) over ``NIGHT_HALF_WIDTH_DAYS`` around the stored instant. Any
  approximate chart whose window cannot be recognised falls back to this rule (fail closed, see
  ``contact_eligibility``).
* ``date_only``: as above over the engine's ±14 h birth-date interval, natal Sun…Pluto only; the
  natal Moon can sit anywhere in a ~13° band, so contacts to it would be invented precision.
* Houses, angles, nodes and Chiron are never read for a non-exact time.
* ``tradition_not_western``: Jyotish stays natal-only. Its transit practice (gochara) counts
  sidereal whole-sign houses from the natal Moon and graha drishti, not the tropical Ptolemaic
  aspects and versioned orbs used here, and the planner keeps Jyotish readings natal-only; mixing
  the two systems would give a sidereal chart Western contacts it does not use. The transiting
  Moon's sign is sky-only and is still returned.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domains.astro.aspects import (
    ASPECTS,
    TRANSIT_ORB_VERSION,
    angular_distance,
    orb_bounds,
    transit_orb_limit,
)
from app.domains.astro.engine import NatalChartEngine, house_for_longitude, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitPhase,
    ZodiacSign,
)

DAILY_SELECTION_VERSION = "daily-sky-selection-v2"
DAILY_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_SAMPLE_MINUTES = 30
DEFAULT_PICK_LIMIT = 3
# One "exact" threshold for both ``phase`` and ``exact_today`` (AS-13); it is the engine's own
# ``_transit_phase`` threshold. A contact is exact only at its in-day closest approach.
EXACT_ORB = 0.2
# The tight orb (AS-15) used for ranking and time chips; the versioned wide orb still defines
# whether a contact is in effect at all.
PEAK_ORB = 1.0
MAX_MOON_PICKS = 2
MAX_SLOW_PICKS = 1
# Two contacts of one transiting body to two natal points in aspect, peaking this close, are
# one sky event (AS-4).
MERGE_WINDOW = timedelta(hours=3)
# Waking hours in Vietnam time: a tie-break between equally scored picks (K-5).
WAKING_START_HOUR = 6
WAKING_END_HOUR = 23
# Tier by measured in-orb length (AS-7).
DAYS_TIER_MAX_DAYS = 7.0
WEEKS_TIER_MAX_DAYS = 45.0
SPAN_STEP = timedelta(hours=6)
# The narrow approximate-window midpoints stored by the birth service (03, 08, 12, 15, 19 h
# local) are at most 3 h from their window's edges (00-06, 06-10, 10-14, 14-18, 18-22 h).
APPROXIMATE_HALF_WIDTH_DAYS = 3.0 / 24.0
DAYTIME_WINDOW_MIDPOINT_HOURS = frozenset({3, 8, 12, 15, 19})
# The night window is stored at 23:00 on the entered date. Records saved before the 00-06 h
# option existed (PL-37) also hold births from 00:00 to 06:00 that date, and the two cannot be
# told apart. The date-only interval is local noon
# ±14 h, which reaches 25 h before a 23:00 instant; ±25 h around it therefore covers the whole
# civil date with the same margin as date-only.
NIGHT_HALF_WIDTH_DAYS = (23.0 - 12.0 + 14.0) / 24.0
_UNIX_EPOCH_JULIAN_DAY = 2440587.5
NATAL_MOON_WINDOW_EXTRA_ORB = 1.0
# Day-by-day trend scan bound in each direction. A window that reaches the bound is flagged
# open on that side.
TREND_SCAN_DAYS = 900
# Two in-orb stretches separated by less than this are one window (retrograde passes, AS-2).
# Fast bodies use a shorter bridge so a contact never bridges to the same aspect from the
# other side (e.g. Mars' second square ~225 days later).
TREND_BRIDGE_DAYS = 400
BRIDGE_DAYS_BY_BODY = {
    BodyName.SUN: 0,
    BodyName.MERCURY: 60,
    BodyName.VENUS: 110,
    BodyName.MARS: 200,
}
# Two closest approaches inside one trend window count separately only when the orb rises by at
# least this much between them; it keeps the true node's short wobble from listing every dip.
TREND_MIN_PROMINENCE = 0.2
# In orb the trend scan steps by the days the body needs to move this far (at most).
TREND_IN_ORB_STEP_DEG = 0.5
# Largest geocentric |speed| in °/day (measured over 25 years with the bundled ephemeris, true
# node 0.257°/day), used to skip out-of-orb stretches safely; ``SPEED_MARGIN`` on top.
MAX_SPEED_DEG_PER_DAY = {
    BodyName.SUN: 1.02,
    BodyName.MOON: 15.4,
    BodyName.MERCURY: 2.21,
    BodyName.VENUS: 1.27,
    BodyName.MARS: 0.80,
    BodyName.JUPITER: 0.25,
    BodyName.SATURN: 0.14,
    BodyName.URANUS: 0.07,
    BodyName.NEPTUNE: 0.04,
    BodyName.PLUTO: 0.04,
    BodyName.TRUE_NODE: 0.26,
    BodyName.MEAN_NODE: 0.06,
    BodyName.CHIRON: 0.16,
}
SPEED_MARGIN = 1.5

MOON_BODIES = frozenset({BodyName.MOON})
DAYS_BODIES = frozenset({BodyName.SUN, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS})
FAST_BODIES = MOON_BODIES | DAYS_BODIES
OUTER_BODIES = frozenset({BodyName.URANUS, BodyName.NEPTUNE, BodyName.PLUTO})
NODE_BODIES = frozenset({BodyName.TRUE_NODE, BodyName.MEAN_NODE})
PREFERRED_NATAL_BODIES = (
    BodyName.SUN,
    BodyName.MOON,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
)
# Natal points read for a non-exact birth time (natal Moon only with a time window).
INTERVAL_NATAL_BODIES = (
    BodyName.SUN,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
    BodyName.JUPITER,
    BodyName.SATURN,
    BodyName.URANUS,
    BodyName.NEPTUNE,
    BodyName.PLUTO,
)
SOFT_KINDS = frozenset({"sextile", "trine"})
TENSE_KINDS = frozenset({"square", "opposition"})
HARD_KINDS = TENSE_KINDS | {"conjunction"}
HEAVY_TRANSITS = frozenset({BodyName.SATURN, BodyName.PLUTO, BodyName.NEPTUNE})
HEAVY_TARGETS = frozenset({BodyName.SUN, BodyName.MOON, BodyName.MARS})

# --- Ranking weights (K-2, K-3, AS-3, AS-14, AS-19) -------------------------------------------
# score = transit weight + natal weight
#       + PEAKS_TODAY_BONUS                      when the closest approach falls inside the day
#         + TIGHT_BONUS                          ... and comes within PEAK_ORB
#         + RARITY_FAST_BONUS / RARITY_SLOW_BONUS ... and is exact for a non-Moon body
#         + STACK_BONUS * other fast contacts on the same natal point (at most 2)
#         + TRIGGER_BONUS                        ... and an active trend contact hits that point
#       + APPLYING_BONUS                         when the contact closes in for most of the day
#                                                (never for an uncertain phase, ``phase=None``)
#       + MERGE_BONUS                            when it is one event over two natal points
#       - ASLEEP_PENALTY                         when it peaks between 23:00 and 06:00
# Bonuses for timing only apply to contacts that peak today, so a contact that runs for days
# without peaking never outranks a Moon contact peaking on a personal point; that keeps the
# top pick rotating (top-1 repeat ≤ 10%).
TRANSIT_WEIGHT = {
    BodyName.MOON: 1.0,
    BodyName.SUN: 2.0,
    BodyName.MERCURY: 1.5,
    BodyName.VENUS: 1.5,
    BodyName.MARS: 2.0,
    BodyName.JUPITER: 2.0,
    BodyName.SATURN: 2.5,
    BodyName.URANUS: 2.5,
    BodyName.NEPTUNE: 2.5,
    BodyName.PLUTO: 2.5,
}
NATAL_WEIGHT = {
    BodyName.SUN: 3.0,
    BodyName.MOON: 3.0,
    BodyName.MERCURY: 2.0,
    BodyName.VENUS: 2.0,
    BodyName.MARS: 2.0,
    BodyName.JUPITER: 1.5,
    BodyName.SATURN: 1.5,
}
DEFAULT_WEIGHT = 1.0
PEAKS_TODAY_BONUS = 2.0
TIGHT_BONUS = 1.0
RARITY_FAST_BONUS = 3.0
RARITY_SLOW_BONUS = 4.0
STACK_BONUS = 1.0
MAX_STACK = 2
TRIGGER_BONUS = 1.5
APPLYING_BONUS = 0.5
MERGE_BONUS = 0.5
# A peak between 23:00 and 06:00 loses less than one natal-weight step, so the waking-hours
# preference only reorders near-equal picks (K-5); exact ties also fall back to waking hours.
ASLEEP_PENALTY = 0.75
# Trend weight = planet * aspect * natal target (AS-8).
TREND_PLANET_WEIGHT = {
    BodyName.PLUTO: 3.0,
    BodyName.NEPTUNE: 3.0,
    BodyName.URANUS: 3.0,
    BodyName.SATURN: 3.0,
    BodyName.JUPITER: 2.0,
    BodyName.MARS: 2.0,
    BodyName.VENUS: 1.5,
    BodyName.MERCURY: 1.5,
    BodyName.SUN: 1.5,
}
ASPECT_WEIGHT = {
    "conjunction": 3.0,
    "opposition": 2.5,
    "square": 2.5,
    "trine": 2.0,
    "sextile": 1.5,
}


class SkyTier(StrEnum):
    TODAY = "today"
    DAYS = "days"
    WEEKS = "weeks"
    TREND = "trend"


class ContactEligibility(StrEnum):
    """Which precision mode produced the contacts (see the module docstring)."""

    EXACT_TIME = "exact_time"
    APPROXIMATE_TIME = "approximate_time"
    APPROXIMATE_NIGHT = "approximate_night"
    DATE_ONLY = "date_only"
    TRADITION_NOT_WESTERN = "tradition_not_western"


class TimeKind(StrEnum):
    """How a contact sits in the day (K-5, AS-5, AS-6).

    ``peaks_today``: its closest approach falls inside the day (``closest_at`` is set).
    ``starts_today`` / ``ends_today``: it enters / leaves orb during the day without peaking.
    ``in_effect_all_day``: in orb all day, part of a contact of at most ``DAYS_TIER_MAX_DAYS``.
    ``multi_day``: in orb all day, part of a longer contact (weeks or trend).
    """

    PEAKS_TODAY = "peaks_today"
    IN_EFFECT_ALL_DAY = "in_effect_all_day"
    STARTS_TODAY = "starts_today"
    ENDS_TODAY = "ends_today"
    MULTI_DAY = "multi_day"


class DayTone(StrEnum):
    """Geometry-only tone of the day (K-1).

    Computed at selection time from the chart and never stored: a tone derived from someone's
    chart is an inference about them, so it stays in memory with the selection (privacy PV-11).
    """

    LIGHT = "light"
    MIXED = "mixed"
    HEAVY = "heavy"


class PassKind(StrEnum):
    EXACT = "exact"
    CLOSEST = "closest"


@dataclass(frozen=True, slots=True)
class DayContact:
    """One transit-to-natal contact as it ran during the local day.

    Times are Vietnam time. ``min_orb`` is the in-day closest approach, interpolated between the
    30-minute samples when it falls inside the day; ``closest_at`` is set only then, so a day
    edge is never reported as a peak. For a non-exact birth time every orb is the worst case
    over the birth interval. ``window_*`` is the in-orb span inside the day and ``peak_*`` the
    span within ``PEAK_ORB``; a bound equal to the day's start or end means the span continues
    past it. ``span_days`` is the measured length of the whole contact for Sun…Mars (``None``
    for the Moon, slow bodies, and fast contacts longer than ``WEEKS_TIER_MAX_DAYS``).

    ``phase`` is ``None`` when it is uncertain (event spec §4): for a non-exact birth time the
    phase read from the worst-case orb must agree with the phase each end of the natal domain
    would get as a point, otherwise the copy must not state a phase and the applying bonus is
    not given.
    """

    id: str
    transit_body: BodyName
    kind: str
    exact_angle: float
    natal_body: BodyName
    tier: SkyTier
    min_orb: float
    orb_limit: float
    closest_at: datetime | None
    phase: TransitPhase | None
    exact_today: bool
    time_kind: TimeKind
    window_start: datetime
    window_end: datetime
    peak_start: datetime | None = None
    peak_end: datetime | None = None
    span_days: float | None = None
    stack: int = 0
    triggers_trend: tuple[str, ...] = ()
    merged: tuple[DayContact, ...] = ()
    score: float = 0.0

    @property
    def preferred_natal(self) -> bool:
        return self.natal_body in PREFERRED_NATAL_BODIES

    @property
    def natal_points(self) -> tuple[BodyName, ...]:
        """The natal point plus those of contacts merged into this one (AS-4)."""

        return (self.natal_body, *(item.natal_body for item in self.merged))

    @property
    def waking(self) -> bool:
        """No in-day peak, or a peak between 06:00 and 23:00 Vietnam time."""

        if self.closest_at is None:
            return True
        return WAKING_START_HOUR <= self.closest_at.hour < WAKING_END_HOUR


@dataclass(frozen=True, slots=True)
class TrendPass:
    """One closest approach in a trend window, with its orb (AS-16)."""

    date: date
    orb: float
    kind: PassKind


@dataclass(frozen=True, slots=True)
class TrendWindow:
    """Local dates a slow contact stays in orb (sampled at local noon) around today.

    In-orb stretches separated by less than the body's bridge (``TREND_BRIDGE_DAYS`` for slow
    bodies) form one window, so every retrograde pass is in ``passes`` (AS-2). ``*_open`` means
    the scan hit ``TREND_SCAN_DAYS`` on that side, so the true start or end lies further away.
    """

    start_date: date
    end_date: date
    passes: tuple[TrendPass, ...]
    start_open: bool
    end_open: bool

    @property
    def closest_dates(self) -> tuple[date, ...]:
        return tuple(item.date for item in self.passes)


@dataclass(frozen=True, slots=True)
class TrendContact:
    contact: DayContact
    window: TrendWindow | None
    weight: float


@dataclass(frozen=True, slots=True)
class MoonContext:
    """The transiting Moon: sign at local noon, and at the day's start and end (K-10)."""

    observed_at: datetime
    sign: ZodiacSign
    longitude: float
    natal_house: int | None
    sign_at_start: ZodiacSign
    sign_at_end: ZodiacSign
    sign_change_at: datetime | None


@dataclass(frozen=True, slots=True)
class DailySkySelection:
    version: str
    local_date: date
    timezone: str
    sample_minutes: int
    orb_policy_version: str
    config_hash: str
    eligibility: ContactEligibility
    tone: DayTone
    picks: tuple[DayContact, ...]
    today: tuple[DayContact, ...]
    days: tuple[DayContact, ...]
    weeks: tuple[DayContact, ...]
    trend: tuple[TrendContact, ...]
    moon: MoonContext


NatalDomains = dict[BodyName, tuple[float, float]]


def contact_eligibility(
    chart: NatalChart, *, birth_timezone: str | None = None
) -> ContactEligibility:
    """Which precision mode applies to this chart (see the module docstring).

    ``NatalChart`` does not carry the approximate window it was built from, only the stored
    midpoint instant (``julian_day_ut``). The window is therefore keyed on the midpoint's local
    hour in the birthplace zone (``birth_timezone``, default ``Asia/Ho_Chi_Minh``): 08, 12, 15
    or 19 h on the minute is a daytime window; 23 h, or any other instant (a foreign birthplace
    read in the wrong zone, a future window table), is treated as the night window, which is the
    wider, date-only-like rule. A caller that knows the birthplace zone should pass it.
    """

    if chart.config.tradition is not Tradition.WESTERN:
        return ContactEligibility.TRADITION_NOT_WESTERN
    if chart.time_precision is TimePrecision.EXACT:
        return ContactEligibility.EXACT_TIME
    if chart.time_precision is TimePrecision.APPROXIMATE:
        zone = ZoneInfo(birth_timezone) if birth_timezone else DAILY_TIMEZONE
        stored = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            days=chart.julian_day_ut - _UNIX_EPOCH_JULIAN_DAY
        )
        local = (stored + timedelta(seconds=30)).astimezone(zone)
        if local.minute == 0 and local.hour in DAYTIME_WINDOW_MIDPOINT_HOURS:
            return ContactEligibility.APPROXIMATE_TIME
        return ContactEligibility.APPROXIMATE_NIGHT
    return ContactEligibility.DATE_ONLY


def natal_domains(
    engine: NatalChartEngine, chart: NatalChart, *, birth_timezone: str | None = None
) -> NatalDomains:
    """Natal points to scan, each as a ``(low, high)`` longitude domain (a point when exact)."""

    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    if eligibility is ContactEligibility.TRADITION_NOT_WESTERN:
        return {}
    if eligibility is ContactEligibility.EXACT_TIME:
        return {
            body.body: (body.longitude, body.longitude)
            for body in chart.bodies
            if body.body is not BodyName.SOUTH_NODE
        }
    if eligibility is ContactEligibility.APPROXIMATE_TIME:
        domains = engine.longitude_domains(chart, half_width_days=APPROXIMATE_HALF_WIDTH_DAYS)
        targets: tuple[BodyName, ...] = (*INTERVAL_NATAL_BODIES, BodyName.MOON)
    elif eligibility is ContactEligibility.APPROXIMATE_NIGHT:
        domains = engine.longitude_domains(chart, half_width_days=NIGHT_HALF_WIDTH_DAYS)
        targets = INTERVAL_NATAL_BODIES
    else:
        domains = engine.longitude_domains(chart)
        targets = INTERVAL_NATAL_BODIES
    return {body: domains[body] for body in targets if body in domains}


def contact_orb_limit(
    transit_body: BodyName, kind: str, natal_body: BodyName, eligibility: ContactEligibility
) -> float:
    limit = transit_orb_limit(transit_body, kind)
    if natal_body is BodyName.MOON and eligibility is ContactEligibility.APPROXIMATE_TIME:
        limit += NATAL_MOON_WINDOW_EXTRA_ORB
    return limit


def worst_orb(longitude: float, domain: tuple[float, float], exact_angle: float) -> float:
    """The aspect orb, worst case over the natal domain (the plain orb for a point)."""

    low, high = domain
    if low == high:
        return abs(angular_distance(longitude, low) - exact_angle)
    return orb_bounds((longitude, longitude), domain, exact_angle)[1]


def tier_for(
    transit_body: BodyName, *, exact_today: bool, span_days: float | None = None
) -> SkyTier:
    """Moon → today; slow bodies → trend; Sun…Mars by exactness and measured length (AS-7).

    ``span_days`` of ``None`` for a fast body means longer than ``WEEKS_TIER_MAX_DAYS``.
    """

    if transit_body in MOON_BODIES:
        return SkyTier.TODAY
    if transit_body not in DAYS_BODIES:
        return SkyTier.TREND
    if exact_today:
        return SkyTier.TODAY
    if span_days is None:
        return SkyTier.TREND
    if span_days <= DAYS_TIER_MAX_DAYS:
        return SkyTier.DAYS
    if span_days <= WEEKS_TIER_MAX_DAYS:
        return SkyTier.WEEKS
    return SkyTier.TREND


def day_bounds(local_date: date) -> tuple[datetime, datetime]:
    """``[start, end)`` of the Vietnam civil day, as UTC instants."""

    start = datetime.combine(local_date, time(), tzinfo=DAILY_TIMEZONE)
    end = datetime.combine(local_date + timedelta(days=1), time(), tzinfo=DAILY_TIMEZONE)
    return start.astimezone(UTC), end.astimezone(UTC)


def scan_day(
    engine: NatalChartEngine,
    chart: NatalChart,
    local_date: date,
    *,
    sample_minutes: int = DEFAULT_SAMPLE_MINUTES,
    domains: NatalDomains | None = None,
    birth_timezone: str | None = None,
) -> tuple[DayContact, ...]:
    """Every contact in orb at some sample of the Vietnam day, scored and sorted by ``rank_key``.

    Samples run over ``[00:00, 24:00]`` local plus one probe on each side, so a contact that
    perfects near midnight is attributed to exactly one day: the one containing its perfection.
    Generational outer-to-outer contacts are dropped (K-9) and an opposition to the natal node
    is labelled a conjunction to the south node (AS-12). Returns nothing for a Jyotish chart.
    """

    if sample_minutes <= 0 or 1440 % sample_minutes:
        raise ValueError("sample_minutes must divide a day")
    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    if eligibility is ContactEligibility.TRADITION_NOT_WESTERN:
        return ()
    if domains is None:
        domains = natal_domains(engine, chart, birth_timezone=birth_timezone)
    start, end = day_bounds(local_date)
    step = timedelta(minutes=sample_minutes)
    in_day = int((end - start) / step)
    indices = range(-1, in_day + 2)
    sky = {
        index: {
            item.body: item
            for item in engine.transiting_positions(start + index * step, chart.config)
        }
        for index in indices
    }
    middle = sky[in_day // 2]
    half_span_days = (in_day // 2 + 1) * step / timedelta(days=1)
    raw: list[DayContact] = []
    for transit_body, transit in middle.items():
        reach = abs(transit.longitude_speed) * half_span_days * 1.1 + 0.05
        for natal_body, domain in domains.items():
            if transit_body in OUTER_BODIES and natal_body in OUTER_BODIES:
                continue
            centre = (domain[0] + domain[1]) / 2.0
            spread = (domain[1] - domain[0]) / 2.0
            separation = angular_distance(transit.longitude, centre)
            for kind, exact_angle, _ in ASPECTS:
                limit = contact_orb_limit(transit_body, kind, natal_body, eligibility)
                if abs(separation - exact_angle) > limit + reach + spread:
                    continue
                orbs = {
                    index: worst_orb(sky[index][transit_body].longitude, domain, exact_angle)
                    for index in indices
                }
                ends: tuple[dict[int, float], ...] = ()
                if domain[0] != domain[1]:
                    # Each end of the natal domain as a point, for the phase check (spec §4).
                    ends = tuple(
                        {
                            index: worst_orb(
                                sky[index][transit_body].longitude, (edge, edge), exact_angle
                            )
                            for index in indices
                        }
                        for edge in domain
                    )
                contact = _day_contact(
                    engine,
                    chart,
                    transit_body,
                    kind,
                    exact_angle,
                    natal_body,
                    domain,
                    limit,
                    orbs,
                    start,
                    step,
                    in_day,
                    ends,
                )
                if contact is not None:
                    raw.append(contact)
    return tuple(sorted(_merge_same_events(_score_all(raw), chart), key=rank_key))


def _day_contact(
    engine: NatalChartEngine,
    chart: NatalChart,
    transit_body: BodyName,
    kind: str,
    exact_angle: float,
    natal_body: BodyName,
    domain: tuple[float, float],
    limit: float,
    orbs: dict[int, float],
    start: datetime,
    step: timedelta,
    in_day: int,
    ends: tuple[dict[int, float], ...] = (),
) -> DayContact | None:
    if not _in_orb_today(orbs, limit, in_day):
        return None
    timing = _series_timing(orbs, limit, in_day)
    position, peaks_today, min_orb = timing.position, timing.peaks_today, timing.min_orb
    in_start, in_end = timing.in_start, timing.in_end
    closest_at = start + position * step if peaks_today else None
    exact_today = timing.phase is TransitPhase.EXACT
    phase: TransitPhase | None = timing.phase
    if not exact_today and any(
        _series_timing(end, limit, in_day).phase is not phase for end in ends
    ):
        # The domain ends disagree with the worst case: the phase is uncertain (spec §4). An
        # exact worst case needs no check: every natal longitude is then within EXACT_ORB.
        phase = None

    # In orb at some sample of [00:00, 24:00], so the in-day window is never empty.
    window_span = _span(orbs, limit, in_day) or (0.0, float(in_day))
    span_days: float | None = None
    if transit_body in DAYS_BODIES:

        def orb_at(at: datetime) -> float:
            position_at = engine.transiting_position(transit_body, at, chart.config)
            return worst_orb(position_at.longitude, domain, exact_angle)

        span_days = _measure_span(orb_at, limit, start, step, in_day, window_span)
    tier = tier_for(transit_body, exact_today=exact_today, span_days=span_days)

    if peaks_today:
        time_kind = TimeKind.PEAKS_TODAY
    elif in_start and in_end:
        long_tiers = (SkyTier.WEEKS, SkyTier.TREND)
        time_kind = TimeKind.MULTI_DAY if tier in long_tiers else TimeKind.IN_EFFECT_ALL_DAY
    elif in_end:
        time_kind = TimeKind.STARTS_TODAY
    else:
        time_kind = TimeKind.ENDS_TODAY

    peak_span = _span(orbs, PEAK_ORB, in_day)
    if peak_span is None and peaks_today and min_orb <= PEAK_ORB:
        peak_span = (position, position)

    def local(steps: float) -> datetime:
        return (start + steps * step).astimezone(DAILY_TIMEZONE)

    shown_body, shown_kind, shown_angle = natal_body, kind, exact_angle
    if natal_body in NODE_BODIES and kind == "opposition":
        # Opposite the north node is on the south node (AS-12).
        shown_body, shown_kind, shown_angle = BodyName.SOUTH_NODE, "conjunction", 0.0
    return DayContact(
        id=f"{transit_body.value}:{shown_kind}:{shown_body.value}",
        transit_body=transit_body,
        kind=shown_kind,
        exact_angle=shown_angle,
        natal_body=shown_body,
        tier=tier,
        min_orb=round(min_orb, 4),
        orb_limit=limit,
        closest_at=local(position) if closest_at is not None else None,
        phase=phase,
        exact_today=exact_today,
        time_kind=time_kind,
        window_start=local(window_span[0]),
        window_end=local(window_span[1]),
        peak_start=local(peak_span[0]) if peak_span else None,
        peak_end=local(peak_span[1]) if peak_span else None,
        span_days=None if span_days is None else round(span_days, 2),
    )


def _in_orb_today(orbs: dict[int, float], limit: float, in_day: int) -> bool:
    """In orb at some instant of ``[00:00, 24:00)``.

    A sample before midnight in orb, or an entry between the last sample and midnight: the
    midnight sample is then strictly inside the limit. A contact that only reaches the limit at
    midnight begins the next day.
    """

    return min(orbs[index] for index in range(in_day)) <= limit or orbs[in_day] < limit


@dataclass(frozen=True, slots=True)
class _SeriesTiming:
    position: float
    peaks_today: bool
    min_orb: float
    in_start: bool
    in_end: bool
    phase: TransitPhase


def _series_timing(orbs: dict[int, float], limit: float, in_day: int) -> _SeriesTiming:
    """Closest approach, in-day peak and day phase of one sampled orb series."""

    # Closest approach over the whole sampled span, refined between its neighbours.
    best = min(orbs, key=lambda index: (orbs[index], index))
    offset, refined_orb = _refine_minimum(orbs, best)
    position = best + offset
    in_start, in_end = orbs[0] <= limit, orbs[in_day] <= limit
    peaks_today = 0 <= position < in_day
    if not peaks_today and not in_start and not in_end:
        # In orb only inside the day: the minimum is inside even if the fit says otherwise.
        position, refined_orb = float(min(max(best, 0), in_day - 1)), orbs[best]
        peaks_today = True
    if peaks_today:
        min_orb = refined_orb
    else:
        min_orb = min(orbs[index] for index in range(in_day + 1))
    if peaks_today and min_orb <= EXACT_ORB:
        phase = TransitPhase.EXACT
    elif peaks_today:
        # A near miss (station): the phase that holds for most of the day.
        phase = TransitPhase.APPROACHING if position >= in_day / 2 else TransitPhase.SEPARATING
    else:
        phase = TransitPhase.APPROACHING if orbs[in_day] < orbs[0] else TransitPhase.SEPARATING
    return _SeriesTiming(position, peaks_today, min_orb, in_start, in_end, phase)


def _span(orbs: dict[int, float], threshold: float, in_day: int) -> tuple[float, float] | None:
    """First entry and last exit of ``orb ≤ threshold`` inside ``[0, in_day]``, in steps."""

    inside = [index for index in range(in_day + 1) if orbs[index] <= threshold]
    if not inside:
        return None
    first, last = inside[0], inside[-1]
    begin = 0.0 if first == 0 else _crossing(orbs, first - 1, first, threshold)
    end = float(in_day) if last == in_day else _crossing(orbs, last, last + 1, threshold)
    return begin, end


def _crossing(orbs: dict[int, float], left: int, right: int, threshold: float) -> float:
    low, high = orbs[left], orbs[right]
    if high == low:
        return float(right)
    return left + (threshold - low) / (high - low)


def _measure_span(
    orb_at: Callable[[datetime], float],
    limit: float,
    start: datetime,
    step: timedelta,
    in_day: int,
    window: tuple[float, float],
) -> float | None:
    """Whole in-orb length in days at ``SPAN_STEP`` resolution; ``None`` past the weeks cap."""

    cap = timedelta(days=WEEKS_TIER_MAX_DAYS)
    entry = start + window[0] * step
    exit_ = start + window[1] * step
    if window[0] == 0:
        at = start
        while orb_at(at - SPAN_STEP) <= limit:
            at -= SPAN_STEP
            if start - at > cap:
                return None
        entry = at - SPAN_STEP / 2
    if window[1] == in_day:
        end = start + in_day * step
        at = end
        while orb_at(at + SPAN_STEP) <= limit:
            at += SPAN_STEP
            if at - end > cap:
                return None
        exit_ = at + SPAN_STEP / 2
    span = (exit_ - entry) / timedelta(days=1)
    return span if span <= WEEKS_TIER_MAX_DAYS else None


def _refine_minimum(samples: dict[int, float], index: int) -> tuple[float, float]:
    """``(offset in steps, orb)`` of the minimum near ``samples[index]``.

    Near its minimum the orb is a "V" (``|speed · Δt| + offset``) as long as the speed is
    steady over two steps, which holds for every fast body outside a station. The steeper
    flank fixes the speed; the other flank fixes where the V bottoms out and how deep.
    """

    centre = samples[index]
    before = samples.get(index - 1)
    after = samples.get(index + 1)
    if before is None or after is None:
        return 0.0, centre
    if before >= after:
        slope = before - centre
        if slope <= 1e-9:
            return 0.0, centre
        floor = max(0.0, (centre + after - slope) / 2.0)
        return min(1.0, (centre - floor) / slope), floor
    slope = after - centre
    if slope <= 1e-9:
        return 0.0, centre
    floor = max(0.0, (centre + before - slope) / 2.0)
    return -min(1.0, (centre - floor) / slope), floor


def score_contact(contact: DayContact) -> float:
    """The documented ranking score (see the weights at the top of the module)."""

    score = TRANSIT_WEIGHT.get(contact.transit_body, DEFAULT_WEIGHT) + NATAL_WEIGHT.get(
        contact.natal_body, DEFAULT_WEIGHT
    )
    if contact.closest_at is not None:
        score += PEAKS_TODAY_BONUS
        if contact.min_orb <= PEAK_ORB:
            score += TIGHT_BONUS
        if contact.exact_today and contact.transit_body not in MOON_BODIES:
            fast = contact.transit_body in DAYS_BODIES
            score += RARITY_FAST_BONUS if fast else RARITY_SLOW_BONUS
        score += STACK_BONUS * min(contact.stack, MAX_STACK)
        if contact.triggers_trend:
            score += TRIGGER_BONUS
    if contact.phase is TransitPhase.APPROACHING:
        score += APPLYING_BONUS
    if contact.merged:
        score += MERGE_BONUS
    if not contact.waking:
        score -= ASLEEP_PENALTY
    return round(score, 4)


def rank_key(contact: DayContact) -> tuple[float, bool, float, str]:
    """Higher score first, then a waking-hours peak (K-5), then the tighter orb, then the id."""

    return (-contact.score, not contact.waking, contact.min_orb, contact.id)


def _score_all(contacts: list[DayContact]) -> list[DayContact]:
    """Annotate stacks (AS-19) and trend triggers (AS-3), then score."""

    fast = [item for item in contacts if item.tier is not SkyTier.TREND]
    trend = [item for item in contacts if item.tier is SkyTier.TREND]
    scored = []
    for item in contacts:
        stack = triggers = None
        if item.tier is not SkyTier.TREND:
            stack = sum(
                1 for other in fast if other is not item and other.natal_body is item.natal_body
            )
            triggers = tuple(
                sorted(
                    other.id
                    for other in trend
                    if other.natal_body is item.natal_body and other is not item
                )
            )
        annotated = replace(item, stack=stack or 0, triggers_trend=triggers or ())
        scored.append(replace(annotated, score=score_contact(annotated)))
    return scored


def _merge_same_events(contacts: list[DayContact], chart: NatalChart) -> list[DayContact]:
    """One transiting body peaking on two aspected natal points within 3 h is one factor."""

    aspected = {(item.body_a, item.body_b) for item in chart.aspects}
    aspected |= {(b, a) for a, b in aspected}
    ranked = sorted(contacts, key=rank_key)
    consumed: set[str] = set()
    result: list[DayContact] = []
    for item in ranked:
        if item.id in consumed:
            continue
        partners = tuple(
            other
            for other in ranked
            if other is not item
            and other.id not in consumed
            and other.transit_body is item.transit_body
            and other.natal_body is not item.natal_body
            and SkyTier.TREND not in (item.tier, other.tier)
            and item.closest_at is not None
            and other.closest_at is not None
            and abs(other.closest_at - item.closest_at) <= MERGE_WINDOW
            and (item.natal_body, other.natal_body) in aspected
        )
        if partners:
            consumed.update(other.id for other in partners)
            merged = replace(item, merged=partners)
            item = replace(merged, score=score_contact(merged))
        consumed.add(item.id)
        result.append(item)
    return result


def pick_daily_factors(
    contacts: tuple[DayContact, ...],
    *,
    limit: int = DEFAULT_PICK_LIMIT,
    allow_fallback: bool = True,
) -> tuple[DayContact, ...]:
    """Up to ``limit`` factors by ``rank_key``; at most two Moon picks and one slow pick.

    Pass 1 takes one contact per natal Sun/Moon/Mercury/Venus/Mars. With ``allow_fallback``,
    pass 2 takes a second contact on one of those points and pass 3 any other natal point
    (AS-11). Trend-tier contacts are picked only when they perfect today (K-2).
    """

    ranked = sorted(
        (item for item in contacts if item.tier is not SkyTier.TREND or item.exact_today),
        key=rank_key,
    )
    chosen: list[DayContact] = []
    used: set[BodyName] = set()

    def allowed(contact: DayContact) -> bool:
        if contact in chosen:
            return False
        if contact.transit_body in MOON_BODIES:
            return sum(item.transit_body in MOON_BODIES for item in chosen) < MAX_MOON_PICKS
        if contact.transit_body not in FAST_BODIES:
            return sum(item.transit_body not in FAST_BODIES for item in chosen) < MAX_SLOW_PICKS
        return True

    passes: tuple[Callable[[DayContact], bool], ...] = (
        lambda item: item.preferred_natal and not used & set(item.natal_points),
        lambda item: item.preferred_natal,
        lambda item: not used & set(item.natal_points),
    )
    for accept in passes if allow_fallback else passes[:1]:
        for contact in ranked:
            if len(chosen) == limit:
                return tuple(chosen)
            if allowed(contact) and accept(contact):
                chosen.append(contact)
                used.update(contact.natal_points)
    return tuple(chosen)


def day_tone(picks: tuple[DayContact, ...], trend: tuple[DayContact, ...]) -> DayTone:
    """The day's tone from geometry alone (K-1); computed per request, never stored (PV-11).

    Heavy when Saturn/Pluto/Neptune conjoin, square or oppose natal Sun/Moon/Mars inside the
    trend orb, or when every pick is hard (square, opposition, or a Saturn/Pluto/Neptune
    conjunction) and one of them is not the Moon's: a day of Moon squares alone is ordinary,
    they pass within hours. "Every" rather than "most": with five aspects about a third of all
    days have two hard picks out of three, which would make most days heavy on top of the trend
    rule. Light when most picks are soft; mixed otherwise.
    """

    heavy_trend = any(
        item.transit_body in HEAVY_TRANSITS
        and item.natal_body in HEAVY_TARGETS
        and item.kind in HARD_KINDS
        for item in (*trend, *picks)
    )
    hard = sum(
        item.kind in TENSE_KINDS
        or (item.kind == "conjunction" and item.transit_body in HEAVY_TRANSITS)
        for item in picks
    )
    hard_beyond_moon = any(
        item.kind in TENSE_KINDS and item.transit_body not in MOON_BODIES for item in picks
    )
    soft = sum(item.kind in SOFT_KINDS for item in picks)
    if heavy_trend or (picks and hard == len(picks) and hard_beyond_moon):
        return DayTone.HEAVY
    if picks and soft * 2 > len(picks):
        return DayTone.LIGHT
    return DayTone.MIXED


def moon_context(engine: NatalChartEngine, chart: NatalChart, local_date: date) -> MoonContext:
    """Transiting Moon at local noon (natal house only for an exact time) and its sign at the
    day's start and end, with the sign change time (to the minute) when it changes (K-10)."""

    observed_at = datetime.combine(local_date, time(hour=12), tzinfo=DAILY_TIMEZONE)
    moon = engine.transiting_position(BodyName.MOON, observed_at, chart.config)
    house = None
    if (
        chart.time_precision is TimePrecision.EXACT
        and chart.houses is not None
        and len(chart.houses) == 12
    ):
        house = house_for_longitude(moon.longitude, chart.houses)
    start, end = day_bounds(local_date)
    last = end - timedelta(minutes=1)

    def sign_at(at: datetime) -> ZodiacSign:
        return sign_for_longitude(
            engine.transiting_position(BodyName.MOON, at, chart.config).longitude
        )

    first_sign, last_sign = sign_at(start), sign_at(last)
    change_at = None
    if first_sign is not last_sign:
        low, high = start, last
        while high - low > timedelta(minutes=1):
            middle = low + (high - low) / 2
            if sign_at(middle) is first_sign:
                low = middle
            else:
                high = middle
        change_at = high.replace(second=0, microsecond=0).astimezone(DAILY_TIMEZONE)
    return MoonContext(
        observed_at=observed_at,
        sign=moon.sign,
        longitude=moon.longitude,
        natal_house=house,
        sign_at_start=first_sign,
        sign_at_end=last_sign,
        sign_change_at=change_at,
    )


def trend_weight(contact: DayContact) -> float:
    """Planet * aspect * natal target (AS-8)."""

    return round(
        TREND_PLANET_WEIGHT.get(contact.transit_body, DEFAULT_WEIGHT)
        * ASPECT_WEIGHT.get(contact.kind, DEFAULT_WEIGHT)
        * NATAL_WEIGHT.get(contact.natal_body, DEFAULT_WEIGHT),
        4,
    )


def _contact_domain(
    engine: NatalChartEngine,
    chart: NatalChart,
    contact: DayContact,
    domains: NatalDomains | None,
    birth_timezone: str | None,
) -> tuple[float, float]:
    if domains is None:
        domains = natal_domains(engine, chart, birth_timezone=birth_timezone)
    if contact.natal_body is BodyName.SOUTH_NODE and BodyName.SOUTH_NODE not in domains:
        node = next(domains[body] for body in NODE_BODIES if body in domains)
        return node[0] + 180.0, node[1] + 180.0
    return domains[contact.natal_body]


def trend_window(
    engine: NatalChartEngine,
    chart: NatalChart,
    contact: DayContact,
    local_date: date,
    *,
    max_scan_days: int = TREND_SCAN_DAYS,
    domains: NatalDomains | None = None,
    birth_timezone: str | None = None,
) -> TrendWindow:
    """In-orb local dates around ``local_date`` for one contact, across retrograde passes.

    Sampled at local noon. In orb the scan steps by the days the body needs, at its largest
    speed, to move ``TREND_IN_ORB_STEP_DEG`` (one day for Jupiter, eight for Pluto),
    then fills every day before an exit so the edges are exact to the day; out of orb it jumps
    ahead by the days the body needs to get back into orb, so bridging a gap costs a few calls.
    Each closest approach is re-sampled daily around it. Callers may cache windows per chart and
    date; they only change daily. Today belongs to the window by construction, even when the
    contact is in orb for only part of it (its noon sample may be just outside).
    """

    domain = _contact_domain(engine, chart, contact, domains, birth_timezone)
    limit = contact.orb_limit
    bridge = BRIDGE_DAYS_BY_BODY.get(contact.transit_body, TREND_BRIDGE_DAYS)
    speed = MAX_SPEED_DEG_PER_DAY.get(contact.transit_body, 1.0) * SPEED_MARGIN
    stride = max(1, int(TREND_IN_ORB_STEP_DEG / speed))
    orbs: dict[int, float] = {}

    def orb_at(offset: int) -> float:
        if offset not in orbs:
            at = datetime.combine(
                local_date + timedelta(days=offset), time(hour=12), tzinfo=DAILY_TIMEZONE
            )
            position = engine.transiting_position(contact.transit_body, at, chart.config)
            orbs[offset] = worst_orb(position.longitude, domain, contact.exact_angle)
        return orbs[offset]

    orb_at(0)
    edges: list[tuple[int, bool]] = []
    for direction in (-1, 1):
        last_in, offset, previous_in = 0, stride, True
        closed = False
        while offset <= max_scan_days:
            orb = orb_at(direction * offset)
            if orb <= limit:
                last_in, previous_in = offset, True
                offset += stride
                continue
            if previous_in:
                # Fill the days skipped since the last in-orb sample so the exit is exact.
                for day in range(last_in + 1, offset):
                    if orb_at(direction * day) <= limit:
                        last_in = day
            previous_in = False
            if offset - last_in > bridge:
                closed = True
                break
            offset += max(1, int((orb - limit) / speed))
        if not closed:
            if previous_in:
                for day in range(last_in + 1, max_scan_days + 1):
                    if orb_at(direction * day) <= limit:
                        last_in = day
            closed = max_scan_days - last_in >= bridge and last_in < max_scan_days
        edges.append((direction * last_in, not closed))
    (start, start_open), (end, end_open) = edges
    window = {offset: orb for offset, orb in orbs.items() if start <= offset <= end}
    passes = _passes(
        window,
        limit,
        stride,
        orb_at,
        start=start,
        end=end,
        start_open=start_open,
        end_open=end_open,
    )
    return TrendWindow(
        start_date=local_date + timedelta(days=start),
        end_date=local_date + timedelta(days=end),
        passes=tuple(
            TrendPass(date=local_date + timedelta(days=day), orb=orb, kind=kind)
            for day, orb, kind in passes
        ),
        start_open=start_open,
        end_open=end_open,
    )


def _passes(
    orbs: dict[int, float],
    limit: float,
    stride: int,
    orb_at: Callable[[int], float],
    *,
    start: int,
    end: int,
    start_open: bool,
    end_open: bool,
) -> list[tuple[int, float, PassKind]]:
    """Separate closest approaches as ``(day offset, orb, kind)``, in date order."""

    offsets = sorted(orbs)
    values = [orbs[offset] for offset in offsets]
    # Outside a closed edge the orb is beyond the limit; outside an open edge it is unknown,
    # so a minimum is never claimed on an open edge.
    outside_low = float("-inf") if start_open else float("inf")
    outside_high = float("-inf") if end_open else float("inf")
    padded = [outside_low, *values, outside_high]
    minima = [
        index
        for index in range(len(values))
        if values[index] <= limit
        and padded[index] >= values[index] < padded[index + 2]
        and not (index == 0 and start_open)
        and not (index == len(values) - 1 and end_open)
    ]
    merged = True
    while merged and len(minima) > 1:
        merged = False
        for position in range(len(minima) - 1):
            first, second = minima[position], minima[position + 1]
            peak = max(values[first : second + 1])
            if peak - max(values[first], values[second]) < TREND_MIN_PROMINENCE:
                drop = second if values[second] >= values[first] else first
                minima.remove(drop)
                merged = True
                break
    if not minima:
        # A monotonic window that runs into the scan bound: report its tightest scanned day.
        minima = [min(range(len(values)), key=lambda index: (values[index], index))]
    passes = []
    for index in minima:
        # Re-sample daily around a strided minimum, then fit the V between days.
        around = range(max(start, offsets[index] - stride), min(end, offsets[index] + stride) + 1)
        best = min(around, key=lambda day: (orb_at(day), day))
        neighbours = {day: orb_at(day) for day in (best - 1, best, best + 1)}
        shift, orb = _refine_minimum(neighbours, best)
        kind = PassKind.EXACT if orb <= EXACT_ORB else PassKind.CLOSEST
        passes.append((best + round(shift), round(orb, 4), kind))
    return passes


def select_daily_sky(
    engine: NatalChartEngine,
    chart: NatalChart,
    local_date: date,
    *,
    sample_minutes: int = DEFAULT_SAMPLE_MINUTES,
    limit: int = DEFAULT_PICK_LIMIT,
    allow_fallback: bool = True,
    include_trend_windows: bool = True,
    max_scan_days: int = TREND_SCAN_DAYS,
    birth_timezone: str | None = None,
) -> DailySkySelection:
    """Select the day's sky for one natal chart and Vietnam-local date.

    ``birth_timezone`` is the birthplace IANA zone; it only matters for an approximate birth
    time, to recognise the stored window (see ``contact_eligibility``).
    """

    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    domains = natal_domains(engine, chart, birth_timezone=birth_timezone)
    contacts = scan_day(
        engine,
        chart,
        local_date,
        sample_minutes=sample_minutes,
        domains=domains,
        birth_timezone=birth_timezone,
    )
    trend_contacts = tuple(
        sorted(
            (item for item in contacts if item.tier is SkyTier.TREND),
            key=lambda item: (-trend_weight(item), item.min_orb, item.id),
        )
    )
    trend = tuple(
        TrendContact(
            contact=contact,
            window=trend_window(
                engine, chart, contact, local_date, max_scan_days=max_scan_days, domains=domains
            )
            if include_trend_windows
            else None,
            weight=trend_weight(contact),
        )
        for contact in trend_contacts
    )
    picks = pick_daily_factors(contacts, limit=limit, allow_fallback=allow_fallback)
    return DailySkySelection(
        version=DAILY_SELECTION_VERSION,
        local_date=local_date,
        timezone=DAILY_TIMEZONE.key,
        sample_minutes=sample_minutes,
        orb_policy_version=TRANSIT_ORB_VERSION,
        config_hash=chart.config_hash,
        eligibility=eligibility,
        tone=day_tone(picks, trend_contacts),
        picks=picks,
        today=tuple(item for item in contacts if item.tier is SkyTier.TODAY),
        days=tuple(item for item in contacts if item.tier is SkyTier.DAYS),
        weeks=tuple(item for item in contacts if item.tier is SkyTier.WEEKS),
        trend=trend,
        moon=moon_context(engine, chart, local_date),
    )
