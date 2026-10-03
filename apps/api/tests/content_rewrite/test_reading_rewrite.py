from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import JsonValue

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_gate_policy_version,
    canonical_projection_scope_key,
    canonical_reading_plan_key,
    canonical_reading_revision_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.rewrite import (
    ReadingRewriteProjector,
    compile_reading_rewrite_request,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _records(
    purpose: ReadingPurpose = ReadingPurpose.READING_DETAIL,
) -> tuple[ReadingPlanRecord, ReadingProjectionRecord, ReadingRevisionRecord]:
    guest_id = UUID("20000000-0000-4000-8000-000000000201")
    profile_id = UUID("30000000-0000-4000-8000-000000000201")
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1998, 6, 15, 1, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.western_recommended(),
    )
    plan = ReadingPlanner().plan(chart, purpose=purpose)
    plan_record = ReadingPlanRecord(
        id=UUID("40000000-0000-4000-8000-000000000201"),
        guest_id=guest_id,
        profile_id=profile_id,
        plan_key=canonical_reading_plan_key(plan),
        plan=plan,
        created_at=NOW,
    )
    baseline = DeterministicVietnameseRenderer().render(plan)
    evaluation = evaluate_candidate(plan, baseline)
    gate_policy = canonical_gate_policy_version(evaluation)
    revision = ReadingRevisionRecord(
        id=UUID("50000000-0000-4000-8000-000000000201"),
        guest_id=guest_id,
        profile_id=profile_id,
        plan_id=plan_record.id,
        revision_key=canonical_reading_revision_key(
            plan_key=plan_record.plan_key,
            source=ReadingRevisionSource.DETERMINISTIC,
            renderer_version=baseline.renderer_version,
            content_version="baseline",
            schema_version=baseline.schema_version,
            rules_version=plan.rules_version,
            gate_policy_version=gate_policy,
        ),
        source=ReadingRevisionSource.DETERMINISTIC,
        renderer_version=baseline.renderer_version,
        content_version="baseline",
        schema_version=baseline.schema_version,
        rules_version=plan.rules_version,
        gate_policy_version=gate_policy,
        evaluation=evaluation,
        created_at=NOW,
    )
    scope_key = canonical_projection_scope_key(
        purpose=plan.purpose,
        tradition=plan.tradition,
        config_hash=plan.config_hash,
        local_date=NOW.date(),
        timezone_name="Asia/Ho_Chi_Minh",
        observed_at=NOW,
        lens_variant=None,
    )
    projection = ReadingProjectionRecord(
        id=uuid4(),
        guest_id=guest_id,
        profile_id=profile_id,
        scope_key=scope_key,
        purpose=plan.purpose,
        tradition=plan.tradition,
        config_hash=plan.config_hash,
        local_date=NOW.date(),
        timezone_name="Asia/Ho_Chi_Minh",
        observed_at=NOW,
        active_revision_id=revision.id,
        created_at=NOW,
        updated_at=NOW,
    )
    return plan_record, projection, revision


def _output(plan_record: ReadingPlanRecord) -> dict[str, JsonValue]:
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    return {
        "headline": baseline.hook,
        "synthesis": baseline.thesis,
        "section_intros": [baseline.manifestation],
        "examples": [baseline.micro_action],
    }


class MemoryRepository:
    def __init__(
        self,
        plan: ReadingPlanRecord,
        projection: ReadingProjectionRecord,
        active: ReadingRevisionRecord,
    ) -> None:
        self.plan = plan
        self.projection = projection
        self.revisions = {active.id: active}

    async def get_plan(self, guest_id, profile_id, plan_id):  # type: ignore[no-untyped-def]
        if (guest_id, profile_id, plan_id) == (
            self.plan.guest_id,
            self.plan.profile_id,
            self.plan.id,
        ):
            return self.plan
        return None

    async def get_projection(self, guest_id, profile_id, scope_key):  # type: ignore[no-untyped-def]
        if (guest_id, profile_id, scope_key) == (
            self.projection.guest_id,
            self.projection.profile_id,
            self.projection.scope_key,
        ):
            return self.projection
        return None

    async def get_revision(self, guest_id, profile_id, revision_id):  # type: ignore[no-untyped-def]
        revision = self.revisions.get(revision_id)
        if revision and (revision.guest_id, revision.profile_id) == (guest_id, profile_id):
            return revision
        return None

    async def save_or_replay_revision(self, record):  # type: ignore[no-untyped-def]
        self.revisions[record.id] = record
        return record, False

    async def publish_available(self, guest_id, profile_id, scope_key, revision_id):  # type: ignore[no-untyped-def]
        assert (guest_id, profile_id, scope_key) == (
            self.projection.guest_id,
            self.projection.profile_id,
            self.projection.scope_key,
        )
        self.projection = self.projection.model_copy(update={"available_revision_id": revision_id})
        return self.projection


def test_reading_compiler_sends_closed_meanings_without_raw_birth_data() -> None:
    plan_record, projection, _revision = _records()
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)

    request = compile_reading_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    assert request.key.surface.value == "natal"
    assert set(request.safe_payload) == {
        "purpose",
        "precision",
        "mode",
        "hero_labels",
        "source_sections",
        "requirements",
        "evidence",
    }
    sections = cast(list[dict[str, JsonValue]], request.safe_payload["source_sections"])
    assert {section["section"] for section in sections} == {
        "hook",
        "thesis",
        "manifestation",
        "micro_action",
    }
    serialized = json.dumps(request.safe_payload, ensure_ascii=False).lower()
    assert "1998-06-15" not in serialized
    assert "21.0278" not in serialized
    assert "105.8342" not in serialized
    assert str(plan_record.profile_id) not in serialized
    assert PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)


@pytest.mark.parametrize(
    ("purpose", "expected_surface"),
    [
        (ReadingPurpose.AURA, "reveal"),
        (ReadingPurpose.READING_DETAIL, "natal"),
        (ReadingPurpose.PERSONALIZED_SKY, "transit_insight"),
    ],
)
def test_reading_compiler_maps_each_long_form_purpose_to_its_surface(
    purpose: ReadingPurpose,
    expected_surface: str,
) -> None:
    plan_record, projection, _revision = _records(purpose)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)

    request = compile_reading_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    assert request.key.surface.value == expected_surface


@pytest.mark.asyncio
async def test_reading_projector_preserves_meaning_and_publishes_available_only() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    request = compile_reading_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    decision = await ReadingRewriteProjector(repository).validate_and_project(
        request,
        _output(plan_record),
        completed_at=NOW,
    )

    assert decision.accepted
    assert repository.projection.active_revision_id == active.id
    assert repository.projection.available_revision_id is not None
    generated = repository.revisions[repository.projection.available_revision_id]
    candidate = generated.evaluation.publishable_candidate
    assert candidate is not None
    assert candidate.semantic_blueprint == baseline.semantic_blueprint
    assert candidate.evidence == baseline.evidence


@pytest.mark.asyncio
async def test_reading_projector_rejects_output_that_drops_required_meaning() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    request = compile_reading_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )
    drifted = _output(plan_record) | {
        "synthesis": "Bạn thích đồ uống mát và những buổi sáng nhiều nắng.",
        "section_intros": ["Hôm nay có thể chọn một món ăn mới."],
        "examples": ["Ghi tên món ăn đó vào một tờ giấy."],
    }

    decision = await ReadingRewriteProjector(repository).validate_and_project(
        request,
        drifted,
        completed_at=NOW,
    )

    assert not decision.accepted
    assert repository.projection.available_revision_id is None
