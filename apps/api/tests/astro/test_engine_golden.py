from datetime import UTC, date, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, ChartInput, ZodiacSign


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
