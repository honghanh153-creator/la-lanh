"""R02 (audit 2026-10-22, US-22 AC07): unknown-time contacts must hold on the whole date domain.

Dense 10-minute sampling is the independent check here; the solver itself uses ends + stations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domains.astro.aspects import (
    ASPECTS,
    angular_distance,
    orb_bounds,
    relationship_chart_orb_limit,
    synastry_orb_limit,
)
from app.domains.astro.engine import (
    BODY_IDS,
    DATE_DOMAIN_HALF_WIDTH_DAYS,
    NatalChartEngine,
    midpoint_longitude,
)
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    NatalChart,
    TimePrecision,
)

CONFIG = CalculationConfig.western_recommended()
IDS = dict(BODY_IDS)
STEP = 10 / 1440


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _exact(engine: NatalChartEngine, when: datetime, lat: float, lon: float) -> NatalChart:
    return engine.calculate_chart(
        ChartInput(utc_datetime=when.astimezone(UTC), latitude=lat, longitude=lon), CONFIG
    )


def _unknown(engine: NatalChartEngine, day: tuple[int, int, int], zone: str) -> NatalChart:
    """Mirror BirthService.calculate_transient_chart for an unknown time: local noon, no Moon,
    houses or angles."""

    chart = _exact(engine, datetime(*day, 12, tzinfo=ZoneInfo(zone)), 10.82, 106.63)
    return chart.model_copy(
        update={
            "time_precision": TimePrecision.UNKNOWN,
            "bodies": tuple(b for b in chart.bodies if b.body is not BodyName.MOON),
            "aspects": tuple(a for a in chart.aspects if BodyName.MOON not in {a.body_a, a.body_b}),
            "houses": None,
            "angles": None,
        }
    )


def _samples(engine: NatalChartEngine, chart: NatalChart, body: BodyName) -> list[float]:
    if chart.time_precision is not TimePrecision.UNKNOWN:
        return [chart.body(body).longitude]
    start = chart.julian_day_ut - DATE_DOMAIN_HALF_WIDTH_DAYS
    count = round(2 * DATE_DOMAIN_HALF_WIDTH_DAYS / STEP)
    return [
        engine._body_position(start + i * STEP, body, IDS[body]).longitude for i in range(count + 1)
    ]


def _unwrap(values: list[float], base: float) -> list[float]:
    return [base + ((v - base + 180.0) % 360.0 - 180.0) for v in values]


@pytest.mark.parametrize(
    ("day", "body"),
    [
        ((1992, 7, 7), BodyName.SUN),
        ((2023, 8, 24), BodyName.MERCURY),  # Mercury stations retrograde 2023-08-23 ~20:00 UTC
        ((2024, 3, 20), BodyName.SUN),  # crosses 0° Aries (and Pisces -> Aries)
        ((1990, 1, 1), BodyName.VENUS),  # Venus retrograde
        ((2000, 6, 15), BodyName.PLUTO),
    ],
)
def test_domain_contains_every_dense_sample_within_a_hundredth(
    engine: NatalChartEngine, day: tuple[int, int, int], body: BodyName
) -> None:
    chart = _unknown(engine, day, "Asia/Ho_Chi_Minh")
    low, high = engine.longitude_domains(chart)[body]
    dense = _unwrap(_samples(engine, chart, body), low)
    assert low <= min(dense) + 1e-9 and max(dense) <= high + 1e-9
    assert min(dense) - low <= 0.01 and high - max(dense) <= 0.01
    assert high - low < 4.0  # unwrapped across 0°, never a 360° span


def test_a_station_inside_the_window_bounds_the_domain(engine: NatalChartEngine) -> None:
    chart = _unknown(engine, (2023, 8, 24), "Asia/Ho_Chi_Minh")
    start = chart.julian_day_ut - DATE_DOMAIN_HALF_WIDTH_DAYS
    end = chart.julian_day_ut + DATE_DOMAIN_HALF_WIDTH_DAYS
    ends = [engine._body_position(t, BodyName.MERCURY, 2) for t in (start, end)]
    assert ends[0].longitude_speed > 0 > ends[1].longitude_speed  # precondition: a station
    high = engine.longitude_domains(chart)[BodyName.MERCURY][1]
    assert high > max(e.longitude for e in ends)  # the maximum is the station, not an end


def test_exact_charts_have_point_domains_and_unchanged_contacts(engine: NatalChartEngine) -> None:
    a = _exact(engine, datetime(1990, 1, 1, 5, 15, tzinfo=UTC), 21.03, 105.85)
    b = _exact(engine, datetime(1992, 7, 7, 5, tzinfo=UTC), 10.82, 106.63)
    assert all(low == high for low, high in engine.longitude_domains(b).values())
    expected = set()
    for body_a in a.bodies:
        for body_b in b.bodies:
            separation = angular_distance(body_a.longitude, body_b.longitude)
            for kind, angle, _ in ASPECTS:
                orb = abs(separation - angle)
                if orb <= synastry_orb_limit(body_a.body, body_b.body, kind):
                    expected.add((body_a.body, body_b.body, kind, round(orb, 4)))
                    break
    contacts = engine.calculate_synastry(a, b).contacts
    assert {(c.body_a, c.body_b, c.kind, c.orb) for c in contacts} == expected


def test_audit_witness_sun_opposition_is_dropped_for_an_unknown_time(
    engine: NatalChartEngine,
) -> None:
    """Noon orb 4.8033° but 5.2800° at the end of the local day, limit 5°: not certain."""

    a = _exact(engine, datetime(1990, 1, 1, 5, 15, tzinfo=UTC), 21.0285, 105.8542)
    b = _unknown(engine, (1992, 7, 7), "Asia/Ho_Chi_Minh")
    noon = b.model_copy(update={"time_precision": TimePrecision.EXACT})
    key = (BodyName.SUN, BodyName.SUN, "opposition")
    assert key in {
        (c.body_a, c.body_b, c.kind) for c in engine.calculate_synastry(a, noon).contacts
    }
    assert key not in {
        (c.body_a, c.body_b, c.kind) for c in engine.calculate_synastry(a, b).contacts
    }


PAIRS = [
    ((1990, 1, 1), (1992, 7, 7)),
    ((1985, 3, 20), (1987, 9, 23)),
    ((1999, 12, 31), (2001, 6, 21)),
    ((1994, 2, 14), (1994, 2, 15)),
    ((2003, 8, 27), (1979, 11, 5)),
]


@pytest.mark.parametrize(("day_a", "day_b"), PAIRS)
@pytest.mark.parametrize("both_unknown", [False, True])
def test_every_kept_contact_is_within_orb_at_every_sampled_instant(
    engine: NatalChartEngine,
    day_a: tuple[int, int, int],
    day_b: tuple[int, int, int],
    both_unknown: bool,
) -> None:
    a = (
        _unknown(engine, day_a, "Asia/Bangkok")
        if both_unknown
        else _exact(engine, datetime(*day_a, 3, tzinfo=UTC), 21.03, 105.85)
    )
    b = _unknown(engine, day_b, "Asia/Ho_Chi_Minh")
    for contact in engine.calculate_synastry(a, b).contacts:
        if contact.body_a not in IDS or contact.body_b not in IDS:
            continue
        limit = synastry_orb_limit(contact.body_a, contact.body_b, contact.kind)
        worst = max(
            abs(angular_distance(la, lb) - contact.exact_angle)
            for la in _samples(engine, a, contact.body_a)
            for lb in _samples(engine, b, contact.body_b)
        )
        assert worst <= limit + 1e-9, contact
        assert contact.orb >= round(worst, 4) - 1e-4  # reported orb is the worst case


@pytest.mark.parametrize(("day_a", "day_b"), PAIRS[:3])
def test_every_kept_composite_aspect_is_within_orb_at_every_sampled_instant(
    engine: NatalChartEngine, day_a: tuple[int, int, int], day_b: tuple[int, int, int]
) -> None:
    a = _exact(engine, datetime(*day_a, 3, tzinfo=UTC), 21.03, 105.85)
    b = _unknown(engine, day_b, "Asia/Ho_Chi_Minh")
    composite = engine.calculate_composite_midpoint(a, b)
    for aspect in composite.aspects:
        tracks = {
            body: [
                midpoint_longitude(a.body(body).longitude, lb) for lb in _samples(engine, b, body)
            ]
            for body in (aspect.body_a, aspect.body_b)
            if body in IDS
        }
        if len(tracks) < 2:
            continue
        worst = max(
            abs(angular_distance(x, y) - aspect.exact_angle)
            for x, y in zip(tracks[aspect.body_a], tracks[aspect.body_b], strict=True)
        )
        assert worst <= relationship_chart_orb_limit(aspect.kind) + 1e-9, aspect


@pytest.mark.parametrize(
    ("domain_a", "domain_b", "angle", "expected"),
    [
        ((10.0, 10.0), (190.0, 190.0), 180.0, (0.0, 0.0)),  # exact control
        ((10.0, 10.0), (14.0, 14.0), 0.0, (4.0, 4.0)),  # point domains = plain orb
        ((10.0, 12.0), (14.0, 15.0), 0.0, (2.0, 5.0)),
        ((358.0, 361.0), (2.0, 3.0), 0.0, (1.0, 5.0)),  # domain unwrapped across 0°
        ((0.0, 0.0), (175.0, 186.0), 180.0, (0.0, 6.0)),  # crosses the exact angle
        ((0.0, 0.0), (176.0, 184.0), 120.0, (56.0, 60.0)),  # crosses the 180° turn
        ((0.0, 0.0), (-3.0, 2.0), 60.0, (57.0, 60.0)),  # crosses the 0° turn
    ],
)
def test_orb_bounds_breakpoints(
    domain_a: tuple[float, float],
    domain_b: tuple[float, float],
    angle: float,
    expected: tuple[float, float],
) -> None:
    low, high = orb_bounds(domain_a, domain_b, angle)
    assert (round(low, 9), round(high, 9)) == expected
