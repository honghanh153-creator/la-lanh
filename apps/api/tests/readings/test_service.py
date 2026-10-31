from datetime import UTC, datetime

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, Tradition
from app.domains.readings.service import InsightReadingService


def test_overview_synthesizes_four_to_six_claims_from_chart_factors() -> None:
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        CalculationConfig.western_recommended(),
    )

    reading = InsightReadingService().overview(chart, observed_at=datetime(2026, 9, 4, tzinfo=UTC))

    assert 4 <= len(reading.claims) <= 6
    assert reading.tradition is Tradition.WESTERN
    assert reading.config_hash == chart.config_hash
    assert all(claim.factor_refs for claim in reading.claims)
    assert all(claim.confidence in {"high", "medium"} for claim in reading.claims)
    assert "tham khảo" in reading.disclaimer.lower()
    moon_claim = next(claim for claim in reading.claims if claim.id == "moon-sign")
    assert "Mặt Trăng" in moon_claim.meaning
    assert "Trong đời thường" in moon_claim.manifestation
    assert moon_claim.watch_for
    assert moon_claim.micro_action
    assert len(moon_claim.evidence) >= 2
    assert any(ref.startswith("natal:moon:house:") for ref in moon_claim.factor_refs)
    assert any(ref.startswith("natal:aspect:moon:") for ref in moon_claim.factor_refs)


def test_jyotish_reading_uses_jyotish_vocabulary_and_provenance() -> None:
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        CalculationConfig.jyotish_recommended(),
    )

    reading = InsightReadingService().overview(chart, observed_at=datetime(2026, 9, 4, tzinfo=UTC))

    assert reading.tradition is Tradition.JYOTISH
    assert reading.provenance.ayanamsa == "lahiri"
    assert any("Nakshatra" in claim.title for claim in reading.claims)
    visible = " ".join(
        " ".join(
            (
                claim.summary,
                claim.hook,
                claim.meaning,
                claim.manifestation,
                claim.watch_for,
                claim.micro_action,
            )
        )
        for claim in reading.claims
    )
    assert "bạn dễ" not in visible and "Bạn sáng rõ" not in visible
    assert "tam hợp" not in visible and "góc vuông" not in visible
    assert "đã tính" in visible
    assert all(
        not any(ref.startswith("natal:aspect:") for ref in claim.factor_refs)
        for claim in reading.claims
    )


def test_planets_in_the_same_sign_never_share_a_card_sentence() -> None:
    """#143 E3: on a synthetic chart with the Sun and Mercury in one sign and Venus and Mars in
    another, every card said the same sign phrase word for word."""

    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1997, 9, 20, 5, 0, tzinfo=UTC), latitude=20.84, longitude=106.69
        )
    )
    signs = {body.body.value: body.sign.value for body in chart.bodies}
    assert signs["sun"] == signs["mercury"] and signs["venus"] == signs["mars"]

    reading = InsightReadingService().overview(chart, observed_at=datetime(2026, 9, 4, tzinfo=UTC))
    tails = [claim.summary.split(":", 1)[1].strip() for claim in reading.claims]
    assert len(tails) == len(set(tails)), tails
