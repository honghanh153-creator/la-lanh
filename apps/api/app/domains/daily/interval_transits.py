"""Transit contacts that hold over an approximate birth-time window (US-21, Daily step 2).

An approximate birth time (#660) gets a Daily from time-stable placements but no transit, so the
same few situations come back day after day. This module gives such a chart the transit contacts
that are true for **every** birth time in its window, in the same ``TransitToNatalSnapshot`` shape
as an exact chart, under ``INTERVAL_TRANSIT_POLICY``:

* The window comes from the trusted birthplace zone (Codex on the step 2 plan, point 1). The
  stored midpoint is read in that zone; 03, 08, 12, 15 or 19 h on the minute is a narrow window
  (± ``APPROXIMATE_HALF_WIDTH_DAYS``), anything else is the night window (±
  ``NIGHT_HALF_WIDTH_DAYS``). Without a zone the night window is used: reading a foreign
  birthplace in Vietnam time could turn a 23:00 birth into a 03:00 one (fail closed).
* Natal targets are Sun, Mercury, Venus and Mars, the planner's personal bodies without the
  Moon (the Moon's sign is never time-stable, ``time_stable_bodies``). A target counts only when
  its whole longitude domain over that same window lies inside one sign, so the transit never
  rests on a placement the window cannot prove.
* A contact counts only when its worst-case orb over the domain (``orb_bounds``) is inside the
  versioned limit; the snapshot's ``orb`` is that worst case, an upper bound, not a measurement.
* Phase (spec §4): exact only when the whole domain is within ``EXACT_ORB``; otherwise the exact
  point must lie outside the domain and both domain ends must agree. A contact whose phase the
  window cannot fix is dropped, because the Daily issue can depend on it (quick-reply →
  repair-reply when separating).
* Western only; nodes, Chiron, houses and angles are never read.

It is geometry only: no copy, no persistence, no logging, deterministic for a chart, zone and
instant. Nothing in the request path calls it yet.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domains.astro.aspects import (
    ASPECTS,
    TRANSIT_ORB_VERSION,
    angular_distance,
    orb_bounds,
    transit_orb_limit,
)
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitPhase,
    TransitToNatalContact,
    TransitToNatalSnapshot,
)
from app.domains.daily.sky_selection import (
    APPROXIMATE_HALF_WIDTH_DAYS,
    DAYTIME_WINDOW_MIDPOINT_HOURS,
    EXACT_ORB,
    NIGHT_HALF_WIDTH_DAYS,
)

# The policy a stored plan names when its transit contacts were proven over a window. A planner
# accepts an interval snapshot only under a version it lists explicitly (Codex point 4).
INTERVAL_TRANSIT_POLICY = f"{TRANSIT_ORB_VERSION}+interval-v1"
INTERVAL_TRANSIT_TARGETS = (BodyName.SUN, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS)
# Same step as the engine's own phase (``_transit_phase``): the orb one hour later.
_PHASE_STEP = timedelta(hours=1)
_UNIX_EPOCH_JULIAN_DAY = 2440587.5


def window_half_width_days(chart: NatalChart, birth_timezone: str | None) -> float:
    """Half-width of the birth-time window, from the stored midpoint in the birthplace zone."""

    if not birth_timezone:
        return NIGHT_HALF_WIDTH_DAYS
    try:
        zone = ZoneInfo(birth_timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return NIGHT_HALF_WIDTH_DAYS
    stored = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
        days=chart.julian_day_ut - _UNIX_EPOCH_JULIAN_DAY
    )
    local = (stored + timedelta(seconds=30)).astimezone(zone)
    if local.minute == 0 and local.hour in DAYTIME_WINDOW_MIDPOINT_HOURS:
        return APPROXIMATE_HALF_WIDTH_DAYS
    return NIGHT_HALF_WIDTH_DAYS


def _one_sign(domain: tuple[float, float]) -> bool:
    low, high = domain
    return math.floor(low / 30.0) == math.floor(high / 30.0) and high - low < 30.0


def _orb(transit: float, natal: float, exact_angle: float) -> float:
    return abs(angular_distance(transit, natal) - exact_angle)


def interval_phase(
    transit: float,
    future_transit: float,
    domain: tuple[float, float],
    exact_angle: float,
) -> TransitPhase | None:
    """The phase every natal longitude in ``domain`` agrees on, or ``None`` (spec §4)."""

    orb_min, orb_max = orb_bounds((transit, transit), domain, exact_angle)
    if orb_max <= EXACT_ORB:
        return TransitPhase.EXACT
    if orb_min <= EXACT_ORB:
        # Exact for part of the window, not for all of it; this includes the exact point lying
        # inside the domain, where approaching turns into separating.
        return None
    phases = set()
    for natal in domain:
        now = _orb(transit, natal, exact_angle)
        later = _orb(future_transit, natal, exact_angle)
        phases.add(TransitPhase.APPROACHING if later < now else TransitPhase.SEPARATING)
    return phases.pop() if len(phases) == 1 else None


def interval_transit_to_natal(
    engine: NatalChartEngine,
    chart: NatalChart,
    observed_at: datetime,
    *,
    birth_timezone: str | None,
) -> TransitToNatalSnapshot | None:
    """Window-proven contacts for a Western approximate chart; ``None`` for any other chart."""

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    if (
        chart.time_precision is not TimePrecision.APPROXIMATE
        or chart.config.tradition is not Tradition.WESTERN
    ):
        return None
    half_width = window_half_width_days(chart, birth_timezone)
    domains = engine.longitude_domains(chart, half_width_days=half_width)
    targets = {
        body: domains[body]
        for body in INTERVAL_TRANSIT_TARGETS
        if body in domains and _one_sign(domains[body])
    }
    now = engine.transiting_positions(observed_at, chart.config)
    later = {
        position.body: position.longitude
        for position in engine.transiting_positions(observed_at + _PHASE_STEP, chart.config)
    }
    contacts: list[TransitToNatalContact] = []
    for transit in now:
        for natal_body, domain in targets.items():
            # Like the engine: the first aspect in orb is the contact; a second one cannot be
            # in orb at the same time for these limits.
            for kind, exact_angle, _ in ASPECTS:
                _, worst = orb_bounds((transit.longitude, transit.longitude), domain, exact_angle)
                if worst > transit_orb_limit(transit.body, kind):
                    continue
                phase = interval_phase(transit.longitude, later[transit.body], domain, exact_angle)
                if phase is not None:
                    contacts.append(
                        TransitToNatalContact(
                            transit_body=transit.body,
                            natal_body=natal_body,
                            kind=kind,
                            exact_angle=exact_angle,
                            # Rounded up: the stored value stays an upper bound.
                            orb=math.ceil(worst * 10_000) / 10_000,
                            phase=phase,
                        )
                    )
                break
    return TransitToNatalSnapshot(
        observed_at=observed_at.astimezone(UTC),
        contacts=tuple(sorted(contacts, key=lambda item: (item.orb, item.transit_body.value))),
        orb_policy_version=INTERVAL_TRANSIT_POLICY,
        provenance=engine.provenance_for(chart.config),
        config=chart.config,
        config_hash=chart.config_hash,
    )
