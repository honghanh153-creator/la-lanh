from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import JsonValue

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    ZodiacSign,
)
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings.companion import companion_issue_entry
from app.domains.readings.daily_psychology import current_scene_lead, split_scene_lead
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    BackgroundLens,
    DailyMeaningBrief,
    GateFailureCode,
    ReadingCandidate,
    ReadingPlan,
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


def _records(
    plan: ReadingPlan | None = None,
) -> tuple[ReadingPlanRecord, ReadingProjectionRecord, ReadingRevisionRecord]:
    guest_id = UUID("20000000-0000-4000-8000-000000000101")
    profile_id = UUID("30000000-0000-4000-8000-000000000101")
    plan = plan or ReadingPlanner().plan(
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


_COMPANION = "Làm thử một bước nhỏ hôm nay thôi nhé."


def _authored_companion(baseline: ReadingCandidate) -> str:
    blueprint = baseline.semantic_blueprint
    return companion_issue_entry(blueprint.mechanism_key if blueprint else None).line.direct


def _good_output(baseline: ReadingCandidate | None = None) -> dict[str, JsonValue]:
    if baseline is not None:
        return {
            "title": baseline.hook,
            "scene": baseline.manifestation,
            "action": baseline.micro_action,
            "companion": _authored_companion(baseline),
        }
    return {
        "title": "Tiến độ của người khác không phải thước đo.",
        "scene": "Khi thấy người khác khoe kết quả, bạn so sánh tiến độ của mình với họ.",
        "action": "Chọn một việc của mình để làm xong trước khi xem tiếp.",
        "companion": _COMPANION,
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
    assert baseline.semantic_blueprint is not None

    serialized = json.dumps(request.safe_payload, ensure_ascii=False).lower()
    assert request.key.surface.value == "daily_home"
    assert set(request.safe_payload) == {
        "context",
        "scene_key",
        "action_key",
        "title_meaning",
        "scene_meaning",
        "action_meaning",
        "companion_meaning",
        "meaning_brief",
        "requirements",
        "evidence",
    }
    # Lá's brief is editorial meaning from the catalog, never the authored sentence.
    entry = companion_issue_entry(baseline.semantic_blueprint.mechanism_key)
    assert request.safe_payload["companion_meaning"] == entry.meaning
    assert entry.line.direct not in serialized and entry.line.roast not in serialized
    assert request.key.schema_version == "daily-rewrite/v2"
    assert "1990" not in serialized
    assert "latitude" not in serialized
    assert "longitude" not in serialized
    assert str(plan_record.guest_id) not in serialized
    assert baseline.semantic_blueprint is not None
    assert baseline.semantic_blueprint.daily_meaning is not None
    assert request.safe_payload["meaning_brief"] == (
        baseline.semantic_blueprint.daily_meaning.model_dump(mode="json")
    )
    assert request.key.gate_version == "daily-rewrite-gates/v4"


def test_daily_compiler_carries_supported_full_chart_meaning_through_privacy_allowlist() -> None:
    from app.domains.content_rewrite.models import RewriteSurface
    from app.infrastructure.generation.privacy import PrivacyMinimiser

    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1980, 3, 10, 0, 15, tzinfo=UTC),
            latitude=21.0278,
            longitude=105.8342,
        ),
        CalculationConfig.western_recommended(),
    )
    plan = ReadingPlanner().plan(
        chart, purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-09"
    )
    record, projection, _ = _records(plan)
    baseline = DeterministicVietnameseRenderer().render(plan)
    request = compile_daily_rewrite_request(
        record, projection, baseline, model_version="offline", prompt_version="test"
    )
    assert baseline.semantic_blueprint is not None
    brief = baseline.semantic_blueprint.daily_meaning
    assert brief is not None and brief.scene_status == "illustrative"
    assert request.safe_payload["meaning_brief"] == brief.model_dump(mode="json")
    safe = PrivacyMinimiser().minimise(RewriteSurface.DAILY_HOME, request.safe_payload)
    assert safe["meaning_brief"] == request.safe_payload["meaning_brief"]
    serialized = json.dumps(safe, ensure_ascii=False)
    assert "1980" not in serialized and "21.0278" not in serialized
    assert all(factor.id not in serialized for factor in plan.factors)
    assert evaluate_daily_rewrite(_good_output(baseline), meaning_brief=brief).passed


def test_daily_compiler_rejects_unaccepted_fallback_before_rewrite() -> None:
    record, projection, _ = _records()
    baseline = DeterministicVietnameseRenderer().render(record.plan)
    with pytest.raises(ValueError, match="gate-accepted baseline"):
        compile_daily_rewrite_request(
            record,
            projection,
            baseline.model_copy(update={"plan_hash": "wrong-plan"}),
            model_version="offline",
            prompt_version="test",
        )


def test_daily_compiler_hashes_meaning_and_preserves_its_allowed_distinction() -> None:
    requests = []
    for sign in (ZodiacSign.CANCER, ZodiacSign.GEMINI):
        plan = ReadingPlanner().plan(
            DateOnlySunResult(
                status="certain",
                sign=sign,
                candidates=(sign,),
                provenance=EngineProvenance(version="test", profile="test"),
            ),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-10-09",
        )
        record, projection, _ = _records(plan)
        baseline = DeterministicVietnameseRenderer().render(plan)
        requests.append(
            compile_daily_rewrite_request(
                record, projection, baseline, model_version="offline", prompt_version="test"
            )
        )
    assert requests[0].key.blueprint_hash != requests[1].key.blueprint_hash
    assert requests[0].safe_payload["action_meaning"] != requests[1].safe_payload["action_meaning"]
    assert requests[0].safe_payload["meaning_brief"] != requests[1].safe_payload["meaning_brief"]


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
            "companion": _COMPANION,
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
            "companion": _COMPANION,
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
        "companion": _COMPANION,
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


def _lens_baseline(lens: BackgroundLens) -> ReadingCandidate:
    plan = ReadingPlanner().plan(
        NatalChartEngine().calculate_chart(
            ChartInput(
                utc_datetime=datetime(1992, 5, 14, 3, 30, tzinfo=UTC),
                latitude=16.0544,
                longitude=108.2022,
            ),
            CalculationConfig.western_recommended(),
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
        background_lens=lens,
        editorial_seed="2026-10-13",
    )
    baseline = DeterministicVietnameseRenderer().render(plan)
    assert evaluate_candidate(plan, baseline).accepted
    return baseline


def _v7_report(baseline: ReadingCandidate, output: dict[str, JsonValue]) -> tuple[str, ...]:
    blueprint = baseline.semantic_blueprint
    assert blueprint is not None
    return evaluate_daily_rewrite(
        output,
        source_scene=blueprint.manifestation,
        source_action=blueprint.micro_action,
        meaning_brief=blueprint.daily_meaning,
    ).failure_codes


@pytest.mark.parametrize(
    "lens", [lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO]
)
def test_v7_baseline_passes_its_own_rewrite_gate_with_the_context_clause(
    lens: BackgroundLens,
) -> None:
    baseline = _lens_baseline(lens)
    lead = current_scene_lead(baseline.manifestation)
    assert lead is not None and lead.endswith(",")
    assert _v7_report(baseline, _good_output(baseline)) == ()


def test_v7_rewrite_must_keep_the_scene_context_clause() -> None:
    baseline = _lens_baseline(BackgroundLens.RELATIONSHIPS)
    lead = current_scene_lead(baseline.manifestation)
    assert lead == "Với người kia,"
    _, scene = split_scene_lead(baseline.manifestation)

    dropped = _good_output(baseline) | {"scene": scene}
    assert "daily_scene_context_lost" in _v7_report(baseline, dropped)

    fragment = _good_output(baseline) | {"scene": f"Ví dụ với người kia. {scene}"}
    codes = _v7_report(baseline, fragment)
    assert "daily_scene_fragment" in codes
    assert "daily_scene_context_lost" in codes


def test_v7_rewrite_must_not_repeat_the_takeaway_already_on_the_card() -> None:
    baseline = _lens_baseline(BackgroundLens.WORK)
    assert baseline.semantic_blueprint is not None
    brief = baseline.semantic_blueprint.daily_meaning
    assert brief is not None
    assert brief.reader_takeaway in baseline.thesis
    repeated = _good_output(baseline) | {"title": brief.reader_takeaway}
    assert "daily_takeaway_repeated" in _v7_report(baseline, repeated)


@pytest.mark.asyncio
async def test_daily_projector_never_lets_a_rewrite_touch_the_two_sentence_thesis() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v4",
    )
    assert "thesis" not in request.safe_payload

    decision = await DailyRewriteProjector(repository).validate_and_project(
        request, _good_output(baseline), completed_at=NOW
    )

    assert decision.accepted
    assert repository.projection.available_revision_id is not None
    generated = repository.revisions[repository.projection.available_revision_id]
    candidate = generated.evaluation.publishable_candidate
    assert candidate is not None
    assert candidate.thesis == baseline.thesis


def test_daily_prompt_teaches_the_v7_card_shape() -> None:
    from app.domains.content_rewrite.models import RewriteSurface
    from app.infrastructure.generation.openai import OPENAI_REWRITE_PROMPT_VERSION
    from app.infrastructure.generation.schemas import surface_output_contract

    instruction = surface_output_contract(RewriteSurface.DAILY_HOME).developer_instruction
    assert OPENAI_REWRITE_PROMPT_VERSION == "surface-rewrite-v5"
    assert "start the scene with exactly that clause" in instruction
    # v5: Lá's companion line, written from companion_meaning in the shared voice.
    assert "companion: one line by Lá (sprout friend)" in instruction
    assert "anyone's thoughts" in instruction
    assert "never write a separate fragment such as 'Ví dụ …'" in instruction
    assert "never repeat it" in instruction
    assert "limitation" not in instruction


@pytest.mark.parametrize(
    ("companion", "failure"),
    [
        ("Ừ.", "daily_companion_budget"),
        ("Mặt Trăng đang đỡ bạn, thử một bước nhỏ nhé.", "daily_companion_astro_term"),
        ("Lá biết bạn sẽ làm được mà, thử đi.", "daily_companion_mind_reading"),
        ("Người kia muốn bạn hỏi trước, nhắn đi nào.", "daily_companion_mind_reading"),
        ("Làm đi, chắc chắn sẽ ổn thôi mà.", "daily_companion_certainty"),
        ("Chọn một việc của mình để làm xong trước khi xem tiếp.", "daily_companion_repeats_card"),
    ],
)
def test_daily_companion_line_keeps_las_rules(companion: str, failure: str) -> None:
    report = evaluate_daily_rewrite(_good_output() | {"companion": companion})
    assert failure in report.failure_codes


def test_daily_companion_line_is_required_and_projected_with_the_card() -> None:
    missing = {key: value for key, value in _good_output().items() if key != "companion"}
    assert evaluate_daily_rewrite(missing).failure_codes == ("daily_required_fields",)


def _companion_case() -> tuple[ReadingCandidate, str]:
    plan_record, _projection, _active = _records()
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)
    assert baseline.semantic_blueprint is not None
    anchor = companion_issue_entry(baseline.semantic_blueprint.mechanism_key).anchors[0]
    return baseline, anchor


@pytest.mark.parametrize(
    ("template", "gate_code"),
    [
        ("{a} xong thì nên tăng thuốc ngay hôm nay nhé.", GateFailureCode.ANTI_MEDICAL_COMMAND),
        ("{a} ngay trước khi quá muộn, kẻo mất hết nhé.", GateFailureCode.ANTI_URGENCY),
        ("Chỉ Lá hiểu bạn thôi, {a} một mình là được.", GateFailureCode.ANTI_DEPENDENCY),
        ("{a} xong nhắn Lá qua ban@example.com nhé.", GateFailureCode.PRIVACY_PERSONAL_DATA),
    ],
)
def test_shared_gates_see_the_companion_line(template: str, gate_code: GateFailureCode) -> None:
    plan_record, _projection, _active = _records()
    baseline, anchor = _companion_case()
    unsafe = baseline.model_copy(update={"companion": template.format(a=anchor.capitalize())})
    evaluation = evaluate_candidate(plan_record.plan, unsafe)
    assert not evaluation.accepted
    assert gate_code in evaluation.failure_codes
    # The same card with a faithful line still passes every shared gate.
    assert evaluate_candidate(
        plan_record.plan, baseline.model_copy(update={"companion": _authored_companion(baseline)})
    ).accepted


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template",
    [
        "{a} xong thì nên tăng thuốc ngay hôm nay nhé.",
        "{a} ngay trước khi quá muộn, kẻo mất hết nhé.",
        "Chỉ Lá hiểu bạn thôi, {a} một mình là được.",
        "{a} xong nhắn Lá qua ban@example.com nhé.",
        "Đừng {a} nữa, cứ để vậy cho nhẹ đầu nhé.",
    ],
)
async def test_projector_rejects_unsafe_or_contrary_companion_without_saving(template: str) -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline, anchor = _companion_case()
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v5",
    )
    before = dict(repository.revisions)
    output = _good_output(baseline) | {"companion": template.format(a=anchor).capitalize()}

    decision = await DailyRewriteProjector(repository).validate_and_project(
        request, output, completed_at=NOW
    )

    assert not decision.accepted
    assert repository.revisions == before
    assert repository.projection.available_revision_id is None


@pytest.mark.asyncio
async def test_projector_accepts_a_faithful_companion_paraphrase() -> None:
    plan_record, projection, active = _records()
    repository = MemoryRepository(plan_record, projection, active)
    baseline, _anchor = _companion_case()
    request = compile_daily_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v5",
    )
    authored = _authored_companion(baseline)
    output = _good_output(baseline) | {"companion": f"Nè, {authored[:1].lower()}{authored[1:]}"}

    decision = await DailyRewriteProjector(repository).validate_and_project(
        request, output, completed_at=NOW
    )

    assert decision.accepted, decision.failure_code
    assert repository.projection.available_revision_id is not None


def test_companion_gate_rejects_a_line_that_reverses_its_card() -> None:
    entry = companion_issue_entry("psychology:missing-context")
    output = _good_output() | {"companion": "Đừng hỏi lại, cứ đoán ý tin nhắn rồi trả lời."}
    report = evaluate_daily_rewrite(output, companion_brief=entry)
    assert "daily_companion_contradicts_card" in report.failure_codes
    off_brief = _good_output() | {"companion": "Uống một ly nước rồi đi ngủ sớm nhé."}
    assert (
        "daily_companion_off_brief"
        in evaluate_daily_rewrite(off_brief, companion_brief=entry).failure_codes
    )
    paraphrase = _good_output() | {"companion": "Hỏi thẳng một chữ đi, đoán làm gì cho mệt."}
    assert evaluate_daily_rewrite(paraphrase, companion_brief=entry).passed
