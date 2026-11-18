"""Daily step 2: transit contacts proven over an approximate birth-time window.

Synthetic charts only (fixed dates, a Vietnamese and a Saudi birthplace); nothing here is a real
person's data.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domains.astro.aspects import angular_distance, transit_orb_limit
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    NatalChart,
    TimePrecision,
    TransitPhase,
)
from app.domains.daily.interval_transits import (
    INTERVAL_TRANSIT_POLICY,
    INTERVAL_TRANSIT_TARGETS,
    interval_phase,
    interval_transit_to_natal,
    window_half_width_days,
)
from app.domains.daily.sky_selection import (
    APPROXIMATE_HALF_WIDTH_DAYS,
    EXACT_ORB,
    NIGHT_HALF_WIDTH_DAYS,
)
from app.domains.readings.planner import _PERSONAL_BODIES


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _window_chart(
    engine: NatalChartEngine, local_day: date, hour: int, zone: str = "Asia/Ho_Chi_Minh"
) -> NatalChart:
    """A synthetic chart stored the way the birth service stores a window midpoint."""

    stored = datetime.combine(local_day, time(hour), tzinfo=ZoneInfo(zone)).astimezone(UTC)
    chart = engine.calculate_chart(ChartInput(utc_datetime=stored, latitude=16.0, longitude=108.0))
    return chart.model_copy(update={"time_precision": TimePrecision.APPROXIMATE})


def test_targets_are_the_planners_personal_bodies_without_the_moon() -> None:
    assert set(INTERVAL_TRANSIT_TARGETS) == _PERSONAL_BODIES - {BodyName.MOON}


def test_the_window_comes_from_the_birthplace_zone_and_unknown_zones_fail_closed(
    engine: NatalChartEngine,
) -> None:
    # A 23:00 birth in Riyadh is 03:00 in Vietnam: read in the wrong zone it would look like the
    # narrow 00-06 h window (Codex point 1).
    riyadh = _window_chart(engine, date(1993, 4, 2), 23, "Asia/Riyadh")
    assert window_half_width_days(riyadh, "Asia/Ho_Chi_Minh") == APPROXIMATE_HALF_WIDTH_DAYS
    assert window_half_width_days(riyadh, "Asia/Riyadh") == NIGHT_HALF_WIDTH_DAYS
    assert window_half_width_days(riyadh, None) == NIGHT_HALF_WIDTH_DAYS
    assert window_half_width_days(riyadh, "Not/AZone") == NIGHT_HALF_WIDTH_DAYS
    dawn = _window_chart(engine, date(1993, 4, 2), 3)
    assert window_half_width_days(dawn, "Asia/Ho_Chi_Minh") == APPROXIMATE_HALF_WIDTH_DAYS
    assert window_half_width_days(dawn, None) == NIGHT_HALF_WIDTH_DAYS


def test_only_a_western_approximate_chart_gets_a_snapshot(engine: NatalChartEngine) -> None:
    observed = datetime(2026, 11, 18, 12, tzinfo=UTC)
    chart = _window_chart(engine, date(1995, 6, 10), 15)
    exact = chart.model_copy(update={"time_precision": TimePrecision.EXACT})
    assert interval_transit_to_natal(engine, exact, observed, birth_timezone=None) is None
    jyotish = chart.model_copy(update={"config": CalculationConfig.jyotish_recommended()})
    assert interval_transit_to_natal(engine, jyotish, observed, birth_timezone=None) is None
    snapshot = interval_transit_to_natal(engine, chart, observed, birth_timezone="Asia/Ho_Chi_Minh")
    assert snapshot is not None
    assert snapshot.orb_policy_version == INTERVAL_TRANSIT_POLICY
    assert snapshot.config_hash == chart.config_hash
    with pytest.raises(ValueError):
        interval_transit_to_natal(engine, chart, datetime(2026, 11, 18), birth_timezone=None)


@pytest.mark.parametrize(
    ("transit", "future", "domain", "expected"),
    [
        (100.05, 100.10, (99.95, 100.15), TransitPhase.EXACT),  # whole window within 0.2°
        (100.0, 100.5, (99.0, 101.0), None),  # the exact point is inside the window
        (100.0, 100.5, (100.1, 101.0), None),  # exact for part of the window only
        (100.0, 100.5, (102.0, 104.0), TransitPhase.APPROACHING),
        (100.0, 99.5, (102.0, 104.0), TransitPhase.SEPARATING),
        (359.0, 359.5, (361.0, 362.0), TransitPhase.APPROACHING),  # across 0°
        (100.0, 100.0 + 1e-9, (102.0, 104.0), TransitPhase.APPROACHING),  # near a station
    ],
)
def test_interval_phase_is_kept_only_when_the_whole_window_agrees(
    transit: float,
    future: float,
    domain: tuple[float, float],
    expected: TransitPhase | None,
) -> None:
    assert interval_phase(transit, future, domain, 0.0) is expected


def _point_phase(transit: float, future: float, natal: float, angle: float) -> TransitPhase:
    orb = abs(angular_distance(transit, natal) - angle)
    if orb <= EXACT_ORB:
        return TransitPhase.EXACT
    later = abs(angular_distance(future, natal) - angle)
    return TransitPhase.APPROACHING if later < orb else TransitPhase.SEPARATING


@pytest.mark.parametrize(
    ("local_day", "hour", "zone"),
    [
        (date(1990, 3, 14), 8, "Asia/Ho_Chi_Minh"),
        (date(1997, 9, 2), 19, "Asia/Ho_Chi_Minh"),
        (date(1993, 4, 2), 23, "Asia/Riyadh"),
    ],
)
def test_every_contact_holds_for_every_birth_time_in_the_window(
    engine: NatalChartEngine, local_day: date, hour: int, zone: str
) -> None:
    """Dense oracle over 120 days: each kept contact is in orb, with the same phase, for every
    natal longitude in its domain; each is also a contact of the midpoint chart; and some
    midpoint contacts that the window cannot prove are dropped."""

    chart = _window_chart(engine, local_day, hour, zone)
    half = window_half_width_days(chart, zone)
    domains = engine.longitude_domains(chart, half_width_days=half)
    kept = 0
    dropped = 0
    for offset in range(120):
        observed = datetime(2026, 9, 1, 5, tzinfo=UTC) + timedelta(days=offset)
        snapshot = interval_transit_to_natal(engine, chart, observed, birth_timezone=zone)
        assert snapshot is not None
        point = engine.calculate_transit_to_natal(chart, observed)
        point_keys = {(c.transit_body, c.natal_body, c.kind): c for c in point.contacts}
        now = {p.body: p.longitude for p in engine.transiting_positions(observed, chart.config)}
        later = {
            p.body: p.longitude
            for p in engine.transiting_positions(observed + timedelta(hours=1), chart.config)
        }
        for contact in snapshot.contacts:
            kept += 1
            assert contact.natal_body in INTERVAL_TRANSIT_TARGETS
            low, high = domains[contact.natal_body]
            assert int(low // 30) == int(high // 30), "the natal sign holds over the window"
            limit = transit_orb_limit(contact.transit_body, contact.kind)
            for step in range(201):
                natal = low + (high - low) * step / 200
                orb = abs(angular_distance(now[contact.transit_body], natal) - contact.exact_angle)
                assert orb <= contact.orb + 1e-9
                assert contact.orb <= limit + 1e-4
                assert (
                    _point_phase(
                        now[contact.transit_body],
                        later[contact.transit_body],
                        natal,
                        contact.exact_angle,
                    )
                    is contact.phase
                )
            midpoint = point_keys.get((contact.transit_body, contact.natal_body, contact.kind))
            assert midpoint is not None, "a window contact is a midpoint contact too"
            assert midpoint.orb <= contact.orb + 1e-4
        dropped += sum(
            1
            for c in point.contacts
            if c.natal_body in INTERVAL_TRANSIT_TARGETS
            and (c.transit_body, c.natal_body, c.kind)
            not in {(k.transit_body, k.natal_body, k.kind) for k in snapshot.contacts}
        )
    assert kept > 0, "the window still proves some contacts"
    assert dropped > 0, "and drops some the midpoint alone would claim"


def test_a_placement_whose_sign_changes_in_the_window_gets_no_contact(
    engine: NatalChartEngine,
) -> None:
    # Find a synthetic day where the Sun crosses a sign boundary inside the night window.
    for offset in range(0, 400):
        day = date(1991, 1, 1) + timedelta(days=offset)
        chart = _window_chart(engine, day, 23)
        sun = engine.longitude_domains(chart, half_width_days=NIGHT_HALF_WIDTH_DAYS)[BodyName.SUN]
        if int(sun[0] // 30) != int(sun[1] // 30):
            break
    else:
        pytest.fail("no sign change found")
    for days in range(0, 60, 3):
        observed = datetime(2026, 9, 1, 5, tzinfo=UTC) + timedelta(days=days)
        snapshot = interval_transit_to_natal(engine, chart, observed, birth_timezone=None)
        assert snapshot is not None
        assert all(c.natal_body is not BodyName.SUN for c in snapshot.contacts)
