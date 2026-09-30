from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content.models import (
    CONTENT_BUNDLE_KEY,
    ContentAuditAction,
    ContentAuditEvent,
    ContentChannel,
    ContentRevision,
    ContentRevisionStatus,
    ContentValidationReceipt,
    canonical_payload_hash,
)
from app.domains.content.tables import ContentAuditEventRow, ContentChannelRow, ContentRevisionRow


class ContentRevisionConflict(RuntimeError):
    pass


class ContentPublishConflict(RuntimeError):
    pass


class PostgresContentRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get_channel(self, bundle_key: str = CONTENT_BUNDLE_KEY) -> ContentChannel:
        async with self._sessions() as session, session.begin():
            row = await session.get(ContentChannelRow, bundle_key)
            if row is None:
                now = datetime.now(UTC)
                row = ContentChannelRow(bundle_key=bundle_key, generation=0, updated_at=now)
                session.add(row)
                await session.flush([row])
            return _channel(row)

    async def get_revision(self, revision_id: UUID) -> ContentRevision | None:
        async with self._sessions() as session:
            row = await session.get(ContentRevisionRow, revision_id)
            return _revision(row) if row is not None else None

    async def list_revisions(
        self, bundle_key: str = CONTENT_BUNDLE_KEY
    ) -> tuple[ContentRevision, ...]:
        async with self._sessions() as session:
            rows = (
                await session.execute(
                    select(ContentRevisionRow)
                    .where(ContentRevisionRow.bundle_key == bundle_key)
                    .order_by(ContentRevisionRow.created_at.desc())
                    .limit(50)
                )
            ).scalars()
            return tuple(_revision(row) for row in rows)

    async def create_draft(
        self,
        payload: dict[str, object],
        *,
        parent_revision_id: UUID | None,
        request_key: str,
        reason: str,
        created_at: datetime | None = None,
    ) -> ContentRevision:
        now = created_at or datetime.now(UTC)
        payload_hash = canonical_payload_hash(payload)
        async with self._sessions() as session, session.begin():
            replay = await _event_by_request_key(session, request_key)
            if replay is not None:
                if replay.action != ContentAuditAction.DRAFT_CREATED.value:
                    raise ContentRevisionConflict("idempotency key belongs to another action")
                replayed_revision = await session.get(ContentRevisionRow, replay.revision_id)
                if replayed_revision is None or replayed_revision.payload_hash != payload_hash:
                    raise ContentRevisionConflict("idempotency key belongs to another payload")
                return _revision(replayed_revision)
            existing = (
                await session.execute(
                    select(ContentRevisionRow).where(
                        ContentRevisionRow.payload_hash == payload_hash
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                return _revision(existing)
            channel = await _channel_row(session)
            row = ContentRevisionRow(
                id=uuid4(),
                bundle_key=CONTENT_BUNDLE_KEY,
                contract_version="daily-content-matrix/v1",
                parent_revision_id=parent_revision_id,
                status=ContentRevisionStatus.DRAFT.value,
                payload=payload,
                payload_hash=payload_hash,
                validation=None,
                created_at=now,
            )
            session.add(row)
            await session.flush([row])
            session.add(
                _event_row(
                    action=ContentAuditAction.DRAFT_CREATED,
                    revision_id=row.id,
                    previous_revision_id=parent_revision_id,
                    generation=channel.generation,
                    request_key=request_key,
                    reason=reason,
                    created_at=now,
                )
            )
            return _revision(row)

    async def record_validation(
        self,
        revision_id: UUID,
        receipt: ContentValidationReceipt,
        *,
        request_key: str,
        reason: str,
        created_at: datetime | None = None,
    ) -> ContentRevision:
        now = created_at or datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            row = await session.get(ContentRevisionRow, revision_id)
            if row is None:
                raise ContentRevisionConflict("content revision does not exist")
            replay = await _event_by_request_key(session, request_key)
            if replay is not None:
                if (
                    replay.action != ContentAuditAction.VALIDATED.value
                    or replay.revision_id != revision_id
                ):
                    raise ContentRevisionConflict("idempotency key belongs to another validation")
                return _revision(row)
            if row.payload_hash != receipt.payload_hash:
                raise ContentRevisionConflict("validation receipt is stale")
            if not receipt.passed:
                return _revision(row)
            if row.status != ContentRevisionStatus.PUBLISHED.value:
                row.status = ContentRevisionStatus.VALIDATED.value
            row.validation = receipt.model_dump(mode="json")
            channel = await _channel_row(session)
            session.add(
                _event_row(
                    action=ContentAuditAction.VALIDATED,
                    revision_id=row.id,
                    previous_revision_id=row.parent_revision_id,
                    generation=channel.generation,
                    request_key=request_key,
                    reason=reason,
                    created_at=now,
                )
            )
            await session.flush([row])
            return _revision(row)

    async def activate(
        self,
        revision_id: UUID,
        *,
        expected_generation: int,
        request_key: str,
        reason: str,
        rollback: bool = False,
        created_at: datetime | None = None,
    ) -> tuple[ContentRevision, ContentChannel]:
        now = created_at or datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            replay = await _event_by_request_key(session, request_key)
            if replay is not None:
                expected_action = (
                    ContentAuditAction.ROLLED_BACK if rollback else ContentAuditAction.PUBLISHED
                )
                revision = await session.get(ContentRevisionRow, revision_id)
                channel = await _channel_row(session)
                if (
                    replay.action != expected_action.value
                    or replay.revision_id != revision_id
                    or revision is None
                    or channel.active_revision_id != revision_id
                    or channel.generation != replay.channel_generation
                ):
                    raise ContentPublishConflict("idempotency key belongs to another activation")
                return _revision(revision), _channel(channel)
            revision = await session.get(ContentRevisionRow, revision_id)
            if revision is None or revision.validation is None:
                raise ContentPublishConflict("revision is not validated")
            receipt = ContentValidationReceipt.model_validate(revision.validation)
            if not receipt.passed or receipt.payload_hash != revision.payload_hash:
                raise ContentPublishConflict("validation receipt is invalid")
            channel = await _channel_row(session)
            previous = channel.active_revision_id
            if rollback:
                prior_activation = (
                    await session.execute(
                        select(ContentAuditEventRow.id)
                        .where(
                            ContentAuditEventRow.revision_id == revision.id,
                            ContentAuditEventRow.action.in_(
                                (
                                    ContentAuditAction.PUBLISHED.value,
                                    ContentAuditAction.ROLLED_BACK.value,
                                )
                            ),
                        )
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if prior_activation is None:
                    raise ContentPublishConflict("rollback target has never been an active release")
            elif revision.parent_revision_id != previous:
                raise ContentPublishConflict(
                    "draft parent is not the current active content release"
                )
            result = await session.execute(
                update(ContentChannelRow)
                .where(
                    ContentChannelRow.bundle_key == CONTENT_BUNDLE_KEY,
                    ContentChannelRow.generation == expected_generation,
                )
                .values(
                    active_revision_id=revision.id,
                    generation=expected_generation + 1,
                    updated_at=now,
                )
            )
            if cast(CursorResult[object], result).rowcount != 1:
                raise ContentPublishConflict("content channel changed; refresh before publishing")
            revision.status = ContentRevisionStatus.PUBLISHED.value
            session.add(
                _event_row(
                    action=(
                        ContentAuditAction.ROLLED_BACK if rollback else ContentAuditAction.PUBLISHED
                    ),
                    revision_id=revision.id,
                    previous_revision_id=previous,
                    generation=expected_generation + 1,
                    request_key=request_key,
                    reason=reason,
                    created_at=now,
                )
            )
            await session.flush([revision])
            refreshed = await session.get(ContentChannelRow, CONTENT_BUNDLE_KEY)
            if refreshed is None:  # pragma: no cover - created in this transaction.
                raise RuntimeError("content channel disappeared")
            return _revision(revision), _channel(refreshed)

    async def list_events(self) -> tuple[ContentAuditEvent, ...]:
        async with self._sessions() as session:
            rows = (
                await session.execute(
                    select(ContentAuditEventRow)
                    .where(ContentAuditEventRow.bundle_key == CONTENT_BUNDLE_KEY)
                    .order_by(ContentAuditEventRow.created_at.desc())
                    .limit(100)
                )
            ).scalars()
            return tuple(_event(row) for row in rows)


async def _channel_row(session: AsyncSession) -> ContentChannelRow:
    row = await session.get(ContentChannelRow, CONTENT_BUNDLE_KEY)
    if row is None:
        values = {
            "bundle_key": CONTENT_BUNDLE_KEY,
            "generation": 0,
            "updated_at": datetime.now(UTC),
        }
        dialect_name = session.get_bind().dialect.name
        if dialect_name == "postgresql":
            postgres_statement = postgresql_insert(ContentChannelRow).values(**values)
            await session.execute(
                postgres_statement.on_conflict_do_nothing(index_elements=["bundle_key"])
            )
        elif dialect_name == "sqlite":
            sqlite_statement = sqlite_insert(ContentChannelRow).values(**values)
            await session.execute(
                sqlite_statement.on_conflict_do_nothing(index_elements=["bundle_key"])
            )
        else:  # pragma: no cover - supported runtime databases are PostgreSQL and SQLite.
            session.add(ContentChannelRow(**values))
            await session.flush()
        row = await session.get(ContentChannelRow, CONTENT_BUNDLE_KEY)
        if row is None:  # pragma: no cover - an upsert followed by a primary-key read is closed.
            raise RuntimeError("content channel could not be initialized")
    return row


async def _event_by_request_key(
    session: AsyncSession, request_key: str
) -> ContentAuditEventRow | None:
    request_key_hash = sha256(request_key.encode()).hexdigest()
    return (
        await session.execute(
            select(ContentAuditEventRow).where(
                ContentAuditEventRow.request_key_hash == request_key_hash
            )
        )
    ).scalar_one_or_none()


def _revision(row: ContentRevisionRow) -> ContentRevision:
    validation = (
        ContentValidationReceipt.model_validate(row.validation)
        if row.validation is not None
        else None
    )
    return ContentRevision(
        id=row.id,
        bundle_key=row.bundle_key,
        contract_version=row.contract_version,
        parent_revision_id=row.parent_revision_id,
        status=ContentRevisionStatus(row.status),
        payload=row.payload,
        payload_hash=row.payload_hash,
        validation=validation,
        created_at=row.created_at,
    )


def _channel(row: ContentChannelRow) -> ContentChannel:
    return ContentChannel(
        bundle_key=row.bundle_key,
        active_revision_id=row.active_revision_id,
        generation=row.generation,
        updated_at=row.updated_at,
    )


def _event_row(
    *,
    action: ContentAuditAction,
    revision_id: UUID,
    previous_revision_id: UUID | None,
    generation: int,
    request_key: str,
    reason: str,
    created_at: datetime,
) -> ContentAuditEventRow:
    return ContentAuditEventRow(
        id=uuid4(),
        bundle_key=CONTENT_BUNDLE_KEY,
        request_key_hash=sha256(request_key.encode()).hexdigest(),
        action=action.value,
        revision_id=revision_id,
        previous_revision_id=previous_revision_id,
        channel_generation=generation,
        reason=reason,
        created_at=created_at,
    )


def _event(row: ContentAuditEventRow) -> ContentAuditEvent:
    return ContentAuditEvent(
        id=row.id,
        request_key_hash=row.request_key_hash,
        action=ContentAuditAction(row.action),
        revision_id=row.revision_id,
        previous_revision_id=row.previous_revision_id,
        channel_generation=row.channel_generation,
        reason=row.reason,
        created_at=row.created_at,
    )
