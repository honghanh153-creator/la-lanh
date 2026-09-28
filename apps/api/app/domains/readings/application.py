from __future__ import annotations

import logging
import re
from asyncio import to_thread
from datetime import UTC, date, datetime, time
from hashlib import sha256
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    DateOnlySunResult,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitToNatalSnapshot,
)
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    AuraTransitionProjection,
    AuraUnlockLayer,
    AvailableReadingUpdate,
    BackgroundLens,
    ClaimTemplateId,
    EvidenceClaim,
    EvidenceDisclosure,
    FactorSource,
    GenerationAttemptRecord,
    PlanMode,
    ProfileReadiness,
    ReadingContentProjection,
    ReadingEvidenceProjection,
    ReadingPlanRecord,
    ReadingProjection,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    ReadingSectionsProjection,
    canonical_gate_policy_version,
    canonical_generation_key,
    canonical_lens_variant,
    canonical_projection_scope_key,
    canonical_reading_plan_key,
    canonical_reading_revision_key,
    experiment_projection_for,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.repository import ReadingProjectionRepository

logger = logging.getLogger(__name__)

MVP_TIMEZONE = "Asia/Ho_Chi_Minh"
DAILY_OBSERVED_HOUR_UTC = 12
DETERMINISTIC_CONTENT_VERSION = "deterministic-reading-v3"
_TRANSIT_PURPOSES = {
    ReadingPurpose.DAILY_NOTE,
    ReadingPurpose.PERSONALIZED_SKY,
}


class ReadingApplicationError(RuntimeError):
    """Safe application-boundary failure with no candidate content attached."""


class ReadingContentRejected(ReadingApplicationError):
    """A candidate failed one or more publication gates and was not stored."""


class ReadingActivationConflict(ReadingApplicationError):
    """The requested update is stale, absent, or outside the owner's projection."""


class ReadingApplicationService:
    def __init__(
        self,
        repository: ReadingProjectionRepository,
        engine: NatalChartEngine | None = None,
        *,
        planner: ReadingPlanner | None = None,
        renderer: DeterministicVietnameseRenderer | None = None,
        generation_enabled: bool = False,
        generation_provider: str = "disabled",
        generation_model: str = "disabled",
        generation_prompt_version: str = "disabled",
        generation_max_attempts: int = 2,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._planner = planner or ReadingPlanner()
        self._renderer = renderer or DeterministicVietnameseRenderer()
        self._generation_enabled = generation_enabled
        self._generation_provider = generation_provider
        self._generation_model = generation_model
        self._generation_prompt_version = generation_prompt_version
        self._generation_max_attempts = generation_max_attempts

    async def project(
        self,
        *,
        guest_id: UUID,
        snapshot: BirthSnapshotRecord,
        purpose: ReadingPurpose,
        chart: DateOnlySunResult | NatalChart | None = None,
        requested_at: datetime | None = None,
        external_generation_authorized: bool = False,
        background_lens: BackgroundLens | None = None,
    ) -> ReadingProjection:
        if snapshot.guest_id != guest_id:
            raise ReadingActivationConflict
        source_chart = chart or snapshot.result
        current = _aware_utc(requested_at or datetime.now(UTC))
        local_date, observed_at = _scope_time(purpose, snapshot.created_at, current)
        transits = await self._optional_transits(source_chart, purpose, observed_at)
        editorial_seed = local_date.isoformat() if purpose is ReadingPurpose.DAILY_NOTE else None
        plan = self._planner.plan(
            source_chart,
            purpose=purpose,
            transits=transits,
            editorial_seed=editorial_seed,
            background_lens=background_lens,
        )
        lens_variant = canonical_lens_variant(plan.background_lens)
        plan_record, _ = await self._repository.save_or_replay_plan(
            ReadingPlanRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=snapshot.profile_id,
                chart_snapshot_id=snapshot.id,
                plan_key=canonical_reading_plan_key(plan),
                plan=plan,
                created_at=current,
            )
        )

        candidate = self._renderer.render(plan_record.plan)
        evaluation = evaluate_candidate(plan_record.plan, candidate)
        if not evaluation.accepted and candidate.transit is not None:
            transit_ids = {
                factor.id
                for factor in plan_record.plan.factors
                if factor.source is FactorSource.TRANSIT
            }
            candidate = candidate.model_copy(
                update={
                    "transit": None,
                    "evidence": EvidenceDisclosure(
                        claims=tuple(
                            claim
                            for claim in candidate.evidence.claims
                            if claim.factor_ref not in transit_ids
                        ),
                    ),
                }
            )
            evaluation = evaluate_candidate(plan_record.plan, candidate)
        if not evaluation.accepted or evaluation.publishable_candidate is None:
            gate_failures = {
                report.gate.value: [code.value for code in report.failure_codes]
                for report in evaluation.reports
                if report.failure_codes
            }
            section_word_counts = [
                len(re.findall(r"\b\w+\b", section)) for section in candidate.all_user_prose
            ]
            logger.warning(
                "Reading candidate rejected before persistence: purpose=%s mode=%s "
                "failures=%s section_word_counts=%s",
                purpose.value,
                plan.mode.value,
                gate_failures,
                section_word_counts,
            )
            raise ReadingContentRejected

        source = ReadingRevisionSource.DETERMINISTIC
        gate_policy_version = canonical_gate_policy_version(evaluation)
        revision, _ = await self._repository.save_or_replay_revision(
            ReadingRevisionRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=snapshot.profile_id,
                plan_id=plan_record.id,
                revision_key=canonical_reading_revision_key(
                    plan_key=plan_record.plan_key,
                    source=source,
                    renderer_version=candidate.renderer_version,
                    content_version=DETERMINISTIC_CONTENT_VERSION,
                    schema_version=candidate.schema_version,
                    rules_version=plan_record.plan.rules_version,
                    gate_policy_version=gate_policy_version,
                ),
                source=source,
                renderer_version=candidate.renderer_version,
                content_version=DETERMINISTIC_CONTENT_VERSION,
                schema_version=candidate.schema_version,
                rules_version=plan_record.plan.rules_version,
                gate_policy_version=gate_policy_version,
                evaluation=evaluation,
                created_at=current,
            )
        )

        scope_key = canonical_projection_scope_key(
            purpose=purpose,
            tradition=plan.tradition,
            config_hash=plan.config_hash,
            local_date=local_date,
            timezone_name=MVP_TIMEZONE,
            observed_at=observed_at,
            lens_variant=lens_variant,
        )
        projection, _ = await self._repository.get_or_create_projection(
            ReadingProjectionRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=snapshot.profile_id,
                scope_key=scope_key,
                purpose=purpose,
                tradition=plan.tradition,
                config_hash=plan.config_hash,
                lens_variant=lens_variant,
                local_date=local_date,
                timezone_name=MVP_TIMEZONE,
                observed_at=observed_at,
                created_at=current,
                updated_at=current,
            )
        )
        projection = await self._repository.publish_available(
            guest_id,
            snapshot.profile_id,
            projection.scope_key,
            revision.id,
        )
        await self._optional_enqueue(
            plan_record,
            projection,
            current,
            external_generation_authorized=external_generation_authorized,
        )
        return await self._hydrate(guest_id, snapshot.profile_id, projection)

    async def _optional_enqueue(
        self,
        plan_record: ReadingPlanRecord,
        projection: ReadingProjectionRecord,
        created_at: datetime,
        *,
        external_generation_authorized: bool,
    ) -> None:
        if (
            not self._generation_enabled
            or not external_generation_authorized
            or plan_record.plan.tradition is not Tradition.WESTERN
        ):
            return
        generation_key = canonical_generation_key(
            plan_key=plan_record.plan_key,
            scope_key=projection.scope_key,
            provider=self._generation_provider,
            model=self._generation_model,
            prompt_version=self._generation_prompt_version,
        )
        try:
            await self._repository.enqueue_generation_attempt(
                GenerationAttemptRecord(
                    id=uuid4(),
                    guest_id=plan_record.guest_id,
                    profile_id=plan_record.profile_id,
                    plan_id=plan_record.id,
                    scope_key=projection.scope_key,
                    generation_key=generation_key,
                    provider=self._generation_provider,
                    model=self._generation_model,
                    prompt_version=self._generation_prompt_version,
                    deletion_epoch=uuid4(),
                    max_attempts=self._generation_max_attempts,
                    next_attempt_at=created_at,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
        except Exception:
            logger.warning(
                "Optional reading generation enqueue failed; deterministic content remains active",
                extra={"purpose": plan_record.plan.purpose.value},
            )

    async def activate(
        self,
        *,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        expected_revision_id: UUID,
        expected_chart_snapshot_id: UUID | None = None,
        updated_at: datetime | None = None,
    ) -> ReadingProjection:
        projection = await self._repository.activate_available(
            guest_id,
            profile_id,
            scope_key,
            expected_revision_id=expected_revision_id,
            expected_chart_snapshot_id=expected_chart_snapshot_id,
            updated_at=_aware_utc(updated_at or datetime.now(UTC)),
        )
        if projection is None:
            raise ReadingActivationConflict
        return await self._hydrate(guest_id, profile_id, projection)

    async def acknowledge_aura_transition(
        self,
        *,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        transition_id: str,
        updated_at: datetime | None = None,
    ) -> ReadingProjection:
        projection = await self._repository.get_projection(guest_id, profile_id, scope_key)
        if projection is None or projection.available_revision_id is None:
            raise ReadingActivationConflict
        available = await self._repository.get_revision(
            guest_id,
            profile_id,
            projection.available_revision_id,
        )
        if available is None:
            raise ReadingApplicationError("available reading revision is unavailable")
        candidate = available.evaluation.publishable_candidate
        if candidate is None:  # ReadingRevisionRecord already protects this invariant.
            raise ReadingApplicationError("accepted Aura evidence is unavailable")
        mode, _ = _public_mode_and_precision(candidate.evidence.claims)
        current_transition_id = _aura_transition_id(scope_key, available.id)
        if mode is not PlanMode.FULL_SYNTHESIS or transition_id != current_transition_id:
            raise ReadingActivationConflict
        acknowledged = await self._repository.acknowledge_aura_transition(
            guest_id,
            profile_id,
            scope_key,
            expected_revision_id=available.id,
            transition_id=current_transition_id,
            updated_at=_aware_utc(updated_at or datetime.now(UTC)),
        )
        if acknowledged is None:
            raise ReadingActivationConflict
        return await self._hydrate(guest_id, profile_id, acknowledged)

    async def _optional_transits(
        self,
        chart: DateOnlySunResult | NatalChart,
        purpose: ReadingPurpose,
        observed_at: datetime,
    ) -> TransitToNatalSnapshot | None:
        if (
            self._engine is None
            or not isinstance(chart, NatalChart)
            or chart.time_precision is not TimePrecision.EXACT
            or chart.config.tradition is Tradition.JYOTISH
            or purpose not in _TRANSIT_PURPOSES
        ):
            return None
        try:
            return await to_thread(self._engine.calculate_transit_to_natal, chart, observed_at)
        except Exception:
            logger.exception(
                "Optional transit calculation failed; continuing with natal reading",
                extra={"purpose": purpose.value},
            )
            return None

    async def _hydrate(
        self,
        guest_id: UUID,
        profile_id: UUID,
        projection: ReadingProjectionRecord,
    ) -> ReadingProjection:
        if projection.active_revision_id is None:
            raise ReadingApplicationError("reading projection has no active revision")
        active_record = await self._repository.get_revision(
            guest_id, profile_id, projection.active_revision_id
        )
        if active_record is None:
            raise ReadingApplicationError("active reading revision is unavailable")
        active = _content_projection(active_record, projection)

        available_update = None
        available_record = None
        if projection.available_revision_id is not None:
            available_record = await self._repository.get_revision(
                guest_id, profile_id, projection.available_revision_id
            )
            if available_record is None:
                raise ReadingApplicationError("available reading revision is unavailable")
            available = _content_projection(available_record, projection)
            available_update = AvailableReadingUpdate(
                revision_id=available.revision_id,
                content=available,
            )
        aura_record = available_record or active_record
        aura_candidate = aura_record.evaluation.publishable_candidate
        if aura_candidate is None:  # ReadingRevisionRecord already protects this invariant.
            raise ReadingApplicationError("accepted Aura evidence is unavailable")
        aura_mode, _ = _public_mode_and_precision(aura_candidate.evidence.claims)
        if aura_mode is PlanMode.FULL_SYNTHESIS:
            transition_id = _aura_transition_id(projection.scope_key, aura_record.id)
            unlock_layers = _aura_unlock_layers(aura_candidate.evidence.claims)
            profile_readiness = ProfileReadiness.AURA_READY
        elif aura_mode is PlanMode.LIMITED:
            transition_id = None
            unlock_layers = ()
            profile_readiness = ProfileReadiness.LIMITED
        else:
            transition_id = None
            unlock_layers = ()
            profile_readiness = ProfileReadiness.VIBE
        return ReadingProjection(
            scope_key=projection.scope_key,
            active=active,
            available_update=available_update,
            aura_transition=AuraTransitionProjection(
                profile_readiness=profile_readiness,
                transition_id=transition_id,
                acknowledged=(
                    profile_readiness is ProfileReadiness.AURA_READY
                    and (
                        (available_record is None and active.mode is PlanMode.FULL_SYNTHESIS)
                        or projection.acknowledged_aura_transition_id == transition_id
                    )
                ),
                unlock_layers=unlock_layers,
            ),
        )


def _content_projection(
    revision: ReadingRevisionRecord,
    projection: ReadingProjectionRecord,
) -> ReadingContentProjection:
    candidate = revision.evaluation.publishable_candidate
    if candidate is None:  # The revision model protects this invariant too.
        raise ReadingApplicationError("accepted reading content is unavailable")
    mode, precision = _public_mode_and_precision(candidate.evidence.claims)
    experiment = None
    if mode is PlanMode.FULL_SYNTHESIS and precision is TimePrecision.EXACT:
        experiment = experiment_projection_for(revision.id, candidate.micro_action)
    return ReadingContentProjection(
        revision_id=revision.id,
        source=revision.source,
        mode=mode,
        purpose=projection.purpose,
        tradition=projection.tradition,
        precision=precision,
        sections=ReadingSectionsProjection(
            hook=candidate.hook,
            thesis=candidate.thesis,
            manifestation=candidate.manifestation,
            transit=candidate.transit,
            micro_action=candidate.micro_action,
        ),
        evidence=ReadingEvidenceProjection(
            title=candidate.evidence.title,
            claims=tuple(claim.display_text for claim in candidate.evidence.claims),
            framework_disclosure=candidate.evidence.framework_disclosure,
        ),
        disclaimer=candidate.disclaimer,
        created_at=revision.created_at,
        experiment=experiment,
    )


def _aura_transition_id(scope_key: str, revision_id: UUID) -> str:
    return sha256(f"aura-transition-v1\x1f{scope_key}\x1f{revision_id}".encode()).hexdigest()


def _aura_unlock_layers(claims: tuple[EvidenceClaim, ...]) -> tuple[AuraUnlockLayer, ...]:
    template_ids = {claim.template_id for claim in claims}
    layers = [AuraUnlockLayer.MULTI_FACTOR]
    if ClaimTemplateId.PLANET_IN_HOUSE in template_ids:
        layers.append(AuraUnlockLayer.HOUSE_ARENA)
    if ClaimTemplateId.ANGLE_LONGITUDE in template_ids:
        layers.append(AuraUnlockLayer.RISING_ANGLES)
    if ClaimTemplateId.TRANSIT_CONTACT in template_ids:
        layers.append(AuraUnlockLayer.CURRENT_SKY)
    return tuple(layers)


def _public_mode_and_precision(
    claims: tuple[EvidenceClaim, ...],
) -> tuple[PlanMode, TimePrecision]:
    """Map the closed evidence contract to public metadata without exposing the plan."""

    if any(claim.template_id is ClaimTemplateId.DATE_ONLY_VIBE for claim in claims):
        return PlanMode.VIBE_FALLBACK, TimePrecision.UNKNOWN
    if not claims:
        return PlanMode.LIMITED, TimePrecision.APPROXIMATE
    return PlanMode.FULL_SYNTHESIS, TimePrecision.EXACT


def _scope_time(
    purpose: ReadingPurpose,
    snapshot_created_at: datetime,
    requested_at: datetime,
) -> tuple[date, datetime]:
    timezone = ZoneInfo(MVP_TIMEZONE)
    if purpose in _TRANSIT_PURPOSES:
        local_date = requested_at.astimezone(timezone).date()
        return local_date, datetime.combine(
            local_date,
            time(hour=DAILY_OBSERVED_HOUR_UTC),
            tzinfo=UTC,
        )
    observed_at = _aware_utc(snapshot_created_at)
    return observed_at.astimezone(timezone).date(), observed_at


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("reading timestamps must be timezone-aware")
    return value.astimezone(UTC)
