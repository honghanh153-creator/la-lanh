import re
from datetime import UTC, date, datetime, timedelta
from itertools import product

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    TimePrecision,
    TransitPhase,
    ZodiacSign,
)
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings.daily_personalization import eligible_daily_situations
from app.domains.readings.daily_psychology import (
    _ARENA_LEADS,
    DAILY_ISSUES,
    DAILY_PSYCHOLOGY_MATRIX_VERSION,
    PSYCHOLOGY_SOURCES,
    issue_source_ids,
    lead_scene,
    source_ids,
    split_scene_lead,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    BackgroundLens,
    CompositionTarget,
    DailyMeaningBrief,
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    FactorSource,
    GateFailureCode,
    PlanMode,
    ReadingCandidate,
    ReadingDomain,
    ReadingPlan,
    ReadingPurpose,
    SemanticArena,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer


def _date_only() -> DateOnlySunResult:
    return DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.CANCER,
        candidates=(ZodiacSign.CANCER,),
        provenance=EngineProvenance(version="2.10.03", profile="psychology-matrix-test"),
    )


def test_psychology_source_registry_has_ten_bounded_editorial_anchors() -> None:
    assert len(PSYCHOLOGY_SOURCES) == len(source_ids()) == 10
    assert issue_source_ids() <= source_ids()
    assert all(source.editorial_use and source.guardrail for source in PSYCHOLOGY_SOURCES)
    assert all(issue.source_ids for issue in DAILY_ISSUES)
    assert all(issue.observation_question.endswith("?") for issue in DAILY_ISSUES)
    assert all(6 <= len(issue.observation_question.split()) <= 20 for issue in DAILY_ISSUES)


def test_daily_matrix_does_not_ship_the_retired_opaque_perfectionism_headline() -> None:
    headlines = {headline.casefold() for issue in DAILY_ISSUES for headline in issue.headlines}

    assert "một việc chưa hoàn hảo có thể nằm yên lâu hơn một việc còn thiếu." not in headlines
    assert "bạn có thể sửa mãi một việc đã đủ dùng." in headlines


def test_daily_matrix_replays_same_day_and_keeps_scene_separate_from_advice() -> None:
    plan = ReadingPlanner().plan(
        _date_only(),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-10-02",
    )
    renderer = DeterministicVietnameseRenderer()

    first = renderer.render(plan)
    second = renderer.render(plan)

    assert first == second
    assert first.semantic_blueprint is not None
    assert first.semantic_blueprint.scene_key.startswith("psychology:")
    assert first.semantic_blueprint.action_key.startswith("psychology:")
    assert first.semantic_blueprint.daily_meaning is not None
    assert first.semantic_blueprint.daily_meaning.observation_question is not None
    meaning = first.semantic_blueprint.daily_meaning
    assert first.thesis.endswith(f" {meaning.reader_takeaway}")
    personal = first.thesis.removesuffix(f" {meaning.reader_takeaway}")
    assert meaning.core_meaning.startswith(f"{personal} ")
    assert not re.search(
        r"(?:^|[.!?]\s+)(?:hãy|thử|nên|đừng)\s+",
        f"{first.hook} {first.manifestation}",
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"(?:hỏi|viết|đợi|đọc|chọn|đặt|tắt|nói|giảm|hoãn|gửi|nhờ|xin|thử|kiểm tra)",
        first.micro_action,
        flags=re.IGNORECASE,
    )
    assert evaluate_candidate(plan, first).accepted is True


def test_year_has_365_distinct_cards_within_one_supported_meaning() -> None:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    start = date(2026, 10, 2)
    cards: set[tuple[str, str, str]] = set()
    meanings: set[str] = set()

    for offset in range(365):
        plan = planner.plan(
            _date_only(),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=(start + timedelta(days=offset)).isoformat(),
        )
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        cards.add((candidate.hook, candidate.manifestation, candidate.micro_action))
        assert candidate.semantic_blueprint is not None
        assert candidate.semantic_blueprint.daily_meaning is not None
        meanings.add(candidate.semantic_blueprint.daily_meaning.core_meaning)

    assert len(cards) == 365
    assert len(meanings) == 1


def test_each_user_selected_context_gets_a_concrete_matching_scene() -> None:
    markers = {
        BackgroundLens.RELATIONSHIPS: ("mối quan hệ", "người kia"),
        BackgroundLens.COMMUNICATION: ("cuộc nói chuyện", "đoạn chat"),
        BackgroundLens.WORK: ("công việc", "chuyện học"),
        BackgroundLens.ENERGY: ("cơ thể", "quá tải"),
        BackgroundLens.SELF_CARE: ("chăm mình", "nghỉ ngơi"),
    }
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()

    for lens, expected in markers.items():
        plan = planner.plan(
            _date_only(),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-10-02",
            background_lens=lens,
        )
        candidate = renderer.render(plan)
        assert any(marker in candidate.manifestation.casefold() for marker in expected)
        assert evaluate_candidate(plan, candidate).accepted is True


def test_reading_detail_does_not_replace_astrology_with_daily_psychology() -> None:
    plan = ReadingPlanner().plan(_date_only(), purpose=ReadingPurpose.READING_DETAIL)

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert candidate.semantic_blueprint is not None
    assert not candidate.semantic_blueprint.scene_key.startswith("psychology:")
    assert DAILY_PSYCHOLOGY_MATRIX_VERSION not in candidate.model_dump_json()


def test_every_authored_daily_combination_passes_the_direct_home_gate() -> None:
    for issue in DAILY_ISSUES:
        brief = DailyMeaningBrief(
            core_meaning=issue.meaning,
            reader_takeaway=issue.takeaway,
            scene_anchors=issue.scene_anchors,
            action_anchors=issue.action_anchors,
        )
        assert len(set(product(issue.headlines, issue.scenes, issue.advice))) == 384
        for arena in (SemanticArena.GENERAL, *issue.arenas):
            actions = (
                issue.relationship_advice if arena is SemanticArena.RELATIONSHIPS else issue.advice
            )
            for title, scene, action in product(issue.headlines, issue.scenes, actions):
                lead = _ARENA_LEADS.get(arena)
                manifestation = lead_scene(lead, scene) if lead else scene
                report = evaluate_daily_rewrite(
                    {"title": title, "scene": manifestation, "action": action}, meaning_brief=brief
                )
                assert report.passed, (issue.key, arena, title, scene, action, report.failure_codes)


def test_direct_contract_runs_before_fallback_publication_not_only_on_luna_output() -> None:
    plan = ReadingPlanner().plan(
        _date_only(), purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-07"
    )
    candidate = DeterministicVietnameseRenderer().render(plan)
    bad = candidate.model_copy(update={"hook": "Ý kiến đông người dễ nghe giống ý kiến đúng."})
    assert (
        GateFailureCode.MEANING_DAILY_DIRECT_CONTRACT in evaluate_candidate(plan, bad).failure_codes
    )


def test_direct_daily_style_survives_a_year_in_every_selected_context() -> None:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    start = date(2026, 10, 2)
    for lens in BackgroundLens:
        cards = set()
        for offset in range(365):
            plan = planner.plan(
                _date_only(),
                purpose=ReadingPurpose.DAILY_NOTE,
                editorial_seed=(start + timedelta(days=offset)).isoformat(),
                background_lens=lens,
            )
            candidate = renderer.render(plan)
            assert candidate.semantic_blueprint is not None
            brief = candidate.semantic_blueprint.daily_meaning
            assert brief is not None and brief.scene_status == "illustrative"
            report = evaluate_daily_rewrite(
                {
                    "title": candidate.hook,
                    "scene": candidate.manifestation,
                    "action": candidate.micro_action,
                },
                meaning_brief=brief,
            )
            assert report.passed, (lens, offset, report.failure_codes)
            assert evaluate_candidate(plan, candidate).accepted
            cards.add((candidate.hook, candidate.manifestation, candidate.micro_action))
        assert len(cards) == 365


def test_explicit_relationship_action_addresses_shared_need_not_only_own_capacity() -> None:
    for sign in (ZodiacSign.CANCER, ZodiacSign.CAPRICORN):
        source = DateOnlySunResult(
            status="certain",
            sign=sign,
            candidates=(sign,),
            provenance=_date_only().provenance,
        )
        planner = ReadingPlanner()
        auto = planner.plan(source, purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-09")
        relationship = planner.plan(
            source,
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-10-09",
            background_lens=BackgroundLens.RELATIONSHIPS,
        )
        first, second = _card(auto), _card(relationship)
        assert first.evidence == second.evidence
        assert first.semantic_blueprint is not None and second.semantic_blueprint is not None
        assert first.semantic_blueprint.daily_meaning == second.semantic_blueprint.daily_meaning
        assert first.micro_action != second.micro_action
        assert "người kia" in second.micro_action and "hỏi" in second.micro_action.lower()


def _placement(body: str, sign: str, *, primary: bool = False) -> DerivedFactor:
    domains = {
        "sun": ReadingDomain.CORE,
        "mercury": ReadingDomain.MIND,
        "moon": ReadingDomain.EMOTIONS,
        "saturn": ReadingDomain.CORE,
        "mars": ReadingDomain.DRIVE,
        "venus": ReadingDomain.RELATING,
    }
    factor_id = f"natal:{body}:sign:{sign}"
    return DerivedFactor(
        id=factor_id,
        tradition=_date_only_plan().tradition,
        source=FactorSource.NATAL,
        kind=FactorKind.PLANET_PLACEMENT,
        domain=domains[body],
        role=FactorRole.PRIMARY if primary else FactorRole.SUPPORTING,
        subjects=(body,),
        evidence_refs=(factor_id,),
        strength=0.9,
        salience=1,
        confidence=FactorConfidence.HIGH,
        allowed_language=(),
        forbidden_language=(),
    )


def _date_only_plan() -> ReadingPlan:
    return ReadingPlanner().plan(
        _date_only(), purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-09"
    )


def _semantic_plan(*factors: DerivedFactor) -> ReadingPlan:
    heroes = tuple(
        factor.id
        for factor in factors
        if factor.role
        in {
            FactorRole.PRIMARY,
            FactorRole.TENSION,
            FactorRole.REINFORCEMENT,
        }
    )
    if len(heroes) < 2 and not any(len(factor.child_refs) >= 2 for factor in factors):
        heroes = tuple(factor.id for factor in factors[:2])
    plan = _date_only_plan().model_copy(
        update={
            "factors": factors,
            "hero_factor_refs": heroes,
            "mode": PlanMode.FULL_SYNTHESIS,
            "precision": TimePrecision.EXACT,
        }
    )
    return ReadingPlan.model_validate(plan.model_dump())


def _card(plan: ReadingPlan) -> ReadingCandidate:
    candidate = DeterministicVietnameseRenderer().render(plan)
    assert evaluate_candidate(plan, candidate).accepted, evaluate_candidate(plan, candidate)
    return candidate


def _meaning(plan: ReadingPlan) -> tuple[str, str, str, str]:
    card = _card(plan)
    assert card.semantic_blueprint is not None and card.semantic_blueprint.daily_meaning is not None
    return (
        card.semantic_blueprint.daily_meaning.core_meaning,
        card.hook,
        card.manifestation,
        card.micro_action,
    )


def test_same_sun_different_relevant_mercury_changes_behavior_and_action() -> None:
    sun = _placement("sun", "pisces")
    earth = _semantic_plan(_placement("mercury", "virgo", primary=True), sun)
    air = _semantic_plan(_placement("mercury", "gemini", primary=True), sun)
    first, second = _meaning(earth), _meaning(air)
    assert "bản nháp" in first[2].lower() and "gửi" in first[3].lower()
    assert "việc" in second[2].lower() and "chọn" in second[3].lower()
    assert first[0] != second[0] and first[2:] != second[2:]


def _pair_plan(
    aspect: str = "square",
    phase: str = "applying",
    strength: float = 0.9,
    bodies: tuple[str, str] = ("mercury", "saturn"),
) -> ReadingPlan:
    a, b = (_placement(body, "virgo") for body in bodies)
    factor_id = f"natal:aspect:{bodies[0]}:{aspect}:{bodies[1]}:orb:0.500"
    interaction = DerivedFactor(
        id=factor_id,
        tradition=a.tradition,
        source=FactorSource.NATAL,
        kind=FactorKind.NATAL_ASPECT,
        domain=a.domain,
        role=FactorRole.TENSION if aspect == "square" else FactorRole.REINFORCEMENT,
        subjects=bodies,
        evidence_refs=(factor_id, f"natal:aspect:{bodies[0]}:{bodies[1]}:phase:{phase}"),
        child_refs=(a.id, b.id),
        strength=strength,
        salience=1.5,
        confidence=FactorConfidence.HIGH,
        allowed_language=(),
        forbidden_language=(),
    )
    return _semantic_plan(interaction, a, b)


def test_aspect_role_strength_and_phase_counterfactuals_change_supported_response() -> None:
    tense, cooperative = _meaning(_pair_plan()), _meaning(_pair_plan("trine"))
    assert "trì hoãn" in tense[0] and "gửi" in tense[3].lower()
    assert "phần" in cooperative[3].lower() and "góp ý" in cooperative[3].lower()
    assert tense[2:] != cooperative[2:]
    assert not any(
        s.rule_key.startswith("pair-") for s in eligible_daily_situations(_pair_plan(strength=0.1))
    )
    before = _meaning(_pair_plan(bodies=("moon", "mars")))
    after = _meaning(_pair_plan(phase="separating", bodies=("moon", "mars")))
    assert "đọc hết" in before[3].lower()
    assert any(term in after[3].lower() for term in ("nhắn lại", "nói lại"))
    assert before[0] != after[0]
    strong = _pair_plan(bodies=("sun", "saturn"))
    weak = _pair_plan(strength=0.1, bodies=("sun", "saturn"))
    assert _meaning(strong)[2:] != _meaning(weak)[2:]
    rerole = strong.factors[0].model_copy(update={"role": FactorRole.REINFORCEMENT})
    rerole_plan = strong.model_copy(update={"factors": (rerole, *strong.factors[1:])})
    assert _meaning(strong)[2:] != _meaning(rerole_plan)[2:]


def test_irrelevant_ids_or_order_do_not_invent_personality() -> None:
    plan = _pair_plan()
    changed = tuple(
        factor.model_copy(
            update={
                "evidence_refs": (
                    *factor.evidence_refs,
                    "opaque:test:unrelated-identifier",
                    "natal:aspect:venus:mars:phase:separating",
                ),
            }
        )
        for factor in reversed(plan.factors)
    )
    assert _meaning(plan) == _meaning(
        plan.model_copy(
            update={
                "plan_hash": "another-owner-independent-hash",
                "config_hash": "another-config",
                "factors": changed,
            }
        )
    )
    # Exact orb formatting is evidence, not a salt for an arbitrary issue.
    aspect = plan.factors[0]
    renamed = aspect.model_copy(update={"id": aspect.id.replace("0.500", "0.501")})
    renamed_plan = plan.model_copy(
        update={
            "factors": (renamed, *plan.factors[1:]),
            "hero_factor_refs": (renamed.id,),
        }
    )
    assert _meaning(plan) == _meaning(renamed_plan)


def test_known_house_refines_context_but_unknown_precision_excludes_it() -> None:
    venus = _placement("venus", "cancer", primary=True)
    sun = _placement("sun", "pisces")

    def house_plan(number: int) -> ReadingPlan:
        house_id = f"natal:venus:house:{number}"
        house = venus.model_copy(
            update={
                "id": house_id,
                "kind": FactorKind.HOUSE_PLACEMENT,
                "subjects": ("venus", f"house:{number}"),
                "evidence_refs": (house_id,),
                "child_refs": (venus.id,),
                "role": FactorRole.SUPPORTING,
            }
        )
        return _semantic_plan(venus, sun, house)

    routine, relating = house_plan(6), house_plan(7)
    assert _meaning(routine)[0] != _meaning(relating)[0]
    assert any(term in _meaning(routine)[3].lower() for term in ("lịch", "thời gian"))
    unknown = routine.model_copy(update={"precision": TimePrecision.UNKNOWN})
    plain = unknown.model_copy(update={"factors": unknown.factors[:2]})
    assert _meaning(unknown) == _meaning(plain)
    card = _card(unknown)
    assert card.semantic_blueprint is not None
    assert "natal:venus:house:6" not in card.semantic_blueprint.evidence_factor_refs
    assert all(claim.factor_ref != "natal:venus:house:6" for claim in card.evidence.claims)


def test_same_known_date_only_facts_legitimately_share_a_card_and_explain_limits() -> None:
    first = _date_only_plan()
    second = first.model_copy(update={"config_hash": "different-birth-input-provenance"})
    assert _meaning(first) == _meaning(second)
    card = _card(first)
    assert card.semantic_blueprint is not None and card.semantic_blueprint.daily_meaning is not None
    # The date-only limit is disclosed by the evidence, not repeated in the main text.
    assert any("chỉ từ ngày sinh" in claim.display_text for claim in card.evidence.claims)
    assert "giờ sinh" not in card.thesis


def test_unknown_sign_uses_explicitly_unpersonalized_hypothetical_scene() -> None:
    plan = ReadingPlanner().plan(
        DateOnlySunResult(
            status="candidates",
            sign=None,
            candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
            provenance=EngineProvenance(version="test", profile="test"),
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-10-09",
    )
    assert not eligible_daily_situations(plan)
    assert "chưa đủ dữ kiện" in _meaning(plan)[0]
    assert "nhà" not in " ".join(_card(plan).all_user_prose).lower()


def test_transit_phase_changes_hypothetical_response_not_event_prediction() -> None:
    moon = _placement("moon", "virgo", primary=True)
    sun = _placement("sun", "pisces")
    base = _semantic_plan(moon, sun)

    def transit_plan(phase: TransitPhase) -> ReadingPlan:
        factor_id = f"transit:mars:square:natal:moon:orb:0.100:phase:{phase.value}"
        contact = DerivedFactor(
            id=factor_id,
            tradition=moon.tradition,
            source=FactorSource.TRANSIT,
            kind=FactorKind.TRANSIT_CONTACT,
            domain=ReadingDomain.CURRENT_SKY,
            role=FactorRole.TRANSIT,
            subjects=("mars", "moon"),
            evidence_refs=(factor_id,),
            child_refs=(moon.id,),
            strength=0.9,
            salience=1,
            confidence=FactorConfidence.HIGH,
            phase=phase,
            allowed_language=(),
            forbidden_language=(),
        )
        plan = base.model_copy(
            update={
                "factors": (*base.factors, contact),
                "composition": CompositionTarget(natal_percent=80, transit_percent=20),
            }
        )
        return ReadingPlan.model_validate(plan.model_dump())

    approaching = transit_plan(TransitPhase.APPROACHING)
    separating = transit_plan(TransitPhase.SEPARATING)
    assert "đọc hết" in _meaning(approaching)[3].lower()
    assert any(term in _meaning(separating)[3].lower() for term in ("nhắn lại", "nói lại"))
    for plan in (approaching, separating):
        card = _card(plan)
        assert "sẽ" not in card.manifestation.lower()
        assert "có thể" in card.manifestation.lower()


def test_unrelated_supporting_body_does_not_change_selected_interaction() -> None:
    plan = _pair_plan()
    extra = _placement("venus", "cancer")
    assert _meaning(plan) == _meaning(
        plan.model_copy(
            update={
                "factors": (*plan.factors, extra),
            }
        )
    )


def test_synthetic_cohort20_measures_copy_collisions_separately_from_meaning() -> None:
    engine, planner = NatalChartEngine(), ReadingPlanner()
    cards: set[tuple[str, str, str]] = set()
    meanings: set[str] = set()
    # Twenty offline charts, ten pairs sharing a Sun season. No user data.
    for index in range(20):
        chart = engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(1980 + index, 3, 10 + index % 5, index % 24, 15, tzinfo=UTC),
                latitude=21.0278,
                longitude=105.8342,
            ),
            CalculationConfig.western_recommended(),
        )
        plan = planner.plan(chart, purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-09")
        card = _card(plan)
        assert card == DeterministicVietnameseRenderer().render(plan)
        assert (
            card.semantic_blueprint is not None
            and card.semantic_blueprint.daily_meaning is not None
        )
        assert set(card.semantic_blueprint.evidence_factor_refs) <= {f.id for f in plan.factors}
        issue_key = card.semantic_blueprint.mechanism_key.split(":")[1]
        assert any(
            situation.issue_key == issue_key
            and set(situation.factor_refs) <= set(card.semantic_blueprint.evidence_factor_refs)
            for situation in eligible_daily_situations(plan)
        )
        cards.add((card.hook, card.manifestation, card.micro_action))
        meanings.add(card.semantic_blueprint.daily_meaning.core_meaning)
    # Bounded knowledge can repeat. This gate checks semantic coverage, not global uniqueness.
    assert len(meanings) >= 8
    assert len(cards) >= 10


def test_browser_synthetic_full_pair_and_house_change_visible_scene_and_action() -> None:
    # A: 1998-03-15 date-only, known Pisces. B: 2000-10-06 14:30 Hanoi,
    # converted to 07:30 UTC. These are synthetic browser QA inputs, not users.
    planner = ReadingPlanner()
    a = planner.plan(
        DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=_date_only().provenance,
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-10-09",
    )
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(2000, 10, 6, 7, 30, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.western_recommended(),
    )
    b = planner.plan(chart, purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-09")
    first, second = _card(a), _card(b)
    assert second.semantic_blueprint is not None
    assert second.semantic_blueprint.mechanism_key == "psychology:specific-feedback"
    assert "chuyện học" in second.manifestation and "bản nháp" in second.manifestation
    assert "góp ý" in second.micro_action
    assert first.manifestation != second.manifestation
    assert first.micro_action != second.micro_action
    assert set(b.hero_factor_refs) <= set(second.semantic_blueprint.evidence_factor_refs)
    assert "natal:venus:house:9" in second.semantic_blueprint.evidence_factor_refs
    # The visible learning/work illustration depends on a supported exact house.
    unknown = b.model_copy(update={"precision": TimePrecision.UNKNOWN})
    unknown_card = _card(unknown)
    assert "chuyện học" not in unknown_card.manifestation
    assert unknown_card.semantic_blueprint is not None
    assert "natal:venus:house:9" not in unknown_card.semantic_blueprint.evidence_factor_refs


def test_equal_eligible_factors_do_not_consume_daily_novelty_slots() -> None:
    plan = _semantic_plan(_placement("mercury", "scorpio"), _placement("moon", "gemini"))
    assert len(eligible_daily_situations(plan)) == 2
    start = date(2026, 9, 12)
    cards, meanings = set(), set()
    for offset in range(365):
        day_plan = plan.model_copy(
            update={"editorial_seed": (start + timedelta(days=offset)).isoformat()}
        )
        card = _card(day_plan)
        assert (
            card.semantic_blueprint is not None
            and card.semantic_blueprint.daily_meaning is not None
        )
        cards.add((card.hook, card.manifestation, card.micro_action))
        meanings.add(card.semantic_blueprint.daily_meaning.core_meaning)
    assert len(cards) == 365
    assert len(meanings) == 1


_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def test_thesis_is_two_subject_sentences_that_do_not_repeat_the_card() -> None:
    """Owner audit 11.10.2026: the main paragraph was four glued, subjectless sentences."""
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    engine = NatalChartEngine()
    charts = [_date_only()] + [
        engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(1985 + i, (i % 12) + 1, 3 + i, (i * 5) % 24, 10, tzinfo=UTC),
                latitude=10.8 + i * 0.3,
                longitude=106.6 - i * 0.2,
            ),
            CalculationConfig.western_recommended(),
        )
        for i in range(8)
    ]
    for chart, lens, offset in product(charts, BackgroundLens, range(0, 60, 7)):
        day = date(2026, 10, 1) + timedelta(days=offset)
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            background_lens=lens,
            editorial_seed=day.isoformat(),
        )
        card = renderer.render(plan)
        sentences = _SENTENCE.split(card.thesis)
        assert len(sentences) == 2, card.thesis
        # Sentence 1 is about the reader; sentence 2 may name another subject
        # ("Người đọc …") but never opens subjectless with advice or a caveat.
        assert sentences[0].startswith(("Bạn ", "Lá ")), sentences[0]
        for sentence in sentences:
            assert not sentence.startswith(("Có thể", "Nên", "Cảnh", "Chỉ là")), sentence
            for other in (card.hook, card.manifestation, card.micro_action):
                assert sentence not in other, (sentence, other)
        assert "dự báo" not in card.thesis and "giờ sinh" not in card.thesis
        # The context lead opens the scene sentence instead of being a fragment.
        assert not card.manifestation.startswith("Ví dụ")
        arena, scene = split_scene_lead(card.manifestation)
        if arena is not None:
            assert lead_scene(_ARENA_LEADS[arena], scene) == card.manifestation
