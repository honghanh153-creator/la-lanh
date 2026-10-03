from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    LeasedRewriteJob,
    RewriteJobRecord,
    RewriteJobResult,
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
    ) -> bool: ...

    async def succeed(
        self,
        *,
        lease: LeasedRewriteJob,
        gate_receipt_id: str,
        output_fingerprint: str,
        completed_at: datetime,
    ) -> bool: ...

    async def cancel_and_purge_owner(self, owner: ArtifactOwnerKey) -> int: ...

    async def cancel_and_purge_authorization(self, authorization_receipt_id: str) -> int: ...
