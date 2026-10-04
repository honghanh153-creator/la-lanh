from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    LeasedRewriteJob,
    RewriteArtifactKey,
    RewriteJobResult,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.repository import ContentRewriteRepository
from app.domains.content_rewrite.rollout import RewriteRolloutMode, SurfaceRolloutPolicy
from app.domains.content_rewrite.service import RewriteProjectionDecision
from app.domains.content_rewrite.worker import ContentRewriteWorker
from app.infrastructure.generation.base import (
    GenerationTransient,
    RewriteGenerationProvider,
    RewriteGenerationResult,
    RewriteGenerationSuccess,
)

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _request() -> RewriteRequestEnvelope:
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.DAILY_HOME,
            owner=ArtifactOwnerKey(namespace="readings", key="daily:anonymous"),
            blueprint_hash="a" * 64,
            model_version="gpt-6-luna",
            prompt_version="surface-rewrite-v1",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
        ),
        authorization_receipt_id="consent-receipt",
        safe_payload={},
    )


def _lease(*, attempt_count: int = 1, max_attempts: int = 2) -> LeasedRewriteJob:
    return LeasedRewriteJob(
        id=uuid4(),
        request=_request(),
        deletion_epoch=uuid4(),
        lease_token=uuid4(),
        lease_expires_at=NOW + timedelta(minutes=2),
        attempt_count=attempt_count,
        max_attempts=max_attempts,
    )


class FakeRepository:
    def __init__(self, lease: LeasedRewriteJob) -> None:
        self.current_lease: LeasedRewriteJob | None = lease
        self.events: list[str] = []
        self.failed_result: RewriteJobResult | None = None
        self.success_usage: tuple[int | None, int | None] | None = None
        self.failure_usage: tuple[int | None, int | None] | None = None
        self.success_cost_nanos: int | None = None
        self.failure_cost_nanos: int | None = None
        self.budget_allowed = True
        self.reserved_tokens: int | None = None
        self.reserved_cost_nanos: int | None = None

    async def lease(self, **kwargs):  # type: ignore[no-untyped-def]
        del kwargs
        lease, self.current_lease = self.current_lease, None
        self.events.append("lease")
        return lease

    async def mark_request_started(self, **kwargs):  # type: ignore[no-untyped-def]
        del kwargs
        self.events.append("marked")
        return True

    async def retry(self, **kwargs):  # type: ignore[no-untyped-def]
        self.failed_result = kwargs["result"]
        self.events.append("retry")
        return True

    async def fail(self, **kwargs):  # type: ignore[no-untyped-def]
        self.failed_result = kwargs["result"]
        self.failure_usage = (kwargs.get("input_tokens"), kwargs.get("output_tokens"))
        self.failure_cost_nanos = kwargs.get("cost_nanos")
        self.events.append("fail")
        return True

    async def succeed(self, **kwargs):  # type: ignore[no-untyped-def]
        self.success_usage = (kwargs["input_tokens"], kwargs["output_tokens"])
        self.success_cost_nanos = kwargs["cost_nanos"]
        self.events.append("succeed")
        return True

    async def reserve_budget(self, **kwargs):  # type: ignore[no-untyped-def]
        self.reserved_tokens = kwargs["requested_tokens"]
        self.reserved_cost_nanos = kwargs["requested_cost_nanos"]
        self.events.append("reserve")
        return self.budget_allowed


class Authorization:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool:
        del request
        return self.allowed


class Provider:
    def __init__(self, result: RewriteGenerationResult) -> None:
        self.result = result
        self.calls = 0

    async def generate_rewrite(self, request: RewriteRequestEnvelope) -> RewriteGenerationResult:
        del request
        self.calls += 1
        return self.result


class ExplodingProvider:
    async def generate_rewrite(self, request: RewriteRequestEnvelope) -> RewriteGenerationResult:
        del request
        raise RuntimeError("private provider detail")


class Projector:
    def __init__(self, accepted: bool = True) -> None:
        self.accepted = accepted
        self.calls = 0
        self.last_publish: bool | None = None

    async def validate_and_project(  # type: ignore[no-untyped-def]
        self, request, output, *, completed_at, publish=True
    ):
        del request, output, completed_at
        self.calls += 1
        self.last_publish = publish
        return RewriteProjectionDecision(
            accepted=self.accepted,
            gate_receipt_id="gate-receipt" if self.accepted else None,
            failure_code=None if self.accepted else "meaning_gate",
        )


@pytest.mark.asyncio
async def test_worker_rechecks_authorization_before_send() -> None:
    repository = FakeRepository(_lease())
    provider = Provider(
        RewriteGenerationSuccess(
            key=_request().key,
            output={"title": "x", "scene": "y", "action": "z"},
        )
    )

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(False),
        Projector(),
        clock=lambda: NOW,
    ).process_one()

    assert provider.calls == 0
    assert repository.failed_result is RewriteJobResult.AUTHORIZATION_REVOKED
    assert repository.events == ["lease", "fail"]


@pytest.mark.asyncio
async def test_worker_projects_then_marks_success() -> None:
    lease = _lease()
    repository = FakeRepository(lease)
    provider = Provider(
        RewriteGenerationSuccess(
            key=lease.request.key,
            output={"title": "Rõ hơn", "scene": "Một cảnh", "action": "Một bước"},
            input_tokens=250,
            output_tokens=60,
        )
    )
    projector = Projector()

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(True),
        projector,
        clock=lambda: NOW,
    ).process_one()

    assert projector.calls == 1
    assert repository.events == ["lease", "marked", "succeed"]
    assert repository.success_usage == (250, 60)
    assert repository.success_cost_nanos == 55_000


@pytest.mark.asyncio
async def test_gate_rejection_keeps_owner_projection_unchanged() -> None:
    lease = _lease()
    repository = FakeRepository(lease)
    provider = Provider(
        RewriteGenerationSuccess(
            key=lease.request.key,
            output={"title": "x"},
            input_tokens=120,
            output_tokens=30,
        )
    )

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(True),
        Projector(accepted=False),
        clock=lambda: NOW,
    ).process_one()

    assert repository.failed_result is RewriteJobResult.GATE_REJECTED
    assert repository.failure_usage == (120, 30)
    assert repository.failure_cost_nanos == 27_000
    assert repository.events[-1] == "fail"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("retry_safe", "attempt_count", "expected_event", "expected_result"),
    [
        (True, 1, "retry", RewriteJobResult.TRANSIENT),
        (True, 2, "fail", RewriteJobResult.TRANSIENT),
        (False, 1, "fail", RewriteJobResult.AMBIGUOUS),
    ],
)
async def test_retry_policy_is_delivery_aware(
    retry_safe: bool,
    attempt_count: int,
    expected_event: str,
    expected_result: RewriteJobResult,
) -> None:
    repository = FakeRepository(_lease(attempt_count=attempt_count))
    provider = Provider(GenerationTransient(retry_safe=retry_safe))

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(True),
        Projector(),
        clock=lambda: NOW,
    ).process_one()

    assert repository.events[-1] == expected_event
    assert repository.failed_result is expected_result


@pytest.mark.asyncio
async def test_unexpected_exception_after_send_is_ambiguous_and_not_retried() -> None:
    repository = FakeRepository(_lease())

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        ExplodingProvider(),
        Authorization(True),
        Projector(),
        clock=lambda: NOW,
    ).process_one()

    assert repository.events == ["lease", "marked", "fail"]
    assert repository.failed_result is RewriteJobResult.AMBIGUOUS


@pytest.mark.asyncio
async def test_daily_token_budget_blocks_before_provider_send() -> None:
    repository = FakeRepository(_lease())
    repository.budget_allowed = False
    provider = Provider(
        RewriteGenerationSuccess(
            key=_request().key,
            output={"title": "x", "scene": "y", "action": "z"},
        )
    )

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(True),
        Projector(),
        daily_token_budget=1_000,
        daily_cost_budget_cents=100,
        clock=lambda: NOW,
    ).process_one()

    assert provider.calls == 0
    assert repository.events == ["lease", "reserve", "fail"]
    assert repository.failed_result is RewriteJobResult.BUDGET_BLOCKED


@pytest.mark.asyncio
async def test_shadow_mode_runs_gates_without_publishing() -> None:
    lease = _lease()
    repository = FakeRepository(lease)
    provider = Provider(
        RewriteGenerationSuccess(
            key=lease.request.key,
            output={"title": "Rõ hơn", "scene": "Một cảnh", "action": "Một bước"},
        )
    )
    projector = Projector()

    await ContentRewriteWorker(
        cast(ContentRewriteRepository, repository),
        cast(RewriteGenerationProvider, provider),
        Authorization(True),
        projector,
        rollout=SurfaceRolloutPolicy({RewriteSurface.DAILY_HOME: RewriteRolloutMode.SHADOW}),
        clock=lambda: NOW,
    ).process_one()

    assert projector.calls == 1
    assert projector.last_publish is False
    assert repository.events[-1] == "succeed"
