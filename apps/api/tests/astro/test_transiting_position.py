from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, CalculationConfig


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
