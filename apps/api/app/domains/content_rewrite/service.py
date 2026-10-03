from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.domains.content_rewrite.models import (
    RewriteJobRecord,
    RewriteRequestEnvelope,
)
from app.domains.content_rewrite.registry import SurfaceRegistry, canonical_surface_registry
from app.domains.content_rewrite.repository import ContentRewriteRepository
from app.infrastructure.generation.privacy import PrivacyMinimiser


class RewriteAuthorizationChecker(Protocol):
    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool: ...


class RewriteProjectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted: bool
    gate_receipt_id: str | None = Field(default=None, min_length=1, max_length=240)
    failure_code: str | None = Field(default=None, min_length=1, max_length=80)


class RewriteProjector(Protocol):
    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
    ) -> RewriteProjectionDecision: ...


class ContentRewriteService:
    def __init__(
        self,
        repository: ContentRewriteRepository,
        authorization: RewriteAuthorizationChecker,
        *,
        registry: SurfaceRegistry | None = None,
        minimiser: PrivacyMinimiser | None = None,
        max_attempts: int = 2,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._registry = registry or canonical_surface_registry()
        self._minimiser = minimiser or PrivacyMinimiser()
        self._max_attempts = max_attempts

    async def enqueue(
        self,
        request: RewriteRequestEnvelope,
        *,
        now: datetime | None = None,
    ) -> tuple[RewriteJobRecord, bool]:
        self._registry.validate_request(request)
        if not await self._authorization.is_authorized(request):
            raise PermissionError("external rewrite authorization is not active")
        safe_payload = self._minimiser.minimise(request.key.surface, request.safe_payload)
        safe_request = request.model_copy(update={"safe_payload": safe_payload})
        created_at = now or datetime.now(UTC)
        record = RewriteJobRecord(
            id=uuid4(),
            request=safe_request,
            deletion_epoch=uuid4(),
            max_attempts=self._max_attempts,
            next_attempt_at=created_at,
            created_at=created_at,
            updated_at=created_at,
        )
        return await self._repository.enqueue(record)
