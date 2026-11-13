"""Daily v2 C2b: houses by birth-time confidence, and angles only with a reliable time.

Every chart here is synthetic (made-up birth instants, round coordinates of a generic place).
"""

from __future__ import annotations

import ast
import dataclasses
import math
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest

from app.domains.astro.aspects import angular_distance
from app.domains.astro.engine import NatalChartEngine, house_for_longitude, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    HouseSystem,
    NatalChart,
    TimePrecision,
    ZodiacSign,
)
from app.domains.birth.models import BirthSupplement
from app.domains.daily.house_confidence import (
    EXACT_TIME_ERROR_MINUTES,
    PLACE_MARGIN_DEG,
    TRADITIONAL_RULERS,
    Birthplace,
    ChartAngle,
    CuspSample,
    HouseFrame,
    house_frame,
)
from app.domains.daily.sky_selection import (
    DAILY_TIMEZONE,
    DayContact,
    NatalDomains,
    birth_time_error_minutes,
    contact_eligibility,
    daily_house_frame,
    natal_domains,
    scan_day,
    select_daily_sky,
)

PLACE = Birthplace(latitude=16.0, longitude=108.0)
# Synthetic births at one generic place, spread over the clock so every house system edge case
# (signs of short and long ascension) is met.
SYNTHETIC_BIRTHS = (
    datetime(2001, 1, 15, 5, 0, tzinfo=UTC),
    datetime(1995, 7, 1, 1, 30, tzinfo=UTC),
    datetime(1990, 3, 10, 14, 45, tzinfo=UTC),
    datetime(1985, 10, 20, 20, 10, tzinfo=UTC),
)
START = date(2026, 11, 2)
NODES = (BodyName.TRUE_NODE, BodyName.MEAN_NODE)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _chart(
    engine: NatalChartEngine,
    born: datetime,
    place: Birthplace = PLACE,
    precision: TimePrecision = TimePrecision.EXACT,
) -> NatalChart:
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=born, latitude=place.latitude, longitude=place.longitude)
    )
    return chart.model_copy(update={"time_precision": precision})


@pytest.fixture(scope="module")
def charts(engine: NatalChartEngine) -> tuple[NatalChart, ...]:
    return tuple(_chart(engine, born) for born in SYNTHETIC_BIRTHS)


def _brute_force_houses(
    engine: NatalChartEngine, born: datetime, error_minutes: float
) -> list[NatalChart]:
    """Independent check: whole charts recalculated over the time error and place margin."""

    minutes = range(-int(error_minutes), int(error_minutes) + 1)
    shifts = (-PLACE_MARGIN_DEG, 0.0, PLACE_MARGIN_DEG)
    return [
        _chart(
            engine,
            born + timedelta(minutes=minute),
            Birthplace(PLACE.latitude + d_lat, PLACE.longitude + d_lon),
        )
        for minute in minutes
        for d_lat in shifts
        for d_lon in shifts
    ]


def _house(chart: NatalChart, longitude: float) -> int:
    assert chart.houses is not None
    return house_for_longitude(longitude, chart.houses)


def test_house_labels_hold_at_every_birth_time_in_the_error_range(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    kept = dropped = 0
    for born, chart in zip(SYNTHETIC_BIRTHS, charts, strict=True):
        frame = house_frame(engine, chart, PLACE, time_error_minutes=EXACT_TIME_ERROR_MINUTES)
        assert frame is not None
        variants = _brute_force_houses(engine, born, EXACT_TIME_ERROR_MINUTES)
        for body in (item.body for item in chart.bodies):
            houses = {_house(variant, variant.body(body).longitude) for variant in variants}
            if body in frame.natal_houses:
                # A label that is used is the same for every birth time and place in range.
                assert houses == {frame.natal_houses[body]}
                kept += 1
            else:
                dropped += 1
            if len(houses) > 1:
                # A label that changes somewhere in the range is never used.
                assert body not in frame.natal_houses
        for number, sign in frame.cusp_signs.items():
            assert {variant.houses[number - 1].sign for variant in variants if variant.houses} == {
                sign
            }
        # With no error at all every body has its plain house: the drops come from the range.
        exact = house_frame(engine, chart, PLACE, time_error_minutes=0.0, place_margin_deg=0.0)
        assert exact is not None
        node = next(item for item in chart.bodies if item.body in NODES)
        assert exact.natal_houses == {
            body.body: _house(chart, body.longitude) for body in chart.bodies
        } | {BodyName.SOUTH_NODE: _house(chart, node.longitude + 180.0)}
        assert len(exact.cusp_signs) == 12
    assert kept and dropped


# Independent reference (#223): the same synthetic births at three round places, with the
# angles worked out by the closed-form spherical-astronomy formulas below rather than by the
# engine. Recorded settings: tropical zodiac, Placidus (the default), UT instants, mean
# obliquity without nutation. The recorded signs are the expected cusp-1 and cusp-10 labels.
REFERENCE_PLACES = (
    Birthplace(latitude=16.0, longitude=108.0),
    Birthplace(latitude=-34.0, longitude=151.0),
    Birthplace(latitude=52.0, longitude=0.0),
)
REFERENCE_SIGNS = {
    (SYNTHETIC_BIRTHS[0], REFERENCE_PLACES[0]): (ZodiacSign.TAURUS, ZodiacSign.CAPRICORN),
    (SYNTHETIC_BIRTHS[0], REFERENCE_PLACES[1]): (ZodiacSign.TAURUS, ZodiacSign.PISCES),
    (SYNTHETIC_BIRTHS[0], REFERENCE_PLACES[2]): (ZodiacSign.SAGITTARIUS, ZodiacSign.LIBRA),
    (SYNTHETIC_BIRTHS[1], REFERENCE_PLACES[0]): (ZodiacSign.LEO, ZodiacSign.TAURUS),
    (SYNTHETIC_BIRTHS[1], REFERENCE_PLACES[1]): (ZodiacSign.LIBRA, ZodiacSign.CANCER),
    (SYNTHETIC_BIRTHS[1], REFERENCE_PLACES[2]): (ZodiacSign.GEMINI, ZodiacSign.CAPRICORN),
    (SYNTHETIC_BIRTHS[2], REFERENCE_PLACES[0]): (ZodiacSign.SCORPIO, ZodiacSign.LEO),
    (SYNTHETIC_BIRTHS[2], REFERENCE_PLACES[1]): (ZodiacSign.CAPRICORN, ZodiacSign.LIBRA),
    (SYNTHETIC_BIRTHS[2], REFERENCE_PLACES[2]): (ZodiacSign.LEO, ZodiacSign.TAURUS),
    (SYNTHETIC_BIRTHS[3], REFERENCE_PLACES[0]): (ZodiacSign.VIRGO, ZodiacSign.GEMINI),
    (SYNTHETIC_BIRTHS[3], REFERENCE_PLACES[1]): (ZodiacSign.SCORPIO, ZodiacSign.LEO),
    (SYNTHETIC_BIRTHS[3], REFERENCE_PLACES[2]): (ZodiacSign.CANCER, ZodiacSign.AQUARIUS),
}
# Nutation is left out of the reference; it moves the angles by well under this.
REFERENCE_TOLERANCE_DEG = 0.01


def _reference_angles(born: datetime, place: Birthplace) -> tuple[float, float]:
    """Ascendant and midheaven from sidereal time and obliquity (Meeus, ch. 12, 13 and 22)."""

    julian_day = born.timestamp() / 86400.0 + 2440587.5
    days = julian_day - 2451545.0
    centuries = days / 36525.0
    sidereal = (
        280.46061837
        + 360.98564736629 * days
        + 0.000387933 * centuries**2
        - centuries**3 / 38710000.0
    )
    ramc = math.radians((sidereal + place.longitude) % 360.0)
    obliquity = math.radians(
        23.0
        + 26.0 / 60.0
        + (21.448 - 46.8150 * centuries - 0.00059 * centuries**2 + 0.001813 * centuries**3) / 3600.0
    )
    latitude = math.radians(place.latitude)
    midheaven = math.atan2(math.sin(ramc), math.cos(ramc) * math.cos(obliquity))
    ascendant = math.atan2(
        math.cos(ramc),
        -(math.sin(ramc) * math.cos(obliquity) + math.tan(latitude) * math.sin(obliquity)),
    )
    return math.degrees(ascendant) % 360.0, math.degrees(midheaven) % 360.0


@pytest.mark.parametrize(("born", "place"), list(REFERENCE_SIGNS))
def test_angles_and_angular_cusps_match_an_independent_reference(
    engine: NatalChartEngine, born: datetime, place: Birthplace
) -> None:
    ascendant, midheaven = _reference_angles(born, place)
    expected = REFERENCE_SIGNS[(born, place)]
    # The recorded labels and the formulas agree, so neither can drift on its own.
    assert (sign_for_longitude(ascendant), sign_for_longitude(midheaven)) == expected
    chart = _chart(engine, born, place)
    assert chart.angles is not None and chart.houses is not None
    assert angular_distance(chart.angles.ascendant, ascendant) < REFERENCE_TOLERANCE_DEG
    assert angular_distance(chart.angles.midheaven, midheaven) < REFERENCE_TOLERANCE_DEG
    assert angular_distance(chart.houses[0].longitude, ascendant) < REFERENCE_TOLERANCE_DEG
    assert angular_distance(chart.houses[9].longitude, midheaven) < REFERENCE_TOLERANCE_DEG
    sharp = house_frame(engine, chart, place, time_error_minutes=0.0, place_margin_deg=0.0)
    assert sharp is not None
    assert (sharp.cusp_signs[1], sharp.cusp_signs[10]) == expected


def test_a_body_near_a_cusp_loses_its_house_but_keeps_it_with_a_reliable_time(
    engine: NatalChartEngine,
) -> None:
    # Find a synthetic birth minute with the ascendant 2° past the Sun: Sun in house 12, near 1.
    day = datetime(2001, 1, 15, tzinfo=UTC)
    for minute in range(0, 1440, 2):
        chart = _chart(engine, day + timedelta(minutes=minute))
        assert chart.angles is not None
        if 1.5 < (chart.angles.ascendant - chart.body(BodyName.SUN).longitude) % 360.0 < 2.5:
            break
    else:
        pytest.fail("no synthetic minute puts the ascendant just past the Sun")
    sharp = house_frame(engine, chart, PLACE, time_error_minutes=0.0, place_margin_deg=0.0)
    loose = house_frame(engine, chart, PLACE, time_error_minutes=EXACT_TIME_ERROR_MINUTES)
    assert sharp is not None and loose is not None
    assert sharp.natal_houses[BodyName.SUN] == 12
    assert BodyName.SUN not in loose.natal_houses
    # A transiting longitude on that cusp has no house either; mid-house it keeps one.
    assert chart.angles is not None
    ascendant = chart.angles.ascendant
    assert loose.house_of(ascendant + 1.0) is None and loose.house_of(ascendant - 1.0) is None
    assert sharp.house_of(ascendant + 1.0) == 1 and sharp.house_of(ascendant - 1.0) == 12
    assert chart.houses is not None
    middle = (
        chart.houses[0].longitude
        + ((chart.houses[1].longitude - chart.houses[0].longitude) % 360.0) / 2.0
    )
    assert loose.house_of(middle) == 1


def test_an_approximate_window_holds_no_house_and_no_angle(engine: NatalChartEngine) -> None:
    # The "Sáng 06-10h" window, stored at its 08:00 midpoint on a synthetic date.
    stored = datetime.combine(date(1990, 3, 14), time(8), tzinfo=DAILY_TIMEZONE)
    chart = _chart(engine, stored.astimezone(UTC), precision=TimePrecision.APPROXIMATE)
    assert chart.houses is not None  # houses on the record are still not trusted
    eligibility = contact_eligibility(chart)
    assert birth_time_error_minutes(eligibility) == 180.0
    frame = daily_house_frame(engine, chart, PLACE)
    assert frame is not None
    # Over ±3 h every cusp sweeps more than a house: nothing holds.
    assert not frame.natal_houses and not frame.cusp_signs and not frame.intercepted_signs
    assert frame.labels().chart_ruler is None
    assert not set(ChartAngle) & set(natal_domains(engine, chart, houses=frame))
    for offset in range(5):
        selection = select_daily_sky(
            engine,
            chart,
            START + timedelta(days=offset),
            include_trend_windows=False,
            birthplace=PLACE,
        )
        assert selection.moon.natal_house is None
        for item in (*selection.today, *selection.days, *selection.weeks):
            assert item.transit_house is None and item.natal_house is None
            assert not item.ruled_houses
            assert not isinstance(item.natal_body, ChartAngle)


def test_no_frame_without_a_time_a_place_or_a_matching_birthplace(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    unknown = _chart(engine, SYNTHETIC_BIRTHS[0], precision=TimePrecision.UNKNOWN)
    night_at = datetime.combine(date(1990, 3, 14), time(23), tzinfo=DAILY_TIMEZONE)
    night = _chart(engine, night_at.astimezone(UTC), precision=TimePrecision.APPROXIMATE)
    jyotish = engine.calculate_chart(
        ChartInput(
            utc_datetime=SYNTHETIC_BIRTHS[0], latitude=PLACE.latitude, longitude=PLACE.longitude
        ),
        CalculationConfig.jyotish_recommended(),
    )
    withheld = charts[0].model_copy(update={"houses": None, "angles": None})
    for chart in (unknown, night, jyotish, withheld):
        assert daily_house_frame(engine, chart, PLACE) is None
    assert daily_house_frame(engine, charts[0], None) is None
    # Coordinates that do not reproduce the chart's own cusps are refused, not trusted.
    elsewhere = Birthplace(latitude=PLACE.latitude + 0.5, longitude=PLACE.longitude)
    assert daily_house_frame(engine, charts[0], elsewhere) is None
    assert daily_house_frame(engine, charts[0], PLACE) is not None
    for chart in (unknown, night):
        selection = select_daily_sky(
            engine, chart, START, include_trend_windows=False, birthplace=PLACE
        )
        assert selection.houses is None and selection.moon.natal_house is None
    with pytest.raises(ValueError):
        Birthplace(latitude=91.0, longitude=0.0)


def _angle_contacts(contacts: tuple[DayContact, ...]) -> list[DayContact]:
    return [
        candidate
        for item in contacts
        for candidate in (item, *item.merged)
        if isinstance(candidate.natal_body, ChartAngle)
    ]


def test_angles_are_contact_points_only_with_a_reliable_time(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    chart = charts[0]
    reliable = daily_house_frame(engine, chart, PLACE, exact_time_error_minutes=0.0)
    typed = daily_house_frame(engine, chart, PLACE)
    assert reliable is not None and typed is not None
    found: list[tuple[DayContact, NatalDomains]] = []
    domains = natal_domains(engine, chart, houses=reliable)
    assert set(ChartAngle) <= set(domains)
    for offset in range(8):
        day = START + timedelta(days=offset)
        found += [
            (item, domains)
            for item in _angle_contacts(scan_day(engine, chart, day, houses=reliable))
        ]
        # With the ±15 min typed-time error the angle spreads further than any orb: none hold.
        assert not _angle_contacts(scan_day(engine, chart, day, houses=typed))
    assert found
    for item, scanned in found:
        low, high = scanned[item.natal_body]
        assert high - low < 2 * 1.5  # the place margin alone
        at = item.closest_at or item.window_start + (item.window_end - item.window_start) / 2
        longitude = engine.transiting_position(item.transit_body, at, chart.config).longitude
        for natal in (low, high):
            # Inside the orb for every angle position in the range (worst case).
            assert abs(angular_distance(longitude, natal) - item.exact_angle) <= item.orb_limit
        assert item.natal_house == (1 if item.natal_body is ChartAngle.ASCENDANT else 10)
        assert item.ruled_houses == ()
    for angle in ChartAngle:
        low, high = typed.angle_domain(angle)
        assert (high - low) / 2.0 > 3.0  # wider than the widest transit orb
    # Approximate and date-only charts never get angle points, whatever frame is passed.
    stored = datetime.combine(date(1990, 3, 14), time(15), tzinfo=DAILY_TIMEZONE)
    window = _chart(engine, stored.astimezone(UTC), precision=TimePrecision.APPROXIMATE)
    window_frame = daily_house_frame(engine, window, PLACE)
    assert not set(ChartAngle) & set(natal_domains(engine, window, houses=window_frame))
    unknown = _chart(engine, SYNTHETIC_BIRTHS[0], precision=TimePrecision.UNKNOWN)
    assert not set(ChartAngle) & set(natal_domains(engine, unknown, houses=reliable))


def test_contacts_carry_only_stable_house_labels(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    seen_transit = seen_dropped = 0
    for chart in charts[:2]:
        frame = daily_house_frame(engine, chart, PLACE)
        assert frame is not None
        for offset in range(4):
            day = START + timedelta(days=offset)
            for item in scan_day(engine, chart, day, houses=frame):
                assert item.natal_house == frame.natal_house(item.natal_body)
                assert item.ruled_houses == frame.ruled_houses(item.natal_body)
                ends = {
                    frame.house_of(
                        engine.transiting_position(item.transit_body, at, chart.config).longitude
                    )
                    for at in (item.window_start, item.window_end)
                }
                if item.transit_house is not None:
                    seen_transit += 1
                    assert ends == {item.transit_house}
                else:
                    seen_dropped += 1
                if len(ends) > 1 or None in ends:
                    assert item.transit_house is None
    assert seen_transit and seen_dropped


def test_cusp_signs_rulers_and_interceptions_from_fixed_cusps() -> None:
    # Aries on cusps 1 and 2, Libra on 7 and 8: Taurus and Scorpio are intercepted.
    cusps = (5.0, 25.0, 70.0, 100.0, 130.0, 160.0, 185.0, 205.0, 250.0, 280.0, 310.0, 340.0)
    frame = HouseFrame.from_samples((CuspSample(cusps=cusps, ascendant=5.0, midheaven=280.0),))
    assert frame.cusp_signs[1] is frame.cusp_signs[2] is ZodiacSign.ARIES
    assert frame.intercepted_signs == {2: (ZodiacSign.TAURUS,), 8: (ZodiacSign.SCORPIO,)}
    assert frame.chart_ruler is BodyName.MARS
    assert frame.ruled_houses(BodyName.MARS) == (1, 2)
    assert frame.ruled_houses(BodyName.VENUS) == (7, 8)
    assert frame.ruled_houses(BodyName.MERCURY) == (3, 6)
    assert frame.ruled_houses(BodyName.URANUS) == (11,)
    # Scorpio is on no cusp: its modern ruler adds no house (rulers only add houses, 1.2).
    assert frame.ruled_houses(BodyName.PLUTO) == ()
    assert frame.ruled_houses(ChartAngle.ASCENDANT) == ()
    labels = frame.labels()
    # Traditional rulers are metadata where they differ (Aquarius 11, Pisces 12).
    assert labels.traditional_rulers == {11: BodyName.SATURN, 12: BodyName.JUPITER}
    assert TRADITIONAL_RULERS[ZodiacSign.SCORPIO] is BodyName.MARS
    assert labels.ruled_houses[BodyName.MARS] == (1, 2)
    assert frame.natal_house(ChartAngle.ASCENDANT) == 1
    assert frame.natal_house(ChartAngle.MIDHEAVEN) == 10
    whole = HouseFrame.from_samples(
        (CuspSample(cusps=cusps, ascendant=5.0, midheaven=280.0),),
        house_system=HouseSystem.WHOLE_SIGN,
    )
    assert whole.natal_house(ChartAngle.MIDHEAVEN) is None

    # A second birth moment with cusp 1 in Pisces: cusp 1's sign, the chart ruler and the
    # interceptions no longer hold; the rest does.
    shifted = (355.0, *cusps[1:])
    moving = HouseFrame.from_samples(
        (
            CuspSample(cusps=cusps, ascendant=5.0, midheaven=280.0),
            CuspSample(cusps=shifted, ascendant=355.0, midheaven=280.0),
        )
    )
    assert 1 not in moving.cusp_signs and moving.chart_ruler is None
    assert moving.intercepted_signs == {}
    assert moving.ruled_houses(BodyName.MARS) == (2,)
    assert moving.angle_domain(ChartAngle.ASCENDANT) == (355.0, 365.0)
    # A longitude between the two positions of cusp 1 has no house; a narrow house inside an
    # arc is caught even when both ends agree.
    assert moving.house_of(0.0) is None and moving.house_of(10.0) == 1
    assert frame.house_of_span(20.0, 30.0) is None  # cusp 2 (25°) lies inside the arc
    assert frame.house_of_span(26.0, 60.0) is None  # a sign or longer: never one house
    assert frame.house_of_span(30.0, 59.9) == 2


def test_no_new_stored_data() -> None:
    """C2b reads only what is already stored; it adds no field, table, log or persistence."""

    # The stored chart and birth supplement keep exactly their fields.
    assert set(NatalChart.model_fields) == {
        "chart_type",
        "julian_day_ut",
        "bodies",
        "houses",
        "angles",
        "aspects",
        "house_system",
        "time_precision",
        "provenance",
        "config",
        "config_hash",
        "nakshatras",
        "graha_drishti",
    }
    assert {item.name for item in dataclasses.fields(BirthSupplement)} == {
        "birth_time_mode",
        "birth_time_ciphertext",
        "approx_window",
        "birth_place_ciphertext",
        "consent_version",
    }
    root = Path(__file__).resolve().parents[2] / "app"
    module = root / "domains" / "daily" / "house_confidence.py"
    imported = {
        node.module
        for node in ast.walk(ast.parse(module.read_text()))
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(ast.parse(module.read_text()))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert all(
        name.startswith(("app.domains.astro", "collections", "dataclasses", "enum", "math"))
        or name == "__future__"
        for name in imported
    ), imported
    # No persistence layer or log line knows the frame or the selection yet.
    for path in root.rglob("*.py"):
        if path.name in {"house_confidence.py", "sky_selection.py"}:
            source = path.read_text()
            assert "import logging" not in source and "getLogger" not in source
            assert "print(" not in source
            continue
        source = path.read_text()
        for name in ("house_confidence", "HouseFrame", "HouseLabels", "select_daily_sky"):
            assert name not in source, (path, name)


# Independent reference (C2b, issue #223): the cusps are recomputed here with closed-form
# spherical astronomy, without Swiss Ephemeris. Recorded settings: tropical zodiac, Placidus,
# mean sidereal time (IAU 1982) and mean obliquity (IAU 1980), no nutation. The nutation the
# engine adds moves the angles by a few thousandths of a degree, inside this tolerance. It has its
# own name so the tighter REFERENCE_TOLERANCE_DEG above is not overwritten (issue #262).
PLACIDUS_REFERENCE_TOLERANCE_DEG = 0.05


def test_the_angle_reference_keeps_its_own_tolerance() -> None:
    assert REFERENCE_TOLERANCE_DEG == 0.01
    assert PLACIDUS_REFERENCE_TOLERANCE_DEG == 0.05


def _reference_placidus(born: datetime, place: Birthplace) -> dict[int, float]:
    jd = born.timestamp() / 86400.0 + 2440587.5
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t
    ramc = math.radians((gmst + place.longitude) % 360.0)
    eps = math.radians(23.439291 - 0.0130042 * t)
    phi = math.radians(place.latitude)

    def ecliptic(ra: float) -> float:
        return math.atan2(math.sin(ra), math.cos(ra) * math.cos(eps))

    def semi_diurnal(lon: float) -> float:
        decl = math.asin(math.sin(eps) * math.sin(lon))
        return math.acos(-math.tan(phi) * math.tan(decl))

    def cusp(fraction: float, above: bool) -> float:
        lon = ecliptic(ramc + (fraction if above else 1.0 - fraction) * math.pi / 2.0)
        for _ in range(60):
            sda = semi_diurnal(lon)
            if above:
                ra = ramc + fraction * sda
            else:
                # Below the horizon the cusp is measured back from the IC along the
                # nocturnal semi-arc: cusp 2 at two thirds, cusp 3 at one third.
                ra = ramc + math.pi - fraction * (math.pi - sda)
            lon = ecliptic(ra)
        return math.degrees(lon) % 360.0

    mc = math.degrees(ecliptic(ramc)) % 360.0
    asc = (
        math.degrees(
            math.atan2(
                math.cos(ramc),
                -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps)),
            )
        )
        % 360.0
    )
    cusps = {
        10: mc,
        11: cusp(1 / 3, above=True),
        12: cusp(2 / 3, above=True),
        1: asc,
        2: cusp(2 / 3, above=False),
        3: cusp(1 / 3, above=False),
    }
    return cusps | {(number + 5) % 12 + 1: (lon + 180.0) % 360.0 for number, lon in cusps.items()}


def test_engine_cusps_match_an_independent_placidus_reference(
    charts: tuple[NatalChart, ...],
) -> None:
    for born, chart in zip(SYNTHETIC_BIRTHS, charts, strict=True):
        assert chart.house_system is HouseSystem.PLACIDUS
        assert chart.houses is not None and chart.angles is not None
        reference = _reference_placidus(born, PLACE)
        for house in chart.houses:
            assert angular_distance(house.longitude, reference[house.number]) < (
                PLACIDUS_REFERENCE_TOLERANCE_DEG
            ), (born, house.number)
            assert house.sign == sign_for_longitude(reference[house.number])
        assert (
            angular_distance(chart.angles.ascendant, reference[1])
            < PLACIDUS_REFERENCE_TOLERANCE_DEG
        )
        assert (
            angular_distance(chart.angles.midheaven, reference[10])
            < PLACIDUS_REFERENCE_TOLERANCE_DEG
        )
