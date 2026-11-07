"""Dated sky events for one Vietnam civil day (Daily v2 "sự kiện bầu trời", issue #180).

Pure and deterministic: positions come from the engine's Swiss Ephemeris wrapper, nothing is
persisted, logged or worded for users. Every instant is a timezone-aware UTC ``datetime`` rounded to
the second; the day is the civil day in ``Asia/Ho_Chi_Minh``, ``[00:00, 24:00)`` local time.

What the day carries (gap register K-7, K-8, K-11, AS-17, AS-18, AS-22):

* **Stations** of Mercury…Pluto and Chiron: the instant the geocentric longitude speed changes
  sign, bracketed on a fixed grid and refined to well under a minute.
* **Retrograde periods** touching the day: both stations plus the shadow by longitude. The
  pre-shadow starts when the planet, still direct, last reaches the longitude of the coming direct
  station; the post-shadow ends when it first returns to the longitude of the retrograde station.
  ``None`` means the planet never left that arc between cycles.
* **Lunations**: New Moon and Full Moon (Sun-Moon elongation 0° and 180°) with the Moon's
  longitude, flagged as a solar or lunar eclipse when Swiss Ephemeris finds an eclipse maximum
  within a day of the lunation (``swe_sol_eclipse_when_glob`` / ``swe_lun_eclipse_when``).
* **Ingresses** of the Sun, Moon and Mercury…Pluto into a new sign (forward or by retrograde).
* **Void-of-course Moon**: from the Moon's last exact Ptolemaic aspect (conjunction, sextile,
  square, trine, opposition) to the Sun or Mercury…Pluto while in a sign, until it enters the next
  sign; with no aspect in the sign the void starts at the ingress. This is the modern convention
  popularised by Al H. Morrison; see The Astrology Podcast ep. 292, "Defining the Void of Course
  Moon" (https://theastrologypodcast.com/transcripts/tap-ep-292-transcript-defining-the-void-of-course-moon/).
* **Moon phase** at a reference instant (local noon by default): eight 45° octants of elongation,
  each principal phase centred on its exact angle (New Moon is -22.5° to +22.5°).
* **Natal hooks** for a chart: a station within ``station_orb`` of a natal point (conjunction), a
  lunation or eclipse within ``lunation_orb`` of a natal point by conjunction, opposition or square,
  and the solar return (the transiting Sun reaching the natal Sun's longitude) inside the day.
  Hooks look only at the day's own stations and lunations.
  Natal longitudes are the engine's ``longitude_domains`` (an interval when the birth time is
  unknown); the natal Moon is skipped when the time is unknown and the angles are used only with an
  exact time.

The zodiac follows the chart's configuration (Jyotish charts are sidereal); without a chart the
tropical Western default is used. Changing any rule above requires bumping ``SKY_EVENTS_VERSION``.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from itertools import pairwise
from zoneinfo import ZoneInfo

from app.domains.astro.engine import AYANAMSA_IDS, NatalChartEngine, sign_for_longitude
from app.domains.astro.ffi.swisseph import NativePosition, SwissEphemerisNative
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    NatalChart,
    TimePrecision,
    Tradition,
    ZodiacSign,
)

SKY_EVENTS_VERSION = "sky-events-v1"
VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_REFERENCE_TIME = time(hour=12)
DEFAULT_STATION_ORB = 1.0
DEFAULT_LUNATION_ORB = 3.0

_UNIX_EPOCH_JULIAN_DAY = 2_440_587.5
_ROOT_TOLERANCE_DAYS = 0.5 / 86_400.0
_SAMPLE_DAYS = 0.25
_ECLIPSE_WINDOW_DAYS = 1.0
_MOON_SEARCH_DAYS = 3.0

_BODY_IDS: dict[BodyName, int] = {
    BodyName.SUN: 0,
    BodyName.MOON: 1,
    BodyName.MERCURY: 2,
    BodyName.VENUS: 3,
    BodyName.MARS: 4,
    BodyName.JUPITER: 5,
    BodyName.SATURN: 6,
    BodyName.URANUS: 7,
    BodyName.NEPTUNE: 8,
    BodyName.PLUTO: 9,
    BodyName.CHIRON: 15,
}
# (scan step, search half-window) in days. The step is shorter than half of the shortest gap
# between two stations of the body (Mercury ~20 d, Venus ~40 d, Mars ~58 d, outer planets and
# Chiron > 4 months), so one step never hides two stations. The window is about one synodic
# period, which holds every retrograde cycle whose shadow can touch the day.
_STATION_SCAN: dict[BodyName, tuple[float, float]] = {
    BodyName.MERCURY: (1.0, 120.0),
    BodyName.VENUS: (3.0, 590.0),
    BodyName.MARS: (4.0, 790.0),
    BodyName.JUPITER: (6.0, 400.0),
    BodyName.SATURN: (6.0, 380.0),
    BodyName.URANUS: (6.0, 372.0),
    BodyName.NEPTUNE: (6.0, 370.0),
    BodyName.PLUTO: (6.0, 370.0),
    BodyName.CHIRON: (6.0, 375.0),
}
STATION_BODIES = tuple(_STATION_SCAN)
INGRESS_BODIES = (
    BodyName.SUN,
    BodyName.MOON,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
    BodyName.JUPITER,
    BodyName.SATURN,
    BodyName.URANUS,
    BodyName.NEPTUNE,
    BodyName.PLUTO,
)
VOID_ASPECT_BODIES = tuple(body for body in INGRESS_BODIES if body is not BodyName.MOON)
_PTOLEMAIC_ASPECTS: tuple[tuple[float, str], ...] = (
    (0.0, "conjunction"),
    (60.0, "sextile"),
    (90.0, "square"),
    (120.0, "trine"),
    (180.0, "opposition"),
    (240.0, "trine"),
    (270.0, "square"),
    (300.0, "sextile"),
)
_LUNATION_ASPECTS: tuple[tuple[float, str], ...] = (
    (0.0, "conjunction"),
    (90.0, "square"),
    (180.0, "opposition"),
)
_NATAL_SKIPPED_BODIES = frozenset({BodyName.SOUTH_NODE})

_SE_ECL_TOTAL = 4
_SE_ECL_ANNULAR = 8
_SE_ECL_PARTIAL = 16
_SE_ECL_ANNULAR_TOTAL = 32
_SE_ECL_PENUMBRAL = 64


class StationKind(StrEnum):
    RETROGRADE = "retrograde"
    DIRECT = "direct"


class RetrogradePhase(StrEnum):
    PRE_SHADOW = "pre_shadow"
    RETROGRADE = "retrograde"
    POST_SHADOW = "post_shadow"


class LunationKind(StrEnum):
    NEW_MOON = "new_moon"
    FULL_MOON = "full_moon"


class EclipseKind(StrEnum):
    SOLAR = "solar"
    LUNAR = "lunar"


class EclipseType(StrEnum):
    TOTAL = "total"
    ANNULAR = "annular"
    HYBRID = "hybrid"
    PARTIAL = "partial"
    PENUMBRAL = "penumbral"


class MoonPhase(StrEnum):
    NEW_MOON = "new_moon"
    WAXING_CRESCENT = "waxing_crescent"
    FIRST_QUARTER = "first_quarter"
    WAXING_GIBBOUS = "waxing_gibbous"
    FULL_MOON = "full_moon"
    WANING_GIBBOUS = "waning_gibbous"
    LAST_QUARTER = "last_quarter"
    WANING_CRESCENT = "waning_crescent"


_MOON_PHASES = tuple(MoonPhase)


@dataclass(frozen=True, slots=True)
class Station:
    body: BodyName
    kind: StationKind
    at: datetime
    longitude: float
    sign: ZodiacSign


@dataclass(frozen=True, slots=True)
class RetrogradePeriod:
    body: BodyName
    retrograde_station: Station
    direct_station: Station
    pre_shadow_start: datetime | None
    post_shadow_end: datetime | None
    phase: RetrogradePhase | None
    """Phase at the reference instant; ``None`` when that instant is outside the shadow span."""

    @property
    def shadow_low(self) -> float:
        return self.direct_station.longitude

    @property
    def shadow_high(self) -> float:
        return self.retrograde_station.longitude


@dataclass(frozen=True, slots=True)
class Eclipse:
    kind: EclipseKind
    type: EclipseType
    maximum_at: datetime


@dataclass(frozen=True, slots=True)
class Lunation:
    kind: LunationKind
    at: datetime
    longitude: float
    """The Moon's longitude at the exact lunation (the Sun is conjunct or opposite)."""
    sign: ZodiacSign
    eclipse: Eclipse | None


@dataclass(frozen=True, slots=True)
class Ingress:
    body: BodyName
    at: datetime
    sign: ZodiacSign
    """The sign entered."""
    retrograde: bool


@dataclass(frozen=True, slots=True)
class VoidOfCourse:
    start: datetime
    end: datetime
    moon_sign: ZodiacSign
    next_sign: ZodiacSign
    last_aspect_body: BodyName | None
    last_aspect: str | None


@dataclass(frozen=True, slots=True)
class MoonPhaseAt:
    at: datetime
    phase: MoonPhase
    elongation: float
    illuminated_fraction: float


@dataclass(frozen=True, slots=True)
class NatalStationContact:
    station: Station
    natal_point: str
    orb: float


@dataclass(frozen=True, slots=True)
class NatalLunationContact:
    lunation: Lunation
    natal_point: str
    aspect: str
    orb: float


@dataclass(frozen=True, slots=True)
class SolarReturn:
    at: datetime
    natal_sun_longitude: float
    approximate: bool
    """True when the natal Sun comes from a birth time that is not exact."""


@dataclass(frozen=True, slots=True)
class NatalHooks:
    stations: tuple[NatalStationContact, ...]
    lunations: tuple[NatalLunationContact, ...]
    solar_return: SolarReturn | None


@dataclass(frozen=True, slots=True)
class DaySkyEvents:
    version: str
    local_date: date
    timezone: str
    zodiac: str
    day_start: datetime
    day_end: datetime
    moon_phase: MoonPhaseAt
    stations: tuple[Station, ...]
    retrograde_periods: tuple[RetrogradePeriod, ...]
    lunations: tuple[Lunation, ...]
    ingresses: tuple[Ingress, ...]
    void_of_course: tuple[VoidOfCourse, ...]
    natal: NatalHooks | None


def julian_day(value: datetime) -> float:
    """UT Julian day of an aware datetime (same as Gregorian ``swe_julday``)."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return _UNIX_EPOCH_JULIAN_DAY + value.timestamp() / 86_400.0


def datetime_from_julian_day(julian_day_ut: float) -> datetime:
    """UTC datetime rounded to the second."""
    seconds = round((julian_day_ut - _UNIX_EPOCH_JULIAN_DAY) * 86_400.0)
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)


def vietnam_day_bounds(local_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(local_date, time(), tzinfo=VIETNAM_TIMEZONE)
    end = datetime.combine(local_date + timedelta(days=1), time(), tzinfo=VIETNAM_TIMEZONE)
    return start.astimezone(UTC), end.astimezone(UTC)


def _wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _round_longitude(value: float) -> float:
    return round(value % 360.0, 6)


def _find_root(
    function: Callable[[float], float],
    low: float,
    high: float,
    f_low: float,
    f_high: float,
) -> float:
    """Root of a continuous ``function`` bracketed by ``[low, high]`` (Illinois false position)."""
    if f_low == 0.0:
        return low
    if f_high == 0.0:
        return high
    if (f_low > 0.0) == (f_high > 0.0):
        raise ValueError("root is not bracketed")
    side = 0
    estimate = low
    for _ in range(80):
        if high - low < _ROOT_TOLERANCE_DAYS:
            break
        estimate = (low * f_high - high * f_low) / (f_high - f_low)
        if not low < estimate < high:
            estimate = (low + high) / 2.0
        value = function(estimate)
        if value == 0.0:
            return estimate
        if (value > 0.0) == (f_high > 0.0):
            high, f_high = estimate, value
            if side == -1:
                f_low /= 2.0
            side = -1
        else:
            low, f_low = estimate, value
            if side == 1:
                f_high /= 2.0
            side = 1
    return (low + high) / 2.0 if high - low < _ROOT_TOLERANCE_DAYS else estimate


class _Sky:
    """Memoised geocentric positions for one computation (one zodiac, one thread)."""

    def __init__(self, native: SwissEphemerisNative, *, sidereal: bool) -> None:
        self._native = native
        self._sidereal = sidereal
        self._cache: dict[tuple[int, float], NativePosition] = {}

    @property
    def native(self) -> SwissEphemerisNative:
        return self._native

    def position(self, julian_day_ut: float, body: BodyName) -> NativePosition:
        key = (_BODY_IDS[body], julian_day_ut)
        cached = self._cache.get(key)
        if cached is None:
            cached = self._native.calculate(julian_day_ut, key[0], sidereal=self._sidereal)
            self._cache[key] = cached
        return cached

    def longitude(self, julian_day_ut: float, body: BodyName) -> float:
        return self.position(julian_day_ut, body).longitude % 360.0

    def speed(self, julian_day_ut: float, body: BodyName) -> float:
        return self.position(julian_day_ut, body).longitude_speed

    def elongation(self, julian_day_ut: float) -> float:
        moon = self.longitude(julian_day_ut, BodyName.MOON)
        return (moon - self.longitude(julian_day_ut, BodyName.SUN)) % 360.0

    def crossing(self, body: BodyName, target: float, low: float, high: float) -> float:
        """Instant in ``[low, high]`` where ``body`` reaches ``target``; the arc is < 180°."""

        def offset(julian_day_ut: float) -> float:
            return _wrap180(self.longitude(julian_day_ut, body) - target)

        return _find_root(offset, low, high, offset(low), offset(high))


@dataclass(frozen=True, slots=True)
class _RawStation:
    body: BodyName
    kind: StationKind
    julian_day_ut: float


def _station(sky: _Sky, raw: _RawStation) -> Station:
    longitude = sky.longitude(raw.julian_day_ut, raw.body)
    return Station(
        body=raw.body,
        kind=raw.kind,
        at=datetime_from_julian_day(raw.julian_day_ut),
        longitude=_round_longitude(longitude),
        sign=sign_for_longitude(longitude),
    )


def _stations_between(sky: _Sky, body: BodyName, start: float, end: float) -> list[_RawStation]:
    """Stations in ``[start, end)`` scanned on a grid anchored at JD 0, so brackets never shift."""
    step = _STATION_SCAN[body][0]

    def speed(julian_day_ut: float) -> float:
        return sky.speed(julian_day_ut, body)

    found: list[_RawStation] = []
    left = math.floor(start / step) * step
    left_speed = speed(left)
    while left < end:
        right = left + step
        right_speed = speed(right)
        if (left_speed > 0.0) != (right_speed > 0.0):
            instant = _find_root(speed, left, right, left_speed, right_speed)
            if start <= instant < end:
                kind = StationKind.RETROGRADE if left_speed > 0.0 else StationKind.DIRECT
                found.append(_RawStation(body, kind, instant))
        left, left_speed = right, right_speed
    return found


def _adjacent_station(
    sky: _Sky, body: BodyName, julian_day_ut: float, *, forward: bool
) -> _RawStation:
    """Nearest station strictly after (or before) ``julian_day_ut``."""
    window = _STATION_SCAN[body][1]
    offset = 1.0 / 1440.0
    if forward:
        stations = _stations_between(sky, body, julian_day_ut + offset, julian_day_ut + window)
        if stations:
            return stations[0]
    else:
        stations = _stations_between(sky, body, julian_day_ut - window, julian_day_ut - offset)
        if stations:
            return stations[-1]
    raise ValueError(f"no {body.value} station within {window} days")  # pragma: no cover


def _shadow_edge(
    sky: _Sky,
    body: BodyName,
    target: float,
    origin: float,
    limit: float,
) -> float | None:
    """Walk from ``origin`` toward ``limit`` until ``body`` reaches ``target``; ``None`` if never.

    The body moves direct the whole way (``origin`` and ``limit`` are consecutive stations), so
    the first sign change of the wrapped offset is the crossing itself, not the ±180° wrap.
    """
    step = _STATION_SCAN[body][0] * (1.0 if limit > origin else -1.0)

    def offset(julian_day_ut: float) -> float:
        return _wrap180(sky.longitude(julian_day_ut, body) - target)

    previous, previous_offset = origin, offset(origin)
    while (limit - previous) * step > 0.0:
        current = previous + step
        if (limit - current) * step < 0.0:
            current = limit
        current_offset = offset(current)
        if (previous_offset > 0.0) != (current_offset > 0.0):
            low, high = sorted((previous, current))
            f_low, f_high = (
                (previous_offset, current_offset)
                if low == previous
                else (current_offset, previous_offset)
            )
            return _find_root(offset, low, high, f_low, f_high)
        previous, previous_offset = current, current_offset
    return None


def _retrograde_context(
    sky: _Sky, body: BodyName, start: float, end: float, reference: float
) -> tuple[list[Station], list[RetrogradePeriod]]:
    window = _STATION_SCAN[body][1]
    raw = _stations_between(sky, body, start - window, end + window)
    if not raw:  # pragma: no cover - every scanned body stations at least once a synodic period
        return [], []
    if raw[0].kind is StationKind.DIRECT:
        raw.insert(0, _adjacent_station(sky, body, raw[0].julian_day_ut, forward=False))
    stations_today = [_station(sky, item) for item in raw if start <= item.julian_day_ut < end]
    periods: list[RetrogradePeriod] = []
    for index, retrograde in enumerate(raw):
        if retrograde.kind is not StationKind.RETROGRADE:
            continue
        direct = (
            raw[index + 1]
            if index + 1 < len(raw)
            else _adjacent_station(sky, body, retrograde.julian_day_ut, forward=True)
        )
        previous_direct = (
            raw[index - 1]
            if index > 0
            else _adjacent_station(sky, body, retrograde.julian_day_ut, forward=False)
        )
        next_retrograde = (
            raw[index + 2]
            if index + 2 < len(raw)
            else _adjacent_station(sky, body, direct.julian_day_ut, forward=True)
        )
        retrograde_longitude = sky.longitude(retrograde.julian_day_ut, body)
        direct_longitude = sky.longitude(direct.julian_day_ut, body)
        pre = _shadow_edge(
            sky,
            body,
            direct_longitude,
            retrograde.julian_day_ut,
            previous_direct.julian_day_ut,
        )
        post = _shadow_edge(
            sky,
            body,
            retrograde_longitude,
            direct.julian_day_ut,
            next_retrograde.julian_day_ut,
        )
        span_start = pre if pre is not None else previous_direct.julian_day_ut
        span_end = post if post is not None else next_retrograde.julian_day_ut
        if not (span_start < end and span_end >= start):
            continue
        phase: RetrogradePhase | None = None
        if span_start <= reference < retrograde.julian_day_ut:
            phase = RetrogradePhase.PRE_SHADOW
        elif retrograde.julian_day_ut <= reference < direct.julian_day_ut:
            phase = RetrogradePhase.RETROGRADE
        elif direct.julian_day_ut <= reference <= span_end:
            phase = RetrogradePhase.POST_SHADOW
        periods.append(
            RetrogradePeriod(
                body=body,
                retrograde_station=_station(sky, retrograde),
                direct_station=_station(sky, direct),
                pre_shadow_start=None if pre is None else datetime_from_julian_day(pre),
                post_shadow_end=None if post is None else datetime_from_julian_day(post),
                phase=phase,
            )
        )
    return stations_today, periods


def _samples(start: float, end: float) -> list[float]:
    count = max(1, math.ceil((end - start) / _SAMPLE_DAYS))
    return [start + (end - start) * index / count for index in range(count + 1)]


def _eclipse(sky: _Sky, kind: LunationKind, julian_day_ut: float) -> Eclipse | None:
    search_from = julian_day_ut - 2.0 * _ECLIPSE_WINDOW_DAYS
    if kind is LunationKind.NEW_MOON:
        found = sky.native.next_solar_eclipse(search_from)
        eclipse_kind = EclipseKind.SOLAR
    else:
        found = sky.native.next_lunar_eclipse(search_from)
        eclipse_kind = EclipseKind.LUNAR
    if abs(found.maximum_julian_day_ut - julian_day_ut) > _ECLIPSE_WINDOW_DAYS:
        return None
    if found.flags & _SE_ECL_ANNULAR_TOTAL:
        eclipse_type = EclipseType.HYBRID
    elif found.flags & _SE_ECL_TOTAL:
        eclipse_type = EclipseType.TOTAL
    elif found.flags & _SE_ECL_ANNULAR:
        eclipse_type = EclipseType.ANNULAR
    elif found.flags & _SE_ECL_PARTIAL:
        eclipse_type = EclipseType.PARTIAL
    elif found.flags & _SE_ECL_PENUMBRAL:
        eclipse_type = EclipseType.PENUMBRAL
    else:  # pragma: no cover - Swiss Ephemeris always sets one type bit
        raise ValueError(f"unknown eclipse flags {found.flags}")
    return Eclipse(
        kind=eclipse_kind,
        type=eclipse_type,
        maximum_at=datetime_from_julian_day(found.maximum_julian_day_ut),
    )


def _lunations(sky: _Sky, start: float, end: float) -> list[Lunation]:
    found: list[Lunation] = []
    points = _samples(start, end)
    for kind, target in ((LunationKind.NEW_MOON, 0.0), (LunationKind.FULL_MOON, 180.0)):

        def offset(julian_day_ut: float, target: float = target) -> float:
            return _wrap180(sky.elongation(julian_day_ut) - target)

        for left, right in pairwise(points):
            f_left, f_right = offset(left), offset(right)
            # Elongation only grows; a negative→non-negative step under 90° is the lunation.
            if f_left < 0.0 <= f_right and f_right - f_left < 90.0:
                instant = _find_root(offset, left, right, f_left, f_right)
                if not start <= instant < end:
                    continue
                longitude = sky.longitude(instant, BodyName.MOON)
                found.append(
                    Lunation(
                        kind=kind,
                        at=datetime_from_julian_day(instant),
                        longitude=_round_longitude(longitude),
                        sign=sign_for_longitude(longitude),
                        eclipse=_eclipse(sky, kind, instant),
                    )
                )
    return sorted(found, key=lambda item: item.at)


def _ingress_instants(
    sky: _Sky, body: BodyName, start: float, end: float
) -> list[tuple[float, int, bool]]:
    """``(instant, new sign index, retrograde)`` for every sign change in ``[start, end)``."""
    result: list[tuple[float, int, bool]] = []
    points = _samples(start, end)
    signs = [int(sky.longitude(point, body) // 30.0) for point in points]
    for (left, left_sign), (right, right_sign) in pairwise(zip(points, signs, strict=True)):
        if left_sign == right_sign:
            continue
        retrograde = (right_sign - left_sign) % 12 == 11
        boundary = (left_sign if retrograde else right_sign) * 30.0
        instant = sky.crossing(body, boundary, left, right)
        if start <= instant < end:
            result.append((instant, right_sign, retrograde))
    return result


def _ingresses(sky: _Sky, start: float, end: float) -> list[Ingress]:
    found = [
        Ingress(
            body=body,
            at=datetime_from_julian_day(instant),
            sign=tuple(ZodiacSign)[sign_index],
            retrograde=retrograde,
        )
        for body in INGRESS_BODIES
        for instant, sign_index, retrograde in _ingress_instants(sky, body, start, end)
    ]
    return sorted(found, key=lambda item: (item.at, INGRESS_BODIES.index(item.body)))


def _last_moon_aspect(
    sky: _Sky, sign_start: float, sign_end: float
) -> tuple[float, BodyName, str] | None:
    """The latest exact Ptolemaic Moon aspect in ``[sign_start, sign_end)``."""
    latest: tuple[float, BodyName, str] | None = None
    for body in VOID_ASPECT_BODIES:

        def separation(julian_day_ut: float, body: BodyName = body) -> float:
            return (
                sky.longitude(julian_day_ut, BodyName.MOON) - sky.longitude(julian_day_ut, body)
            ) % 360.0

        first = separation(sign_start)
        # The Moon always outpaces the planets, so separation grows monotonically (< 60°/sign).
        last = first + (separation(sign_end) - first) % 360.0
        best: tuple[float, str] | None = None
        for angle, name in _PTOLEMAIC_ASPECTS:
            for target in (angle, angle + 360.0):
                if first <= target < last and (best is None or target > best[0]):
                    best = (target, name)
        if best is None:
            continue
        target, name = best

        def offset(julian_day_ut: float, target: float = target, body: BodyName = body) -> float:
            return _wrap180(separation(julian_day_ut, body) - target)

        instant = _find_root(offset, sign_start, sign_end, first - target, last - target)
        if latest is None or instant > latest[0]:
            latest = (instant, body, name)
    return latest


def _void_of_course(sky: _Sky, start: float, end: float) -> list[VoidOfCourse]:
    moon_ingresses = _ingress_instants(
        sky, BodyName.MOON, start - _MOON_SEARCH_DAYS, end + _MOON_SEARCH_DAYS
    )
    periods: list[VoidOfCourse] = []
    for (sign_start, sign_index, _), (sign_end, next_index, _) in pairwise(moon_ingresses):
        if sign_end < start or sign_start >= end:
            continue
        aspect = _last_moon_aspect(sky, sign_start, sign_end)
        void_start = aspect[0] if aspect is not None else sign_start
        if void_start >= end:
            continue
        periods.append(
            VoidOfCourse(
                start=datetime_from_julian_day(void_start),
                end=datetime_from_julian_day(sign_end),
                moon_sign=tuple(ZodiacSign)[sign_index],
                next_sign=tuple(ZodiacSign)[next_index],
                last_aspect_body=None if aspect is None else aspect[1],
                last_aspect=None if aspect is None else aspect[2],
            )
        )
    return periods


def moon_phase_for_elongation(elongation: float) -> MoonPhase:
    """Eight 45° octants of Sun-Moon elongation, each centred on its principal angle."""
    return _MOON_PHASES[int(((elongation + 22.5) % 360.0) // 45.0)]


def _moon_phase(sky: _Sky, reference: float) -> MoonPhaseAt:
    elongation = sky.elongation(reference)
    return MoonPhaseAt(
        at=datetime_from_julian_day(reference),
        phase=moon_phase_for_elongation(elongation),
        elongation=_round_longitude(elongation),
        illuminated_fraction=round((1.0 - math.cos(math.radians(elongation))) / 2.0, 4),
    )


def _max_orb_to_domain(longitude: float, low: float, high: float, angle: float) -> float:
    """Largest ``|separation - angle|`` over ``[low, high]``: the orb certain across the domain.

    The orb is the smaller circular distance to the two targets ``longitude ± angle``. Its maximum
    over an arc lies at an endpoint, at a target's antipode, or where both targets are equidistant
    (``longitude`` and its antipode), so only those points are evaluated.
    """
    targets = (longitude + angle, longitude - angle)
    width = high - low
    candidates = [low, high]
    for point in (targets[0] + 180.0, targets[1] + 180.0, longitude, longitude + 180.0):
        distance = (point - low) % 360.0
        if distance <= width:
            candidates.append(low + distance)
    return max(min(abs(_wrap180(point - target)) for target in targets) for point in candidates)


def _natal_points(engine: NatalChartEngine, chart: NatalChart) -> list[tuple[str, float, float]]:
    domains = engine.longitude_domains(chart)
    points: list[tuple[str, float, float]] = []
    for body in chart.bodies:
        if body.body in _NATAL_SKIPPED_BODIES:
            continue
        if body.body is BodyName.MOON and chart.time_precision is TimePrecision.UNKNOWN:
            continue
        low, high = domains[body.body]
        points.append((body.body.value, low, high))
    if chart.time_precision is TimePrecision.EXACT and chart.angles is not None:
        points.append(("ascendant", chart.angles.ascendant, chart.angles.ascendant))
        points.append(("midheaven", chart.angles.midheaven, chart.angles.midheaven))
    return points


def _natal_hooks(
    engine: NatalChartEngine,
    sky: _Sky,
    chart: NatalChart,
    start: float,
    end: float,
    stations: tuple[Station, ...],
    lunations: tuple[Lunation, ...],
    *,
    station_orb: float,
    lunation_orb: float,
) -> NatalHooks:
    points = _natal_points(engine, chart)
    station_contacts = [
        NatalStationContact(station=station, natal_point=name, orb=round(orb, 4))
        for station in stations
        for name, low, high in points
        if (orb := _max_orb_to_domain(station.longitude, low, high, 0.0)) <= station_orb
    ]
    lunation_contacts: list[NatalLunationContact] = []
    for lunation in lunations:
        for name, low, high in points:
            for angle, aspect in _LUNATION_ASPECTS:
                orb = _max_orb_to_domain(lunation.longitude, low, high, angle)
                if orb <= lunation_orb:
                    lunation_contacts.append(
                        NatalLunationContact(
                            lunation=lunation, natal_point=name, aspect=aspect, orb=round(orb, 4)
                        )
                    )
    natal_sun = chart.body(BodyName.SUN).longitude
    solar_return: SolarReturn | None = None

    def offset(julian_day_ut: float) -> float:
        return _wrap180(sky.longitude(julian_day_ut, BodyName.SUN) - natal_sun)

    f_start, f_end = offset(start), offset(end)
    if f_start <= 0.0 < f_end and f_end - f_start < 90.0:
        instant = _find_root(offset, start, end, f_start, f_end)
        if instant < end:
            solar_return = SolarReturn(
                at=datetime_from_julian_day(instant),
                natal_sun_longitude=_round_longitude(natal_sun),
                approximate=chart.time_precision is not TimePrecision.EXACT,
            )
    return NatalHooks(
        stations=tuple(sorted(station_contacts, key=lambda item: (item.orb, item.natal_point))),
        lunations=tuple(
            sorted(lunation_contacts, key=lambda item: (item.orb, item.natal_point, item.aspect))
        ),
        solar_return=solar_return,
    )


def day_sky_events(
    engine: NatalChartEngine,
    local_date: date,
    chart: NatalChart | None = None,
    *,
    reference_time: time = DEFAULT_REFERENCE_TIME,
    station_orb: float = DEFAULT_STATION_ORB,
    lunation_orb: float = DEFAULT_LUNATION_ORB,
) -> DaySkyEvents:
    """All dated sky events of one Vietnam civil day, with natal hooks when ``chart`` is given."""
    if isinstance(local_date, datetime) or not isinstance(local_date, date):
        raise TypeError("local_date must be a date")
    if not 0.0 <= station_orb <= 10.0 or not 0.0 <= lunation_orb <= 10.0:
        raise ValueError("orbs must be between 0° and 10°")
    config = chart.config if chart is not None else CalculationConfig.western_recommended()
    sidereal = config.tradition is Tradition.JYOTISH
    sidereal_mode = AYANAMSA_IDS[config.ayanamsa] if config.ayanamsa else None
    zodiac = f"sidereal_{config.ayanamsa.value}" if config.ayanamsa else "tropical"
    day_start, day_end = vietnam_day_bounds(local_date)
    start, end = julian_day(day_start), julian_day(day_end)
    reference = julian_day(datetime.combine(local_date, reference_time, tzinfo=VIETNAM_TIMEZONE))
    native: SwissEphemerisNative = engine._native  # the engine's verified Swiss Ephemeris handle
    # Sidereal mode is process-global in Swiss Ephemeris, so a sidereal day holds the engine lock
    # throughout; tropical calls lock per position and never block other requests for long.
    scope = native.calculation_scope(sidereal_mode) if sidereal else nullcontext()
    with scope:
        sky = _Sky(native, sidereal=sidereal)
        stations: list[Station] = []
        periods: list[RetrogradePeriod] = []
        for body in STATION_BODIES:
            body_stations, body_periods = _retrograde_context(sky, body, start, end, reference)
            stations += body_stations
            periods += body_periods
        lunations = tuple(_lunations(sky, start, end))
        station_tuple = tuple(sorted(stations, key=lambda item: item.at))
        natal = (
            None
            if chart is None
            else _natal_hooks(
                engine,
                sky,
                chart,
                start,
                end,
                station_tuple,
                lunations,
                station_orb=station_orb,
                lunation_orb=lunation_orb,
            )
        )
        return DaySkyEvents(
            version=SKY_EVENTS_VERSION,
            local_date=local_date,
            timezone=VIETNAM_TIMEZONE.key,
            zodiac=zodiac,
            day_start=day_start,
            day_end=day_end,
            moon_phase=_moon_phase(sky, reference),
            stations=station_tuple,
            retrograde_periods=tuple(periods),
            lunations=lunations,
            ingresses=tuple(_ingresses(sky, start, end)),
            void_of_course=tuple(_void_of_course(sky, start, end)),
            natal=natal,
        )
