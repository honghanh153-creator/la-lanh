from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitPhase,
    TransitToNatalContact,
    TransitToNatalSnapshot,
    ZodiacSign,
)
from app.domains.readings.models import (
    INTERPRETATION_KNOWLEDGE_VERSION,
    BackgroundLens,
    FactorKind,
    FactorSource,
    PlanMode,
    ReadingPlan,
    ReadingPurpose,
)
from app.domains.readings.planner import ReadingPlanner, normalized_vietnamese_word_count
from app.domains.readings.service import InsightReadingService

OBSERVED_AT = datetime(2026, 9, 7, 12, tzinfo=UTC)


def _chart(*, tradition: Tradition = Tradition.WESTERN) -> NatalChart:
    config = (
        CalculationConfig.western_recommended()
        if tradition is Tradition.WESTERN
        else CalculationConfig.jyotish_recommended()
    )
    return NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        config,
    )


def _transits(chart: NatalChart, *contacts: TransitToNatalContact) -> TransitToNatalSnapshot:
    return TransitToNatalSnapshot(
        observed_at=OBSERVED_AT,
        contacts=contacts,
        orb_policy_version="transit-orbs-v1",
        provenance=chart.provenance,
        config=chart.config,
        config_hash=chart.config_hash,
    )


def test_exact_western_plan_is_immutable_canonical_and_full_synthesis() -> None:
    chart = _chart()
    planner = ReadingPlanner()

    first = planner.plan(chart, purpose=ReadingPurpose.READING_DETAIL)
    second = planner.plan(chart, purpose=ReadingPurpose.READING_DETAIL)

    assert first == second
    assert first.schema_version == "reading-plan/v1"
    assert first.rules_version == "factor-planner-v2"
    assert first.knowledge_version == INTERPRETATION_KNOWLEDGE_VERSION
    assert first.plan_hash == second.plan_hash
    assert first.mode is PlanMode.FULL_SYNTHESIS
    assert first.tradition is Tradition.WESTERN
    assert first.precision is TimePrecision.EXACT
    assert len(first.hero_factor_refs) >= 2 or any(
        factor.id in first.hero_factor_refs and len(factor.child_refs) >= 2
        for factor in first.factors
    )
    assert all(factor.tradition is Tradition.WESTERN for factor in first.factors)
    assert all(factor.evidence_refs for factor in first.factors)
    assert len({factor.id for factor in first.factors}) == len(first.factors)
    with pytest.raises(ValidationError):
        first.purpose = ReadingPurpose.AURA  # type: ignore[misc]


def test_full_synthesis_rejects_two_factors_from_the_same_subject() -> None:
    plan = ReadingPlanner().plan(_chart(), purpose=ReadingPurpose.READING_DETAIL)
    original = next(factor for factor in plan.factors if factor.kind is FactorKind.PLANET_PLACEMENT)
    parts = original.id.split(":")
    alternate_sign = "aries" if parts[3] != "aries" else "taurus"
    duplicate_id = f"natal:{parts[1]}:sign:{alternate_sign}"
    duplicate_subject = original.model_copy(
        update={
            "id": duplicate_id,
            "evidence_refs": (duplicate_id,),
        }
    )
    payload = plan.model_dump()
    payload["factors"] = (*plan.factors, duplicate_subject)
    payload["hero_factor_refs"] = (original.id, duplicate_subject.id)

    with pytest.raises(ValidationError, match="independent factors"):
        ReadingPlan.model_validate(payload)


@pytest.mark.parametrize("purpose", tuple(ReadingPurpose))
def test_planner_builds_a_canonical_plan_for_every_purpose(purpose: ReadingPurpose) -> None:
    plan = ReadingPlanner().plan(_chart(), purpose=purpose)

    assert plan.purpose is purpose
    assert plan.plan_hash
    assert plan.allowed_language
    assert plan.forbidden_language


def test_date_only_is_labelled_one_factor_vibe_fallback() -> None:
    result = DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.PISCES,
        candidates=(ZodiacSign.PISCES,),
        provenance=EngineProvenance(version="2.10.03", profile="test"),
    )

    plan = ReadingPlanner().plan(result, purpose=ReadingPurpose.DAILY_NOTE)

    assert plan.mode is PlanMode.VIBE_FALLBACK
    assert plan.precision is TimePrecision.UNKNOWN
    assert len(plan.factors) == 1
    assert plan.factors[0].kind is FactorKind.DATE_ONLY_VIBE
    assert plan.factors[0].source is FactorSource.NATAL
    assert plan.hero_factor_refs == (plan.factors[0].id,)
    serialized = plan.model_dump_json().lower()
    assert "house" not in serialized
    assert "rising" not in serialized
    assert "ascendant" not in serialized


def test_daily_editorial_seed_creates_a_new_plan_without_changing_chart_facts() -> None:
    chart = _chart()
    planner = ReadingPlanner()

    first = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    second = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-13",
    )

    assert first.editorial_seed == "2026-09-12"
    assert second.editorial_seed == "2026-09-13"
    assert first.plan_hash != second.plan_hash
    assert first.config_hash == second.config_hash == chart.config_hash


def test_western_placement_factors_keep_degree_and_motion_as_private_evidence() -> None:
    chart = _chart()

    plan = ReadingPlanner().plan(chart, purpose=ReadingPurpose.READING_DETAIL)

    placements = [factor for factor in plan.factors if factor.kind is FactorKind.PLANET_PLACEMENT]
    assert placements
    assert all(
        any(":degree_in_sign:" in ref for ref in factor.evidence_refs) for factor in placements
    )
    assert all(
        any(ref.endswith(":direct") or ref.endswith(":retrograde") for ref in factor.evidence_refs)
        for factor in placements
    )


def test_approximate_excludes_midpoint_facts_without_engine_stability_proof() -> None:
    approximate = _chart().model_copy(
        update={
            "time_precision": TimePrecision.APPROXIMATE,
            "houses": None,
            "angles": None,
        }
    )

    plan = ReadingPlanner().plan(approximate, purpose=ReadingPurpose.READING_DETAIL)

    assert plan.mode is PlanMode.LIMITED
    assert plan.factors == ()
    assert plan.hero_factor_refs == ()
    assert plan.composition.natal_percent == 100
    assert plan.composition.transit_percent == 0
    serialized = plan.model_dump_json().lower()
    assert "house" not in serialized
    assert "rising" not in serialized
    assert "ascendant" not in serialized


def test_eligible_transit_is_secondary_phase_only_and_allocates_70_30() -> None:
    chart = _chart()
    transits = _transits(
        chart,
        TransitToNatalContact(
            transit_body=BodyName.PLUTO,
            natal_body=BodyName.SUN,
            kind="conjunction",
            exact_angle=0.0,
            orb=0.1,
            phase=TransitPhase.APPROACHING,
        ),
        TransitToNatalContact(
            transit_body=BodyName.SATURN,
            natal_body=BodyName.MOON,
            kind="square",
            exact_angle=90.0,
            orb=0.2,
            phase=TransitPhase.SEPARATING,
        ),
    )

    plan = ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.READING_DETAIL,
        transits=transits,
    )

    transit_factors = [factor for factor in plan.factors if factor.source is FactorSource.TRANSIT]
    assert len(transit_factors) == 1
    assert transit_factors[0].phase in set(TransitPhase)
    assert plan.composition.natal_percent == 70
    assert plan.composition.transit_percent == 30
    assert plan.composition.tolerance_percentage_points == 10
    assert plan.composition.count_scope == "user_prose_only"
    assert set(plan.composition.excluded_parts) == {
        "headings",
        "evidence",
        "cta",
        "disclaimer",
    }
    serialized = plan.model_dump_json().lower()
    assert "2026-09-07" not in serialized
    assert "observed_at" not in type(transit_factors[0]).model_fields
    assert "duration" not in type(transit_factors[0]).model_fields


def test_no_eligible_transit_is_natal_only_and_threshold_is_deterministic() -> None:
    chart = _chart()
    weak = _transits(
        chart,
        TransitToNatalContact(
            transit_body=BodyName.MOON,
            natal_body=BodyName.JUPITER,
            kind="sextile",
            exact_angle=60.0,
            orb=2.0,
            phase=TransitPhase.EXACT,
        ),
    )
    planner = ReadingPlanner()

    first = planner.plan(chart, purpose=ReadingPurpose.READING_DETAIL, transits=weak)
    second = planner.plan(chart, purpose=ReadingPurpose.READING_DETAIL, transits=weak)

    assert first == second
    assert all(factor.source is FactorSource.NATAL for factor in first.factors)
    assert first.composition.natal_percent == 100
    assert first.composition.transit_percent == 0


def test_background_lens_never_changes_evidence_or_salience() -> None:
    chart = _chart()
    planner = ReadingPlanner()

    plain = planner.plan(chart, purpose=ReadingPurpose.READING_DETAIL)
    contextual = planner.plan(
        chart,
        purpose=ReadingPurpose.READING_DETAIL,
        background_lens=BackgroundLens.WORK,
    )

    assert contextual.background_lens is BackgroundLens.WORK
    assert [(item.id, item.salience, item.evidence_refs) for item in contextual.factors] == [
        (item.id, item.salience, item.evidence_refs) for item in plain.factors
    ]
    assert contextual.hero_factor_refs == plain.hero_factor_refs
    assert all("work" not in ref for factor in contextual.factors for ref in factor.evidence_refs)


def test_jyotish_plan_uses_only_jyotish_grammar_and_factors() -> None:
    plan = ReadingPlanner().plan(
        _chart(tradition=Tradition.JYOTISH),
        purpose=ReadingPurpose.READING_DETAIL,
    )

    assert plan.tradition is Tradition.JYOTISH
    assert all(factor.tradition is Tradition.JYOTISH for factor in plan.factors)
    assert all(factor.kind is not FactorKind.NATAL_ASPECT for factor in plan.factors)
    assert any(
        factor.kind in {FactorKind.NAKSHATRA, FactorKind.GRAHA_DRISHTI} for factor in plan.factors
    )
    serialized = plan.model_dump_json().lower()
    assert all(name not in serialized for name in ("uranus", "neptune", "pluto", "chiron"))


def test_cross_tradition_transit_is_rejected_instead_of_mixed() -> None:
    western = _chart()
    jyotish = _chart(tradition=Tradition.JYOTISH)
    mixed = _transits(
        jyotish,
        TransitToNatalContact(
            transit_body=BodyName.SATURN,
            natal_body=BodyName.SUN,
            kind="conjunction",
            exact_angle=0.0,
            orb=0.1,
            phase=TransitPhase.EXACT,
        ),
    )

    with pytest.raises(ValueError, match="tradition"):
        ReadingPlanner().plan(
            western,
            purpose=ReadingPurpose.READING_DETAIL,
            transits=mixed,
        )


def test_vietnamese_prose_ratio_uses_normalized_words_and_keeps_short_natal_fallback() -> None:
    chart = _chart()
    eligible = _transits(
        chart,
        TransitToNatalContact(
            transit_body=BodyName.PLUTO,
            natal_body=BodyName.SUN,
            kind="conjunction",
            exact_angle=0.0,
            orb=0.1,
            phase=TransitPhase.EXACT,
        ),
    )
    target = (
        ReadingPlanner()
        .plan(
            chart,
            purpose=ReadingPurpose.READING_DETAIL,
            transits=eligible,
        )
        .composition
    )

    assert normalized_vietnamese_word_count("Mình chậm-lại, rồi thở.") == 4
    assert target.accepts("một hai ba bốn năm sáu bảy", "tám chín mười") is True
    assert target.accepts("một hai ba bốn năm", "sáu bảy tám chín mười") is False
    assert target.accepts("thở", "") is True


def test_service_exposes_the_same_canonical_planner_contract() -> None:
    chart = _chart()

    plan = InsightReadingService().plan(chart, purpose=ReadingPurpose.AURA)

    assert plan == ReadingPlanner().plan(chart, purpose=ReadingPurpose.AURA)
