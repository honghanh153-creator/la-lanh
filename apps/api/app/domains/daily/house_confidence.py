"""House labels and chart angles that hold over the birth-time uncertainty (Daily v2 C2b).

A typed ``HH:MM`` is not a proof of the minute (gap register AS-10: with ±15 min about a
quarter of the planets change house), and the birthplace is a province's catalogue point, not
the birth address (AS-21). House cusps turn a full circle a day, so a house label is only used
when it is the same everywhere in that uncertainty:

* the birth time runs over ``± time_error_minutes`` around the chart's instant: the exact-time
  error ``EXACT_TIME_ERROR_MINUTES``, or the approximate window's half-width (the caller maps the
  precision, see ``sky_selection.birth_time_error_minutes``); a date-only chart, or the wide
  night window, gets no frame at all;
* the place runs over ``± PLACE_MARGIN_DEG`` of latitude and of longitude. Cusps depend on the
  sidereal time at the place, so a longitude shift is the same as a time shift
  (``1°`` ≈ 4 min); it widens the time range rather than adding another axis.

``house_frame`` samples the cusps over that range (every ``SAMPLE_STEP_MINUTES`` and every
``LATITUDE_STEP_DEG``; cusps move monotonically with sidereal time, so a label that is equal at
every sample is equal in between). A label that differs anywhere is dropped, not guessed:

* ``natal_houses``: a natal body's house, its longitude bounded over the time error;
* ``house_of(longitude)``: the natal house a transiting longitude falls in;
* ``cusp_signs``: the sign on each cusp; ``intercepted_signs`` only when all twelve hold;
* ``ruled_houses(body)``: the houses whose cusp sign the body rules (modern rulers, decision
  1.2: a ruler only *adds* houses to a factor, it never chooses a meaning); traditional rulers
  are metadata for the "Vì sao Lá đọc vậy?" layer only;
* ``angle_domain``: the ascendant and midheaven as ``(low, high)`` over the whole range, for the
  worst-case orb rule of ``sky_selection`` (an angle contact counts only while its worst-case
  orb is inside the limit).

Privacy (PV-1, PL-17): every value here is derived from the birth time and place and narrows the
birth time down. Nothing is stored, logged or put in an identifier; the frame lives in memory
for one selection. The caller passes the birthplace coordinates it already decrypted for the
request; they must reproduce the chart's own cusps, otherwise there is no frame (fail closed).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from app.domains.astro.engine import NatalChartEngine, sign_for_longitude
from app.domains.astro.ffi.swisseph import SwissEphemerisError
from app.domains.astro.models import (
    BodyName,
    HouseSystem,
    NatalChart,
    Tradition,
    ZodiacSign,
)

HOUSE_CONFIDENCE_VERSION = "daily-house-confidence-v1"
# AS-10: the error assumed for a typed HH:MM. People round birth times to the quarter hour; a
# label that survives ±15 min survives that rounding.
EXACT_TIME_ERROR_MINUTES = 15.0
# AS-21: the birthplace is the province's catalogue point. ±1° of latitude and longitude covers
# a birth anywhere within about 110 km of it.
PLACE_MARGIN_DEG = 1.0
LATITUDE_STEP_DEG = 0.5
SAMPLE_STEP_MINUTES = 2.0
SIDEREAL_DEG_PER_DAY = 360.98564736629
# The coordinates must reproduce the chart's own cusps and angles to this tolerance.
NOMINAL_TOLERANCE_DEG = 0.01
MAX_SAMPLE_LATITUDE = 89.0
# Systems whose tenth cusp is the midheaven; in whole-sign and equal houses it is not.
QUADRANT_SYSTEMS = frozenset({HouseSystem.PLACIDUS})
NODE_BODIES = (BodyName.TRUE_NODE, BodyName.MEAN_NODE)


class ChartAngle(StrEnum):
    """A natal angle used as a contact point (K-6). Values never clash with ``BodyName``."""

    ASCENDANT = "ascendant"
    MIDHEAVEN = "midheaven"


MODERN_RULERS: Mapping[ZodiacSign, BodyName] = {
    ZodiacSign.ARIES: BodyName.MARS,
    ZodiacSign.TAURUS: BodyName.VENUS,
    ZodiacSign.GEMINI: BodyName.MERCURY,
    ZodiacSign.CANCER: BodyName.MOON,
    ZodiacSign.LEO: BodyName.SUN,
    ZodiacSign.VIRGO: BodyName.MERCURY,
    ZodiacSign.LIBRA: BodyName.VENUS,
    ZodiacSign.SCORPIO: BodyName.PLUTO,
    ZodiacSign.SAGITTARIUS: BodyName.JUPITER,
    ZodiacSign.CAPRICORN: BodyName.SATURN,
    ZodiacSign.AQUARIUS: BodyName.URANUS,
    ZodiacSign.PISCES: BodyName.NEPTUNE,
}
# Metadata only (plan decision 1.2): shown in the "why" layer, never used to pick or rank.
TRADITIONAL_RULERS: Mapping[ZodiacSign, BodyName] = {
    **MODERN_RULERS,
    ZodiacSign.SCORPIO: BodyName.MARS,
    ZodiacSign.AQUARIUS: BodyName.SATURN,
    ZodiacSign.PISCES: BodyName.JUPITER,
}
_SIGNS = tuple(ZodiacSign)


@dataclass(frozen=True, slots=True)
class Birthplace:
    """The birthplace coordinates of the chart, held in memory for one request."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0 or not -180.0 <= self.longitude <= 180.0:
            raise ValueError("birthplace coordinates are out of range")


@dataclass(frozen=True, slots=True)
class CuspSample:
    """Cusps 1..12 and the two angles at one possible birth moment and place."""

    cusps: tuple[float, ...]
    ascendant: float
    midheaven: float


@dataclass(frozen=True, slots=True)
class HouseLabels:
    """The stable labels only, without a degree: what a Daily layer may read.

    Still derived from the birth time (an ascendant sign narrows it to about two hours), so it
    is in-memory only, like the rest of the selection.
    """

    house_system: HouseSystem
    time_error_minutes: float
    cusp_signs: Mapping[int, ZodiacSign]
    intercepted_signs: Mapping[int, tuple[ZodiacSign, ...]]
    natal_houses: Mapping[BodyName, int]
    ruled_houses: Mapping[BodyName, tuple[int, ...]]
    chart_ruler: BodyName | None
    traditional_rulers: Mapping[int, BodyName]


@dataclass(frozen=True, slots=True)
class HouseFrame:
    """Cusp samples over the birth-time and place uncertainty, and the labels that hold."""

    house_system: HouseSystem
    time_error_minutes: float
    place_margin_deg: float
    samples: tuple[CuspSample, ...] = field(repr=False)
    natal_houses: Mapping[BodyName, int]
    cusp_signs: Mapping[int, ZodiacSign]
    intercepted_signs: Mapping[int, tuple[ZodiacSign, ...]]
    angle_domains: Mapping[ChartAngle, tuple[float, float]] = field(repr=False)

    @classmethod
    def from_samples(
        cls,
        samples: tuple[CuspSample, ...],
        *,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        natal_domains: Mapping[BodyName, tuple[float, float]] | None = None,
        time_error_minutes: float = 0.0,
        place_margin_deg: float = 0.0,
    ) -> HouseFrame:
        """Derive every stable label from the samples (``natal_domains`` per natal body).

        ``samples[0]`` is the chart's own instant and place; angle domains unwrap around it.
        """

        if not samples or any(len(item.cusps) != 12 for item in samples):
            raise ValueError("a house frame needs samples of twelve cusps")
        cusp_signs: dict[int, ZodiacSign] = {}
        for index in range(12):
            signs = {sign_for_longitude(item.cusps[index]) for item in samples}
            if len(signs) == 1:
                cusp_signs[index + 1] = signs.pop()
        spans = dict(natal_domains or {})
        node = next((spans[item] for item in NODE_BODIES if item in spans), None)
        if node is not None and BodyName.SOUTH_NODE not in spans:
            # Opposite the north node (sky_selection relabels that contact, AS-12).
            spans[BodyName.SOUTH_NODE] = (node[0] + 180.0, node[1] + 180.0)
        natal: dict[BodyName, int] = {}
        for body, (low, high) in spans.items():
            house = _stable_span(samples, low, high)
            if house is not None:
                natal[body] = house
        intercepted: dict[int, tuple[ZodiacSign, ...]] = {}
        if len(cusp_signs) == 12:
            on_cusps = set(cusp_signs.values())
            grouped: dict[int, list[ZodiacSign]] = {}
            for position, sign in enumerate(_SIGNS):
                if sign in on_cusps:
                    continue
                start = position * 30.0
                house = _stable_span(samples, start, start + 29.999999)
                if house is None:
                    # A sign without a cusp lies inside one house; if the samples disagree the
                    # interception is not stable either, so none is reported.
                    intercepted = {}
                    break
                grouped.setdefault(house, []).append(sign)
            else:
                intercepted = {house: tuple(signs) for house, signs in sorted(grouped.items())}
        nominal = samples[0]
        angles = {
            ChartAngle.ASCENDANT: _unwrapped_domain(
                nominal.ascendant, (item.ascendant for item in samples)
            ),
            ChartAngle.MIDHEAVEN: _unwrapped_domain(
                nominal.midheaven, (item.midheaven for item in samples)
            ),
        }
        return cls(
            house_system=house_system,
            time_error_minutes=time_error_minutes,
            place_margin_deg=place_margin_deg,
            samples=samples,
            natal_houses=natal,
            cusp_signs=cusp_signs,
            intercepted_signs=intercepted,
            angle_domains=angles,
        )

    def house_of(self, longitude: float) -> int | None:
        """The natal house of a fixed (e.g. transiting) longitude, if every sample agrees."""

        return _stable_span(self.samples, longitude, longitude)

    def house_of_span(self, low: float, high: float) -> int | None:
        """The one house holding the short arc ``low → high`` at every sample, else ``None``."""

        return _stable_span(self.samples, low, high)

    def natal_house(self, point: BodyName | ChartAngle) -> int | None:
        """A natal point's stable house; the ascendant opens house 1 and, in a quadrant
        system, the midheaven house 10 (in whole-sign or equal houses it has no fixed one)."""

        if isinstance(point, BodyName):
            return self.natal_houses.get(point)
        if point is ChartAngle.ASCENDANT:
            return 1
        return 10 if self.house_system in QUADRANT_SYSTEMS else None

    def ruled_houses(self, point: BodyName | ChartAngle) -> tuple[int, ...]:
        """Houses whose stable cusp sign ``point`` rules (modern rulers); angles rule none."""

        if not isinstance(point, BodyName):
            return ()
        return tuple(
            sorted(house for house, sign in self.cusp_signs.items() if MODERN_RULERS[sign] is point)
        )

    @property
    def chart_ruler(self) -> BodyName | None:
        sign = self.cusp_signs.get(1)
        return MODERN_RULERS[sign] if sign is not None else None

    def angle_domain(self, angle: ChartAngle) -> tuple[float, float]:
        return self.angle_domains[angle]

    def labels(self) -> HouseLabels:
        rulers = sorted({MODERN_RULERS[sign] for sign in self.cusp_signs.values()})
        return HouseLabels(
            house_system=self.house_system,
            time_error_minutes=self.time_error_minutes,
            cusp_signs=dict(self.cusp_signs),
            intercepted_signs=dict(self.intercepted_signs),
            natal_houses=dict(self.natal_houses),
            ruled_houses={body: self.ruled_houses(body) for body in rulers},
            chart_ruler=self.chart_ruler,
            traditional_rulers={
                house: TRADITIONAL_RULERS[sign]
                for house, sign in self.cusp_signs.items()
                if TRADITIONAL_RULERS[sign] is not MODERN_RULERS[sign]
            },
        )


def house_frame(
    engine: NatalChartEngine,
    chart: NatalChart,
    birthplace: Birthplace | None,
    *,
    time_error_minutes: float | None,
    place_margin_deg: float = PLACE_MARGIN_DEG,
) -> HouseFrame | None:
    """Sample the chart's cusps over the birth-time and place uncertainty.

    ``None`` (no house label, no angle) when the chart is not Western, has no houses or angles
    (no place, or houses withheld for an uncertain UTC offset), no ``birthplace`` or no
    ``time_error_minutes`` is given, the coordinates do not reproduce the chart's cusps, or the
    house system cannot be calculated somewhere in the range (polar latitudes, AS-20).
    """

    if (
        chart.config.tradition is not Tradition.WESTERN
        or birthplace is None
        or time_error_minutes is None
        or chart.houses is None
        or len(chart.houses) != 12
        or chart.angles is None
    ):
        return None
    if time_error_minutes < 0 or place_margin_deg < 0:
        raise ValueError("uncertainty must not be negative")
    system = chart.house_system
    try:
        cusps, ascendant, midheaven = engine.house_cusps_at(
            chart.julian_day_ut, birthplace.latitude, birthplace.longitude, system, chart.config
        )
    except SwissEphemerisError:
        return None
    stored = tuple(item.longitude for item in sorted(chart.houses, key=lambda item: item.number))
    expected = (*stored, chart.angles.ascendant, chart.angles.midheaven)
    if any(
        _distance(first, second) > NOMINAL_TOLERANCE_DEG
        for first, second in zip((*cusps, ascendant, midheaven), expected, strict=True)
    ):
        return None

    half_minutes = time_error_minutes + place_margin_deg / SIDEREAL_DEG_PER_DAY * 1440.0
    offsets = _grid(half_minutes, SAMPLE_STEP_MINUTES)
    latitudes = tuple(
        max(-MAX_SAMPLE_LATITUDE, min(MAX_SAMPLE_LATITUDE, birthplace.latitude + delta))
        for delta in _grid(place_margin_deg, LATITUDE_STEP_DEG)
    )
    samples: list[CuspSample] = []
    try:
        for latitude in latitudes:
            for offset in offsets:
                values, asc, mc = engine.house_cusps_at(
                    chart.julian_day_ut + offset / 1440.0,
                    latitude,
                    birthplace.longitude,
                    system,
                    chart.config,
                )
                samples.append(CuspSample(cusps=values, ascendant=asc, midheaven=mc))
    except SwissEphemerisError:
        return None
    # The chart's own sample comes first: angle domains unwrap around it.
    nominal = CuspSample(cusps=cusps, ascendant=ascendant, midheaven=midheaven)
    spans: dict[BodyName, tuple[float, float]] = {
        body: domain
        for body, domain in engine.longitude_domains(
            chart, half_width_days=time_error_minutes / 1440.0
        ).items()
        if body is not BodyName.SOUTH_NODE
    }
    return HouseFrame.from_samples(
        (nominal, *samples),
        house_system=system,
        natal_domains=spans,
        time_error_minutes=time_error_minutes,
        place_margin_deg=place_margin_deg,
    )


def _grid(half_width: float, step: float) -> tuple[float, ...]:
    """``-half_width … +half_width`` in at most ``step`` increments, both ends included."""

    if half_width == 0:
        return (0.0,)
    count = max(1, math.ceil(2 * half_width / step))
    return tuple(-half_width + 2 * half_width * index / count for index in range(count + 1))


def _house_index(longitude: float, cusps: tuple[float, ...]) -> int:
    """``engine.house_for_longitude`` on bare cusps (half-open ``[cusp, next cusp)``)."""

    value = longitude % 360.0
    for index in range(12):
        start = cusps[index] % 360.0
        span = (cusps[(index + 1) % 12] - start) % 360.0
        if (value - start) % 360.0 < span:
            return index + 1
    raise ValueError("longitude could not be assigned to a house")


def _stable_span(samples: tuple[CuspSample, ...], low: float, high: float) -> int | None:
    if high - low >= 30.0 or high < low:
        return None
    houses = {
        _house_index(point, item.cusps)
        for item in samples
        for point in ((low,) if low == high else (low, high))
    }
    if len(houses) != 1:
        return None
    house = houses.pop()
    if low != high:
        # Both ends in one house still allow the arc to run through a narrower house between
        # them; require that no cusp lies strictly inside the arc at any sample.
        for item in samples:
            for cusp in item.cusps:
                if 0.0 < (cusp - low) % 360.0 <= high - low:
                    return None
    return house


def _unwrapped_domain(centre: float, values: Iterable[float]) -> tuple[float, float]:
    unwrapped = [centre + ((value - centre + 180.0) % 360.0 - 180.0) for value in values]
    low = min(unwrapped)
    if low < 0:
        low, high = low + 360.0, max(unwrapped) + 360.0
    else:
        high = max(unwrapped)
    return low, high


def _distance(first: float, second: float) -> float:
    raw = abs(first - second) % 360.0
    return min(raw, 360.0 - raw)
