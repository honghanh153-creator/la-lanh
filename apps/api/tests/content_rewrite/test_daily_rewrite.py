from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import JsonValue

from app.domains.astro.models import DateOnlySunResult, EngineProvenance, ZodiacSign
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    DailyMeaningBrief,
    ReadingCandidate,
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
    DailyRewriteProjector,
    compile_daily_rewrite_request,
)

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _records() -> tuple[ReadingPlanRecord, ReadingProjectionRecord, ReadingRevisionRecord]:
    guest_id = UUID("20000000-0000-4000-8000-000000000101")
    profile_id = UUID("30000000-0000-4000-8000-000000000101")
    plan = ReadingPlanner().plan(
        DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=EngineProvenance(version="test", profile="test"),
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-10-03",
    )
    plan_record = ReadingPlanRecord(
        id=UUID("40000000-0000-4000-8000-000000000101"),
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
        id=UUID("50000000-0000-4000-8000-000000000101"),
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
        purpose=ReadingPurpose.DAILY_NOTE,
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
        purpose=ReadingPurpose.DAILY_NOTE,
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


def _good_output(baseline: ReadingCandidate | None = None) -> dict[str, JsonValue]:
    if baseline is not None:
        return {
            "title": baseline.hook,
            "scene": baseline.manifestation,
            "action": baseline.micro_action,
        }
    return {
        "title": "Tiến độ của người khác không phải thước đo.",
        "scene": "Khi thấy người khác khoe kết quả, bạn so sánh tiến độ của mình với họ.",
        "action": "Chọn một việc của mình để làm xong trước khi xem tiếp.",
    }


def test_daily_gate_requires_plain_connected_scene_and_action() -> None:
    assert evaluate_daily_rewrite(_good_output()).passed

    abstract = _good_output() | {"scene": "Tín hiệu vũ trụ đang mời gọi một nhịp bên trong."}
    report = evaluate_daily_rewrite(abstract)
    assert not report.passed
    assert "daily_opaque_filler" in report.failure_codes

    disconnected = _good_output() | {"action": "Ghi ba món đồ đang có trên bàn."}
    report = evaluate_daily_rewrite(disconnected)
    assert not report.passed
    assert "daily_scene_action_disconnected" in report.failure_codes


def test_daily_gate_rejects_copy_that_drifts_from_source_meaning() -> None:
    report = evaluate_daily_rewrite(
        _good_output(),
        source_scene="Khi một tin nhắn ngắn khiến ý của người kia chưa rõ.",
        source_action="Hỏi lại một câu rõ ràng trước khi kết luận.",
    )

    assert not report.passed
    assert "daily_scene_meaning_drift" in report.failure_codes
    assert "daily_action_meaning_drift" in report.failure_codes


def test_daily_compiler_sends_only_derived_safe_brief() -> None:
    plan_record, projection, _revision = _records()
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)

    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    serialized = json.dumps(request.safe_payload, ensure_ascii=False).lower()
    assert request.key.surface.value == "daily_home"
    assert set(request.safe_payload) == {
        "context",
        "scene_key",
        "action_key",
        "title_meaning",
        "scene_meaning",
        "action_meaning",
        "meaning_brief",
        "requirements",
        "evidence",
    }
    assert "1990" not in serialized
    assert "latitude" not in serialized
    assert "longitude" not in serialized
    assert str(plan_record.guest_id) not in serialized
    assert baseline.semantic_blueprint is not None
    assert baseline.semantic_blueprint.daily_meaning is not None
    assert request.safe_payload["meaning_brief"] == (
        baseline.semantic_blueprint.daily_meaning.model_dump(mode="json")
    )
    assert request.key.gate_version == "daily-rewrite-gates/v2"


def test_daily_gate_rejects_the_exact_opaque_card_reported_by_the_user() -> None:
    report = evaluate_daily_rewrite(
        {
            "title": "Ý kiến đông người dễ nghe giống ý kiến đúng.",
            "scene": (
                "Hôm nay, khi cả nhóm đồng ý nhanh, bạn dễ gật theo dù vẫn còn một câu hỏi. "
                "Sự tự tin của người nói có thể đang được nghe như bằng chứng."
            ),
            "action": (
                "Nói câu bạn còn chưa rõ trước khi đồng ý. Làm xong, xem tình hình có dễ hơn không."
            ),
        }
    )
    assert not report.passed
    assert "daily_opaque_filler" in report.failure_codes


def test_daily_action_does_not_ask_to_act_before_a_choice_already_made() -> None:
    report = evaluate_daily_rewrite(
        {
            "title": "Bạn gật đầu, nhưng vẫn chưa hiểu hết.",
            "scene": (
                "Khi cả nhóm chuyển sang việc tiếp theo, bạn có thể đã gật đầu "
                "dù chưa hiểu rõ điều vừa chốt."
            ),
            "action": "Hỏi cả nhóm vì sao chọn cách đó trước khi đồng ý.",
        }
    )
    assert "daily_action_timing_conflict" in report.failure_codes


def test_daily_brief_rejects_wrong_advice_even_when_both_scenes_mention_a_question() -> None:
    brief = DailyMeaningBrief(
        core_meaning="Cả nhóm chốt nhưng mình vẫn còn phần chưa hiểu.",
        reader_takeaway="Có thể hỏi lại phần chưa hiểu.",
        scene_anchors=("nhóm",),
        action_anchors=("giải thích", "nhóm", "chưa hiểu"),
    )
    good = {
        "title": "Bạn gật đầu, nhưng vẫn chưa hiểu hết.",
        "scene": (
            "Khi cả nhóm chốt rất nhanh, bạn có thể đồng ý theo dù vẫn còn một chỗ muốn hỏi lại."
        ),
        "action": "Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?",
    }
    assert evaluate_daily_rewrite(good, meaning_brief=brief).passed
    wrong_action = good | {"action": "Hỏi người gửi tin nhắn xem họ muốn nói gì."}
    report = evaluate_daily_rewrite(wrong_action, meaning_brief=brief)
    assert "daily_action_brief_drift" in report.failure_codes
    wrong_scene = good | {
        "scene": "Khi nhận một tin nhắn ngắn, bạn có thể chưa hiểu người gửi muốn nói gì."
    }
    assert (
        "daily_scene_brief_drift"
        in evaluate_daily_rewrite(wrong_scene, meaning_brief=brief).failure_codes
    )


@pytest.mark.parametrize(
    ("scene", "failure"),
    [
        ("Hãy hỏi cả nhóm trước khi chốt lựa chọn của mình.", "daily_advice_in_scene"),
        (
            "Khi cả nhóm chốt, bạn chắc chắn sẽ đồng ý theo dù chưa hiểu.",
            "daily_unwarranted_certainty",
        ),
    ],
)
def test_daily_scene_does_not_become_advice_or_a_certain_prediction(
    scene: str, failure: str
) -> None:
    report = evaluate_daily_rewrite(_good_output() | {"scene": scene})
    assert failure in report.failure_codes


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


@pytest.mark.asyncio
async def test_daily_projector_keeps_blueprint_and_publishes_as_available_only() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    decision = await DailyRewriteProjector(repository).validate_and_project(
        request,
        _good_output(baseline),
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
    assert candidate.hook == _good_output(baseline)["title"]


@pytest.mark.asyncio
async def test_daily_shadow_validates_and_saves_candidate_without_exposing_it() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    decision = await DailyRewriteProjector(repository).validate_and_project(
        request,
        _good_output(baseline),
        completed_at=NOW,
        publish=False,
    )

    assert decision.accepted
    assert repository.projection.active_revision_id == active.id
    assert repository.projection.available_revision_id is None
    assert len(repository.revisions) == 2
