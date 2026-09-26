from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    Ayanamsa,
    BodyName,
    CalculationConfig,
    ChartInput,
    HouseSystem,
    NodeMode,
    Tradition,
)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _input() -> ChartInput:
    return ChartInput(
        utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
        latitude=10.8231,
        longitude=106.6297,
    )


def test_western_and_jyotish_are_distinct_snapshot_families(
    engine: NatalChartEngine,
) -> None:
    western = engine.calculate_chart(
        _input(),
        CalculationConfig.western_recommended(),
    )
    jyotish = engine.calculate_chart(
        _input(),
        CalculationConfig.jyotish_recommended(),
    )

    assert western.config.tradition is Tradition.WESTERN
    assert jyotish.config.tradition is Tradition.JYOTISH
    assert jyotish.config.ayanamsa is Ayanamsa.LAHIRI
    assert western.config_hash != jyotish.config_hash
    assert western.body(BodyName.SUN).longitude == pytest.approx(280.8142608, abs=1e-7)
    assert jyotish.body(BodyName.SUN).longitude == pytest.approx(257.0935469, abs=1e-7)
    assert jyotish.provenance.zodiac == "sidereal"
    assert jyotish.provenance.ayanamsa == "lahiri"


def test_jyotish_adds_ketu_nakshatra_and_classical_drishti(
    engine: NatalChartEngine,
) -> None:
    chart = engine.calculate_chart(_input(), CalculationConfig.jyotish_recommended())

    rahu = chart.body(BodyName.TRUE_NODE)
    ketu = chart.body(BodyName.SOUTH_NODE)
    assert (ketu.longitude - rahu.longitude) % 360 == pytest.approx(180)
    assert chart.nakshatras
    assert {item.body for item in chart.nakshatras} >= {
        BodyName.SUN,
        BodyName.MOON,
        BodyName.TRUE_NODE,
        BodyName.SOUTH_NODE,
    }
    assert all(1 <= item.pada <= 4 for item in chart.nakshatras)
    assert chart.graha_drishti


@pytest.mark.parametrize(
    ("ayanamsa", "node_mode", "house_system"),
    [
        (Ayanamsa.RAMAN, NodeMode.TRUE, HouseSystem.WHOLE_SIGN),
        (Ayanamsa.KRISHNAMURTI, NodeMode.MEAN, HouseSystem.EQUAL),
    ],
)
def test_supported_custom_calculations_keep_explicit_provenance(
    engine: NatalChartEngine,
    ayanamsa: Ayanamsa,
    node_mode: NodeMode,
    house_system: HouseSystem,
) -> None:
    config = CalculationConfig(
        tradition=Tradition.JYOTISH,
        ayanamsa=ayanamsa,
        node_mode=node_mode,
        house_system=house_system,
    )
    chart = engine.calculate_chart(_input(), config)
    transit = engine.calculate_daily_transit(date(2026, 9, 1), config)
    selected_node = BodyName.TRUE_NODE if node_mode is NodeMode.TRUE else BodyName.MEAN_NODE
    other_node = BodyName.MEAN_NODE if node_mode is NodeMode.TRUE else BodyName.TRUE_NODE

    assert chart.provenance.ayanamsa == ayanamsa.value
    assert chart.config.node_mode is node_mode
    assert chart.house_system is house_system
    assert len(chart.houses or ()) == 12
    assert chart.body(selected_node)
    assert selected_node in {position.body for position in transit.bodies}
    assert other_node not in {position.body for position in transit.bodies}
    assert transit.config_hash == chart.config_hash


def test_parallel_tropical_and_sidereal_batches_do_not_cross_contaminate(
    engine: NatalChartEngine,
) -> None:
    def calculate(tradition: Tradition) -> tuple[Tradition, float]:
        config = (
            CalculationConfig.western_recommended()
            if tradition is Tradition.WESTERN
            else CalculationConfig.jyotish_recommended()
        )
        chart = engine.calculate_chart(_input(), config)
        return tradition, chart.body(BodyName.SUN).longitude

    traditions = [Tradition.WESTERN, Tradition.JYOTISH] * 12
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(calculate, traditions))

    for tradition, longitude in results:
        expected = 280.8142608 if tradition is Tradition.WESTERN else 257.0935469
        assert longitude == pytest.approx(expected, abs=1e-7)
