from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, CalculationConfig, ChartInput


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


@pytest.mark.parametrize(
    "config", [CalculationConfig.western_recommended(), CalculationConfig.jyotish_recommended()]
)
def test_single_body_matches_the_daily_transit_snapshot(
    engine: NatalChartEngine, config: CalculationConfig
) -> None:
    snapshot = engine.calculate_daily_transit(date(2026, 11, 2), config)
    noon = datetime(2026, 11, 2, 12, tzinfo=UTC)
    for expected in snapshot.bodies:
        assert engine.transiting_position(expected.body, noon, config) == expected


def test_rejects_naive_instants_and_derived_bodies(engine: NatalChartEngine) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        engine.transiting_position(BodyName.MOON, datetime(2026, 11, 2, 12))
    with pytest.raises(ValueError, match="south_node"):
        engine.transiting_position(BodyName.SOUTH_NODE, datetime(2026, 11, 2, 12, tzinfo=UTC))


@pytest.mark.parametrize(
    "config", [CalculationConfig.western_recommended(), CalculationConfig.jyotish_recommended()]
)
def test_all_bodies_at_an_instant_match_the_daily_transit_snapshot(
    engine: NatalChartEngine, config: CalculationConfig
) -> None:
    noon = datetime(2026, 11, 2, 12, tzinfo=UTC)
    assert engine.transiting_positions(noon, config) == (
        engine.calculate_daily_transit(date(2026, 11, 2), config).bodies
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        engine.transiting_positions(datetime(2026, 11, 2, 12))


def test_longitude_domains_can_bound_an_approximate_time_window(
    engine: NatalChartEngine,
) -> None:
    born = datetime(1993, 4, 18, 8, 0, tzinfo=UTC)  # synthetic
    chart = engine.calculate_chart(ChartInput(utc_datetime=born, latitude=21.0, longitude=105.8))
    points = engine.longitude_domains(chart)
    assert all(low == high for low, high in points.values())
    narrow = engine.longitude_domains(chart, half_width_days=1.0 / 24.0)
    wide = engine.longitude_domains(chart, half_width_days=3.0 / 24.0)
    for body, (low, high) in wide.items():
        point = points[body][0]
        assert (low <= point + 1e-9 and point - 1e-9 <= high) or low <= point + 360.0 <= high
        assert narrow[body][0] >= low - 1e-9 and narrow[body][1] <= high + 1e-9
    moon_low, moon_high = wide[BodyName.MOON]
    assert 2.5 < moon_high - moon_low < 4.5  # ~13°/day over six hours
    with pytest.raises(ValueError, match="half_width_days"):
        engine.longitude_domains(chart, half_width_days=-1.0)
