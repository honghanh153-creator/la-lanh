from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    HouseSystem,
    TimePrecision,
    ZodiacSign,
)
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.content_rewrite.models import RewriteRequestEnvelope
from app.domains.content_rewrite.service import ContentRewriteService
from app.domains.readings.application import (
    ReadingActivationConflict,
    ReadingApplicationService,
    ReadingContentRejected,
)
from app.domains.readings.models import (
    AuraUnlockLayer,
    BackgroundLens,
    GenerationAttemptRecord,
    PlanMode,
    ProfileReadiness,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_lens_variant,
)
from app.domains.readings.renderers import DeterministicVietnameseRenderer

NOW = datetime(2026, 9, 7, 4, 30, tzinfo=UTC)


class MemoryReadingRepository:
    def __init__(self) -> None:
        self.plans: dict[tuple[UUID, UUID, str], ReadingPlanRecord] = {}
        self.revisions: dict[tuple[UUID, UUID, UUID], ReadingRevisionRecord] = {}
        self.revision_keys: dict[tuple[UUID, UUID, str], ReadingRevisionRecord] = {}
        self.projections: dict[tuple[UUID, UUID, str], ReadingProjectionRecord] = {}
        self.generation_attempts: list[GenerationAttemptRecord] = []

    async def save_or_replay_plan(
        self, record: ReadingPlanRecord
    ) -> tuple[ReadingPlanRecord, bool]:
        key = (record.guest_id, record.profile_id, record.plan_key)
        existing = self.plans.get(key)
        if existing is not None:
            return existing, True
        self.plans[key] = record
        return record, False

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]:
        key = (record.guest_id, record.profile_id, record.revision_key)
        existing = self.revision_keys.get(key)
        if existing is not None:
            return existing, True
        self.revision_keys[key] = record
        self.revisions[(record.guest_id, record.profile_id, record.id)] = record
        return record, False

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None:
        return self.revisions.get((guest_id, profile_id, revision_id))

    async def get_or_create_projection(
        self, record: ReadingProjectionRecord
    ) -> tuple[ReadingProjectionRecord, bool]:
        key = (record.guest_id, record.profile_id, record.scope_key)
        existing = self.projections.get(key)
        if existing is not None:
            return existing, True
        self.projections[key] = record
        return record, False

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None:
        return self.projections.get((guest_id, profile_id, scope_key))

    async def publish_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        revision_id: UUID,
    ) -> ReadingProjectionRecord:
        key = (guest_id, profile_id, scope_key)
        projection = self.projections[key]
        revision = self.revisions[(guest_id, profile_id, revision_id)]
        plan = next(record for record in self.plans.values() if record.id == revision.plan_id)
        assert projection.config_hash == plan.plan.config_hash
        if projection.active_revision_id is None:
            updated = projection.model_copy(
                update={"active_revision_id": revision_id, "available_revision_id": None}
            )
        elif projection.active_revision_id == revision_id:
            updated = projection
        else:
            updated = projection.model_copy(update={"available_revision_id": revision_id})
        self.projections[key] = updated
        return updated

    async def activate_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        updated_at: datetime,
        expected_chart_snapshot_id: UUID | None = None,
    ) -> ReadingProjectionRecord | None:
        key = (guest_id, profile_id, scope_key)
        projection = self.projections.get(key)
        if projection is None or projection.available_revision_id != expected_revision_id:
            return None
        revision = self.revisions[(guest_id, profile_id, expected_revision_id)]
        plan = next(record for record in self.plans.values() if record.id == revision.plan_id)
        if (
            expected_chart_snapshot_id is not None
            and plan.chart_snapshot_id != expected_chart_snapshot_id
        ):
            return None
        updated = projection.model_copy(
            update={
                "active_revision_id": expected_revision_id,
                "available_revision_id": None,
                "updated_at": updated_at,
            }
        )
        self.projections[key] = updated
        return updated

    async def acknowledge_aura_transition(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        transition_id: str,
        updated_at: datetime,
    ) -> ReadingProjectionRecord | None:
        key = (guest_id, profile_id, scope_key)
        projection = self.projections.get(key)
        if projection is None or projection.available_revision_id != expected_revision_id:
            return None
        updated = projection.model_copy(
            update={
                "acknowledged_aura_transition_id": transition_id,
                "updated_at": updated_at,
            }
        )
        self.projections[key] = updated
        return updated

    async def enqueue_generation_attempt(
        self, record: GenerationAttemptRecord
    ) -> tuple[GenerationAttemptRecord, bool]:
        self.generation_attempts.append(record)
        return record, False


class CapturingRewriteService:
    def __init__(self) -> None:
        self.requests: list[RewriteRequestEnvelope] = []

    async def enqueue(
        self,
        request: RewriteRequestEnvelope,
        *,
        now: datetime | None = None,
    ) -> tuple[object, bool]:
        del now
        self.requests.append(request)
        return object(), False


def _date_only_snapshot(guest_id: UUID, profile_id: UUID) -> BirthSnapshotRecord:
    return BirthSnapshotRecord(
        id=UUID("10000000-0000-4000-8000-000000000001"),
        guest_id=guest_id,
        profile_id=profile_id,
        input_hash=b"date-only",
        birth_date_ciphertext="encrypted",
        result=DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=EngineProvenance(
                version="2.10.03",
                profile="test",
                config_hash=CalculationConfig.western_recommended().fingerprint,
            ),
        ),
        created_at=NOW,
    )


def _exact_snapshot(
    guest_id: UUID, profile_id: UUID, engine: NatalChartEngine
) -> BirthSnapshotRecord:
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    return BirthSnapshotRecord(
        id=UUID("10000000-0000-4000-8000-000000000002"),
        guest_id=guest_id,
        profile_id=profile_id,
        input_hash=b"exact",
        birth_date_ciphertext="encrypted",
        result=chart,
        created_at=NOW,
    )


@pytest.mark.asyncio
async def test_date_only_daily_creates_stable_private_vibe_projection() -> None:
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(repository, NatalChartEngine())
    guest_id = UUID("20000000-0000-4000-8000-000000000001")
    profile_id = UUID("30000000-0000-4000-8000-000000000001")
    snapshot = _date_only_snapshot(guest_id, profile_id)

    first = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    second = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )

    assert first == second
    assert first.active.mode is PlanMode.VIBE_FALLBACK
    assert first.active.sections.transit is None
    assert first.active.evidence.title == "Căn cứ trong lá số"
    assert first.active.disclaimer == "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn."
    assert first.aura_transition.profile_readiness is ProfileReadiness.VIBE
    assert first.aura_transition.transition_id is None
    assert first.aura_transition.acknowledged is False
    assert first.aura_transition.unlock_layers == ()
    assert first.active.experiment is None
    assert first.available_update is None
    assert (
        first.active.model_dump()
        .keys()
        .isdisjoint(
            {"evaluation", "reports", "provider", "model", "prompt", "guest_id", "profile_id"}
        )
    )


@pytest.mark.asyncio
async def test_context_lens_has_a_distinct_replayable_projection_identity() -> None:
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(repository, NatalChartEngine())
    guest_id = UUID("20000000-0000-4000-8000-000000000021")
    profile_id = UUID("30000000-0000-4000-8000-000000000021")
    snapshot = _date_only_snapshot(guest_id, profile_id)

    automatic = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    relationships = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        background_lens=BackgroundLens.RELATIONSHIPS,
    )
    replay = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        background_lens=BackgroundLens.RELATIONSHIPS,
    )

    assert relationships == replay
    assert relationships.scope_key != automatic.scope_key
    auto_record = repository.projections[(guest_id, profile_id, automatic.scope_key)]
    lens_record = repository.projections[(guest_id, profile_id, relationships.scope_key)]
    assert auto_record.lens_variant is None
    assert lens_record.lens_variant == canonical_lens_variant(BackgroundLens.RELATIONSHIPS)
    assert lens_record.lens_variant != BackgroundLens.RELATIONSHIPS.value
    assert relationships.active.evidence == automatic.active.evidence
    assert relationships.active.mode == automatic.active.mode
    assert relationships.active.precision == automatic.active.precision
    assert relationships.active.sections.manifestation != (automatic.active.sections.manifestation)
    assert relationships.active.sections.micro_action != automatic.active.sections.micro_action


@pytest.mark.asyncio
async def test_daily_projection_rotates_after_local_date_boundary() -> None:
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(repository, NatalChartEngine())
    guest_id = UUID("20000000-0000-4000-8000-000000000011")
    profile_id = UUID("30000000-0000-4000-8000-000000000011")
    snapshot = _date_only_snapshot(guest_id, profile_id)

    first = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    next_day = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW.replace(day=8),
    )

    assert first.scope_key != next_day.scope_key
    assert first.active.revision_id != next_day.active.revision_id
    assert first.active.sections != next_day.active.sections


@pytest.mark.asyncio
async def test_daily_scope_uses_ho_chi_minh_midnight_not_utc_midnight() -> None:
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(repository, NatalChartEngine())
    guest_id = UUID("20000000-0000-4000-8000-000000000012")
    profile_id = UUID("30000000-0000-4000-8000-000000000012")
    snapshot = _date_only_snapshot(guest_id, profile_id)

    before = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=datetime(2026, 9, 7, 16, 59, 59, tzinfo=UTC),
    )
    after = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=datetime(2026, 9, 7, 17, 0, tzinfo=UTC),
    )

    assert before.scope_key != after.scope_key
    assert before.active.revision_id != after.active.revision_id
    assert before.active.sections.hook != after.active.sections.hook


@pytest.mark.asyncio
async def test_external_generation_requires_explicit_purpose_authorization() -> None:
    repository = MemoryReadingRepository()
    service = ReadingApplicationService(
        repository,
        NatalChartEngine(),
        generation_enabled=True,
        generation_provider="openai",
        generation_model="test-model",
        generation_prompt_version="test-prompt",
    )
    guest_id = UUID("20000000-0000-4000-8000-000000000013")
    profile_id = UUID("30000000-0000-4000-8000-000000000013")
    snapshot = _exact_snapshot(guest_id, profile_id, NatalChartEngine())

    await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
    )
    assert repository.generation_attempts == []

    await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
        external_generation_authorized=True,
    )
    assert len(repository.generation_attempts) == 1

    jyotish_chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        CalculationConfig.jyotish_recommended(),
    )
    await service.project(
        guest_id=guest_id,
        snapshot=replace(
            snapshot,
            id=UUID("10000000-0000-4000-8000-000000000013"),
            result=jyotish_chart,
        ),
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
        external_generation_authorized=True,
    )
    assert len(repository.generation_attempts) == 1


@pytest.mark.asyncio
async def test_authorized_daily_uses_generic_rewrite_queue_instead_of_legacy_queue() -> None:
    repository = MemoryReadingRepository()
    rewrite_service = CapturingRewriteService()
    service = ReadingApplicationService(
        repository,
        NatalChartEngine(),
        generation_enabled=True,
        generation_provider="openai",
        generation_model="gpt-6-luna",
        generation_prompt_version="chart-synthesis-v1",
        content_rewrite_service=cast(ContentRewriteService, rewrite_service),
    )
    guest_id = UUID("20000000-0000-4000-8000-000000000113")
    profile_id = UUID("30000000-0000-4000-8000-000000000113")

    projection = await service.project(
        guest_id=guest_id,
        snapshot=_date_only_snapshot(guest_id, profile_id),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        external_generation_authorized=True,
    )

    assert projection.active.source is ReadingRevisionSource.DETERMINISTIC
    assert repository.generation_attempts == []
    assert len(rewrite_service.requests) == 1
    assert rewrite_service.requests[0].key.surface.value == "daily_home"


@pytest.mark.asyncio
async def test_authorized_natal_uses_generic_rewrite_queue_instead_of_legacy_queue() -> None:
    repository = MemoryReadingRepository()
    rewrite_service = CapturingRewriteService()
    engine = NatalChartEngine()
    service = ReadingApplicationService(
        repository,
        engine,
        generation_enabled=True,
        generation_provider="openai",
        generation_model="gpt-6-luna",
        generation_prompt_version="chart-synthesis-v1",
        content_rewrite_service=cast(ContentRewriteService, rewrite_service),
    )
    guest_id = UUID("20000000-0000-4000-8000-000000000213")
    profile_id = UUID("30000000-0000-4000-8000-000000000213")

    projection = await service.project(
        guest_id=guest_id,
        snapshot=_exact_snapshot(guest_id, profile_id, engine),
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
        external_generation_authorized=True,
    )

    assert projection.active.source is ReadingRevisionSource.DETERMINISTIC
    assert repository.generation_attempts == []
    assert len(rewrite_service.requests) == 1
    assert rewrite_service.requests[0].key.surface.value == "natal"


@pytest.mark.asyncio
async def test_rejected_renderer_cannot_publish_a_revision_or_projection() -> None:
    class RejectingRenderer(DeterministicVietnameseRenderer):
        def render(self, plan):  # type: ignore[no-untyped-def]
            return (
                super()
                .render(plan)
                .model_copy(
                    update={"manifestation": "Chuyển toàn bộ tiền tiết kiệm sang Bitcoin hôm nay."}
                )
            )

    repository = MemoryReadingRepository()
    service = ReadingApplicationService(
        repository,
        NatalChartEngine(),
        renderer=RejectingRenderer(),
    )
    guest_id = UUID("20000000-0000-4000-8000-000000000014")
    profile_id = UUID("30000000-0000-4000-8000-000000000014")

    with pytest.raises(ReadingContentRejected):
        await service.project(
            guest_id=guest_id,
            snapshot=_date_only_snapshot(guest_id, profile_id),
            purpose=ReadingPurpose.DAILY_NOTE,
            requested_at=NOW,
        )

    assert repository.revisions == {}
    assert repository.projections == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "retired",
    [
        "Một việc chưa hoàn hảo có thể nằm yên lâu hơn một việc còn thiếu.",
        "Hai nhu cầu này dễ cùng bật lên và giành phần ưu tiên.",
        "Ý kiến đông người dễ nghe giống ý kiến đúng.",
    ],
)
async def test_retired_copy_is_repaired_without_asking_the_user_to_activate_it(
    retired: str,
) -> None:
    class LegacyRenderer(DeterministicVietnameseRenderer):
        version = "deterministic-vi-legacy"

        def render(self, plan):  # type: ignore[no-untyped-def]
            candidate = super().render(plan)
            assert candidate.semantic_blueprint is not None
            return candidate.model_copy(
                update={
                    "hook": retired,
                    "renderer_version": self.version,
                    "semantic_blueprint": candidate.semantic_blueprint.model_copy(
                        update={"hook": retired, "daily_meaning": None}
                    ),
                }
            )

    repository = MemoryReadingRepository()
    guest_id = UUID("20000000-0000-4000-8000-000000000114")
    profile_id = UUID("30000000-0000-4000-8000-000000000114")
    snapshot = _date_only_snapshot(guest_id, profile_id)
    legacy = ReadingApplicationService(
        repository,
        NatalChartEngine(),
        renderer=LegacyRenderer(),
    )

    first = await legacy.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    repaired = await ReadingApplicationService(repository, NatalChartEngine()).project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )

    assert first.active.sections.hook == retired
    assert repaired.active.revision_id != first.active.revision_id
    assert repaired.active.sections.hook != retired
    assert first.active.sections.hook == retired  # Historical snapshot remains unchanged.
    assert repaired.available_update is None


@pytest.mark.asyncio
async def test_daily_without_a_meaning_brief_repairs_only_the_active_projection() -> None:
    class LegacyRenderer(DeterministicVietnameseRenderer):
        version = "deterministic-vi-v9"

        def render(self, plan):  # type: ignore[no-untyped-def]
            candidate = super().render(plan)
            assert candidate.semantic_blueprint is not None
            return candidate.model_copy(
                update={
                    "renderer_version": self.version,
                    "semantic_blueprint": candidate.semantic_blueprint.model_copy(
                        update={"daily_meaning": None}
                    ),
                }
            )

    repository = MemoryReadingRepository()
    guest_id = UUID("20000000-0000-4000-8000-000000000115")
    profile_id = UUID("30000000-0000-4000-8000-000000000115")
    snapshot = _date_only_snapshot(guest_id, profile_id)
    first = await ReadingApplicationService(
        repository, NatalChartEngine(), renderer=LegacyRenderer()
    ).project(
        guest_id=guest_id, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE, requested_at=NOW
    )
    service = ReadingApplicationService(repository, NatalChartEngine())
    repaired = await service.project(
        guest_id=guest_id, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE, requested_at=NOW
    )
    replay = await service.project(
        guest_id=guest_id, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE, requested_at=NOW
    )
    assert repaired.active.revision_id != first.active.revision_id
    assert replay.active.revision_id == repaired.active.revision_id
    assert repaired.available_update is None
    historical = await repository.get_revision(guest_id, profile_id, first.active.revision_id)
    assert historical is not None
    old_candidate = historical.evaluation.publishable_candidate
    assert old_candidate is not None and old_candidate.semantic_blueprint is not None
    assert old_candidate.semantic_blueprint.daily_meaning is None


@pytest.mark.asyncio
async def test_exact_supplement_waits_as_full_gift_until_explicit_activation() -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    guest_id = UUID("20000000-0000-4000-8000-000000000002")
    profile_id = UUID("30000000-0000-4000-8000-000000000002")

    vibe = await service.project(
        guest_id=guest_id,
        snapshot=_date_only_snapshot(guest_id, profile_id),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    upgraded = await service.project(
        guest_id=guest_id,
        snapshot=_exact_snapshot(guest_id, profile_id, engine),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )

    assert upgraded.active.revision_id == vibe.active.revision_id
    assert upgraded.active.mode is PlanMode.VIBE_FALLBACK
    assert upgraded.available_update is not None
    assert upgraded.available_update.message == "Có một bản đọc mới đang chờ bạn"
    assert upgraded.available_update.content.mode is PlanMode.FULL_SYNTHESIS
    assert upgraded.aura_transition.profile_readiness is ProfileReadiness.AURA_READY
    assert upgraded.aura_transition.transition_id is not None
    assert len(upgraded.aura_transition.transition_id) == 64
    assert upgraded.aura_transition.acknowledged is False
    assert upgraded.aura_transition.unlock_layers == (
        AuraUnlockLayer.MULTI_FACTOR,
        AuraUnlockLayer.HOUSE_ARENA,
        AuraUnlockLayer.CURRENT_SKY,
    )
    assert upgraded.active.experiment is None
    assert upgraded.available_update.content.experiment is not None
    experiment = upgraded.available_update.content.experiment
    assert experiment.action == upgraded.available_update.content.sections.micro_action
    assert len(experiment.action_key) == 64
    assert experiment.observation
    assert experiment.permission
    full_revision = repository.revisions[
        (guest_id, profile_id, upgraded.available_update.revision_id)
    ]
    full_candidate = full_revision.evaluation.publishable_candidate
    assert full_candidate is not None and full_candidate.semantic_blueprint is not None
    assert full_candidate.semantic_blueprint.daily_meaning is not None
    assert experiment.observation == (
        full_candidate.semantic_blueprint.daily_meaning.observation_question
    )
    assert "một khác biệt nhỏ" not in experiment.observation
    assert experiment.permission == "Không hợp với tình huống của bạn thì bỏ qua."

    assert upgraded.aura_transition.transition_id is not None
    with pytest.raises(ReadingActivationConflict):
        await service.acknowledge_aura_transition(
            guest_id=guest_id,
            profile_id=profile_id,
            scope_key=upgraded.scope_key,
            transition_id="f" * 64,
            updated_at=NOW,
        )

    acknowledged = await service.acknowledge_aura_transition(
        guest_id=guest_id,
        profile_id=profile_id,
        scope_key=upgraded.scope_key,
        transition_id=upgraded.aura_transition.transition_id,
        updated_at=NOW,
    )
    assert acknowledged.available_update is not None
    assert acknowledged.aura_transition.acknowledged is True

    refreshed = await service.project(
        guest_id=guest_id,
        snapshot=_exact_snapshot(guest_id, profile_id, engine),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    assert refreshed.aura_transition.transition_id == upgraded.aura_transition.transition_id
    assert refreshed.aura_transition.acknowledged is True

    with pytest.raises(ReadingActivationConflict):
        await service.activate(
            guest_id=guest_id,
            profile_id=profile_id,
            scope_key=upgraded.scope_key,
            expected_revision_id=upgraded.available_update.revision_id,
            expected_chart_snapshot_id=UUID("10000000-0000-4000-8000-000000000099"),
            updated_at=NOW,
        )

    activated = await service.activate(
        guest_id=guest_id,
        profile_id=profile_id,
        scope_key=upgraded.scope_key,
        expected_revision_id=upgraded.available_update.revision_id,
        expected_chart_snapshot_id=UUID("10000000-0000-4000-8000-000000000002"),
        updated_at=NOW,
    )
    assert activated.active.mode is PlanMode.FULL_SYNTHESIS
    assert activated.available_update is None
    assert activated.aura_transition.profile_readiness is ProfileReadiness.AURA_READY
    assert activated.aura_transition.transition_id == upgraded.aura_transition.transition_id
    assert activated.aura_transition.acknowledged is True
    assert activated.active.experiment == experiment

    with pytest.raises(ReadingActivationConflict):
        await service.activate(
            guest_id=guest_id,
            profile_id=profile_id,
            scope_key=upgraded.scope_key,
            expected_revision_id=vibe.active.revision_id,
            updated_at=NOW,
        )


@pytest.mark.asyncio
async def test_exact_reading_detail_is_full_on_first_use_and_snapshot_scoped() -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    guest_id = UUID("20000000-0000-4000-8000-000000000003")
    profile_id = UUID("30000000-0000-4000-8000-000000000003")
    snapshot = _exact_snapshot(guest_id, profile_id, engine)

    projection = await service.project(
        guest_id=guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW.replace(day=8),
    )

    assert projection.active.mode is PlanMode.FULL_SYNTHESIS
    assert projection.active.purpose is ReadingPurpose.READING_DETAIL
    assert projection.active.sections.transit is None
    assert projection.active.created_at.tzinfo is not None
    assert projection.available_update is None


@pytest.mark.asyncio
async def test_projection_scope_separates_chart_calculation_configs() -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    guest_id = UUID("20000000-0000-4000-8000-000000000006")
    profile_id = UUID("30000000-0000-4000-8000-000000000006")
    chart_input = ChartInput(
        utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
        latitude=10.8231,
        longitude=106.6297,
    )
    placidus_chart = engine.calculate_chart(chart_input, CalculationConfig.western_recommended())
    whole_sign_chart = engine.calculate_chart(
        chart_input, CalculationConfig(house_system=HouseSystem.WHOLE_SIGN)
    )
    placidus_snapshot = replace(
        _exact_snapshot(guest_id, profile_id, engine), result=placidus_chart
    )
    whole_sign_snapshot = replace(
        placidus_snapshot,
        id=UUID("10000000-0000-4000-8000-000000000006"),
        result=whole_sign_chart,
    )

    placidus = await service.project(
        guest_id=guest_id,
        snapshot=placidus_snapshot,
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
    )
    whole_sign = await service.project(
        guest_id=guest_id,
        snapshot=whole_sign_snapshot,
        purpose=ReadingPurpose.READING_DETAIL,
        requested_at=NOW,
    )

    assert placidus.scope_key != whole_sign.scope_key
    for result, expected_config_hash in (
        (placidus, placidus_chart.config_hash),
        (whole_sign, whole_sign_chart.config_hash),
    ):
        stored_projection = repository.projections[(guest_id, profile_id, result.scope_key)]
        assert stored_projection.config_hash == expected_config_hash
        active_revision = repository.revisions[(guest_id, profile_id, result.active.revision_id)]
        active_plan = next(
            record for record in repository.plans.values() if record.id == active_revision.plan_id
        )
        assert active_plan.plan.config_hash == expected_config_hash


@pytest.mark.asyncio
async def test_approximate_chart_is_limited_without_houses_or_empty_transit() -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    guest_id = UUID("20000000-0000-4000-8000-000000000004")
    profile_id = UUID("30000000-0000-4000-8000-000000000004")
    exact = _exact_snapshot(guest_id, profile_id, engine)
    approximate = BirthSnapshotRecord(
        id=exact.id,
        guest_id=exact.guest_id,
        profile_id=exact.profile_id,
        input_hash=exact.input_hash,
        birth_date_ciphertext=exact.birth_date_ciphertext,
        result=exact.result.model_copy(
            update={
                "time_precision": TimePrecision.APPROXIMATE,
                "houses": None,
                "angles": None,
            }
        ),
        created_at=exact.created_at,
    )

    projection = await service.project(
        guest_id=guest_id,
        snapshot=approximate,
        purpose=ReadingPurpose.PERSONALIZED_SKY,
        requested_at=NOW,
    )

    assert projection.active.mode is PlanMode.LIMITED
    assert projection.active.precision is TimePrecision.APPROXIMATE
    assert projection.aura_transition.profile_readiness is ProfileReadiness.LIMITED
    assert projection.aura_transition.transition_id is None
    assert projection.aura_transition.unlock_layers == ()
    assert projection.active.experiment is None
    assert projection.active.sections.transit is None
    serialized = projection.active.model_dump_json().lower()
    assert "nhà " not in serialized
    assert "ascendant" not in serialized


@pytest.mark.asyncio
async def test_transit_engine_failure_keeps_deterministic_natal_content() -> None:
    class BrokenTransitEngine(NatalChartEngine):
        def calculate_transit_to_natal(self, natal, observed_at):  # type: ignore[no-untyped-def]
            raise RuntimeError("ephemeris unavailable")

    repository = MemoryReadingRepository()
    source_engine = NatalChartEngine()
    service = ReadingApplicationService(repository, BrokenTransitEngine())
    guest_id = UUID("20000000-0000-4000-8000-000000000005")
    profile_id = UUID("30000000-0000-4000-8000-000000000005")

    projection = await service.project(
        guest_id=guest_id,
        snapshot=_exact_snapshot(guest_id, profile_id, source_engine),
        purpose=ReadingPurpose.PERSONALIZED_SKY,
        requested_at=NOW,
    )

    assert projection.active.mode is PlanMode.FULL_SYNTHESIS
    assert projection.active.sections.transit is None
    assert projection.aura_transition.unlock_layers == (
        AuraUnlockLayer.MULTI_FACTOR,
        AuraUnlockLayer.HOUSE_ARENA,
    )
