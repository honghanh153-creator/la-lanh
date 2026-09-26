from datetime import UTC, date, datetime

import pytest

from app.domains.astro.aspects import transit_orb_limit
from app.domains.astro.engine import NatalChartEngine, _transit_phase, midpoint_longitude
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    ChartType,
    HouseSystem,
    NodeMode,
    TransitPhase,
    ZodiacSign,
)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def test_positions_match_official_swetest_2103(engine: NatalChartEngine) -> None:
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    expected = {
        BodyName.SUN: 280.8142608,
        BodyName.MOON: 333.2676547,
        BodyName.MERCURY: 295.6728253,
        BodyName.VENUS: 306.2219607,
        BodyName.MARS: 250.0000853,
        BodyName.JUPITER: 95.1487939,
        BodyName.SATURN: 285.6574982,
        BodyName.URANUS: 275.7854403,
        BodyName.NEPTUNE: 282.0381065,
        BodyName.PLUTO: 227.0931178,
        BodyName.TRUE_NODE: 316.8703604,
        BodyName.CHIRON: 103.8132564,
    }
    assert {position.body for position in chart.bodies} == set(expected)
    for position in chart.bodies:
        assert position.longitude == pytest.approx(expected[position.body], abs=1e-7)


def test_placidus_houses_match_official_swetest(engine: NatalChartEngine) -> None:
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    assert chart.houses is not None
    assert chart.angles is not None
    assert [house.longitude for house in chart.houses] == pytest.approx(
        [
            119.4028849,
            146.9178299,
            177.3583594,
            209.5801771,
            241.0047058,
            270.6230107,
            299.4028849,
            326.9178299,
            357.3583594,
            29.5801771,
            61.0047058,
            90.6230107,
        ],
        abs=1e-7,
    )
    assert chart.angles.ascendant == pytest.approx(119.4028849, abs=1e-7)
    assert chart.angles.midheaven == pytest.approx(29.5801771, abs=1e-7)


def test_chart_profiles_keep_house_system_explicit(engine: NatalChartEngine) -> None:
    placidus = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
            house_system=HouseSystem.PLACIDUS,
        )
    )
    whole_sign = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
            house_system=HouseSystem.WHOLE_SIGN,
        )
    )
    assert placidus.chart_type is ChartType.NATAL
    assert whole_sign.house_system is HouseSystem.WHOLE_SIGN
    assert placidus.houses is not None
    assert whole_sign.houses is not None
    assert [house.longitude for house in placidus.houses] != [
        house.longitude for house in whole_sign.houses
    ]


def test_daily_transit_is_typed_and_deterministic(engine: NatalChartEngine) -> None:
    first = engine.calculate_daily_transit(date(2026, 9, 1))
    second = engine.calculate_daily_transit(date(2026, 9, 1))
    assert first.chart_type is ChartType.DAILY_TRANSIT
    assert first.julian_day_ut == second.julian_day_ut
    assert [position.longitude for position in first.bodies] == [
        position.longitude for position in second.bodies
    ]


def test_daily_transit_mean_node_matches_official_swetest_body_10(
    engine: NatalChartEngine,
) -> None:
    snapshot = engine.calculate_daily_transit(
        date(2026, 9, 1), CalculationConfig(node_mode=NodeMode.MEAN)
    )
    by_body = {position.body: position for position in snapshot.bodies}

    assert BodyName.TRUE_NODE not in by_body
    assert by_body[BodyName.MEAN_NODE].longitude == pytest.approx(329.2774860, abs=1e-7)


def test_transit_to_natal_uses_observed_instant_and_exposes_phase(
    engine: NatalChartEngine,
) -> None:
    natal = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        )
    )
    observed_at = datetime(2026, 9, 6, 8, 30, tzinfo=UTC)

    snapshot = engine.calculate_transit_to_natal(natal, observed_at)

    assert snapshot.chart_type is ChartType.TRANSIT_TO_NATAL
    assert snapshot.observed_at == observed_at
    assert snapshot.contacts
    assert all(contact.phase in TransitPhase for contact in snapshot.contacts)
    assert all(contact.orb >= 0 for contact in snapshot.contacts)
    assert all(
        contact.orb <= transit_orb_limit(contact.transit_body, contact.kind)
        for contact in snapshot.contacts
    )


def test_transit_phase_distinguishes_exact_approaching_separating_and_retrograde() -> None:
    assert _transit_phase(0.2, 0.0, 0.0, 0.1) is TransitPhase.EXACT
    assert _transit_phase(4.0, 0.0, 0.0, 5.0) is TransitPhase.APPROACHING
    assert _transit_phase(6.0, 0.0, 0.0, 5.0) is TransitPhase.SEPARATING
    assert _transit_phase(54.0, 0.0, 60.0, 5.0) is TransitPhase.SEPARATING


def test_transit_to_natal_rejects_naive_observation_time(engine: NatalChartEngine) -> None:
    natal = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        )
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        engine.calculate_transit_to_natal(natal, datetime(2026, 9, 6, 8, 30))


def test_synastry_composite_and_compatibility_are_fact_layers(
    engine: NatalChartEngine,
) -> None:
    chart_a = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    chart_b = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1992, 8, 14, 2, 30, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        )
    )
    synastry = engine.calculate_synastry(chart_a, chart_b)
    composite = engine.calculate_composite_midpoint(chart_a, chart_b)
    compatibility = engine.calculate_compatibility(chart_a, chart_b)
    assert synastry.chart_type is ChartType.SYNASTRY
    assert composite.chart_type is ChartType.COMPOSITE_MIDPOINT
    assert "mathematical" in composite.caveat
    assert compatibility.chart_type is ChartType.COMPATIBILITY_FACTS
    assert 0 <= compatibility.total_score <= 1


def test_composite_midpoint_wraps_across_zero_degrees() -> None:
    assert midpoint_longitude(350, 10) == pytest.approx(0)
    assert midpoint_longitude(10, 350) == pytest.approx(0)


def test_date_only_mid_sign_is_certain(engine: NatalChartEngine) -> None:
    result = engine.calculate_date_only_sun(date(1990, 1, 1))
    assert result.status == "certain"
    assert result.sign is ZodiacSign.CAPRICORN
    assert result.candidates == (ZodiacSign.CAPRICORN,)


def test_date_only_ingress_returns_candidates_without_guessing(engine: NatalChartEngine) -> None:
    result = engine.calculate_date_only_sun(date(2024, 3, 20))
    assert result.status == "candidates"
    assert result.sign is None
    assert result.candidates == (ZodiacSign.PISCES, ZodiacSign.ARIES)
