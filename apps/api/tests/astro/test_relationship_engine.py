from datetime import UTC, datetime

import pytest

from app.domains.astro.aspects import SYNASTRY_ORB_VERSION, synastry_orb_limit
from app.domains.astro.engine import NatalChartEngine, house_for_longitude, navamsa_longitude
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    ChartType,
    HousePosition,
    HouseSystem,
    RelationshipDimension,
    ZodiacSign,
)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _inputs() -> tuple[ChartInput, ChartInput]:
    return (
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.0,
            longitude=100.0,
        ),
        ChartInput(
            utc_datetime=datetime(1992, 1, 3, 12, tzinfo=UTC),
            latitude=20.0,
            longitude=110.0,
        ),
    )


def test_synastry_uses_strict_versioned_orbs_and_bidirectional_overlays(
    engine: NatalChartEngine,
) -> None:
    input_a, input_b = _inputs()
    chart_a = engine.calculate_chart(input_a)
    chart_b = engine.calculate_chart(input_b)

    facts = engine.calculate_synastry(chart_a, chart_b)

    assert facts.orb_policy_version == SYNASTRY_ORB_VERSION
    assert len(facts.house_overlays) == len(chart_a.bodies) + len(chart_b.bodies)
    assert {item.body_owner for item in facts.house_overlays} == {"a", "b"}
    assert facts.contacts
    for contact in facts.contacts:
        assert contact.orb <= synastry_orb_limit(contact.body_a, contact.body_b, contact.kind)
        assert 0 <= contact.strength <= 1
        assert contact.dimensions


def test_relationship_bundle_is_multidimensional_and_never_a_scalar_score(
    engine: NatalChartEngine,
) -> None:
    input_a, input_b = _inputs()
    chart_a = engine.calculate_chart(input_a)
    chart_b = engine.calculate_chart(input_b)

    bundle = engine.calculate_relationship_bundle(
        chart_a, chart_b, input_a=input_a, input_b=input_b
    )

    assert bundle.chart_type is ChartType.RELATIONSHIP_BUNDLE
    assert bundle.scalar_score_eligible is False
    assert {item.dimension for item in bundle.dimensions} == set(RelationshipDimension)
    assert bundle.composite.aspects
    assert bundle.davison is not None
    assert bundle.davison.generated_interpretation_eligible is False


def test_davison_uses_explicit_arithmetic_time_and_place_midpoint(
    engine: NatalChartEngine,
) -> None:
    input_a, input_b = _inputs()
    result = engine.calculate_davison_relationship(input_a, input_b)

    assert result.chart_type is ChartType.DAVISON_RELATIONSHIP
    assert result.midpoint_input.utc_datetime == datetime(1991, 1, 2, 12, tzinfo=UTC)
    assert result.midpoint_input.latitude == pytest.approx(15.0)
    assert result.midpoint_input.longitude == pytest.approx(105.0)
    assert "not the corrected" in result.caveat


def test_navamsa_is_factual_gated_jyotish_output(engine: NatalChartEngine) -> None:
    input_a, _ = _inputs()
    western = engine.calculate_chart(input_a)
    with pytest.raises(ValueError, match="Jyotish"):
        engine.calculate_navamsa(western)

    jyotish = engine.calculate_chart(input_a, CalculationConfig.jyotish_recommended())
    navamsa = engine.calculate_navamsa(jyotish)

    assert navamsa.chart_type is ChartType.JYOTISH_NAVAMSA
    assert navamsa.generated_interpretation_eligible is False
    sun = next(point for point in navamsa.points if point.body is BodyName.SUN)
    assert sun.longitude == pytest.approx((jyotish.body(BodyName.SUN).longitude * 9) % 360)


def test_navamsa_mapping_covers_all_108_classical_cells() -> None:
    movable = {0, 3, 6, 9}
    fixed = {1, 4, 7, 10}
    cell_size = 30 / 9
    for source_sign in range(12):
        if source_sign in movable:
            start_sign = source_sign
        elif source_sign in fixed:
            start_sign = (source_sign + 8) % 12
        else:
            start_sign = (source_sign + 4) % 12
        for part in range(9):
            source_longitude = source_sign * 30 + part * cell_size + cell_size / 2
            assert int(navamsa_longitude(source_longitude) // 30) == (start_sign + part) % 12


def test_relationship_pair_rejects_mixed_calculation_configs(engine: NatalChartEngine) -> None:
    input_a, input_b = _inputs()
    chart_a = engine.calculate_chart(input_a)
    chart_b = engine.calculate_chart(
        input_b,
        CalculationConfig(house_system=HouseSystem.WHOLE_SIGN),
    )
    with pytest.raises(ValueError, match="identical calculation config"):
        engine.calculate_synastry(chart_a, chart_b)


def test_house_assignment_handles_zero_degree_wrap() -> None:
    houses = tuple(
        HousePosition(
            number=index + 1,
            longitude=(345 + index * 30) % 360,
            sign=ZodiacSign(
                (
                    "pisces",
                    "aries",
                    "taurus",
                    "gemini",
                    "cancer",
                    "leo",
                    "virgo",
                    "libra",
                    "scorpio",
                    "sagittarius",
                    "capricorn",
                    "aquarius",
                )[index]
            ),
        )
        for index in range(12)
    )
    assert house_for_longitude(359.9, houses) == 1
    assert house_for_longitude(15.0, houses) == 2
