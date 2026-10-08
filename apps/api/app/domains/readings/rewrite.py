from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from typing import Protocol, cast
from uuid import UUID, uuid4

from pydantic import JsonValue

from app.domains.content_rewrite.authorization import content_rewrite_receipt_id
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.content_rewrite.service import RewriteProjectionDecision, RewriteProjector
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    ClaimSlotName,
    ReadingCandidate,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    SemanticArena,
    canonical_gate_policy_version,
    canonical_reading_revision_key,
)
from app.domains.readings.renderers import DeterministicVietnameseRenderer, canonical_evidence_claim

DAILY_REWRITE_RENDERER_VERSION = "gpt-6-luna-daily-v1"
READING_REWRITE_RENDERER_VERSION = "gpt-6-luna-reading-v1"

_READING_SURFACE_BY_PURPOSE = {
    ReadingPurpose.AURA: RewriteSurface.REVEAL,
    ReadingPurpose.READING_DETAIL: RewriteSurface.NATAL,
    ReadingPurpose.PERSONALIZED_SKY: RewriteSurface.TRANSIT_INSIGHT,
}


class DailyRewriteRepository(Protocol):
    async def get_plan(
        self, guest_id: UUID, profile_id: UUID, plan_id: UUID
    ) -> ReadingPlanRecord | None: ...

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None: ...

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None: ...

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]: ...

    async def publish_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        revision_id: UUID,
    ) -> ReadingProjectionRecord: ...


def _owner_key(guest_id: UUID, profile_id: UUID, plan_id: UUID, scope_key: str) -> ArtifactOwnerKey:
    return ArtifactOwnerKey(
        namespace="readings",
        key=f"daily|{guest_id}|{profile_id}|{plan_id}|{scope_key}",
    )


def _parse_owner(owner: ArtifactOwnerKey) -> tuple[UUID, UUID, UUID, str]:
    parts = owner.key.split("|")
    if owner.namespace != "readings" or len(parts) != 5 or parts[0] != "daily":
        raise ValueError("invalid Daily rewrite owner")
    guest_id, profile_id, plan_id = (UUID(value) for value in parts[1:4])
    scope_key = parts[4]
    if len(scope_key) != 64:
        raise ValueError("invalid Daily rewrite scope")
    return guest_id, profile_id, plan_id, scope_key


def _reading_owner_key(
    surface: RewriteSurface,
    guest_id: UUID,
    profile_id: UUID,
    plan_id: UUID,
    scope_key: str,
) -> ArtifactOwnerKey:
    return ArtifactOwnerKey(
        namespace="readings",
        key=f"reading|{surface.value}|{guest_id}|{profile_id}|{plan_id}|{scope_key}",
    )


def _parse_reading_owner(
    owner: ArtifactOwnerKey,
) -> tuple[RewriteSurface, UUID, UUID, UUID, str]:
    parts = owner.key.split("|")
    if owner.namespace != "readings" or len(parts) != 6 or parts[0] != "reading":
        raise ValueError("invalid Reading rewrite owner")
    surface = RewriteSurface(parts[1])
    if surface not in set(_READING_SURFACE_BY_PURPOSE.values()):
        raise ValueError("unsupported Reading rewrite surface")
    guest_id, profile_id, plan_id = (UUID(value) for value in parts[2:5])
    scope_key = parts[5]
    if len(scope_key) != 64:
        raise ValueError("invalid Reading rewrite scope")
    return surface, guest_id, profile_id, plan_id, scope_key


def compile_daily_rewrite_request(
    plan_record: ReadingPlanRecord,
    projection: ReadingProjectionRecord,
    baseline: ReadingCandidate,
    *,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope:
    blueprint = baseline.semantic_blueprint
    if blueprint is None or plan_record.plan.purpose is not ReadingPurpose.DAILY_NOTE:
        raise ValueError("Daily rewrite requires a deterministic Daily semantic blueprint")
    context = {
        SemanticArena.RELATIONSHIPS: "relationships",
        SemanticArena.COMMUNICATION: "communication",
        SemanticArena.WORK: "work",
        SemanticArena.ENERGY: "energy",
        SemanticArena.SELF_CARE: "energy",
    }.get(blueprint.arena, "general")
    factors = {factor.id: factor for factor in plan_record.plan.factors}
    evidence: list[dict[str, JsonValue]] = []
    for index, factor_ref in enumerate(blueprint.evidence_factor_refs, start=1):
        factor = factors.get(factor_ref)
        if factor is None:
            continue
        claim = canonical_evidence_claim(factor)
        labels: list[dict[str, JsonValue]] = []
        for slot in claim.slots:
            safe_name = {
                ClaimSlotName.BODY: "body",
                ClaimSlotName.BODY_A: "body",
                ClaimSlotName.BODY_B: "other_body",
                ClaimSlotName.SIGN: "sign",
                ClaimSlotName.HOUSE: "house",
                ClaimSlotName.ASPECT: "aspect",
                ClaimSlotName.ANGLE: "angle",
                ClaimSlotName.PHASE: "phase",
                ClaimSlotName.MOTION: "motion",
            }.get(slot.name)
            if safe_name is not None:
                labels.append({"name": safe_name, "value": slot.value})
        evidence.append(
            {
                "label": f"factor_{index}",
                "source": factor.source.value,
                "kind": factor.kind.value,
                "domain": factor.domain.value,
                "role": factor.role.value,
                "confidence": factor.confidence.value,
                "phase": factor.phase.value if factor.phase else None,
                "labels": cast(JsonValue, labels),
            }
        )
    if not evidence:
        raise ValueError("Daily rewrite requires anonymous evidence")
    blueprint_json = json.dumps(
        blueprint.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.DAILY_HOME,
            owner=_owner_key(
                plan_record.guest_id,
                plan_record.profile_id,
                plan_record.id,
                projection.scope_key,
            ),
            blueprint_hash=sha256(blueprint_json.encode()).hexdigest(),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version="daily-rewrite/v1",
            gate_version=canonical_surface_registry()
            .require(RewriteSurface.DAILY_HOME)
            .gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(plan_record.guest_id),
        safe_payload={
            "context": context,
            "scene_key": blueprint.scene_key,
            "action_key": blueprint.action_key,
            "title_meaning": blueprint.hook,
            "scene_meaning": blueprint.manifestation,
            "action_meaning": blueprint.micro_action,
            "meaning_brief": (
                blueprint.daily_meaning.model_dump(mode="json") if blueprint.daily_meaning else None
            ),
            "requirements": [
                requirement.model_dump(mode="json") for requirement in blueprint.requirements
            ],
            "evidence": evidence,
        },
    )


def compile_reading_rewrite_request(
    plan_record: ReadingPlanRecord,
    projection: ReadingProjectionRecord,
    baseline: ReadingCandidate,
    *,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope:
    blueprint = baseline.semantic_blueprint
    try:
        surface = _READING_SURFACE_BY_PURPOSE[plan_record.plan.purpose]
    except KeyError as error:
        raise ValueError("Reading rewrite does not support this purpose") from error
    if blueprint is None:
        raise ValueError("Reading rewrite requires a deterministic semantic blueprint")

    factors = {factor.id: factor for factor in plan_record.plan.factors}
    factor_labels = {
        factor_id: f"factor_{index}" for index, factor_id in enumerate(factors, start=1)
    }
    evidence: list[dict[str, JsonValue]] = []
    for factor_id, label in factor_labels.items():
        factor = factors[factor_id]
        claim = canonical_evidence_claim(factor)
        labels: list[dict[str, JsonValue]] = []
        for slot in claim.slots:
            safe_name = {
                ClaimSlotName.BODY: "body",
                ClaimSlotName.BODY_A: "body",
                ClaimSlotName.BODY_B: "other_body",
                ClaimSlotName.SIGN: "sign",
                ClaimSlotName.HOUSE: "house",
                ClaimSlotName.ASPECT: "aspect",
                ClaimSlotName.ANGLE: "angle",
                ClaimSlotName.PHASE: "phase",
                ClaimSlotName.MOTION: "motion",
            }.get(slot.name)
            if safe_name is not None:
                labels.append({"name": safe_name, "value": slot.value})
        evidence.append(
            {
                "label": label,
                "source": factor.source.value,
                "kind": factor.kind.value,
                "domain": factor.domain.value,
                "role": factor.role.value,
                "confidence": factor.confidence.value,
                "phase": factor.phase.value if factor.phase else None,
                "labels": cast(JsonValue, labels),
            }
        )
    if not evidence:
        raise ValueError("Reading rewrite requires anonymous evidence")

    source_sections: list[dict[str, JsonValue]] = [
        {"section": "hook", "meaning": baseline.hook, "source": "natal"},
        {"section": "thesis", "meaning": baseline.thesis, "source": "natal"},
        {
            "section": "manifestation",
            "meaning": baseline.manifestation,
            "source": "natal",
        },
        {
            "section": "micro_action",
            "meaning": baseline.micro_action,
            "source": "natal",
        },
    ]
    if baseline.transit:
        source_sections.append(
            {"section": "transit", "meaning": baseline.transit, "source": "transit"}
        )

    blueprint_json = json.dumps(
        {
            "surface": surface.value,
            "blueprint": blueprint.model_dump(mode="json"),
            "transit": baseline.transit,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    safe_payload: dict[str, JsonValue] = {
        "purpose": plan_record.plan.purpose.value,
        "precision": plan_record.plan.precision.value,
        "mode": plan_record.plan.mode.value,
        "hero_labels": [
            factor_labels[factor_ref]
            for factor_ref in plan_record.plan.hero_factor_refs
            if factor_ref in factor_labels
        ],
        "source_sections": cast(JsonValue, source_sections),
        "requirements": cast(
            JsonValue,
            [requirement.model_dump(mode="json") for requirement in blueprint.requirements],
        ),
        "evidence": cast(JsonValue, evidence),
    }
    if plan_record.plan.background_lens is not None:
        safe_payload["background_lens"] = plan_record.plan.background_lens.value
    surface_spec = canonical_surface_registry().require(surface)
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=surface,
            owner=_reading_owner_key(
                surface,
                plan_record.guest_id,
                plan_record.profile_id,
                plan_record.id,
                projection.scope_key,
            ),
            blueprint_hash=sha256(blueprint_json.encode()).hexdigest(),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=surface_spec.schema_version,
            gate_version=surface_spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(plan_record.guest_id),
        safe_payload=safe_payload,
    )


class DailyRewriteProjector(RewriteProjector):
    def __init__(
        self,
        repository: DailyRewriteRepository,
        renderer: DeterministicVietnameseRenderer | None = None,
    ) -> None:
        self._repository = repository
        self._renderer = renderer or DeterministicVietnameseRenderer()

    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
        publish: bool = True,
    ) -> RewriteProjectionDecision:
        try:
            guest_id, profile_id, plan_id, scope_key = _parse_owner(request.key.owner)
        except ValueError:
            return RewriteProjectionDecision(accepted=False, failure_code="invalid_owner")
        plan_record = await self._repository.get_plan(guest_id, profile_id, plan_id)
        projection = await self._repository.get_projection(guest_id, profile_id, scope_key)
        if plan_record is None or projection is None or projection.active_revision_id is None:
            return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
        active = await self._repository.get_revision(
            guest_id,
            profile_id,
            projection.active_revision_id,
        )
        if active is None or active.plan_id != plan_id:
            return RewriteProjectionDecision(accepted=False, failure_code="stale_domain_version")
        baseline = self._renderer.render(plan_record.plan)
        if baseline.semantic_blueprint is None:
            return RewriteProjectionDecision(accepted=False, failure_code="missing_blueprint")
        daily_report = evaluate_daily_rewrite(
            output,
            source_scene=baseline.semantic_blueprint.manifestation,
            source_action=baseline.semantic_blueprint.micro_action,
            meaning_brief=baseline.semantic_blueprint.daily_meaning,
        )
        if not daily_report.passed:
            return RewriteProjectionDecision(
                accepted=False,
                failure_code=daily_report.failure_codes[0],
            )
        candidate = baseline.model_copy(
            update={
                "renderer_version": DAILY_REWRITE_RENDERER_VERSION,
                "hook": str(output["title"]),
                "manifestation": str(output["scene"]),
                "micro_action": str(output["action"]),
            }
        )
        evaluation = evaluate_candidate(plan_record.plan, candidate)
        if not evaluation.accepted or evaluation.publishable_candidate is None:
            return RewriteProjectionDecision(accepted=False, failure_code="reading_gate_rejected")
        gate_policy = canonical_gate_policy_version(evaluation)
        revision, _ = await self._repository.save_or_replay_revision(
            ReadingRevisionRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=profile_id,
                plan_id=plan_id,
                revision_key=canonical_reading_revision_key(
                    plan_key=plan_record.plan_key,
                    source=ReadingRevisionSource.GENERATED,
                    renderer_version=DAILY_REWRITE_RENDERER_VERSION,
                    content_version=f"daily-luna-{request.key.cache_key[:16]}",
                    schema_version=candidate.schema_version,
                    rules_version=plan_record.plan.rules_version,
                    gate_policy_version=gate_policy,
                ),
                source=ReadingRevisionSource.GENERATED,
                renderer_version=DAILY_REWRITE_RENDERER_VERSION,
                content_version=f"daily-luna-{request.key.cache_key[:16]}",
                schema_version=candidate.schema_version,
                rules_version=plan_record.plan.rules_version,
                gate_policy_version=gate_policy,
                evaluation=evaluation,
                created_at=completed_at,
            )
        )
        if publish:
            await self._repository.publish_available(guest_id, profile_id, scope_key, revision.id)
        receipt = sha256(
            f"{request.key.cache_key}\x00{revision.id}\x00{gate_policy}\x00{daily_report.version}".encode()
        ).hexdigest()
        return RewriteProjectionDecision(accepted=True, gate_receipt_id=receipt)


def _reading_candidate_from_output(
    surface: RewriteSurface,
    baseline: ReadingCandidate,
    output: dict[str, JsonValue],
) -> ReadingCandidate | None:
    if surface in {RewriteSurface.REVEAL, RewriteSurface.NATAL}:
        expected = {"headline", "synthesis", "section_intros", "examples"}
        if set(output) != expected:
            return None
        intros = output.get("section_intros")
        examples = output.get("examples")
        if (
            not isinstance(output.get("headline"), str)
            or not isinstance(output.get("synthesis"), str)
            or not isinstance(intros, list)
            or not isinstance(examples, list)
            or not intros
            or not examples
            or not all(isinstance(value, str) and value.strip() for value in (*intros, *examples))
        ):
            return None
        headline = str(output["headline"]).strip()
        synthesis = str(output["synthesis"]).strip()
        manifestation = "\n\n".join(str(value).strip() for value in intros)
        micro_action = "\n\n".join(str(value).strip() for value in examples)
        if (
            not headline
            or not synthesis
            or len(headline) > 280
            or len(synthesis) > 700
            or len(manifestation) > 700
            or len(micro_action) > 500
        ):
            return None
        return baseline.model_copy(
            update={
                "renderer_version": READING_REWRITE_RENDERER_VERSION,
                "hook": headline,
                "thesis": synthesis,
                "manifestation": manifestation,
                "micro_action": micro_action,
            }
        )

    if surface is RewriteSurface.TRANSIT_INSIGHT:
        expected = {"hook", "explanation", "everyday_example", "bounded_action"}
        if set(output) != expected or not all(
            isinstance(output.get(field), str) and str(output[field]).strip() for field in expected
        ):
            return None
        hook = str(output["hook"]).strip()
        explanation = str(output["explanation"]).strip()
        everyday_example = str(output["everyday_example"]).strip()
        bounded_action = str(output["bounded_action"]).strip()
        if (
            len(hook) > 280
            or len(explanation) > 700
            or len(everyday_example) > 700
            or len(bounded_action) > 500
        ):
            return None
        return baseline.model_copy(
            update={
                "renderer_version": READING_REWRITE_RENDERER_VERSION,
                "hook": hook,
                "thesis": explanation,
                "manifestation": everyday_example,
                "micro_action": bounded_action,
            }
        )
    return None


class LongFormReadingRewriteProjector(RewriteProjector):
    def __init__(
        self,
        repository: DailyRewriteRepository,
        renderer: DeterministicVietnameseRenderer | None = None,
    ) -> None:
        self._repository = repository
        self._renderer = renderer or DeterministicVietnameseRenderer()

    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
        publish: bool = True,
    ) -> RewriteProjectionDecision:
        try:
            surface, guest_id, profile_id, plan_id, scope_key = _parse_reading_owner(
                request.key.owner
            )
        except ValueError:
            return RewriteProjectionDecision(accepted=False, failure_code="invalid_owner")
        if request.key.surface is not surface:
            return RewriteProjectionDecision(accepted=False, failure_code="surface_owner_mismatch")
        plan_record = await self._repository.get_plan(guest_id, profile_id, plan_id)
        projection = await self._repository.get_projection(guest_id, profile_id, scope_key)
        if plan_record is None or projection is None or projection.active_revision_id is None:
            return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
        if _READING_SURFACE_BY_PURPOSE.get(plan_record.plan.purpose) is not surface:
            return RewriteProjectionDecision(
                accepted=False, failure_code="purpose_surface_mismatch"
            )
        active = await self._repository.get_revision(
            guest_id,
            profile_id,
            projection.active_revision_id,
        )
        if active is None or active.plan_id != plan_id:
            return RewriteProjectionDecision(accepted=False, failure_code="stale_domain_version")

        baseline = self._renderer.render(plan_record.plan)
        if baseline.semantic_blueprint is None:
            return RewriteProjectionDecision(accepted=False, failure_code="missing_blueprint")
        candidate = _reading_candidate_from_output(surface, baseline, output)
        if candidate is None:
            return RewriteProjectionDecision(accepted=False, failure_code="invalid_surface_output")
        evaluation = evaluate_candidate(plan_record.plan, candidate)
        if not evaluation.accepted or evaluation.publishable_candidate is None:
            return RewriteProjectionDecision(accepted=False, failure_code="reading_gate_rejected")

        gate_policy = canonical_gate_policy_version(evaluation)
        content_version = f"{surface.value}-luna-{request.key.cache_key[:16]}"
        revision, _ = await self._repository.save_or_replay_revision(
            ReadingRevisionRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=profile_id,
                plan_id=plan_id,
                revision_key=canonical_reading_revision_key(
                    plan_key=plan_record.plan_key,
                    source=ReadingRevisionSource.GENERATED,
                    renderer_version=READING_REWRITE_RENDERER_VERSION,
                    content_version=content_version,
                    schema_version=candidate.schema_version,
                    rules_version=plan_record.plan.rules_version,
                    gate_policy_version=gate_policy,
                ),
                source=ReadingRevisionSource.GENERATED,
                renderer_version=READING_REWRITE_RENDERER_VERSION,
                content_version=content_version,
                schema_version=candidate.schema_version,
                rules_version=plan_record.plan.rules_version,
                gate_policy_version=gate_policy,
                evaluation=evaluation,
                created_at=completed_at,
            )
        )
        if publish:
            await self._repository.publish_available(guest_id, profile_id, scope_key, revision.id)
        receipt = sha256(
            f"{request.key.cache_key}\x00{revision.id}\x00{gate_policy}".encode()
        ).hexdigest()
        return RewriteProjectionDecision(accepted=True, gate_receipt_id=receipt)


class ReadingRewriteProjector(RewriteProjector):
    """Route reading-owned rewrite surfaces to their domain-specific projector."""

    def __init__(
        self,
        repository: DailyRewriteRepository,
        renderer: DeterministicVietnameseRenderer | None = None,
    ) -> None:
        self._daily = DailyRewriteProjector(repository, renderer)
        self._long_form = LongFormReadingRewriteProjector(repository, renderer)

    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
        publish: bool = True,
    ) -> RewriteProjectionDecision:
        if request.key.surface is RewriteSurface.DAILY_HOME:
            return await self._daily.validate_and_project(
                request,
                output,
                completed_at=completed_at,
                publish=publish,
            )
        return await self._long_form.validate_and_project(
            request,
            output,
            completed_at=completed_at,
            publish=publish,
        )
