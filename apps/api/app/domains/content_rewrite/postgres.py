from __future__ import annotations

import json
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, select, update
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
)
from app.domains.content_rewrite.tables import ContentRewriteJobRow
from app.infrastructure.crypto import EnvelopeCipher


def owner_fingerprint(owner: ArtifactOwnerKey) -> str:
    return sha256(f"{owner.namespace}\x00{owner.key}".encode()).hexdigest()


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
    ) -> bool:
        async with self._sessions() as session, session.begin():
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
                    updated_at=updated_at,
                )
            )
            return cast(CursorResult[Any], updated).rowcount == 1

    async def succeed(
        self,
        *,
        lease: LeasedRewriteJob,
        gate_receipt_id: str,
        output_fingerprint: str,
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
