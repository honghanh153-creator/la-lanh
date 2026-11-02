"""Select the day's sky factors for the Daily v2 note (pure, additive engine layer).

The current Daily note ranks one transit by exactness and natal weight at a single instant, so a
slow contact that stays in orb for months wins day after day. This module selects instead from
what changes *within the user's day*:

* the day is the Vietnam civil day (``Asia/Ho_Chi_Minh``), sampled every 30 minutes;
* ``today`` holds transiting-Moon contacts and any fast contact that perfects today;
* ``days`` holds the other Sun/Mercury/Venus/Mars contacts (they last a few days);
* ``trend`` holds Jupiter and slower bodies (incl. Chiron and the nodes), shown only as
  "Xu hướng hiện tại" with a date range, never as one of the day's picks.

It returns geometry only (no copy, no persistence) and is deterministic for a chart and date.
Nothing in the request path calls it yet; the Daily service and planner wiring come later.

Eligibility mirrors the existing Daily path. Transit contacts are produced only for Western
charts with an exact birth time: ``DailyNoteService`` builds its Sky Chapter only for
``TimePrecision.EXACT`` and the planner keeps non-exact Daily notes on the limited plan and
Jyotish readings natal-only. Without a birth time the natal Moon can sit anywhere in a ~13° band
and the house cusps are unknown, so contacts to it and house placement would be invented
precision. The transiting Moon's sign is sky-only and is still returned.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domains.astro.aspects import TRANSIT_ORB_VERSION, angular_distance, transit_orb_limit
from app.domains.astro.engine import NatalChartEngine, house_for_longitude
from app.domains.astro.models import (
    BodyName,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitPhase,
    ZodiacSign,
)

DAILY_SELECTION_VERSION = "daily-sky-selection-v1"
DAILY_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_SAMPLE_MINUTES = 30
DEFAULT_PICK_LIMIT = 3
# A fast contact whose closest approach today is under this orb counts as "exact today".
EXACT_TODAY_ORB = 0.3
# The engine's own "exact" phase threshold (``_transit_phase``).
EXACT_PHASE_ORB = 0.2
# Day-by-day trend scan bound in each direction. Pluto can hold a 2° orb for about two years
# with its retrograde loops; a window that reaches the bound is flagged open on that side.
TREND_SCAN_DAYS = 900
# Two closest approaches inside one trend window count separately only when the orb rises by at
# least this much between them; it keeps the true node's short wobble from listing every dip.
TREND_MIN_PROMINENCE = 0.2

MOON_BODIES = frozenset({BodyName.MOON})
DAYS_BODIES = frozenset({BodyName.SUN, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS})
FAST_BODIES = MOON_BODIES | DAYS_BODIES
PREFERRED_NATAL_BODIES = (
    BodyName.SUN,
    BodyName.MOON,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
)


class SkyTier(StrEnum):
    TODAY = "today"
    DAYS = "days"
    TREND = "trend"


class ContactEligibility(StrEnum):
    ELIGIBLE = "eligible"
    TIME_NOT_EXACT = "time_not_exact"
    TRADITION_NOT_WESTERN = "tradition_not_western"


@dataclass(frozen=True, slots=True)
class DayContact:
    """One transit-to-natal contact as it ran during the local day.

    ``min_orb`` and ``closest_at`` describe the closest approach inside the day. When the
    contact perfects inside the day they are interpolated between the 30-minute samples;
    otherwise they are the nearest in-day sample. ``closest_at`` is in Vietnam time.
    """

    id: str
    transit_body: BodyName
    kind: str
    exact_angle: float
    natal_body: BodyName
    tier: SkyTier
    min_orb: float
    orb_limit: float
    closest_at: datetime
    phase: TransitPhase
    exact_today: bool

    @property
    def preferred_natal(self) -> bool:
        return self.natal_body in PREFERRED_NATAL_BODIES


@dataclass(frozen=True, slots=True)
class TrendWindow:
    """Local dates a slow contact stays in orb (sampled at local noon) around today.

    ``closest_dates`` lists every separate closest approach (retrograde loops can give up to
    three). ``*_open`` means the scan hit ``TREND_SCAN_DAYS`` on that side, so the true start or
    end lies further away than the date reported.
    """

    start_date: date
    end_date: date
    closest_dates: tuple[date, ...]
    start_open: bool
    end_open: bool


@dataclass(frozen=True, slots=True)
class TrendContact:
    contact: DayContact
    window: TrendWindow | None


@dataclass(frozen=True, slots=True)
class MoonContext:
    observed_at: datetime
    sign: ZodiacSign
    longitude: float
    natal_house: int | None


@dataclass(frozen=True, slots=True)
class DailySkySelection:
    version: str
    local_date: date
    timezone: str
    sample_minutes: int
    orb_policy_version: str
    config_hash: str
    eligibility: ContactEligibility
    picks: tuple[DayContact, ...]
    today: tuple[DayContact, ...]
    days: tuple[DayContact, ...]
    trend: tuple[TrendContact, ...]
    moon: MoonContext


def contact_eligibility(chart: NatalChart) -> ContactEligibility:
    """Whether transit contacts may be read from this chart (see the module docstring)."""

    if chart.config.tradition is not Tradition.WESTERN:
        return ContactEligibility.TRADITION_NOT_WESTERN
    if chart.time_precision is not TimePrecision.EXACT:
        return ContactEligibility.TIME_NOT_EXACT
    return ContactEligibility.ELIGIBLE


def tier_for(transit_body: BodyName, *, exact_today: bool) -> SkyTier:
    if transit_body in MOON_BODIES or (transit_body in DAYS_BODIES and exact_today):
        return SkyTier.TODAY
    if transit_body in DAYS_BODIES:
        return SkyTier.DAYS
    return SkyTier.TREND


def day_bounds(local_date: date) -> tuple[datetime, datetime]:
    """``[start, end)`` of the Vietnam civil day, as UTC instants."""

    start = datetime.combine(local_date, time(), tzinfo=DAILY_TIMEZONE)
    end = datetime.combine(local_date + timedelta(days=1), time(), tzinfo=DAILY_TIMEZONE)
    return start.astimezone(UTC), end.astimezone(UTC)


@dataclass(slots=True)
class _Series:
    transit_body: BodyName
    kind: str
    exact_angle: float
    natal_body: BodyName
    samples: dict[int, tuple[float, TransitPhase]]


def scan_day(
    engine: NatalChartEngine,
    chart: NatalChart,
    local_date: date,
    *,
    sample_minutes: int = DEFAULT_SAMPLE_MINUTES,
) -> tuple[DayContact, ...]:
    """Every contact in orb at some sample of the Vietnam day, sorted by ``rank_key``.

    Samples run over ``[00:00, 24:00)`` local plus one probe on each side, so a contact that
    perfects near midnight is attributed to exactly one day: the one containing its perfection.
    Returns nothing for an ineligible chart.
    """

    if sample_minutes <= 0 or 1440 % sample_minutes:
        raise ValueError("sample_minutes must divide a day")
    if contact_eligibility(chart) is not ContactEligibility.ELIGIBLE:
        return ()
    start, end = day_bounds(local_date)
    step = timedelta(minutes=sample_minutes)
    in_day = int((end - start) / step)
    series: dict[tuple[BodyName, str, BodyName], _Series] = {}
    for index in range(-1, in_day + 2):
        snapshot = engine.calculate_transit_to_natal(chart, start + index * step)
        for contact in snapshot.contacts:
            key = (contact.transit_body, contact.kind, contact.natal_body)
            item = series.get(key)
            if item is None:
                item = series[key] = _Series(
                    contact.transit_body, contact.kind, contact.exact_angle, contact.natal_body, {}
                )
            item.samples[index] = (contact.orb, contact.phase)
    day_contacts = [
        day_contact
        for item in series.values()
        if (day_contact := _day_contact(item, start, step, in_day)) is not None
    ]
    return tuple(sorted(day_contacts, key=rank_key))


def _day_contact(item: _Series, start: datetime, step: timedelta, in_day: int) -> DayContact | None:
    in_day_samples = {index: value for index, value in item.samples.items() if 0 <= index < in_day}
    if not in_day_samples:
        return None
    # Closest approach over the whole sampled span, refined between its neighbours.
    best = min(item.samples, key=lambda index: (item.samples[index][0], index))
    offset, refined_orb = _refine_minimum(item.samples, best)
    refined_at = start + (best + offset) * step
    if start <= refined_at < start + in_day * step:
        closest_at, min_orb = refined_at, refined_orb
        sample_phase = item.samples[best][1]
        perfects_today = True
    else:
        # The closest approach falls on another day; today only sees one flank of it.
        nearest = min(in_day_samples, key=lambda index: (in_day_samples[index][0], index))
        closest_at, min_orb = start + nearest * step, in_day_samples[nearest][0]
        sample_phase = in_day_samples[nearest][1]
        perfects_today = False
    exact_today = perfects_today and min_orb < EXACT_TODAY_ORB
    # A refined orb is never above its sample, so a sampled EXACT phase stays consistent.
    phase = TransitPhase.EXACT if min_orb <= EXACT_PHASE_ORB else sample_phase
    return DayContact(
        id=f"{item.transit_body.value}:{item.kind}:{item.natal_body.value}",
        transit_body=item.transit_body,
        kind=item.kind,
        exact_angle=item.exact_angle,
        natal_body=item.natal_body,
        tier=tier_for(item.transit_body, exact_today=exact_today),
        min_orb=round(min_orb, 4),
        orb_limit=transit_orb_limit(item.transit_body, item.kind),
        closest_at=closest_at.astimezone(DAILY_TIMEZONE),
        phase=phase,
        exact_today=exact_today,
    )


def _refine_minimum(
    samples: dict[int, tuple[float, TransitPhase]], index: int
) -> tuple[float, float]:
    """``(offset in steps, orb)`` of the minimum near ``samples[index]``.

    Near its minimum the orb is a "V" (``|speed · Δt| + offset``) as long as the speed is
    steady over two steps, which holds for every fast body outside a station. The steeper
    flank fixes the speed; the other flank fixes where the V bottoms out and how deep.
    """

    centre = samples[index][0]
    before = samples.get(index - 1)
    after = samples.get(index + 1)
    if before is None or after is None:
        return 0.0, centre
    left, right = before[0], after[0]
    if left >= right:
        slope = left - centre
        if slope <= 1e-9:
            return 0.0, centre
        floor = max(0.0, (centre + right - slope) / 2.0)
        return min(1.0, (centre - floor) / slope), floor
    slope = right - centre
    if slope <= 1e-9:
        return 0.0, centre
    floor = max(0.0, (centre + left - slope) / 2.0)
    return -min(1.0, (centre - floor) / slope), floor


def rank_key(contact: DayContact) -> tuple[bool, bool, float, str]:
    """Exact-today first, then Moon contacts, then the tighter orb, then the stable id."""

    return (
        not contact.exact_today,
        contact.transit_body not in MOON_BODIES,
        contact.min_orb,
        contact.id,
    )


def pick_daily_factors(
    contacts: tuple[DayContact, ...],
    *,
    limit: int = DEFAULT_PICK_LIMIT,
    allow_fallback: bool = True,
) -> tuple[DayContact, ...]:
    """Up to ``limit`` fast contacts, at most one per natal point.

    Natal Sun/Moon/Mercury/Venus/Mars are taken first; other natal points only fill the
    remaining slots when ``allow_fallback`` is set. Trend-tier contacts are never picked.
    """

    ranked = sorted((item for item in contacts if item.tier is not SkyTier.TREND), key=rank_key)
    chosen: list[DayContact] = []
    used: set[BodyName] = set()
    passes = (True, False) if allow_fallback else (True,)
    for preferred_only in passes:
        for contact in ranked:
            if len(chosen) == limit:
                return tuple(chosen)
            if contact.natal_body in used or (preferred_only and not contact.preferred_natal):
                continue
            chosen.append(contact)
            used.add(contact.natal_body)
    return tuple(chosen)


def moon_context(engine: NatalChartEngine, chart: NatalChart, local_date: date) -> MoonContext:
    """Transiting Moon at local noon, with its natal house when the birth time is exact."""

    observed_at = datetime.combine(local_date, time(hour=12), tzinfo=DAILY_TIMEZONE)
    moon = engine.transiting_position(BodyName.MOON, observed_at, chart.config)
    house = None
    if (
        chart.time_precision is TimePrecision.EXACT
        and chart.houses is not None
        and len(chart.houses) == 12
    ):
        house = house_for_longitude(moon.longitude, chart.houses)
    return MoonContext(
        observed_at=observed_at,
        sign=moon.sign,
        longitude=moon.longitude,
        natal_house=house,
    )


def trend_window(
    engine: NatalChartEngine,
    chart: NatalChart,
    contact: DayContact,
    local_date: date,
    *,
    max_scan_days: int = TREND_SCAN_DAYS,
) -> TrendWindow:
    """Contiguous in-orb local dates around ``local_date`` for one contact.

    One ephemeris call per scanned day (sampled at local noon): a full ±900-day scan is about
    1,800 calls, measured at ~18 ms on a developer laptop, and a typical chart has ~6 trend
    contacts whose windows end long before the bound. It is request-path safe at that cost, but
    the windows only change daily, so callers may cache them per chart and date. Today belongs
    to the window by construction (the contact was in orb during today's scan).
    """

    natal_longitude = chart.body(contact.natal_body).longitude

    def orb_on(day: date) -> float:
        at = datetime.combine(day, time(hour=12), tzinfo=DAILY_TIMEZONE)
        position = engine.transiting_position(contact.transit_body, at, chart.config)
        return abs(angular_distance(position.longitude, natal_longitude) - contact.exact_angle)

    orbs: dict[date, float] = {local_date: orb_on(local_date)}
    edges: list[tuple[date, bool]] = []
    for direction in (-1, 1):
        edge, open_edge = local_date, True
        for offset in range(1, max_scan_days + 1):
            day = local_date + timedelta(days=direction * offset)
            orb = orb_on(day)
            if orb > contact.orb_limit:
                open_edge = False
                break
            orbs[day] = orb
            edge = day
        edges.append((edge, open_edge))
    (start, start_open), (end, end_open) = edges
    days = sorted(orbs)
    return TrendWindow(
        start_date=start,
        end_date=end,
        closest_dates=_closest_dates(days, orbs, start_open=start_open, end_open=end_open),
        start_open=start_open,
        end_open=end_open,
    )


def _closest_dates(
    days: list[date], orbs: dict[date, float], *, start_open: bool, end_open: bool
) -> tuple[date, ...]:
    values = [orbs[day] for day in days]
    # Outside a closed edge the orb is beyond the limit; outside an open edge it is unknown,
    # so a minimum is never claimed on an open edge.
    outside_low = float("-inf") if start_open else float("inf")
    outside_high = float("-inf") if end_open else float("inf")
    padded = [outside_low, *values, outside_high]
    minima = [
        index
        for index in range(len(values))
        if padded[index] >= values[index] < padded[index + 2]
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
    return tuple(days[index] for index in minima)


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
) -> DailySkySelection:
    """Select the day's sky for one natal chart and Vietnam-local date."""

    eligibility = contact_eligibility(chart)
    contacts = scan_day(engine, chart, local_date, sample_minutes=sample_minutes)
    trend = tuple(
        TrendContact(
            contact=contact,
            window=trend_window(engine, chart, contact, local_date, max_scan_days=max_scan_days)
            if include_trend_windows
            else None,
        )
        for contact in sorted(
            (item for item in contacts if item.tier is SkyTier.TREND),
            key=lambda item: (not item.preferred_natal, item.min_orb, item.id),
        )
    )
    return DailySkySelection(
        version=DAILY_SELECTION_VERSION,
        local_date=local_date,
        timezone=DAILY_TIMEZONE.key,
        sample_minutes=sample_minutes,
        orb_policy_version=TRANSIT_ORB_VERSION,
        config_hash=chart.config_hash,
        eligibility=eligibility,
        picks=pick_daily_factors(contacts, limit=limit, allow_fallback=allow_fallback),
        today=tuple(item for item in contacts if item.tier is SkyTier.TODAY),
        days=tuple(item for item in contacts if item.tier is SkyTier.DAYS),
        trend=trend,
        moon=moon_context(engine, chart, local_date),
    )
