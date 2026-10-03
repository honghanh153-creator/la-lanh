from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from typing import Protocol, cast
from uuid import UUID, uuid4

from pydantic import JsonValue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.service import (
    RewriteAuthorizationChecker,
    RewriteProjectionDecision,
    RewriteProjector,
)
from app.domains.guest.tables import ConsentRow
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

CONTENT_REWRITE_CONSENT_VERSION = "external-content-rewrite-v1"
CONTENT_REWRITE_CONSENT_PURPOSE = "external_content_rewrite"
DAILY_REWRITE_RENDERER_VERSION = "gpt-6-luna-daily-v1"


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


def content_rewrite_receipt_id(guest_id: UUID) -> str:
    return sha256(
        f"{CONTENT_REWRITE_CONSENT_VERSION}\x00{CONTENT_REWRITE_CONSENT_PURPOSE}\x00{guest_id}".encode()
    ).hexdigest()


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
            gate_version="daily-rewrite-gates/v1",
        ),
        authorization_receipt_id=content_rewrite_receipt_id(plan_record.guest_id),
        safe_payload={
            "context": context,
            "scene_key": blueprint.scene_key,
            "action_key": blueprint.action_key,
            "title_meaning": blueprint.hook,
            "scene_meaning": blueprint.manifestation,
            "action_meaning": blueprint.micro_action,
            "requirements": [
                requirement.model_dump(mode="json") for requirement in blueprint.requirements
            ],
            "evidence": evidence,
        },
    )


class DatabaseRewriteAuthorization(RewriteAuthorizationChecker):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def authorized_guest(self, guest_id: UUID) -> bool:
        async with self._sessions() as session:
            consent = await session.scalar(
                select(ConsentRow).where(
                    ConsentRow.guest_id == guest_id,
                    ConsentRow.version == CONTENT_REWRITE_CONSENT_VERSION,
                    ConsentRow.purpose == CONTENT_REWRITE_CONSENT_PURPOSE,
                    ConsentRow.revoked_at.is_(None),
                )
            )
            return consent is not None

    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool:
        try:
            guest_id, _profile_id, _plan_id, _scope_key = _parse_owner(request.key.owner)
        except ValueError:
            return False
        if request.authorization_receipt_id != content_rewrite_receipt_id(guest_id):
            return False
        return await self.authorized_guest(guest_id)


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
        await self._repository.publish_available(guest_id, profile_id, scope_key, revision.id)
        receipt = sha256(
            f"{request.key.cache_key}\x00{revision.id}\x00{gate_policy}\x00{daily_report.version}".encode()
        ).hexdigest()
        return RewriteProjectionDecision(accepted=True, gate_receipt_id=receipt)
