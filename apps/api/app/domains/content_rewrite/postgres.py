from __future__ import annotations

import json
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

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
from app.domains.content_rewrite.tables import ContentRewriteJobRow
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

    async def enqueue(self, record: RewriteJobRecord) -> tuple[RewriteJobRecord, bool]:
        if record.status is not RewriteJobStatus.PENDING or record.attempt_count != 0:
            raise ValueError("new rewrite jobs must be pending and unattempted")
        async with self._sessions() as session, session.begin():
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
            await session.execute(
                update(ContentRewriteJobRow)
                .where(
                    ContentRewriteJobRow.status == RewriteJobStatus.LEASED.value,
                    ContentRewriteJobRow.lease_expires_at <= now,
                    ContentRewriteJobRow.request_started_at.is_not(None),
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
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(job_id, lease_token, deletion_epoch))
                .where(ContentRewriteJobRow.request_started_at.is_(None))
                .values(request_started_at=started_at, updated_at=started_at)
            )
            return cast(CursorResult[Any], result).rowcount == 1

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
        async with self._sessions() as session, session.begin():
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
        async with self._sessions() as session, session.begin():
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
        async with self._sessions() as session, session.begin():
            updated = await session.execute(
                update(ContentRewriteJobRow)
                .where(self._lease_match(lease.id, lease.lease_token, lease.deletion_epoch))
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
    ) -> bool:
        if (
            requested_tokens <= 0
            or daily_token_limit <= 0
            or requested_cost_nanos <= 0
            or daily_cost_limit_nanos <= 0
            or not pricing_version
        ):
            return False
        async with self._sessions() as session, session.begin():
            rows = tuple(
                await session.scalars(
                    select(ContentRewriteJobRow)
                    .where(ContentRewriteJobRow.updated_at >= since)
                    .with_for_update()
                )
            )
            current = next(
                (
                    row
                    for row in rows
                    if row.id == job_id
                    and row.status == RewriteJobStatus.LEASED.value
                    and row.lease_token == lease_token
                    and row.deletion_epoch == deletion_epoch
                    and row.request_started_at is None
                ),
                None,
            )
            if current is None:
                return False
            spent = sum((row.input_tokens or 0) + (row.output_tokens or 0) for row in rows)
            reserved = sum(
                row.budget_reserved_tokens
                for row in rows
                if row.id != job_id and row.status == RewriteJobStatus.LEASED.value
            )
            cost_spent = sum(row.cost_nanos or 0 for row in rows)
            cost_reserved = sum(
                row.budget_reserved_cost_nanos
                for row in rows
                if row.id != job_id and row.status == RewriteJobStatus.LEASED.value
            )
            if spent + reserved + requested_tokens > daily_token_limit:
                return False
            if cost_spent + cost_reserved + requested_cost_nanos > daily_cost_limit_nanos:
                return False
            current.budget_reserved_tokens = requested_tokens
            current.budget_reserved_cost_nanos = requested_cost_nanos
            current.pricing_version = pricing_version
            current.updated_at = updated_at
            await session.flush([current])
            return True

    def _row(self, record: RewriteJobRecord) -> ContentRewriteJobRow:
        request_ciphertext = self._envelope.encrypt(
            record.request.model_dump_json().encode(),
            context=self._context(record.id),
        )
        key = record.request.key
        return ContentRewriteJobRow(
            id=record.id,
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
