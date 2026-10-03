from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    LeasedRewriteJob,
    RewriteJobRecord,
    RewriteJobResult,
    RewriteReviewRecord,
)


class ContentRewriteRepository(Protocol):
    async def enqueue(self, record: RewriteJobRecord) -> tuple[RewriteJobRecord, bool]: ...

    async def lease(self, *, now: datetime, lease_for_seconds: int) -> LeasedRewriteJob | None: ...

    async def mark_request_started(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        started_at: datetime,
    ) -> bool: ...

    async def retry(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: RewriteJobResult,
        next_attempt_at: datetime,
        updated_at: datetime,
    ) -> bool: ...

    async def fail(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: RewriteJobResult,
        updated_at: datetime,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> bool: ...

    async def succeed(
        self,
        *,
        lease: LeasedRewriteJob,
        gate_receipt_id: str,
        output_fingerprint: str,
        input_tokens: int | None,
        output_tokens: int | None,
        completed_at: datetime,
    ) -> bool: ...

    async def cancel_and_purge_owner(self, owner: ArtifactOwnerKey) -> int: ...

    async def cancel_and_purge_authorization(self, authorization_receipt_id: str) -> int: ...

    async def list_review_records(self, *, limit: int = 100) -> tuple[RewriteReviewRecord, ...]: ...

    async def tokens_used_since(self, since: datetime) -> int: ...

    async def reserve_token_budget(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        since: datetime,
        requested_tokens: int,
        daily_limit: int,
        updated_at: datetime,
    ) -> bool: ...
