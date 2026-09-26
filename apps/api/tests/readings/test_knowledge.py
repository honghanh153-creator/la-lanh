from datetime import date, timedelta

import pytest

from app.domains.astro.models import (
    DateOnlySunResult,
    EngineProvenance,
    Tradition,
    TransitPhase,
    ZodiacSign,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.interpretive_lenses import (
    CURRENT_FORCES,
    ELEMENTS,
    METHODOLOGY_SOURCE_IDS,
    METHODOLOGY_VERSION,
    MODALITIES,
    PLANET_PERSPECTIVES,
    SIGN_STRUCTURE,
    InterpretiveLens,
    resolve_daily_editorial_variant,
    resolve_interpretive_lens,
)
from app.domains.readings.knowledge import (
    ASPECTS,
    HOUSES,
    KNOWLEDGE_VERSION,
    PLANETS,
    SIGNS,
    full_frame,
    transit_copy,
)
from app.domains.readings.models import (
    INTERPRETATION_KNOWLEDGE_VERSION,
    BackgroundLens,
    CompositionTarget,
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    FactorSource,
    PlanMode,
    ReadingDomain,
    ReadingPlan,
    ReadingPurpose,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer


def _date_only(sign: ZodiacSign) -> DateOnlySunResult:
    return DateOnlySunResult(
        status="certain",
        sign=sign,
        candidates=(sign,),
        provenance=EngineProvenance(version="2.10.03", profile="knowledge-test"),
    )


def test_interpretation_catalog_has_complete_launch_coverage() -> None:
    assert KNOWLEDGE_VERSION == INTERPRETATION_KNOWLEDGE_VERSION
    assert set(SIGNS) == {sign.value for sign in ZodiacSign}
    assert set(HOUSES) == set(range(1, 13))
    assert {
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "chiron",
        "true_node",
        "mean_node",
        "south_node",
    } <= set(PLANETS)
    assert set(ASPECTS) == {
        "conjunction",
        "opposition",
        "square",
        "trine",
        "sextile",
        "quincunx",
    }
    assert set(SIGN_STRUCTURE) == {sign.value for sign in ZodiacSign}
    assert set(ELEMENTS) == {"fire", "earth", "air", "water"}
    assert set(MODALITIES) == {"cardinal", "fixed", "mutable"}
    assert set(PLANETS) <= set(PLANET_PERSPECTIVES)
    assert set(PLANETS) <= set(CURRENT_FORCES)
    assert METHODOLOGY_VERSION == "western-synthesis-method-2026-09-v1"
    assert len(METHODOLOGY_SOURCE_IDS) == len(set(METHODOLOGY_SOURCE_IDS)) == 5


def test_daily_cycle_uses_every_interpretive_lens_without_changing_chart_facts() -> None:
    lenses = {
        resolve_interpretive_lens(date(2026, 9, day).isoformat(), None) for day in range(12, 24)
    }

    assert lenses == set(InterpretiveLens)


def test_daily_editorial_cycle_has_365_non_repeating_semantic_signatures() -> None:
    start = date(2026, 9, 12)
    signatures = {
        resolve_daily_editorial_variant(
            (start + timedelta(days=offset)).isoformat(), None
        ).signature
        for offset in range(365)
    }

    assert len(signatures) == 365


def test_date_only_daily_note_has_365_publishable_non_repeating_days() -> None:
    renderer = DeterministicVietnameseRenderer()
    planner = ReadingPlanner()
    start = date(2026, 9, 12)
    copies: set[tuple[str, ...]] = set()

    for offset in range(365):
        plan = planner.plan(
            _date_only(ZodiacSign.CANCER),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=(start + timedelta(days=offset)).isoformat(),
        )
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        copies.add(candidate.all_user_prose)

    assert len(copies) == 365


def test_ambiguous_date_only_note_has_365_publishable_non_repeating_days() -> None:
    renderer = DeterministicVietnameseRenderer()
    planner = ReadingPlanner()
    chart = DateOnlySunResult(
        status="candidates",
        sign=None,
        candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
        provenance=EngineProvenance(version="2.10.03", profile="knowledge-test"),
    )
    start = date(2026, 9, 12)
    copies: set[tuple[str, ...]] = set()

    for offset in range(365):
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=(start + timedelta(days=offset)).isoformat(),
        )
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        copies.add(candidate.all_user_prose)

    assert len(copies) == 365


def test_full_daily_note_has_365_publishable_non_repeating_days() -> None:
    renderer = DeterministicVietnameseRenderer()
    start = date(2026, 9, 12)
    copies: set[tuple[str, ...]] = set()

    for offset in range(365):
        plan = _controlled_full_plan().model_copy(
            update={
                "purpose": ReadingPurpose.DAILY_NOTE,
                "editorial_seed": (start + timedelta(days=offset)).isoformat(),
            }
        )
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        copies.add(candidate.all_user_prose)

    assert len(copies) == 365


def test_every_date_only_sign_produces_publishable_specific_copy() -> None:
    renderer = DeterministicVietnameseRenderer()
    hooks: set[str] = set()

    for sign in ZodiacSign:
        plan = ReadingPlanner().plan(
            _date_only(sign),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=date(2026, 9, 12).isoformat(),
        )
        candidate = renderer.render(plan)
        hooks.add(candidate.hook)

        assert evaluate_candidate(plan, candidate).accepted is True
        assert "tín hiệu vũ trụ" not in candidate.model_dump_json().lower()
        assert sign.value in candidate.evidence.claims[0].factor_ref

    assert len(hooks) == len(tuple(ZodiacSign))


def _factor(
    factor_id: str,
    *,
    kind: FactorKind,
    subjects: tuple[str, ...],
    child_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] | None = None,
    source: FactorSource = FactorSource.NATAL,
    phase: TransitPhase | None = None,
) -> DerivedFactor:
    return DerivedFactor(
        id=factor_id,
        tradition=Tradition.WESTERN,
        source=source,
        kind=kind,
        domain=ReadingDomain.CORE,
        role=FactorRole.TRANSIT if source is FactorSource.TRANSIT else FactorRole.PRIMARY,
        subjects=subjects,
        evidence_refs=evidence_refs or (factor_id,),
        child_refs=child_refs,
        strength=0.9,
        salience=1.0,
        confidence=FactorConfidence.HIGH,
        phase=phase,
        allowed_language=("approved-matrix",),
        forbidden_language=("prediction",),
    )


def _controlled_full_plan(
    *,
    body_a: str = "sun",
    body_b: str = "moon",
    sign_a: str = "aries",
    sign_b: str = "cancer",
    degree: float = 5,
    aspect: str = "square",
    orb: float = 0.5,
    house: int = 1,
) -> ReadingPlan:
    placement_a_id = f"natal:{body_a}:sign:{sign_a}"
    placement_b_id = f"natal:{body_b}:sign:{sign_b}"
    aspect_id = f"natal:aspect:{body_a}:{aspect}:{body_b}:orb:{orb:.3f}"
    house_id = f"natal:{body_a}:house:{house}"
    factors = (
        _factor(
            placement_a_id,
            kind=FactorKind.PLANET_PLACEMENT,
            subjects=(body_a,),
            evidence_refs=(
                placement_a_id,
                f"natal:{body_a}:degree_in_sign:{degree:.3f}",
                f"natal:{body_a}:motion:direct",
            ),
        ),
        _factor(
            placement_b_id,
            kind=FactorKind.PLANET_PLACEMENT,
            subjects=(body_b,),
            evidence_refs=(
                placement_b_id,
                f"natal:{body_b}:degree_in_sign:12.000",
                f"natal:{body_b}:motion:direct",
            ),
        ),
        _factor(
            aspect_id,
            kind=FactorKind.NATAL_ASPECT,
            subjects=(body_a, body_b),
            child_refs=(placement_a_id, placement_b_id),
        ),
        _factor(
            house_id,
            kind=FactorKind.HOUSE_PLACEMENT,
            subjects=(body_a, f"house:{house}"),
            child_refs=(placement_a_id,),
        ),
    )
    return ReadingPlan(
        plan_hash="controlled-plan",
        tradition=Tradition.WESTERN,
        config_hash="controlled-config",
        purpose=ReadingPurpose.READING_DETAIL,
        precision="exact",
        mode=PlanMode.FULL_SYNTHESIS,
        factors=factors,
        hero_factor_refs=(aspect_id,),
        composition=CompositionTarget(natal_percent=100, transit_percent=0),
        allowed_language=("approved-matrix",),
        forbidden_language=("prediction",),
    )


def test_matrix_changes_visible_copy_for_planets_houses_and_aspects() -> None:
    base = full_frame(_controlled_full_plan())
    assert full_frame(_controlled_full_plan(body_a="mercury")).hook != base.hook
    assert full_frame(_controlled_full_plan(house=12)).manifestation != base.manifestation
    assert full_frame(_controlled_full_plan(aspect="trine")).thesis != base.thesis


def test_same_element_aspect_names_both_needs_without_repeating_the_same_clause() -> None:
    plan = _controlled_full_plan(
        body_a="moon",
        body_b="venus",
        sign_a="cancer",
        sign_b="pisces",
        aspect="conjunction",
        orb=4.1,
    ).model_copy(
        update={
            "background_lens": BackgroundLens.RELATIONSHIPS,
            "editorial_seed": "2026-09-22",
        }
    )

    thesis = full_frame(plan).thesis

    assert "Mặt Trăng cần được an toàn trước khi mở lòng" in thesis
    assert "Sao Kim cần biết mình được trân trọng theo cách nào" in thesis
    assert thesis.count("cần độ an toàn, kết nối và thời gian để cảm nhận") <= 1
    assert "nhu cầu nào đang cầm lái" not in thesis
    assert "sắc độ nền" not in thesis
    assert "chỉ xem là nét phụ" in thesis


@pytest.mark.parametrize("aspect", tuple(ASPECTS))
@pytest.mark.parametrize("orb", (0.5, 2.0, 4.1))
def test_same_element_relationship_matrix_stays_publishable_and_concrete(
    aspect: str, orb: float
) -> None:
    same_element_pairs = (
        ("aries", "leo"),
        ("taurus", "virgo"),
        ("gemini", "libra"),
        ("cancer", "pisces"),
    )

    for sign_a, sign_b in same_element_pairs:
        plan = _controlled_full_plan(
            body_a="moon",
            body_b="venus",
            sign_a=sign_a,
            sign_b=sign_b,
            aspect=aspect,
            orb=orb,
        ).model_copy(update={"editorial_seed": "2026-09-22"})
        candidate = DeterministicVietnameseRenderer().render(plan)

        assert evaluate_candidate(plan, candidate).accepted is True
        assert candidate.thesis.count("nhịp kia") == 0
        assert "sắc độ nền" not in candidate.thesis


def test_lens_rotation_changes_life_angle_but_preserves_evidence_references() -> None:
    base = _controlled_full_plan()
    first = full_frame(base.model_copy(update={"editorial_seed": "2026-09-12"}))
    second = full_frame(base.model_copy(update={"editorial_seed": "2026-09-13"}))

    assert first.hook != second.hook or first.manifestation != second.manifestation
    assert first.evidence_factor_refs == second.evidence_factor_refs
    assert any(ref.startswith("lens:") for ref in first.knowledge_refs)
    assert any(ref.startswith(("element:", "modality:")) for ref in first.knowledge_refs)


def test_every_interpretive_lens_produces_a_distinct_publishable_projection() -> None:
    renderer = DeterministicVietnameseRenderer()
    candidates = {}

    for day in range(12, 24):
        seed = date(2026, 9, day).isoformat()
        lens = resolve_interpretive_lens(seed, None)
        if lens in candidates:
            continue
        plan = _controlled_full_plan().model_copy(update={"editorial_seed": seed})
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        candidates[lens] = candidate

    assert set(candidates) == set(InterpretiveLens)
    assert len({candidate.hook for candidate in candidates.values()}) == len(InterpretiveLens)


def test_orb_changes_visible_weight_while_degree_stays_in_evidence_only() -> None:
    degree_copy = {
        full_frame(_controlled_full_plan(degree=value)).thesis for value in (9.999, 10.0, 20.0)
    }
    orb_copy = {full_frame(_controlled_full_plan(orb=value)).thesis for value in (1.0, 3.0, 3.001)}
    assert len(degree_copy) == 1
    assert len(orb_copy) == 3


def test_transit_phase_changes_only_the_current_activation_language() -> None:
    copies = set()
    for phase in TransitPhase:
        factor_id = f"transit:jupiter:trine:natal:sun:orb:0.500:phase:{phase.value}"
        copies.add(
            transit_copy(
                _factor(
                    factor_id,
                    kind=FactorKind.TRANSIT_CONTACT,
                    subjects=("jupiter", "sun"),
                    source=FactorSource.TRANSIT,
                    phase=phase,
                )
            )
        )
    assert len(copies) == len(tuple(TransitPhase))


def test_same_chart_gets_stable_copy_today_and_fresh_copy_tomorrow() -> None:
    renderer = DeterministicVietnameseRenderer()
    chart = _date_only(ZodiacSign.CANCER)
    planner = ReadingPlanner()

    today = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    today_replay = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )
    tomorrow = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-13",
    )

    assert renderer.render(today) == renderer.render(today_replay)
    assert renderer.render(today).hook != renderer.render(tomorrow).hook
    assert renderer.render(today).micro_action != renderer.render(tomorrow).micro_action


def test_ambiguous_date_only_result_does_not_pick_one_candidate_as_fact() -> None:
    chart = DateOnlySunResult(
        status="candidates",
        sign=None,
        candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
        provenance=EngineProvenance(version="2.10.03", profile="knowledge-test"),
    )
    plan = ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-09-12",
    )

    candidate = DeterministicVietnameseRenderer().render(plan)
    prose = " ".join(candidate.all_user_prose).lower()

    assert evaluate_candidate(plan, candidate).accepted is True
    assert "chưa thể biết chắc" in candidate.thesis
    assert "song ngư" not in prose
    assert "bạch dương" not in prose
    assert "moon" not in prose
    assert "nhà" not in prose
