from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.readings.models import (
    GenerationAttemptRecord,
    GenerationAttemptResult,
    LeasedGenerationAttempt,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingRevisionRecord,
)


class ReadingRepository(Protocol):
    async def save_or_replay_plan(
        self, record: ReadingPlanRecord
    ) -> tuple[ReadingPlanRecord, bool]: ...

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]: ...

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None: ...

    async def get_or_create_projection(
        self, record: ReadingProjectionRecord
    ) -> tuple[ReadingProjectionRecord, bool]: ...

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None: ...

    async def publish_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        revision_id: UUID,
    ) -> ReadingProjectionRecord: ...

    async def activate_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        updated_at: datetime,
        expected_chart_snapshot_id: UUID | None = None,
    ) -> ReadingProjectionRecord | None: ...

    async def acknowledge_aura_transition(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        transition_id: str,
        updated_at: datetime,
    ) -> ReadingProjectionRecord | None: ...

    async def enqueue_generation_attempt(
        self, record: GenerationAttemptRecord
    ) -> tuple[GenerationAttemptRecord, bool]: ...

    async def lease_generation_attempt(
        self, *, now: datetime, lease_for_seconds: int
    ) -> LeasedGenerationAttempt | None: ...

    async def mark_generation_request_started(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        started_at: datetime,
    ) -> bool: ...

    async def retry_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        next_attempt_at: datetime,
        updated_at: datetime,
    ) -> bool: ...

    async def fail_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        updated_at: datetime,
    ) -> bool: ...

    async def finalize_generation_success(
        self,
        *,
        lease: LeasedGenerationAttempt,
        revision: ReadingRevisionRecord,
        completed_at: datetime,
    ) -> bool: ...


class ReadingProjectionRepository(Protocol):
    """Small application-facing surface; queue execution stays outside request handling."""

    async def save_or_replay_plan(
        self, record: ReadingPlanRecord
    ) -> tuple[ReadingPlanRecord, bool]: ...

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]: ...

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None: ...

    async def get_or_create_projection(
        self, record: ReadingProjectionRecord
    ) -> tuple[ReadingProjectionRecord, bool]: ...

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None: ...

    async def publish_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        revision_id: UUID,
    ) -> ReadingProjectionRecord: ...

    async def activate_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        updated_at: datetime,
        expected_chart_snapshot_id: UUID | None = None,
    ) -> ReadingProjectionRecord | None: ...

    async def acknowledge_aura_transition(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        transition_id: str,
        updated_at: datetime,
    ) -> ReadingProjectionRecord | None: ...

    async def enqueue_generation_attempt(
        self, record: GenerationAttemptRecord
    ) -> tuple[GenerationAttemptRecord, bool]: ...


class GenerationWorkerRepository(Protocol):
    """Worker-only queue surface; excludes projection request APIs."""

    async def lease_generation_attempt(
        self, *, now: datetime, lease_for_seconds: int
    ) -> LeasedGenerationAttempt | None: ...

    async def mark_generation_request_started(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        started_at: datetime,
    ) -> bool: ...

    async def retry_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        next_attempt_at: datetime,
        updated_at: datetime,
    ) -> bool: ...

    async def fail_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        updated_at: datetime,
    ) -> bool: ...

    async def finalize_generation_success(
        self,
        *,
        lease: LeasedGenerationAttempt,
        revision: ReadingRevisionRecord,
        completed_at: datetime,
    ) -> bool: ...
