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
* the day's natal sky events (``sky_events.NatalHooks``) come before the score (K-3, K-7,
  AS-22): the solar return (transiting Sun conjunct natal Sun) first, then a planet stationing
  in conjunction with a natal point. They only re-rank contacts the scan already found, within
  ``DEFAULT_STATION_ORB`` under the same worst-case orb, so no factor is invented;
* each contact carries its timing: ``time_kind``, the in-orb window and the tight 1° peak window
  inside the day, and a closest moment only when the closest approach really falls inside it;
* at most ``MAX_TREND_TAGS`` trend contacts are kept, the heaviest by ``trend_weight``;
* trend contacts carry a weight and their ``episode`` (``transit_episodes``); generational
  outer-to-outer contacts are dropped. The episode is the C2c contract: one aspect point, every
  pass with its motion, and a key that is the same on every day of the episode.

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
* Nodes and Chiron are never read for a non-exact time.
* Houses and angles (C2b, ``house_confidence``). Labels come from a ``HouseFrame`` sampled over
  the birth-time error (``birth_time_error_minutes``: ±``EXACT_TIME_ERROR_MINUTES`` for a typed
  time, the window's half-width for ``approximate_time``) and the birthplace margin; a label
  that changes anywhere in that range is dropped. ``approximate_night`` and ``date_only`` get no
  frame. Without the birthplace coordinates there is no frame either (fail closed). Each contact
  carries ``transit_house`` (the natal house the transiting body passes through during the
  contact's in-day window, the house that names the factor's area, PL-20), ``natal_house`` (the
  touched natal point's house) and ``ruled_houses`` (the houses the touched natal planet rules;
  decision 1.2: a ruler only adds houses, it never picks a meaning). Ranking does not read them.
  The ascendant and midheaven are natal points only for ``exact_time``, as ``(low, high)``
  domains over the same range, under the worst-case orb rule: an angle contact counts only when
  it holds for every birth time in the range, so with the ±15 min default it is rare (the angle
  itself spreads several degrees); a more reliable time level would be needed to see more.
* ``tradition_not_western``: Jyotish stays natal-only. Its transit practice (gochara) counts
  sidereal whole-sign houses from the natal Moon and graha drishti, not the tropical Ptolemaic
  aspects and versioned orbs used here, and the planner keeps Jyotish readings natal-only; mixing
  the two systems would give a sidereal chart Western contacts it does not use. The transiting
  Moon's sign is sky-only and is still returned.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from app.domains.astro.aspects import (
    ASPECTS,
    TRANSIT_ORB_VERSION,
    angular_distance,
    orb_bounds,
    transit_orb_limit,
)
from app.domains.astro.engine import NatalChartEngine, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitPhase,
    ZodiacSign,
)
from app.domains.astro.sky_events import DEFAULT_STATION_ORB, NatalHooks, day_sky_events
from app.domains.daily.house_confidence import (
    EXACT_TIME_ERROR_MINUTES,
    Birthplace,
    ChartAngle,
    HouseFrame,
    HouseLabels,
    house_frame,
)

if TYPE_CHECKING:
    from app.domains.daily.transit_episodes import TransitEpisode

DAILY_SELECTION_VERSION = "daily-sky-selection-v4"
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
# Two closest approaches of one episode count separately only when the orb rises by at least
# this much between them; it keeps the true node's short wobble from listing every dip.
TREND_MIN_PROMINENCE = 0.2
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

# A contact's natal point: a body, or an angle (exact time only, C2b).
NatalPoint = BodyName | ChartAngle
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
NATAL_WEIGHT: dict[BodyName | ChartAngle, float] = {
    ChartAngle.ASCENDANT: 2.0,
    ChartAngle.MIDHEAVEN: 2.0,
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
# At most this many trend tags ("Xu hướng hiện tại") a day, the top ones by ``trend_weight``
# (AS-8/PL-23: one or two tags). ``day_tone`` still reads every trend contact in orb.
MAX_TREND_TAGS = 2


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


class SkyEventPriority(StrEnum):
    """A natal sky event carried by a contact; it ranks before any score (K-3, K-7, AS-22)."""

    SOLAR_RETURN = "solar_return"
    NATAL_STATION = "natal_station"


# Lower comes first: the solar return, then a station on a natal point, then everything else.
_SKY_EVENT_RANK: dict[SkyEventPriority | None, int] = {
    SkyEventPriority.SOLAR_RETURN: 0,
    SkyEventPriority.NATAL_STATION: 1,
    None: 2,
}


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
    natal_body: NatalPoint
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
    transit_house: int | None = None
    natal_house: int | None = None
    ruled_houses: tuple[int, ...] = ()
    sky_event: SkyEventPriority | None = None

    @property
    def preferred_natal(self) -> bool:
        return self.natal_body in PREFERRED_NATAL_BODIES

    @property
    def natal_points(self) -> tuple[NatalPoint, ...]:
        """The natal point plus those of contacts merged into this one (AS-4)."""

        return (self.natal_body, *(item.natal_body for item in self.merged))

    @property
    def waking(self) -> bool:
        """No in-day peak, or a peak between 06:00 and 23:00 Vietnam time."""

        if self.closest_at is None:
            return True
        return WAKING_START_HOUR <= self.closest_at.hour < WAKING_END_HOUR


@dataclass(frozen=True, slots=True)
class TrendContact:
    contact: DayContact
    weight: float
    episode: TransitEpisode | None = None


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
    houses: HouseLabels | None = None


NatalDomains = dict[NatalPoint, tuple[float, float]]


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


def birth_time_error_minutes(
    eligibility: ContactEligibility, *, exact_time_error_minutes: float = EXACT_TIME_ERROR_MINUTES
) -> float | None:
    """Half-width of the birth-time range house labels must hold over; ``None``: no houses."""

    if eligibility is ContactEligibility.EXACT_TIME:
        return exact_time_error_minutes
    if eligibility is ContactEligibility.APPROXIMATE_TIME:
        return APPROXIMATE_HALF_WIDTH_DAYS * 1440.0
    return None


def daily_house_frame(
    engine: NatalChartEngine,
    chart: NatalChart,
    birthplace: Birthplace | None,
    *,
    birth_timezone: str | None = None,
    exact_time_error_minutes: float = EXACT_TIME_ERROR_MINUTES,
) -> HouseFrame | None:
    """The chart's ``HouseFrame`` for its precision (``None`` when no house may be read)."""

    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    error = birth_time_error_minutes(eligibility, exact_time_error_minutes=exact_time_error_minutes)
    return house_frame(engine, chart, birthplace, time_error_minutes=error)


def natal_domains(
    engine: NatalChartEngine,
    chart: NatalChart,
    *,
    birth_timezone: str | None = None,
    houses: HouseFrame | None = None,
) -> NatalDomains:
    """Natal points to scan, each as a ``(low, high)`` longitude domain (a point when exact).

    With an exact time and a ``houses`` frame the ascendant and midheaven are added as domains
    over the frame's birth-time and place range (C2b, K-6).
    """

    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    if eligibility is ContactEligibility.TRADITION_NOT_WESTERN:
        return {}
    if eligibility is ContactEligibility.EXACT_TIME:
        points: NatalDomains = {
            body.body: (body.longitude, body.longitude)
            for body in chart.bodies
            if body.body is not BodyName.SOUTH_NODE
        }
        if houses is not None:
            for angle in ChartAngle:
                points[angle] = houses.angle_domain(angle)
        return points
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
    transit_body: BodyName, kind: str, natal_body: NatalPoint, eligibility: ContactEligibility
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
    houses: HouseFrame | None = None,
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
        domains = natal_domains(engine, chart, birth_timezone=birth_timezone, houses=houses)
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
                    raw.append(_with_houses(contact, houses, sky, start, step))
    return tuple(sorted(_merge_same_events(_score_all(raw), chart), key=rank_key))


def _with_houses(
    contact: DayContact,
    houses: HouseFrame | None,
    sky: dict[int, dict[BodyName, BodyPosition]],
    start: datetime,
    step: timedelta,
) -> DayContact:
    """Stable house labels for a contact (C2b); unchanged when there is no frame.

    ``transit_house`` holds only when every sample of the in-day window puts the transiting body
    in the same stable natal house: a Moon that crosses a cusp during the contact gets none.
    """

    if houses is None:
        return contact
    first = math.floor((contact.window_start.astimezone(UTC) - start) / step)
    last = math.ceil((contact.window_end.astimezone(UTC) - start) / step)
    labels = {
        houses.house_of(sky[index][contact.transit_body].longitude)
        for index in range(first, last + 1)
        if index in sky
    }
    transit_house = labels.pop() if len(labels) == 1 else None
    return replace(
        contact,
        transit_house=transit_house,
        natal_house=houses.natal_house(contact.natal_body),
        ruled_houses=houses.ruled_houses(contact.natal_body),
    )


def _day_contact(
    engine: NatalChartEngine,
    chart: NatalChart,
    transit_body: BodyName,
    kind: str,
    exact_angle: float,
    natal_body: NatalPoint,
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


def rank_key(contact: DayContact) -> tuple[int, float, bool, float, str]:
    """A natal sky event first (``SkyEventPriority``), then the higher score, then a waking-hours
    peak (K-5), then the tighter orb, then the id. Without events this is the score order."""

    return (
        _SKY_EVENT_RANK[contact.sky_event],
        -contact.score,
        not contact.waking,
        contact.min_orb,
        contact.id,
    )


def mark_sky_events(
    contacts: tuple[DayContact, ...], hooks: NatalHooks | None
) -> tuple[DayContact, ...]:
    """Tag the contacts that carry the day's natal sky events and re-sort by ``rank_key``.

    The solar return is the transiting Sun conjunct natal Sun; a natal station is the stationing
    planet conjunct the natal point it stations on. A contact is tagged only when it is that
    conjunction and its worst-case in-day orb is within ``DEFAULT_STATION_ORB``, so the hook never
    adds a point or a precision the scan did not allow (AS-1). A merged factor carries the event
    of any contact folded into it (AS-4).
    """

    if hooks is None:
        return contacts
    wanted: dict[tuple[BodyName, str], SkyEventPriority] = {
        (item.station.body, item.natal_point): SkyEventPriority.NATAL_STATION
        for item in hooks.stations
    }
    if hooks.solar_return is not None:
        wanted[(BodyName.SUN, BodyName.SUN.value)] = SkyEventPriority.SOLAR_RETURN

    def event_of(item: DayContact) -> SkyEventPriority | None:
        if item.kind != "conjunction" or item.min_orb > DEFAULT_STATION_ORB:
            return None
        return wanted.get((item.transit_body, item.natal_body.value))

    marked = []
    for item in contacts:
        parts = (item, *item.merged)
        tagged = [(event, part) for part in parts if (event := event_of(part)) is not None]
        if tagged:
            event, head = min(tagged, key=lambda pair: _SKY_EVENT_RANK[pair[0]])
            if head is not item:
                # The event contact leads its merged factor, so the factor is named by it.
                head = replace(head, merged=tuple(part for part in parts if part is not head))
                head = replace(head, score=score_contact(head))
            item = replace(head, sky_event=event)
        marked.append(item)
    return tuple(sorted(marked, key=rank_key))


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

    Pass 0 takes the contacts tagged with a natal sky event (``mark_sky_events``: the solar
    return, then a station on a natal point), on any natal point. Pass 1 takes one contact per
    natal Sun/Moon/Mercury/Venus/Mars. With ``allow_fallback``, pass 2 takes a second contact on
    one of those points and pass 3 any other natal point (AS-11). Trend-tier contacts are picked
    only when they perfect today (K-2) or carry a sky event (a slow planet stationing on a natal
    point, K-7). The Moon and slow caps hold in every pass.
    """

    ranked = sorted(
        (
            item
            for item in contacts
            if item.tier is not SkyTier.TREND or item.exact_today or item.sky_event is not None
        ),
        key=rank_key,
    )
    chosen: list[DayContact] = []
    used: set[NatalPoint] = set()

    def allowed(contact: DayContact) -> bool:
        if contact in chosen:
            return False
        if contact.transit_body in MOON_BODIES:
            return sum(item.transit_body in MOON_BODIES for item in chosen) < MAX_MOON_PICKS
        if contact.transit_body not in FAST_BODIES:
            return sum(item.transit_body not in FAST_BODIES for item in chosen) < MAX_SLOW_PICKS
        return True

    passes: tuple[Callable[[DayContact], bool], ...] = (
        lambda item: item.sky_event is not None,
        lambda item: item.preferred_natal and not used & set(item.natal_points),
        lambda item: item.preferred_natal,
        lambda item: not used & set(item.natal_points),
    )
    for accept in passes if allow_fallback else passes[:2]:
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


def moon_context(
    engine: NatalChartEngine,
    chart: NatalChart,
    local_date: date,
    *,
    houses: HouseFrame | None = None,
) -> MoonContext:
    """Transiting Moon at local noon (natal house only when ``houses`` holds it over the
    birth-time range, C2b) and its sign at the day's start and end, with the sign change time
    (to the minute) when it changes (K-10)."""

    observed_at = datetime.combine(local_date, time(hour=12), tzinfo=DAILY_TIMEZONE)
    moon = engine.transiting_position(BodyName.MOON, observed_at, chart.config)
    house = houses.house_of(moon.longitude) if houses is not None else None
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


def cap_trend_tags(
    ranked: tuple[DayContact, ...], limit: int = MAX_TREND_TAGS
) -> tuple[DayContact, ...]:
    """The first ``limit`` of trend contacts already ranked by ``trend_weight`` (AS-8/PL-23).

    Only cuts; the order is the caller's ranking and is never changed here.
    """

    if limit < 1:
        raise ValueError("limit must be at least 1")
    return ranked[:limit]


def _contact_domain(
    engine: NatalChartEngine,
    chart: NatalChart,
    contact: DayContact,
    domains: NatalDomains | None,
    birth_timezone: str | None,
) -> tuple[float, float]:
    if domains is None:
        if isinstance(contact.natal_body, ChartAngle):
            raise ValueError("an angle contact needs the domains it was scanned with")
        domains = natal_domains(engine, chart, birth_timezone=birth_timezone)
    if contact.natal_body is BodyName.SOUTH_NODE and BodyName.SOUTH_NODE not in domains:
        node = next(domains[body] for body in NODE_BODIES if body in domains)
        return node[0] + 180.0, node[1] + 180.0
    return domains[contact.natal_body]


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
    birthplace: Birthplace | None = None,
    exact_time_error_minutes: float = EXACT_TIME_ERROR_MINUTES,
) -> DailySkySelection:
    """Select the day's sky for one natal chart and Vietnam-local date.

    ``birth_timezone`` is the birthplace IANA zone; it only matters for an approximate birth
    time, to recognise the stored window (see ``contact_eligibility``). ``birthplace`` is the
    chart's birthplace coordinates, held in memory only; without it no house label or angle is
    read (C2b). ``exact_time_error_minutes`` is the error assumed for a typed time.
    """

    from app.domains.daily.transit_episodes import trend_episode  # imports this module

    eligibility = contact_eligibility(chart, birth_timezone=birth_timezone)
    houses = daily_house_frame(
        engine,
        chart,
        birthplace,
        birth_timezone=birth_timezone,
        exact_time_error_minutes=exact_time_error_minutes,
    )
    domains = natal_domains(engine, chart, birth_timezone=birth_timezone, houses=houses)
    contacts = scan_day(
        engine,
        chart,
        local_date,
        sample_minutes=sample_minutes,
        domains=domains,
        birth_timezone=birth_timezone,
        houses=houses,
    )
    if contacts:
        contacts = mark_sky_events(contacts, day_sky_events(engine, local_date, chart).natal)
    trend_contacts = tuple(
        sorted(
            (item for item in contacts if item.tier is SkyTier.TREND),
            key=lambda item: (-trend_weight(item), item.min_orb, item.id),
        )
    )
    trend = tuple(
        TrendContact(
            contact=contact,
            weight=trend_weight(contact),
            episode=trend_episode(
                engine, chart, contact, local_date, max_scan_days=max_scan_days, domains=domains
            )
            if include_trend_windows
            else None,
        )
        for contact in cap_trend_tags(trend_contacts)
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
        moon=moon_context(engine, chart, local_date, houses=houses),
        houses=houses.labels() if houses is not None else None,
    )
