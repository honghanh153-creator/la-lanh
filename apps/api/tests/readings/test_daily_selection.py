"""B1b: the Daily situation is chosen once and a transit is shown only as its real reason."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    BodyName,
    CalculationConfig,
    ChartInput,
    NatalChart,
    TransitPhase,
    TransitToNatalContact,
    TransitToNatalSnapshot,
)
from app.domains.readings import application as application_module
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.daily_personalization import PAIR_RULES
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    CandidateEvaluation,
    DailyTransitRole,
    FactorSource,
    ReadingCandidate,
    ReadingPlan,
    ReadingPurpose,
    canonical_reading_plan_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_application import NOW, MemoryReadingRepository, _exact_snapshot

_ENGINE = NatalChartEngine()


def _chart(index: int) -> NatalChart:
    return _ENGINE.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1985 + index, (index % 12) + 1, 3 + index, 9, 10, tzinfo=UTC),
            latitude=10.8 + index * 0.3,
            longitude=106.6 - index * 0.2,
        ),
        CalculationConfig.western_recommended(),
    )


def _oracle_issue(transit_id: str) -> str | None:
    """Independent re-implementation of what a transit's pair rule means.

    Written from PAIR_RULES and the factor id only, so the audit does not grade
    the selector with its own predicate.
    """
    parts = transit_id.split(":")
    body_a, aspect, body_b, phase = parts[1], parts[2], parts[4], parts[8]
    rule = next((rule for rule in PAIR_RULES if rule.bodies == {body_a, body_b}), None)
    if rule is None:
        return None
    if aspect in {"square", "opposition"}:
        issue = rule.tension_issue
        return "repair-reply" if issue == "quick-reply" and phase == "separating" else issue
    if aspect in {"trine", "sextile"}:
        return rule.cooperative_issue
    return rule.conjunction_issue


def _daily(chart: NatalChart, day: datetime) -> ReadingPlan:
    return ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=_ENGINE.calculate_transit_to_natal(chart, day),
        editorial_seed=day.date().isoformat(),
    )


def test_every_shown_transit_passes_the_independent_mechanism_oracle() -> None:
    shown = 0
    for index in range(4):
        chart = _chart(index)
        for offset in range(0, 40, 2):
            plan = _daily(chart, datetime(2026, 10, 1, 5, tzinfo=UTC) + timedelta(days=offset))
            selection = plan.daily_selection
            assert selection is not None
            transits = [f for f in plan.factors if f.source is FactorSource.TRANSIT]
            if selection.transit_role is DailyTransitRole.NONE:
                assert not transits
                continue
            (transit,) = transits
            shown += 1
            assert transit.id == selection.transit_ref
            assert _oracle_issue(transit.id) == selection.issue_key
            if selection.transit_role is DailyTransitRole.DRIVES:
                assert transit.id in selection.support_refs
            else:
                assert set(transit.child_refs) & set(selection.support_refs)
    assert shown > 0  # the sample must exercise the transit path


def test_planning_is_idempotent_and_independent_of_contact_order() -> None:
    chart = _chart(2)
    day = datetime(2026, 10, 9, 5, tzinfo=UTC)
    snapshot = _ENGINE.calculate_transit_to_natal(chart, day)
    reversed_snapshot = snapshot.model_copy(update={"contacts": snapshot.contacts[::-1]})
    planner = ReadingPlanner()
    plans = [
        planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            transits=transits,
            editorial_seed=day.date().isoformat(),
        )
        for transits in (snapshot, snapshot, reversed_snapshot)
    ]
    assert plans[0] == plans[1] == plans[2]
    assert len({canonical_reading_plan_key(plan) for plan in plans}) == 1


def test_rendered_situation_is_exactly_the_frozen_one() -> None:
    chart = _chart(1)
    for offset in range(0, 30, 3):
        plan = _daily(chart, datetime(2026, 10, 1, 5, tzinfo=UTC) + timedelta(days=offset))
        candidate = DeterministicVietnameseRenderer().render(plan)
        assert plan.daily_selection is not None
        assert candidate.semantic_blueprint is not None
        assert candidate.semantic_blueprint.mechanism_key == (
            f"psychology:{plan.daily_selection.issue_key}"
        )


def test_plans_stored_before_b1b_keep_their_key() -> None:
    plan = ReadingPlanner().plan(_chart(0), purpose=ReadingPurpose.READING_DETAIL)
    assert plan.daily_selection is None
    stored = plan.model_dump(mode="json")
    stored.pop("daily_selection")
    reloaded = ReadingPlan.model_validate(stored)
    assert canonical_reading_plan_key(reloaded) == canonical_reading_plan_key(plan)
    assert "daily_selection" not in plan.model_dump_json(exclude={"daily_selection"})


class _MarsSquareMoonEngine(NatalChartEngine):
    def calculate_transit_to_natal(
        self, chart: NatalChart, observed_at: datetime
    ) -> TransitToNatalSnapshot:
        return TransitToNatalSnapshot(
            observed_at=observed_at,
            contacts=(
                TransitToNatalContact(
                    transit_body=BodyName.MARS,
                    natal_body=BodyName.MOON,
                    kind="square",
                    exact_angle=90.0,
                    orb=0.1,
                    phase=TransitPhase.APPROACHING,
                ),
            ),
            orb_policy_version="transit-orbs-v1",
            provenance=chart.provenance,
            config=chart.config,
            config_hash=chart.config_hash,
        )


@pytest.mark.asyncio
async def test_rejected_daily_transit_replans_natal_only_instead_of_keeping_its_words(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _MarsSquareMoonEngine()
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(repository, engine)
    real_evaluate = evaluate_candidate
    rejected_plans: list[ReadingPlan] = []

    def reject_transits(plan: ReadingPlan, candidate: ReadingCandidate) -> CandidateEvaluation:
        evaluation = real_evaluate(plan, candidate)
        if candidate.transit is not None:
            rejected_plans.append(plan)
            return evaluation.model_copy(update={"accepted": False, "publishable_candidate": None})
        return evaluation

    monkeypatch.setattr(application_module, "evaluate_candidate", reject_transits)
    guest_id = UUID("20000000-0000-4000-8000-0000000000b1")
    profile_id = UUID("30000000-0000-4000-8000-0000000000b1")

    projection = await service.project(
        guest_id=guest_id,
        snapshot=_exact_snapshot(guest_id, profile_id, engine),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )

    assert rejected_plans, "the fixture must offer a transit reason first"
    first = rejected_plans[0].daily_selection
    assert first is not None and first.transit_ref is not None
    content = projection.active
    assert content.sections.transit is None
    # Transit claims read "X đang <góc> Y"; natal claims never use "đang".
    assert all(" đang " not in claim for claim in content.evidence.claims)
    assert all(
        "đang tạo góc căng" not in section
        for section in content.sections.model_dump().values()
        if isinstance(section, str)
    )
