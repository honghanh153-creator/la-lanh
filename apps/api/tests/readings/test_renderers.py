from datetime import UTC, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    TimePrecision,
    TransitPhase,
    TransitToNatalContact,
    TransitToNatalSnapshot,
    ZodiacSign,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION,
    BackgroundLens,
    CompositionTarget,
    FactorSource,
    GateFailureCode,
    PlanMode,
    ReadingPlan,
    ReadingPurpose,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import (
    DETERMINISTIC_RENDERER_VERSION,
    DeterministicVietnameseRenderer,
    canonical_evidence_claim,
)

OBSERVED_AT = datetime(2026, 9, 7, 12, tzinfo=UTC)


def _chart() -> NatalChart:
    return NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1998, 6, 15, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.western_recommended(),
    )


def _plan(
    *,
    purpose: ReadingPurpose = ReadingPurpose.READING_DETAIL,
    transit: bool = False,
    lens: BackgroundLens | None = None,
) -> ReadingPlan:
    chart = _chart()
    transits = None
    if transit:
        transits = TransitToNatalSnapshot(
            observed_at=OBSERVED_AT,
            contacts=(
                TransitToNatalContact(
                    transit_body=BodyName.PLUTO,
                    natal_body=BodyName.SUN,
                    kind="conjunction",
                    exact_angle=0.0,
                    orb=0.1,
                    phase=TransitPhase.APPROACHING,
                ),
            ),
            orb_policy_version="transit-orbs-v1",
            provenance=chart.provenance,
            config=chart.config,
            config_hash=chart.config_hash,
        )
    return ReadingPlanner().plan(
        chart,
        purpose=purpose,
        transits=transits,
        background_lens=lens,
    )


@pytest.mark.parametrize("purpose", tuple(ReadingPurpose))
def test_deterministic_renderer_is_stable_and_passes_all_five_gates(
    purpose: ReadingPurpose,
) -> None:
    plan = _plan(purpose=purpose)
    renderer = DeterministicVietnameseRenderer()

    first = renderer.render(plan)
    second = renderer.render(plan)
    evaluation = evaluate_candidate(plan, first)

    assert first == second
    assert first.renderer_version.startswith(DETERMINISTIC_RENDERER_VERSION)
    assert first.plan_hash == plan.plan_hash
    assert first.hook and first.thesis and first.manifestation and first.micro_action
    assert first.transit is None
    assert first.evidence.title == "Căn cứ trong lá số"
    assert first.disclaimer == "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn."
    assert "không phải bằng chứng khoa học" in first.evidence.framework_disclosure
    assert evaluation.accepted is True
    assert evaluation.publishable_candidate == first
    assert [report.gate.value for report in evaluation.reports] == [
        "evidence",
        "anti_influence",
        "editorial",
        "meaning",
        "privacy",
    ]


def test_renderer_only_uses_plan_owned_claims_and_bounded_slots() -> None:
    plan = _plan()

    candidate = DeterministicVietnameseRenderer().render(plan)

    factor_ids = {factor.id for factor in plan.factors}
    assert candidate.evidence.claims
    assert all(claim.factor_ref in factor_ids for claim in candidate.evidence.claims)
    assert all(len(claim.slots) <= 6 for claim in candidate.evidence.claims)
    assert all(
        slot.value and len(slot.value) <= 64
        for claim in candidate.evidence.claims
        for slot in claim.slots
    )
    assert all(claim.display_text for claim in candidate.evidence.claims)
    placement_claims = [
        claim for claim in candidate.evidence.claims if claim.template_id.value == "planet_in_sign"
    ]
    assert placement_claims
    assert all("°" in claim.display_text for claim in placement_claims)
    assert all(
        {slot.name.value for slot in claim.slots} >= {"body", "sign", "degree", "motion"}
        for claim in placement_claims
    )


def test_jyotish_nakshatra_and_drishti_claims_render_without_mixing_western_aspects() -> None:
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1998, 6, 15, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.jyotish_recommended(),
    )
    plan = ReadingPlanner().plan(chart, purpose=ReadingPurpose.READING_DETAIL)

    candidate = DeterministicVietnameseRenderer().render(plan)
    rendered = candidate.model_dump_json()

    assert evaluate_candidate(plan, candidate).accepted is True
    assert plan.knowledge_version == JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION
    nakshatra_factor = next(factor for factor in plan.factors if ":nakshatra:" in factor.id)
    assert "Nakshatra" in canonical_evidence_claim(nakshatra_factor).display_text
    assert "đối đỉnh" not in rendered
    assert "tam hợp" not in rendered


def test_transit_is_optional_secondary_and_composition_excludes_disclosure() -> None:
    plan = _plan(transit=True)

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert candidate.transit
    assert (
        len(
            [
                claim
                for claim in candidate.evidence.claims
                if next(f for f in plan.factors if f.id == claim.factor_ref).source
                is FactorSource.TRANSIT
            ]
        )
        == 1
    )
    assert plan.composition.accepts(candidate.natal_user_prose, candidate.transit)
    assert evaluate_candidate(plan, candidate).accepted is True
    assert candidate.disclaimer not in candidate.natal_user_prose
    assert candidate.evidence.framework_disclosure not in candidate.natal_user_prose


def test_impossible_composition_falls_back_to_accepted_natal_content() -> None:
    plan = _plan(transit=True).model_copy(
        update={
            "composition": CompositionTarget(
                natal_percent=99,
                transit_percent=1,
                tolerance_percentage_points=0,
            )
        }
    )

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert candidate.transit is None
    assert all(
        next(factor for factor in plan.factors if factor.id == claim.factor_ref).source
        is FactorSource.NATAL
        for claim in candidate.evidence.claims
    )
    assert evaluate_candidate(plan, candidate).accepted is True


def test_date_only_vibe_is_honestly_one_factor_and_asks_for_exact_time() -> None:
    date_only = DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.PISCES,
        candidates=(ZodiacSign.PISCES,),
        provenance=EngineProvenance(version="2.10.03", profile="test"),
    )
    plan = ReadingPlanner().plan(date_only, purpose=ReadingPurpose.DAILY_NOTE)

    candidate = DeterministicVietnameseRenderer().render(plan)
    rendered = candidate.model_dump_json().lower()

    assert plan.mode is PlanMode.VIBE_FALLBACK
    # Precision belongs to evidence/UI disclosure, not a paragraph appended to the explanation.
    assert len(candidate.evidence.claims) == 1
    assert "chỉ từ ngày sinh" in candidate.evidence.claims[0].display_text
    assert candidate.semantic_blueprint is not None
    assert candidate.semantic_blueprint.scene_key.startswith("psychology:")
    assert all(term not in rendered for term in ("nhà 7", "rising", "ascendant"))
    assert evaluate_candidate(plan, candidate).accepted is True


def test_empty_limited_plan_returns_useful_copy_without_fabricated_evidence() -> None:
    approximate = _chart().model_copy(
        update={
            "time_precision": TimePrecision.APPROXIMATE,
            "houses": None,
            "angles": None,
        }
    )
    plan = ReadingPlanner().plan(approximate, purpose=ReadingPurpose.READING_DETAIL)

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert plan.mode is PlanMode.LIMITED
    assert candidate.evidence.claims == ()
    assert "giờ sinh chính xác" in candidate.micro_action
    assert "chưa đủ dữ liệu" in candidate.thesis.lower()
    assert evaluate_candidate(plan, candidate).accepted is True


def test_background_lens_renders_one_coherent_allowlisted_scene() -> None:
    renderer = DeterministicVietnameseRenderer()
    plain = renderer.render(_plan())
    work = renderer.render(_plan(lens=BackgroundLens.WORK))

    assert work.manifestation != plain.manifestation
    assert work.micro_action != plain.micro_action
    assert "công việc" in work.hook.lower()
    assert "công việc" in work.manifestation.lower()
    assert work.thesis == plain.thesis
    assert work.transit == plain.transit
    assert work.evidence == plain.evidence
    assert evaluate_candidate(_plan(lens=BackgroundLens.WORK), work).accepted is True


@pytest.mark.parametrize(
    "lens",
    [
        BackgroundLens.RELATIONSHIPS,
        BackgroundLens.COMMUNICATION,
        BackgroundLens.WORK,
        BackgroundLens.ENERGY,
        BackgroundLens.SELF_CARE,
    ],
)
@pytest.mark.parametrize("mode", ["date_only", "cusp", "limited", "full"])
def test_every_reading_mode_keeps_evidence_while_rendering_one_contextual_scene(
    lens: BackgroundLens,
    mode: str,
) -> None:
    source: DateOnlySunResult | NatalChart
    if mode == "date_only":
        source = DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=EngineProvenance(version="2.10.03", profile="test"),
        )
    elif mode == "cusp":
        source = DateOnlySunResult(
            status="candidates",
            sign=None,
            candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
            provenance=EngineProvenance(version="2.10.03", profile="test"),
        )
    elif mode == "limited":
        source = _chart().model_copy(
            update={
                "time_precision": TimePrecision.APPROXIMATE,
                "houses": None,
                "angles": None,
            }
        )
    else:
        source = _chart()

    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    plain_plan = planner.plan(
        source,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    contextual_plan = planner.plan(
        source,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
        background_lens=lens,
    )
    plain = renderer.render(plain_plan)
    contextual = renderer.render(contextual_plan)

    assert contextual.manifestation != plain.manifestation
    # Context may select the same sensible action. Changing its words is not personalization.
    assert contextual.micro_action
    # Daily explanation follows the selected situation, not an unrelated natal paragraph.
    assert contextual.semantic_blueprint is not None
    assert contextual.semantic_blueprint.daily_meaning is not None
    assert contextual.thesis == (
        f"{contextual.semantic_blueprint.daily_meaning.core_meaning} "
        f"{contextual.semantic_blueprint.daily_meaning.reader_takeaway}"
    )
    assert contextual.semantic_blueprint is not None
    assert contextual.semantic_blueprint.arena.value == lens.value
    assert contextual.transit == plain.transit
    assert contextual.evidence == plain.evidence
    assert contextual_plan.factors == plain_plan.factors
    assert contextual_plan.hero_factor_refs == plain_plan.hero_factor_refs
    assert contextual_plan.precision == plain_plan.precision
    assert contextual_plan.mode == plain_plan.mode
    assert evaluate_candidate(contextual_plan, contextual).accepted is True


def test_date_only_copy_uses_the_actual_sun_sign_and_daily_editorial_cycle() -> None:
    date_only = DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.PISCES,
        candidates=(ZodiacSign.PISCES,),
        provenance=EngineProvenance(version="2.10.03", profile="test"),
    )
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()

    first_plan = planner.plan(
        date_only,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    second_plan = planner.plan(
        date_only,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-13",
    )
    first = renderer.render(first_plan)
    second = renderer.render(second_plan)

    assert first != second
    assert "chỉ từ ngày sinh" in first.evidence.claims[0].display_text
    assert "tín hiệu vũ trụ" not in first.model_dump_json().lower()
    assert evaluate_candidate(first_plan, first).accepted is True
    assert evaluate_candidate(second_plan, second).accepted is True


def test_full_copy_is_specific_to_selected_planet_house_aspect_and_orb() -> None:
    plan = _plan(purpose=ReadingPurpose.DAILY_NOTE)

    candidate = DeterministicVietnameseRenderer().render(plan)
    prose = candidate.model_dump_json().lower()

    assert "có một nhịp kéo và đẩy đáng để để ý" not in prose
    assert "tín hiệu phụ" not in prose
    assert candidate.semantic_blueprint is not None
    assert candidate.semantic_blueprint.scene_key.startswith("psychology:")
    assert candidate.evidence.claims
    assert len(candidate.evidence.claims) >= 2
    assert evaluate_candidate(plan, candidate).accepted is True


def test_full_daily_synthesis_changes_visible_focus_on_the_next_day() -> None:
    chart = _chart()
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    first_plan = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    second_plan = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-13",
    )

    first = renderer.render(first_plan)
    second = renderer.render(second_plan)

    assert first_plan.hero_factor_refs != second_plan.hero_factor_refs
    assert first.hook != second.hook or first.thesis != second.thesis
    assert evaluate_candidate(first_plan, first).accepted is True
    assert evaluate_candidate(second_plan, second).accepted is True


def test_jyotish_planner_ignores_western_style_transit_contacts() -> None:
    engine = NatalChartEngine()
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1998, 6, 15, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.jyotish_recommended(),
    )
    transits = engine.calculate_transit_to_natal(chart, OBSERVED_AT)

    plan = ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=transits,
        editorial_seed="2026-09-12",
    )

    assert all(factor.source is not FactorSource.TRANSIT for factor in plan.factors)
    assert plan.composition.transit_percent == 0
    assert DeterministicVietnameseRenderer().render(plan).transit is None


def test_daily_transit_copy_explains_chart_phase_without_inventing_a_life_event() -> None:
    plan = _plan(purpose=ReadingPurpose.DAILY_NOTE, transit=True)

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert candidate.transit is not None
    assert "tín hiệu" not in candidate.transit.lower()
    transit_factor = next(
        factor for factor in plan.factors if factor.source is FactorSource.TRANSIT
    )
    assert canonical_evidence_claim(transit_factor).display_text in candidate.transit
    assert "Hai vị trí đang" in candidate.transit
    assert any(word in candidate.transit for word in ("tiến gần", "ở sát", "đi xa"))
    assert plan.composition.accepts(candidate.natal_user_prose, candidate.transit)
    assert evaluate_candidate(plan, candidate).accepted is True
    incorrect_phase = candidate.model_copy(
        update={"transit": candidate.transit.replace("pha tiến gần", "pha tách dần")}
    )
    assert (
        GateFailureCode.EVIDENCE_ASTRO_LABEL
        in evaluate_candidate(plan, incorrect_phase).failure_codes
    )
