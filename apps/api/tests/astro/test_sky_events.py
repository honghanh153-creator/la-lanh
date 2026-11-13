"""Dated sky events (Daily v2, issue #180) against public ephemerides and brute-force scans.

Reference sources, fetched 2026-11-03 and frozen below (times rounded as published):

* Eclipses: NASA GSFC, F. Espenak, "Solar Eclipses: 2021-2030"
  https://eclipse.gsfc.nasa.gov/SEdecade/SEdecade2021.html and "Lunar Eclipses: 2021-2030"
  https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html. Greatest-eclipse times are in TD;
  UT = TD - ΔT with ΔT = 69 s (NAOJ celestial phenomena 2026/2027 header).
* Lunations: NASA GSFC "Phases of the Moon: 2001 to 2100"
  https://eclipse.gsfc.nasa.gov/phase/phases2001.html (UT), identical to the USNO API
  https://aa.usno.navy.mil/api/moon/phases/year?year=2027 except 2027-09-15 (NASA 23:04, USNO
  23:03).
* Sun ingresses into the cardinal signs: USNO "Earth's Seasons"
  https://aa.usno.navy.mil/api/seasons?year=2027 (UT).
* Stations: NASA JPL Horizons (DE441) geocentric apparent ecliptic longitude, quantity 31, hourly,
  https://ssd.jpl.nasa.gov/api/horizons.api; station = vertex of a least-squares parabola over
  ±12 h (Mercury, Venus, Mars) or ±72 h (slower bodies). Swiss Ephemeris uses the true equinox of
  date, so slow planets differ by up to ~25 minutes; the contract allows one hour.

Every natal chart here is synthetic (fixed instants, no real person's birth data).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    CalculationConfig,
    ChartAngles,
    ChartInput,
    NatalChart,
    TimePrecision,
    ZodiacSign,
)
from app.domains.astro.sky_events import (
    INGRESS_BODIES,
    SKY_EVENTS_VERSION,
    STATION_BODIES,
    VIETNAM_TIMEZONE,
    VOID_ASPECT_BODIES,
    DaySkyEvents,
    EclipseKind,
    EclipseType,
    LunationKind,
    MoonPhase,
    RetrogradePhase,
    StationKind,
    _max_orb_to_domain,
    datetime_from_julian_day,
    day_sky_events,
    julian_day,
    moon_phase_for_elongation,
    vietnam_day_bounds,
)

BODY_IDS = {
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
PTOLEMAIC = (0, 60, 90, 120, 180, 240, 270, 300)
RANGE_START = datetime(2026, 11, 1, tzinfo=UTC)
RANGE_END = datetime(2028, 1, 1, tzinfo=UTC)
DELTA_T = timedelta(seconds=69)
TWO_MINUTES = 120.0
ONE_HOUR = 3600.0

# (kind, type, greatest eclipse in TD) - NASA GSFC Espenak decade tables.
NASA_ECLIPSES_TD = (
    (EclipseKind.SOLAR, EclipseType.ANNULAR, datetime(2026, 2, 17, 12, 13, 5, tzinfo=UTC)),
    (EclipseKind.LUNAR, EclipseType.TOTAL, datetime(2026, 3, 3, 11, 34, 52, tzinfo=UTC)),
    (EclipseKind.SOLAR, EclipseType.TOTAL, datetime(2026, 8, 12, 17, 47, 5, tzinfo=UTC)),
    (EclipseKind.LUNAR, EclipseType.PARTIAL, datetime(2026, 8, 28, 4, 14, 4, tzinfo=UTC)),
    (EclipseKind.SOLAR, EclipseType.ANNULAR, datetime(2027, 2, 6, 16, 0, 47, tzinfo=UTC)),
    (EclipseKind.LUNAR, EclipseType.PENUMBRAL, datetime(2027, 2, 20, 23, 14, 6, tzinfo=UTC)),
    (EclipseKind.LUNAR, EclipseType.PENUMBRAL, datetime(2027, 7, 18, 16, 4, 9, tzinfo=UTC)),
    (EclipseKind.SOLAR, EclipseType.TOTAL, datetime(2027, 8, 2, 10, 7, 49, tzinfo=UTC)),
    (EclipseKind.LUNAR, EclipseType.PENUMBRAL, datetime(2027, 8, 17, 7, 14, 59, tzinfo=UTC)),
)

# NASA GSFC phases table (UT, minute precision), November 2026 to December 2027.
_NEW = LunationKind.NEW_MOON
_FULL = LunationKind.FULL_MOON
NASA_LUNATIONS_UT = (
    (_NEW, "2026-11-09 07:02"),
    (_FULL, "2026-11-24 14:53"),
    (_NEW, "2026-12-09 00:52"),
    (_FULL, "2026-12-24 01:28"),
    (_NEW, "2027-01-07 20:24"),
    (_FULL, "2027-01-22 12:17"),
    (_NEW, "2027-02-06 15:56"),
    (_FULL, "2027-02-20 23:23"),
    (_NEW, "2027-03-08 09:29"),
    (_FULL, "2027-03-22 10:44"),
    (_NEW, "2027-04-06 23:51"),
    (_FULL, "2027-04-20 22:27"),
    (_NEW, "2027-05-06 10:58"),
    (_FULL, "2027-05-20 10:59"),
    (_NEW, "2027-06-04 19:40"),
    (_FULL, "2027-06-19 00:44"),
    (_NEW, "2027-07-04 03:02"),
    (_FULL, "2027-07-18 15:45"),
    (_NEW, "2027-08-02 10:05"),
    (_FULL, "2027-08-17 07:29"),
    (_NEW, "2027-08-31 17:41"),
    (_FULL, "2027-09-15 23:04"),
    (_NEW, "2027-09-30 02:36"),
    (_FULL, "2027-10-15 13:47"),
    (_NEW, "2027-10-29 13:36"),
    (_FULL, "2027-11-14 03:26"),
    (_NEW, "2027-11-28 03:24"),
    (_FULL, "2027-12-13 16:09"),
    (_NEW, "2027-12-27 20:12"),
)

# USNO Earth's Seasons (UT): the Sun entering the cardinal signs.
USNO_CARDINAL_INGRESSES_UT = (
    (ZodiacSign.CAPRICORN, "2026-12-21 20:50"),
    (ZodiacSign.ARIES, "2027-03-20 20:25"),
    (ZodiacSign.CANCER, "2027-06-21 14:11"),
    (ZodiacSign.LIBRA, "2027-09-23 06:02"),
    (ZodiacSign.CAPRICORN, "2027-12-22 02:42"),
)

# JPL Horizons stations (UT), November 2026 to December 2027.
_R = StationKind.RETROGRADE
_D = StationKind.DIRECT
JPL_STATIONS_UT = (
    (BodyName.MERCURY, _D, "2026-11-13 15:55", 215.0335),
    (BodyName.VENUS, _D, "2026-11-14 00:27", 202.8637),
    (BodyName.SATURN, _D, "2026-12-10 23:29", 7.9310),
    (BodyName.NEPTUNE, _D, "2026-12-12 22:20", 1.6129),
    (BodyName.JUPITER, _R, "2026-12-13 00:55", 147.0246),
    (BodyName.CHIRON, _D, "2027-01-06 11:05", 26.2645),
    (BodyName.MARS, _R, "2027-01-10 12:58", 160.4290),
    (BodyName.URANUS, _D, "2027-02-08 12:22", 61.6826),
    (BodyName.MERCURY, _R, "2027-02-09 17:35", 335.9812),
    (BodyName.MERCURY, _D, "2027-03-03 12:33", 320.9232),
    (BodyName.MARS, _D, "2027-04-01 14:08", 140.9266),
    (BodyName.JUPITER, _D, "2027-04-13 02:20", 136.9955),
    (BodyName.PLUTO, _R, "2027-05-08 13:01", 307.1780),
    (BodyName.MERCURY, _R, "2027-06-10 18:15", 96.3611),
    (BodyName.MERCURY, _D, "2027-07-04 19:38", 87.4692),
    (BodyName.NEPTUNE, _R, "2027-07-09 23:01", 6.6595),
    (BodyName.CHIRON, _R, "2027-08-08 02:58", 34.6677),
    (BodyName.SATURN, _R, "2027-08-09 18:08", 27.8804),
    (BodyName.URANUS, _R, "2027-09-15 09:16", 69.9557),
    (BodyName.MERCURY, _R, "2027-10-07 14:34", 214.9278),
    (BodyName.PLUTO, _D, "2027-10-18 04:16", 304.7483),
    (BodyName.MERCURY, _D, "2027-10-28 14:11", 199.3121),
    (BodyName.NEPTUNE, _D, "2027-12-15 09:22", 3.8526),
    (BodyName.SATURN, _D, "2027-12-24 02:46", 21.0206),
)


def _utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


def _vietnam_date(value: datetime) -> date:
    return value.astimezone(VIETNAM_TIMEZONE).date()


def _wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


class _Days:
    """Memoised ``day_sky_events`` per Vietnam date so many tests share one computation."""

    def __init__(self, engine: NatalChartEngine) -> None:
        self._engine = engine
        self._days: dict[date, DaySkyEvents] = {}

    def __call__(self, local_date: date) -> DaySkyEvents:
        if local_date not in self._days:
            self._days[local_date] = day_sky_events(self._engine, local_date)
        return self._days[local_date]


@pytest.fixture(scope="module")
def days(engine: NatalChartEngine) -> _Days:
    return _Days(engine)


def _longitude(engine: NatalChartEngine, instant: float, body: BodyName) -> float:
    return engine._native.calculate(instant, BODY_IDS[body]).longitude % 360.0


def _hourly(start: datetime, end: datetime) -> Iterator[float]:
    first, last = julian_day(start), julian_day(end)
    steps = round((last - first) * 24)
    for index in range(steps + 1):
        yield first + index / 24.0


@dataclass(frozen=True)
class _BruteForce:
    stations: list[tuple[BodyName, StationKind, float]]
    lunations: list[tuple[LunationKind, float]]
    ingresses: list[tuple[BodyName, ZodiacSign, float]]


@pytest.fixture(scope="module")
def brute_force(engine: NatalChartEngine) -> _BruteForce:
    """Independent hourly scans with linear interpolation (no shared code with the module)."""
    native = engine._native
    stations: list[tuple[BodyName, StationKind, float]] = []
    lunations: list[tuple[LunationKind, float]] = []
    ingresses: list[tuple[BodyName, ZodiacSign, float]] = []
    previous: dict[BodyName, tuple[float, float, float]] = {}
    previous_elongation: tuple[float, float] | None = None
    for instant in _hourly(RANGE_START - timedelta(hours=1), RANGE_END):
        positions = {body: native.calculate(instant, body_id) for body, body_id in BODY_IDS.items()}
        elongation = (
            positions[BodyName.MOON].longitude - positions[BodyName.SUN].longitude
        ) % 360.0
        if previous_elongation is not None:
            last_instant, last = previous_elongation
            for phase, target in ((LunationKind.NEW_MOON, 0.0), (LunationKind.FULL_MOON, 180.0)):
                a, b = _wrap180(last - target), _wrap180(elongation - target)
                if a < 0.0 <= b and b - a < 90.0:
                    lunations.append(
                        (phase, last_instant + (instant - last_instant) * (-a) / (b - a))
                    )
        previous_elongation = (instant, elongation)
        for body, position in positions.items():
            longitude, speed = position.longitude % 360.0, position.longitude_speed
            if body in previous:
                last_instant, last_longitude, last_speed = previous[body]
                if body in STATION_BODIES and (last_speed > 0.0) != (speed > 0.0):
                    fraction = last_speed / (last_speed - speed)
                    kind = StationKind.RETROGRADE if last_speed > 0.0 else StationKind.DIRECT
                    stations.append((body, kind, last_instant + fraction / 24.0))
                old_sign, new_sign = int(last_longitude // 30), int(longitude // 30)
                if body in INGRESS_BODIES and old_sign != new_sign:
                    retrograde = (new_sign - old_sign) % 12 == 11
                    boundary = (old_sign if retrograde else new_sign) * 30.0
                    a = _wrap180(last_longitude - boundary)
                    b = _wrap180(longitude - boundary)
                    ingresses.append(
                        (
                            body,
                            tuple(ZodiacSign)[new_sign],
                            last_instant + (instant - last_instant) * (-a) / (b - a),
                        )
                    )
            previous[body] = (instant, longitude, speed)
    return _BruteForce(stations=stations, lunations=lunations, ingresses=ingresses)


def _in_range(instant: float) -> bool:
    return julian_day(RANGE_START) <= instant < julian_day(RANGE_END)


def test_lunations_match_nasa_phase_table_and_brute_force(
    days: _Days, brute_force: _BruteForce
) -> None:
    scanned = [item for item in brute_force.lunations if _in_range(item[1])]
    assert len(scanned) == len(NASA_LUNATIONS_UT) == 29
    for (kind, published), (scanned_kind, scanned_instant) in zip(
        NASA_LUNATIONS_UT, scanned, strict=True
    ):
        reference = _utc(published)
        found = [item for item in days(_vietnam_date(reference)).lunations if item.kind is kind]
        assert len(found) == 1, published
        lunation = found[0]
        assert abs((lunation.at - reference).total_seconds()) <= TWO_MINUTES, published
        assert scanned_kind is kind
        brute = datetime_from_julian_day(scanned_instant)
        assert abs((lunation.at - brute).total_seconds()) <= TWO_MINUTES, published


def test_eclipses_match_nasa_espenak_tables(days: _Days) -> None:
    for kind, eclipse_type, greatest_td in NASA_ECLIPSES_TD:
        greatest_ut = greatest_td - DELTA_T
        lunation_kind = LunationKind.NEW_MOON if kind is EclipseKind.SOLAR else _FULL
        candidates = [
            lunation
            for offset in (-1, 0, 1)
            for lunation in days(_vietnam_date(greatest_ut) + timedelta(days=offset)).lunations
            if lunation.kind is lunation_kind and lunation.eclipse is not None
        ]
        assert len(candidates) == 1, greatest_td
        eclipse = candidates[0].eclipse
        assert eclipse is not None
        assert eclipse.kind is kind
        assert eclipse.type is eclipse_type
        assert abs((eclipse.maximum_at - greatest_ut).total_seconds()) <= TWO_MINUTES


def test_only_the_published_eclipses_are_flagged(days: _Days) -> None:
    flagged = {
        _vietnam_date(lunation.at)
        for kind, published in NASA_LUNATIONS_UT
        for lunation in days(_vietnam_date(_utc(published))).lunations
        if lunation.eclipse is not None
    }
    expected = {
        _vietnam_date(greatest - DELTA_T)
        for _, _, greatest in NASA_ECLIPSES_TD
        if greatest - DELTA_T >= RANGE_START
    }
    assert flagged == expected


def test_vietnam_day_moves_a_late_utc_eclipse_to_the_next_date(days: _Days) -> None:
    # New Moon 2026-08-12 17:37 UT is 00:37 on 13 August in Vietnam.
    assert not days(date(2026, 8, 12)).lunations
    (lunation,) = days(date(2026, 8, 13)).lunations
    assert lunation.eclipse is not None
    assert lunation.eclipse.type is EclipseType.TOTAL


def test_stations_match_jpl_horizons_and_brute_force(days: _Days, brute_force: _BruteForce) -> None:
    scanned = [item for item in brute_force.stations if _in_range(item[2])]
    assert len(scanned) == len(JPL_STATIONS_UT)
    for body, kind, published, longitude in JPL_STATIONS_UT:
        reference = _utc(published)
        found = [
            item
            for item in days(_vietnam_date(reference)).stations
            if item.body is body and item.kind is kind
        ]
        assert len(found) == 1, (body, published)
        station = found[0]
        assert abs((station.at - reference).total_seconds()) <= ONE_HOUR, (body, published)
        assert abs(_wrap180(station.longitude - longitude)) <= 0.01, (body, published)
        brute = [
            datetime_from_julian_day(item[2])
            for item in scanned
            if item[0] is body and item[1] is kind
        ]
        assert min(abs((station.at - item).total_seconds()) for item in brute) <= ONE_HOUR


def test_sun_cardinal_ingresses_match_usno_seasons(days: _Days) -> None:
    for sign, published in USNO_CARDINAL_INGRESSES_UT:
        reference = _utc(published)
        found = [
            item for item in days(_vietnam_date(reference)).ingresses if item.body is BodyName.SUN
        ]
        assert len(found) == 1, published
        assert found[0].sign is sign
        assert abs((found[0].at - reference).total_seconds()) <= TWO_MINUTES


def test_planet_ingresses_match_brute_force_scan(days: _Days, brute_force: _BruteForce) -> None:
    scanned = [
        item
        for item in brute_force.ingresses
        if item[0] is not BodyName.MOON and _in_range(item[2])
    ]
    assert len(scanned) > 40
    for body, sign, instant in scanned:
        brute = datetime_from_julian_day(instant)
        found = [item for item in days(_vietnam_date(brute)).ingresses if item.body is body]
        assert any(
            item.sign is sign and abs((item.at - brute).total_seconds()) <= TWO_MINUTES
            for item in found
        ), (body, sign, brute)
    assert any(item[0] is BodyName.MERCURY and item[1] is ZodiacSign.GEMINI for item in scanned), (
        "a retrograde re-entry is covered"
    )


def test_sampled_days_are_complete_against_brute_force(
    days: _Days, brute_force: _BruteForce
) -> None:
    for offset in range(0, 426, 11):
        local_date = date(2026, 11, 1) + timedelta(days=offset)
        start, end = (julian_day(value) for value in vietnam_day_bounds(local_date))
        events = days(local_date)

        def inside(instant: float, start: float = start, end: float = end) -> bool:
            return start <= instant < end

        expected_ingresses = sorted(
            (item[0], item[1]) for item in brute_force.ingresses if inside(item[2])
        )
        assert sorted((item.body, item.sign) for item in events.ingresses) == expected_ingresses
        assert sorted(item.kind for item in events.lunations) == sorted(
            item[0] for item in brute_force.lunations if inside(item[1])
        )
        assert sorted((item.body, item.kind) for item in events.stations) == sorted(
            (item[0], item[1]) for item in brute_force.stations if inside(item[2])
        )


def test_moon_ingress_times_match_brute_force(days: _Days, brute_force: _BruteForce) -> None:
    moon = [
        datetime_from_julian_day(item[2])
        for item in brute_force.ingresses
        if item[0] is BodyName.MOON
    ][:40]
    for brute in moon:
        found = [
            item for item in days(_vietnam_date(brute)).ingresses if item.body is BodyName.MOON
        ]
        assert min(abs((item.at - brute).total_seconds()) for item in found) <= TWO_MINUTES


def test_void_of_course_runs_from_last_ptolemaic_aspect_to_ingress(
    engine: NatalChartEngine, days: _Days
) -> None:
    checked = 0
    for offset in range(0, 60, 3):
        for period in days(date(2027, 1, 1) + timedelta(days=offset)).void_of_course:
            start, end = julian_day(period.start), julian_day(period.end)
            before = _longitude(engine, end - 1 / 1440, BodyName.MOON)
            after = _longitude(engine, end + 1 / 1440, BodyName.MOON)
            assert tuple(ZodiacSign)[int(before // 30)] is period.moon_sign
            assert tuple(ZodiacSign)[int(after // 30)] is period.next_sign
            assert period.last_aspect_body is not None
            separation = (
                _longitude(engine, start, BodyName.MOON)
                - _longitude(engine, start, period.last_aspect_body)
            ) % 360.0
            assert min(abs(_wrap180(separation - angle)) for angle in PTOLEMAIC) < 0.01
            # Brute force: no exact Ptolemaic aspect after the start, up to the ingress.
            instant = start + 2 / 1440
            while instant < end - 1 / 1440:
                following = min(instant + 10 / 1440, end - 1 / 1440)
                for body in VOID_ASPECT_BODIES:
                    first = (
                        _longitude(engine, instant, BodyName.MOON)
                        - _longitude(engine, instant, body)
                    ) % 360.0
                    second = first + (
                        (
                            _longitude(engine, following, BodyName.MOON)
                            - _longitude(engine, following, body)
                            - first
                        )
                        % 360.0
                    )
                    for angle in (*PTOLEMAIC, 360, 420):
                        assert not first < angle <= second, (period, body, angle)
                instant = following
            checked += 1
    assert checked >= 10


def test_void_of_course_definition_source_is_cited() -> None:
    import app.domains.astro.sky_events as module

    assert module.__doc__ is not None
    assert "theastrologypodcast.com" in module.__doc__


def test_retrograde_period_shadow_by_longitude(engine: NatalChartEngine, days: _Days) -> None:
    events = days(date(2027, 2, 20))
    (period,) = [item for item in events.retrograde_periods if item.body is BodyName.MERCURY]
    assert period.phase is RetrogradePhase.RETROGRADE
    assert period.pre_shadow_start is not None and period.post_shadow_end is not None
    assert (
        period.pre_shadow_start
        < period.retrograde_station.at
        < period.direct_station.at
        < period.post_shadow_end
    )
    pre = _longitude(engine, julian_day(period.pre_shadow_start), BodyName.MERCURY)
    post = _longitude(engine, julian_day(period.post_shadow_end), BodyName.MERCURY)
    assert abs(_wrap180(pre - period.shadow_low)) < 1e-3
    assert abs(_wrap180(post - period.shadow_high)) < 1e-3
    assert period.shadow_low == period.direct_station.longitude

    before = days(_vietnam_date(period.pre_shadow_start) + timedelta(days=1))
    after = days(_vietnam_date(period.post_shadow_end) - timedelta(days=1))
    outside = days(_vietnam_date(period.post_shadow_end) + timedelta(days=2))
    phase = {
        item.body: item.phase
        for item in before.retrograde_periods
        if item.retrograde_station == period.retrograde_station
    }
    assert phase == {BodyName.MERCURY: RetrogradePhase.PRE_SHADOW}
    assert any(
        item.retrograde_station == period.retrograde_station
        and item.phase is RetrogradePhase.POST_SHADOW
        for item in after.retrograde_periods
    )
    assert all(
        item.retrograde_station != period.retrograde_station for item in outside.retrograde_periods
    )


def test_station_is_identical_whichever_day_finds_it(days: _Days) -> None:
    station_day = days(date(2027, 2, 10))
    (station,) = [item for item in station_day.stations if item.body is BodyName.MERCURY]
    for other in (date(2027, 1, 30), date(2027, 2, 25), date(2027, 3, 15)):
        periods = [item for item in days(other).retrograde_periods if item.body is BodyName.MERCURY]
        assert station in [item.retrograde_station for item in periods]


def test_moon_phase_octants_are_centred_on_principal_angles() -> None:
    expected = {
        0.0: MoonPhase.NEW_MOON,
        22.4: MoonPhase.NEW_MOON,
        22.5: MoonPhase.WAXING_CRESCENT,
        90.0: MoonPhase.FIRST_QUARTER,
        150.0: MoonPhase.WAXING_GIBBOUS,
        180.0: MoonPhase.FULL_MOON,
        225.0: MoonPhase.WANING_GIBBOUS,
        270.0: MoonPhase.LAST_QUARTER,
        330.0: MoonPhase.WANING_CRESCENT,
        337.5: MoonPhase.NEW_MOON,
        359.9: MoonPhase.NEW_MOON,
    }
    assert {key: moon_phase_for_elongation(key) for key in expected} == expected


def test_moon_phase_at_local_noon(days: _Days) -> None:
    full = days(date(2027, 5, 20)).moon_phase
    assert full.phase is MoonPhase.FULL_MOON
    assert full.at == datetime(2027, 5, 20, 5, tzinfo=UTC)
    assert full.illuminated_fraction > 0.99
    assert days(date(2027, 5, 13)).moon_phase.phase is MoonPhase.FIRST_QUARTER


def test_day_bounds_are_vietnam_civil_day(days: _Days) -> None:
    events = days(date(2027, 1, 1))
    assert events.version == SKY_EVENTS_VERSION
    assert events.timezone == "Asia/Ho_Chi_Minh"
    assert events.zodiac == "tropical"
    assert events.day_start == datetime(2026, 12, 31, 17, tzinfo=UTC)
    assert events.day_end == datetime(2027, 1, 1, 17, tzinfo=UTC)
    assert events.natal is None
    for ingress in events.ingresses:
        assert events.day_start <= ingress.at < events.day_end


def test_result_is_deterministic_and_frozen(engine: NatalChartEngine) -> None:
    first = day_sky_events(engine, date(2027, 2, 6))
    second = day_sky_events(NatalChartEngine(), date(2027, 2, 6))
    assert first == second
    with pytest.raises(AttributeError):
        setattr(first, "version", "other")  # noqa: B010 - proves the dataclass is frozen


def test_invalid_arguments_are_refused(engine: NatalChartEngine) -> None:
    with pytest.raises(TypeError):
        day_sky_events(engine, datetime(2027, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError):
        day_sky_events(engine, date(2027, 1, 1), station_orb=-1.0)
    with pytest.raises(ValueError):
        julian_day(datetime(2027, 1, 1))


def _synthetic_chart(engine: NatalChartEngine, **overrides: float) -> NatalChart:
    """A synthetic chart (fixed instant, not a person) with chosen body longitudes."""
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1991, 3, 4, 5, 6, tzinfo=UTC), latitude=16.0, longitude=108.0
        )
    )
    bodies: list[BodyPosition] = []
    for body in chart.bodies:
        if body.body.value in overrides:
            longitude = overrides[body.body.value] % 360.0
            body = body.model_copy(
                update={
                    "longitude": longitude,
                    "sign": tuple(ZodiacSign)[int(longitude // 30)],
                    "degree_in_sign": longitude % 30.0,
                }
            )
        bodies.append(body)
    update: dict[str, object] = {"bodies": tuple(bodies)}
    if "ascendant" in overrides:
        assert chart.angles is not None
        update["angles"] = ChartAngles(
            ascendant=overrides["ascendant"],
            midheaven=chart.angles.midheaven,
            armc=chart.angles.armc,
            vertex=chart.angles.vertex,
        )
    return chart.model_copy(update=update)


def test_station_on_a_natal_point_is_hooked(engine: NatalChartEngine) -> None:
    # Mars stations retrograde at ~160.43° on 2027-01-10.
    chart = _synthetic_chart(engine, venus=160.9, ascendant=159.6, mercury=170.0)
    events = day_sky_events(engine, date(2027, 1, 10), chart)
    assert events.natal is not None
    hooks = {(item.station.body, item.natal_point): item.orb for item in events.natal.stations}
    assert hooks.keys() == {(BodyName.MARS, "venus"), (BodyName.MARS, "ascendant")}
    assert hooks[(BodyName.MARS, "venus")] == pytest.approx(0.471, abs=0.01)

    tighter = day_sky_events(engine, date(2027, 1, 10), chart, station_orb=0.3)
    assert tighter.natal is not None and not tighter.natal.stations


def test_angles_need_an_exact_birth_time(engine: NatalChartEngine) -> None:
    chart = _synthetic_chart(engine, ascendant=160.4).model_copy(
        update={"time_precision": TimePrecision.APPROXIMATE}
    )
    events = day_sky_events(engine, date(2027, 1, 10), chart)
    assert events.natal is not None
    assert all(item.natal_point != "ascendant" for item in events.natal.stations)


def test_eclipse_on_a_natal_point_is_hooked(engine: NatalChartEngine) -> None:
    # Total solar eclipse 2027-08-02 at ~129.92° (Leo).
    chart = _synthetic_chart(engine, jupiter=131.0, saturn=219.0, mars=312.5, uranus=70.0)
    events = day_sky_events(engine, date(2027, 8, 2), chart)
    assert events.natal is not None
    contacts = {(item.natal_point, item.aspect) for item in events.natal.lunations}
    assert ("jupiter", "conjunction") in contacts
    assert ("saturn", "square") in contacts
    assert ("mars", "opposition") in contacts
    assert all(item.natal_point != "uranus" for item in events.natal.lunations)
    eclipse = next(item for item in events.natal.lunations if item.natal_point == "jupiter")
    assert eclipse.lunation.eclipse is not None
    assert eclipse.orb == pytest.approx(1.083, abs=0.01)


def test_solar_return_day(engine: NatalChartEngine) -> None:
    chart = _synthetic_chart(engine, sun=238.4)
    hits = []
    for day in range(25):
        local_date = date(2027, 11, 10) + timedelta(days=day)
        events = day_sky_events(engine, local_date, chart)
        assert events.natal is not None
        if events.natal.solar_return is not None:
            hits.append((local_date, events.natal.solar_return))
    assert len(hits) == 1
    local_date, solar_return = hits[0]
    assert not solar_return.approximate
    sun = _longitude(engine, julian_day(solar_return.at), BodyName.SUN)
    assert abs(_wrap180(sun - 238.4)) < 1e-3
    assert _vietnam_date(solar_return.at) == local_date


def test_solar_return_exactly_at_day_start_is_kept(engine: NatalChartEngine) -> None:
    # Synthetic natal Sun placed on the transiting Sun at the Vietnam midnight of 2027-11-20.
    local_date = date(2027, 11, 20)
    day_start, _ = vietnam_day_bounds(local_date)
    natal_sun = _longitude(engine, julian_day(day_start), BodyName.SUN)
    chart = _synthetic_chart(engine, sun=natal_sun)
    events = day_sky_events(engine, local_date, chart)
    assert events.natal is not None and events.natal.solar_return is not None
    assert events.natal.solar_return.at == day_start
    previous = day_sky_events(engine, local_date - timedelta(days=1), chart)
    assert previous.natal is not None and previous.natal.solar_return is None


def test_natal_contact_orb_holds_across_the_whole_domain() -> None:
    # Synthetic unknown-time domain [0°, 2°]: a station at 359.5° is 0.5° from one end only.
    assert _max_orb_to_domain(359.5, 0.0, 2.0, 0.0) == pytest.approx(2.5)
    assert _max_orb_to_domain(1.0, 0.5, 1.5, 0.0) == pytest.approx(0.5)
    assert _max_orb_to_domain(100.0, 10.0, 10.0, 90.0) == pytest.approx(0.0)
    assert _max_orb_to_domain(100.0, 5.0, 15.0, 90.0) == pytest.approx(5.0)
    assert _max_orb_to_domain(0.0, 170.0, 190.0, 0.0) == pytest.approx(180.0)


def test_possible_but_uncertain_station_contact_is_not_hooked(engine: NatalChartEngine) -> None:
    # Mars stations at ~160.43° on 2027-01-10; a synthetic Venus domain [160.0°, 162.5°] only
    # reaches it at one end, so the contact is possible but not certain within 1°.
    chart = _synthetic_chart(engine, venus=160.0)
    original = engine.longitude_domains

    def domains(value: NatalChart, **kwargs: float | None) -> dict[BodyName, tuple[float, float]]:
        result = dict(original(value, **kwargs))
        result[BodyName.VENUS] = (160.0, 162.5)
        return result

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(engine, "longitude_domains", domains)
        events = day_sky_events(engine, date(2027, 1, 10), chart)
    assert events.natal is not None
    assert all(item.natal_point != "venus" for item in events.natal.stations)


def test_unknown_birth_time_skips_moon_and_marks_return_approximate(
    engine: NatalChartEngine,
) -> None:
    exact = _synthetic_chart(engine)
    unknown = exact.model_copy(update={"time_precision": TimePrecision.UNKNOWN})
    natal_sun = exact.body(BodyName.SUN).longitude
    # Find the return day for the synthetic Sun in 2027.
    local_date = date(2027, 3, 1)
    for _ in range(20):
        events = day_sky_events(engine, local_date, unknown)
        assert events.natal is not None
        if events.natal.solar_return is not None:
            break
        local_date += timedelta(days=1)
    assert events.natal is not None and events.natal.solar_return is not None
    assert events.natal.solar_return.approximate
    assert events.natal.solar_return.natal_sun_longitude == pytest.approx(natal_sun, abs=1e-5)
    full_moon = day_sky_events(engine, date(2027, 3, 22), unknown)
    assert full_moon.natal is not None
    assert all(
        item.natal_point not in {"moon", "ascendant", "midheaven"}
        for item in full_moon.natal.lunations
    )


def test_sidereal_chart_uses_its_zodiac(engine: NatalChartEngine) -> None:
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1991, 3, 4, 5, 6, tzinfo=UTC), latitude=16.0, longitude=108.0
        ),
        CalculationConfig.jyotish_recommended(),
    )
    sun_ingress = [
        (local_date, item)
        for local_date in (date(2027, 1, 13) + timedelta(days=offset) for offset in range(4))
        for item in day_sky_events(engine, local_date, chart).ingresses
        if item.body is BodyName.SUN
    ]
    assert [item.sign for _, item in sun_ingress] == [ZodiacSign.CAPRICORN]
    tropical = day_sky_events(engine, date(2027, 1, 22))
    sidereal = day_sky_events(engine, date(2027, 1, 22), chart)
    assert sidereal.zodiac == "sidereal_lahiri"
    assert [item.at for item in sidereal.lunations] == [item.at for item in tropical.lunations]
    assert sidereal.lunations[0].sign is not tropical.lunations[0].sign or (
        sidereal.lunations[0].longitude != tropical.lunations[0].longitude
    )


def test_julian_day_round_trip_matches_swiss_ephemeris(engine: NatalChartEngine) -> None:
    instant = datetime(2027, 7, 18, 15, 44, 56, tzinfo=UTC)
    assert julian_day(instant) == pytest.approx(
        engine._native.julian_day(2027, 7, 18, 15 + 44 / 60 + 56 / 3600), abs=1e-9
    )
    assert datetime_from_julian_day(julian_day(instant)) == instant
