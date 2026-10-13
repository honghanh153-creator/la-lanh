from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.db.rewrite_scope import bind_rewrite_session, rewrite_session
from app.domains.content_rewrite.authorization import (
    consent_scope_for_surface,
    content_rewrite_receipt_id,
    guest_id_from_rewrite_owner,
    lock_rewrite_authority,
    rewrite_subjects,
)
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    LeasedRewriteJob,
    RewriteJobRecord,
    RewriteJobResult,
    RewriteJobStatus,
    RewriteRequestEnvelope,
    RewriteReviewRecord,
    RewriteSurface,
)
from app.domains.content_rewrite.tables import (
    ContentRewriteJobRow,
    ContentRewriteSpendDayRow,
    ContentRewriteSpendMonthRow,
    RewriteSendFenceRow,
)
from app.infrastructure.crypto import EnvelopeCipher


def owner_fingerprint(owner: ArtifactOwnerKey) -> str:
    return sha256(f"{owner.namespace}\x00{owner.key}".encode()).hexdigest()


def authorization_fingerprint(authorization_receipt_id: str) -> str:
    return sha256(
        f"content-rewrite-authorization\x00{authorization_receipt_id}".encode()
    ).hexdigest()


def output_fingerprint(output: dict[str, object]) -> str:
    canonical = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode()).hexdigest()


class PostgresContentRewriteRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    @asynccontextmanager
    async def execution_guard(self, lease: LeasedRewriteJob) -> AsyncIterator[bool]:
        """Short authority transaction for send admission or atomic publication.

        Never hold this context across provider I/O. Projection repositories borrow
        the publication session; send admission commits its independent drain fences.
        """
        try:
            guest_id = guest_id_from_rewrite_owner(lease.request.key.owner)
        except ValueError:
            yield False
            return
        async with self._sessions() as session, session.begin():
            authority = await lock_rewrite_authority(session, lease.request, guest_id)
            parent_valid = await self._parent_exists(session, lease.request, guest_id)
            row = await session.scalar(
                select(ContentRewriteJobRow)
                .where(self._lease_match(lease.id, lease.lease_token, lease.deletion_epoch))
                .with_for_update()
            )
            now = datetime.now(UTC)
            valid = (
                authority is not None
                and authority.expires_at > now
                and row is not None
                and row.owner_guest_id == guest_id
                and row.lease_expires_at is not None
                and row.lease_expires_at > now
                and authority.accepted_at <= row.created_at
                and self._request(row) == lease.request
                and lease.request.authorization_receipt_id
                == content_rewrite_receipt_id(
                    guest_id, scope=consent_scope_for_surface(lease.request.key.surface)
                )
            )
            async with bind_rewrite_session(self._sessions, session):
                yield bool(valid and parent_valid)

    @staticmethod
    async def _parent_exists(
        session: AsyncSession, request: RewriteRequestEnvelope, guest_id: UUID
    ) -> bool:
        from app.domains.birth.tables import BirthProfileRow
        from app.domains.radar.tables import RadarRequestRow
        from app.domains.readings.tables import ReadingPlanRow
        from app.domains.tarot.tables import TarotSessionRow

        parts = request.key.owner.key.split("|")
        if request.key.owner.namespace == "readings":
            plan_id = UUID(parts[3] if parts[0] == "daily" else parts[4])
            profile = await session.scalar(
                select(BirthProfileRow)
                .where(BirthProfileRow.guest_id == guest_id)
                .with_for_update()
            )
            parent = await session.scalar(
                select(ReadingPlanRow)
                .where(ReadingPlanRow.id == plan_id, ReadingPlanRow.guest_id == guest_id)
                .with_for_update()
            )
            return (
                parent is not None
                and profile is not None
                and parent.profile_id == profile.id
                and parent.chart_snapshot_id == profile.current_snapshot_id
            )
        if request.key.owner.namespace == "tarot":
            tarot = await session.scalar(
                select(TarotSessionRow)
                .where(TarotSessionRow.id == UUID(parts[2]), TarotSessionRow.guest_id == guest_id)
                .with_for_update()
            )
            return (
                tarot is not None
                and tarot.state == "complete"
                and tarot.expires_at > datetime.now(UTC)
            )
        if request.key.owner.namespace == "radar":
            radar = await session.scalar(
                select(RadarRequestRow)
                .where(RadarRequestRow.id == UUID(parts[2]))
                .with_for_update()
            )
            return (
                radar is not None
                and radar.status == "completed"
                and radar.withdrawn_at is None
                and radar.revoked_at is None
                and radar.expires_at > datetime.now(UTC)
                and guest_id
                == (radar.owner_guest_id if parts[3] == "owner" else radar.recipient_guest_id)
            )
        return False

    async def enqueue(self, record: RewriteJobRecord) -> tuple[RewriteJobRecord, bool]:
        if record.status is not RewriteJobStatus.PENDING or record.attempt_count != 0:
            raise ValueError("new rewrite jobs must be pending and unattempted")
        async with self._sessions() as session, session.begin():
            try:
                guest_id = guest_id_from_rewrite_owner(record.request.key.owner)
            except ValueError:
                guest_id = None
            if guest_id is not None:
                authority = await lock_rewrite_authority(session, record.request, guest_id)
                if authority is None or authority.accepted_at > record.created_at:
                    raise PermissionError("rewrite authority was withdrawn before enqueue")
                if not await self._parent_exists(session, record.request, guest_id):
                    raise PermissionError("rewrite parent was withdrawn before enqueue")
            existing = await session.scalar(
                select(ContentRewriteJobRow).where(
                    ContentRewriteJobRow.generation_key == record.request.key.cache_key
                )
            )
            if existing is not None:
                stored = self._record(existing)
                self._assert_same_request(stored, record)
                return stored, True
            try:
                async with session.begin_nested():
                    row = self._row(record)
                    session.add(row)
                    await session.flush([row])
            except IntegrityError:
                existing = await session.scalar(
                    select(ContentRewriteJobRow).where(
                        ContentRewriteJobRow.generation_key == record.request.key.cache_key
                    )
                )
                if existing is None:
                    raise
                stored = self._record(existing)
                self._assert_same_request(stored, record)
                return stored, True
            return self._record(row), False

    async def lease(self, *, now: datetime, lease_for_seconds: int) -> LeasedRewriteJob | None:
        async with self._sessions() as session, session.begin():
            # Bounded recoverable payload retention, including abandoned pending jobs.
            stale_ids = list(
                await session.scalars(
                    select(ContentRewriteJobRow.id)
                    .where(
                        ContentRewriteJobRow.created_at < now - timedelta(hours=24),
                        or_(
                            ContentRewriteJobRow.status != RewriteJobStatus.LEASED.value,
                            ContentRewriteJobRow.lease_expires_at <= now,
                        ),
                    )
                    .order_by(ContentRewriteJobRow.id)
                    .limit(100)
                    .with_for_update(skip_locked=True)
                )
            )
            await session.execute(
                delete(ContentRewriteJobRow).where(ContentRewriteJobRow.id.in_(stale_ids))
            )
            await session.execute(
                update(ContentRewriteJobRow)
                .where(
                    ContentRewriteJobRow.status == RewriteJobStatus.LEASED.value,
                    ContentRewriteJobRow.lease_expires_at <= now,
                    or_(
                        ContentRewriteJobRow.request_started_at.is_not(None),
                        ContentRewriteJobRow.budget_reserved_tokens > 0,
                        ContentRewriteJobRow.budget_reserved_cost_nanos > 0,
                    ),
                )
                .values(
                    status=RewriteJobStatus.FAILED.value,
                    last_result=RewriteJobResult.AMBIGUOUS.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    input_tokens=func.coalesce(
                        ContentRewriteJobRow.input_tokens,
                        func.nullif(ContentRewriteJobRow.budget_reserved_tokens, 0),
                    ),
                    cost_nanos=func.coalesce(
                        ContentRewriteJobRow.cost_nanos,
                        func.nullif(ContentRewriteJobRow.budget_reserved_cost_nanos, 0),
                    ),
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    updated_at=now,
                )
            )
            await session.execute(
                update(ContentRewriteJobRow)
                .where(
                    ContentRewriteJobRow.status == RewriteJobStatus.LEASED.value,
                    ContentRewriteJobRow.lease_expires_at <= now,
                    ContentRewriteJobRow.request_started_at.is_(None),
                    ContentRewriteJobRow.budget_reserved_tokens == 0,
                    ContentRewriteJobRow.budget_reserved_cost_nanos == 0,
                    ContentRewriteJobRow.attempt_count < ContentRewriteJobRow.max_attempts,
                )
                .values(
                    status=RewriteJobStatus.PENDING.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    next_attempt_at=now,
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    pricing_version=None,
                    updated_at=now,
                )
            )
            await session.execute(
                update(ContentRewriteJobRow)
                .where(
                    ContentRewriteJobRow.status == RewriteJobStatus.LEASED.value,
                    ContentRewriteJobRow.lease_expires_at <= now,
                    ContentRewriteJobRow.request_started_at.is_(None),
                    ContentRewriteJobRow.budget_reserved_tokens == 0,
                    ContentRewriteJobRow.budget_reserved_cost_nanos == 0,
                    ContentRewriteJobRow.attempt_count >= ContentRewriteJobRow.max_attempts,
                )
                .values(
                    status=RewriteJobStatus.FAILED.value,
                    last_result=RewriteJobResult.TRANSIENT.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    pricing_version=None,
                    updated_at=now,
                )
            )
            row = await session.scalar(
                select(ContentRewriteJobRow)
                .where(
                    ContentRewriteJobRow.status == RewriteJobStatus.PENDING.value,
                    ContentRewriteJobRow.created_at >= now - timedelta(hours=24),
                    ContentRewriteJobRow.next_attempt_at <= now,
                    ContentRewriteJobRow.attempt_count < ContentRewriteJobRow.max_attempts,
                )
                .order_by(ContentRewriteJobRow.next_attempt_at, ContentRewriteJobRow.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if row is None:
                return None
            lease_token = uuid4()
            lease_expires_at = now + timedelta(seconds=lease_for_seconds)
            row.status = RewriteJobStatus.LEASED.value
            row.lease_token = lease_token
            row.lease_expires_at = lease_expires_at
            row.request_started_at = None
            row.budget_reserved_tokens = 0
            row.budget_reserved_cost_nanos = 0
            row.pricing_version = None
            row.attempt_count += 1
            row.updated_at = now
            await session.flush([row])
            return LeasedRewriteJob(
                id=row.id,
                request=self._request(row),
                deletion_epoch=row.deletion_epoch,
                lease_token=lease_token,
                lease_expires_at=lease_expires_at,
                attempt_count=row.attempt_count,
                max_attempts=row.max_attempts,
            )

    async def mark_request_started(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        started_at: datetime,
    ) -> bool:
        async with rewrite_session(self._sessions, transaction=True) as session:
            result = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(job_id, lease_token, deletion_epoch))
                .where(ContentRewriteJobRow.request_started_at.is_(None))
                .where(ContentRewriteJobRow.lease_expires_at > started_at)
                .values(request_started_at=started_at, updated_at=started_at)
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                return False
            row = await session.get(ContentRewriteJobRow, job_id, populate_existing=True)
            if row is not None and row.owner_guest_id is not None and row.lease_expires_at:
                subjects = await rewrite_subjects(session, self._request(row), row.owner_guest_id)
                if subjects is None:
                    raise PermissionError("rewrite subjects changed before admission")
                session.add_all(
                    [
                        RewriteSendFenceRow(
                            job_id=job_id,
                            lease_token=lease_token,
                            subject_id=subject,
                            # Includes the entire maximum provider window after a delayed
                            # admission. A dead worker cannot resend an expired lease.
                            expires_at=row.lease_expires_at + timedelta(seconds=60),
                        )
                        for subject in subjects
                    ]
                )
                await session.flush()
            return True

    async def finish_send(self, *, job_id: UUID, lease_token: UUID) -> None:
        # This transaction must survive projector rollback/source cascades.
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(RewriteSendFenceRow).where(
                    RewriteSendFenceRow.job_id == job_id,
                    RewriteSendFenceRow.lease_token == lease_token,
                )
            )

    async def retry(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: RewriteJobResult,
        next_attempt_at: datetime,
        updated_at: datetime,
    ) -> bool:
        async with rewrite_session(self._sessions, transaction=True) as session:
            updated = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(job_id, lease_token, deletion_epoch))
                .values(
                    status=RewriteJobStatus.PENDING.value,
                    last_result=result.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    next_attempt_at=next_attempt_at,
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    pricing_version=None,
                    updated_at=updated_at,
                )
            )
            return cast(CursorResult[Any], updated).rowcount == 1

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
        cost_nanos: int | None = None,
    ) -> bool:
        async with rewrite_session(self._sessions, transaction=True) as session:
            usage_values: dict[str, object]
            usage_values = {
                "input_tokens": (
                    input_tokens
                    if input_tokens is not None
                    else func.coalesce(
                        ContentRewriteJobRow.input_tokens,
                        func.nullif(ContentRewriteJobRow.budget_reserved_tokens, 0),
                    )
                ),
                "output_tokens": (
                    output_tokens
                    if output_tokens is not None
                    else ContentRewriteJobRow.output_tokens
                ),
                "cost_nanos": (
                    cost_nanos
                    if cost_nanos is not None
                    else func.coalesce(
                        ContentRewriteJobRow.cost_nanos,
                        func.nullif(ContentRewriteJobRow.budget_reserved_cost_nanos, 0),
                    )
                ),
            }
            updated = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(job_id, lease_token, deletion_epoch))
                .values(
                    status=(
                        RewriteJobStatus.CANCELLED.value
                        if result is RewriteJobResult.AUTHORIZATION_REVOKED
                        else RewriteJobStatus.FAILED.value
                    ),
                    last_result=result.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    provider_output_ciphertext=None,
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    updated_at=updated_at,
                    **usage_values,
                )
            )
            return cast(CursorResult[Any], updated).rowcount == 1

    async def succeed(
        self,
        *,
        lease: LeasedRewriteJob,
        gate_receipt_id: str,
        output_fingerprint: str,
        input_tokens: int | None,
        output_tokens: int | None,
        cost_nanos: int | None,
        completed_at: datetime,
    ) -> bool:
        async with rewrite_session(self._sessions, transaction=True) as session:
            updated = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(lease.id, lease.lease_token, lease.deletion_epoch))
                .where(ContentRewriteJobRow.lease_expires_at > completed_at)
                .values(
                    status=RewriteJobStatus.SUCCEEDED.value,
                    last_result=RewriteJobResult.ACCEPTED.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    provider_output_ciphertext=None,
                    output_fingerprint=output_fingerprint,
                    gate_receipt_id=gate_receipt_id,
                    input_tokens=(
                        input_tokens
                        if input_tokens is not None
                        else func.coalesce(
                            ContentRewriteJobRow.input_tokens,
                            func.nullif(ContentRewriteJobRow.budget_reserved_tokens, 0),
                        )
                    ),
                    output_tokens=(
                        output_tokens
                        if output_tokens is not None
                        else ContentRewriteJobRow.output_tokens
                    ),
                    cost_nanos=(
                        cost_nanos
                        if cost_nanos is not None
                        else func.coalesce(
                            ContentRewriteJobRow.cost_nanos,
                            func.nullif(ContentRewriteJobRow.budget_reserved_cost_nanos, 0),
                        )
                    ),
                    budget_reserved_tokens=0,
                    budget_reserved_cost_nanos=0,
                    updated_at=completed_at,
                )
            )
            return cast(CursorResult[Any], updated).rowcount == 1

    async def cancel_and_purge_owner(self, owner: ArtifactOwnerKey) -> int:
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(ContentRewriteJobRow).where(
                    ContentRewriteJobRow.owner_namespace == owner.namespace,
                    ContentRewriteJobRow.owner_fingerprint == owner_fingerprint(owner),
                )
            )
            return cast(CursorResult[Any], result).rowcount

    async def cancel_and_purge_authorization(self, authorization_receipt_id: str) -> int:
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(ContentRewriteJobRow).where(
                    ContentRewriteJobRow.authorization_fingerprint
                    == authorization_fingerprint(authorization_receipt_id)
                )
            )
            return cast(CursorResult[Any], result).rowcount

    async def list_review_records(self, *, limit: int = 100) -> tuple[RewriteReviewRecord, ...]:
        bounded_limit = min(max(limit, 1), 200)
        async with self._sessions() as session:
            rows = tuple(
                await session.scalars(
                    select(ContentRewriteJobRow)
                    .order_by(ContentRewriteJobRow.created_at.desc())
                    .limit(bounded_limit)
                )
            )
        return tuple(
            RewriteReviewRecord(
                id=row.id,
                surface=RewriteSurface(row.surface),
                status=RewriteJobStatus(row.status),
                last_result=RewriteJobResult(row.last_result) if row.last_result else None,
                candidate_variant=row.candidate_variant,
                provider=row.provider,
                model=row.model,
                prompt_version=row.prompt_version,
                schema_version=row.schema_version,
                gate_version=row.gate_version,
                gate_receipt_id=row.gate_receipt_id,
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                cost_nanos=row.cost_nanos,
                pricing_version=row.pricing_version,
                attempt_count=row.attempt_count,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        )

    async def tokens_used_since(self, since: datetime) -> int:
        async with self._sessions() as session:
            value = await session.scalar(
                select(
                    func.coalesce(
                        func.sum(
                            func.coalesce(ContentRewriteJobRow.input_tokens, 0)
                            + func.coalesce(ContentRewriteJobRow.output_tokens, 0)
                        ),
                        0,
                    )
                ).where(ContentRewriteJobRow.updated_at >= since)
            )
        return int(value or 0)

    async def cost_used_since(self, since: datetime) -> int:
        async with self._sessions() as session:
            value = await session.scalar(
                select(func.coalesce(func.sum(ContentRewriteJobRow.cost_nanos), 0)).where(
                    ContentRewriteJobRow.updated_at >= since
                )
            )
        return int(value or 0)

    async def reserve_budget(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        since: datetime,
        requested_tokens: int,
        daily_token_limit: int,
        requested_cost_nanos: int,
        daily_cost_limit_nanos: int,
        pricing_version: str,
        updated_at: datetime,
        monthly_cost_limit_nanos: int | None = None,
    ) -> bool:
        if (
            requested_tokens <= 0
            or daily_token_limit <= 0
            or requested_cost_nanos <= 0
            or daily_cost_limit_nanos <= 0
            or not pricing_version
            or (monthly_cost_limit_nanos is not None and monthly_cost_limit_nanos <= 0)
        ):
            return False
        async with self._sessions() as session, session.begin():
            if session.get_bind().dialect.name == "sqlite":
                # SQLite has no row locks; acquire its writer lock before source reads.
                await session.connection(execution_options={"sqlite_write": True})
            observed = await session.get(ContentRewriteJobRow, job_id)
            if observed is None:
                return False
            request = self._request(observed)
            try:
                guest_id = guest_id_from_rewrite_owner(request.key.owner)
            except ValueError:
                guest_id = None  # Synthetic repository fixtures cannot pass execution_guard.
            if guest_id is not None:
                authority = await lock_rewrite_authority(session, request, guest_id)
                if (
                    authority is None
                    or authority.accepted_at > observed.created_at
                    or not await self._parent_exists(session, request, guest_id)
                ):
                    return False
            # Same lock order as execution/erasure: owner, parent, job, then budget.
            current = await session.scalar(
                select(ContentRewriteJobRow)
                .where(
                    self._lease_match(job_id, lease_token, deletion_epoch),
                    ContentRewriteJobRow.request_started_at.is_(None),
                    ContentRewriteJobRow.budget_reserved_tokens == 0,
                    ContentRewriteJobRow.budget_reserved_cost_nanos == 0,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if current is None:
                return False
            if not await _debit_spend_ledger(
                session,
                requested_tokens=requested_tokens,
                daily_token_limit=daily_token_limit,
                requested_cost_nanos=requested_cost_nanos,
                daily_cost_limit_nanos=daily_cost_limit_nanos,
                monthly_cost_limit_nanos=monthly_cost_limit_nanos,
                updated_at=updated_at,
            ):
                return False
            current.budget_reserved_tokens = requested_tokens
            current.budget_reserved_cost_nanos = requested_cost_nanos
            current.pricing_version = pricing_version
            current.updated_at = updated_at
            await session.flush([current])
            return True

    async def reserve_standalone_budget(
        self,
        *,
        requested_tokens: int,
        daily_token_limit: int,
        requested_cost_nanos: int,
        daily_cost_limit_nanos: int,
        monthly_cost_limit_nanos: int,
        updated_at: datetime,
    ) -> bool:
        """Debit the shared anonymous day/month ledger for out-of-queue synthetic work.

        Same limits, locks and non-refundable semantics as ``reserve_budget``, but no
        job row exists: used only by operator-run synthetic evaluations so their spend
        counts against the same caps as the worker. A monthly limit is mandatory.
        """

        if (
            requested_tokens <= 0
            or daily_token_limit <= 0
            or requested_cost_nanos <= 0
            or daily_cost_limit_nanos <= 0
            or monthly_cost_limit_nanos <= 0
        ):
            return False
        async with self._sessions() as session, session.begin():
            if session.get_bind().dialect.name == "sqlite":
                await session.connection(execution_options={"sqlite_write": True})
            return await _debit_spend_ledger(
                session,
                requested_tokens=requested_tokens,
                daily_token_limit=daily_token_limit,
                requested_cost_nanos=requested_cost_nanos,
                daily_cost_limit_nanos=daily_cost_limit_nanos,
                monthly_cost_limit_nanos=monthly_cost_limit_nanos,
                updated_at=updated_at,
            )

    def _row(self, record: RewriteJobRecord) -> ContentRewriteJobRow:
        request_ciphertext = self._envelope.encrypt(
            record.request.model_dump_json().encode(),
            context=self._context(record.id),
        )
        key = record.request.key
        parts = key.owner.key.split("|")
        parents: dict[str, UUID] = {}
        try:
            owner_guest_id = guest_id_from_rewrite_owner(key.owner)
            if key.owner.namespace == "readings":
                parents["reading_plan_id"] = UUID(parts[3] if parts[0] == "daily" else parts[4])
            elif key.owner.namespace == "tarot":
                parents["tarot_session_id"] = UUID(parts[2])
            elif key.owner.namespace == "radar":
                parents["radar_request_id"] = UUID(parts[2])
        except ValueError:
            # Repository-only test fixtures may use synthetic owners; execution fails closed.
            owner_guest_id = None
        return ContentRewriteJobRow(
            id=record.id,
            owner_guest_id=owner_guest_id,
            **parents,
            generation_key=key.cache_key,
            surface=key.surface.value,
            owner_namespace=key.owner.namespace,
            owner_fingerprint=owner_fingerprint(key.owner),
            authorization_fingerprint=authorization_fingerprint(
                record.request.authorization_receipt_id
            ),
            candidate_variant=key.candidate_variant,
            provider="openai",
            model=key.model_version,
            prompt_version=key.prompt_version,
            schema_version=key.schema_version,
            gate_version=key.gate_version,
            request_ciphertext=request_ciphertext,
            deletion_epoch=record.deletion_epoch,
            status=record.status.value,
            attempt_count=record.attempt_count,
            max_attempts=record.max_attempts,
            next_attempt_at=record.next_attempt_at,
            last_result=record.last_result.value if record.last_result else None,
            budget_reserved_tokens=0,
            budget_reserved_cost_nanos=0,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _request(self, row: ContentRewriteJobRow) -> RewriteRequestEnvelope:
        plaintext = self._envelope.decrypt(
            row.request_ciphertext,
            context=self._context(row.id),
        )
        return RewriteRequestEnvelope.model_validate_json(plaintext)

    def _record(self, row: ContentRewriteJobRow) -> RewriteJobRecord:
        return RewriteJobRecord(
            id=row.id,
            request=self._request(row),
            status=RewriteJobStatus(row.status),
            deletion_epoch=row.deletion_epoch,
            attempt_count=row.attempt_count,
            max_attempts=row.max_attempts,
            next_attempt_at=row.next_attempt_at,
            last_result=RewriteJobResult(row.last_result) if row.last_result else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _context(job_id: UUID) -> bytes:
        return f"content-rewrite-job:{job_id}".encode()

    @staticmethod
    def _lease_match(job_id: UUID, lease_token: UUID, deletion_epoch: UUID) -> ColumnElement[bool]:
        return and_(
            ContentRewriteJobRow.id == job_id,
            ContentRewriteJobRow.status == RewriteJobStatus.LEASED.value,
            ContentRewriteJobRow.lease_token == lease_token,
            ContentRewriteJobRow.deletion_epoch == deletion_epoch,
        )

    @staticmethod
    def _assert_same_request(stored: RewriteJobRecord, incoming: RewriteJobRecord) -> None:
        if stored.request != incoming.request or stored.max_attempts != incoming.max_attempts:
            raise ValueError("generation key collision with different rewrite request")


async def _debit_spend_ledger(
    session: AsyncSession,
    *,
    requested_tokens: int,
    daily_token_limit: int,
    requested_cost_nanos: int,
    daily_cost_limit_nanos: int,
    monthly_cost_limit_nanos: int | None,
    updated_at: datetime,
) -> bool:
    """Lock and debit the anonymous month then day rows; False leaves both untouched."""

    monthly = None
    if monthly_cost_limit_nanos is not None:
        month = updated_at.astimezone(UTC).strftime("%Y-%m")
        insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
        await session.execute(
            insert(ContentRewriteSpendMonthRow)
            .values(month=month, reserved_cost_nanos=0)
            .on_conflict_do_nothing(index_elements=["month"])
        )
        monthly = await session.scalar(
            select(ContentRewriteSpendMonthRow)
            .where(ContentRewriteSpendMonthRow.month == month)
            .with_for_update()
        )
        if monthly is None:
            return False
    day = updated_at.astimezone(UTC).strftime("%Y-%m-%d")
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    await session.execute(
        insert(ContentRewriteSpendDayRow)
        .values(day=day, reserved_cost_nanos=0, reserved_tokens=0)
        .on_conflict_do_nothing(index_elements=["day"])
    )
    daily = await session.scalar(
        select(ContentRewriteSpendDayRow)
        .where(ContentRewriteSpendDayRow.day == day)
        .with_for_update()
    )
    if daily is None:
        return False
    if daily.reserved_tokens + requested_tokens > daily_token_limit:
        return False
    if daily.reserved_cost_nanos + requested_cost_nanos > daily_cost_limit_nanos:
        return False
    if monthly is not None and monthly_cost_limit_nanos is not None:
        if monthly.reserved_cost_nanos + requested_cost_nanos > monthly_cost_limit_nanos:
            return False
        # Non-refundable worst-case debit: no owner identifiers, no deletion reset.
        monthly.reserved_cost_nanos += requested_cost_nanos
        await session.flush([monthly])
    # Anonymous, non-refundable debits survive deletion, cancellation and retries.
    daily.reserved_tokens += requested_tokens
    daily.reserved_cost_nanos += requested_cost_nanos
    await session.flush([daily])
    return True
