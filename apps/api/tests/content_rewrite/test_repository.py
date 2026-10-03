from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.session import Database
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteJobRecord,
    RewriteJobResult,
    RewriteJobStatus,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.service import ContentRewriteService
from app.domains.content_rewrite.tables import ContentRewriteJobRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


class Authorization:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool:
        del request
        return self.allowed


def _request(*, owner_key: str = "daily:anonymous") -> RewriteRequestEnvelope:
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.DAILY_HOME,
            owner=ArtifactOwnerKey(namespace="readings", key=owner_key),
            blueprint_hash="a" * 64,
            model_version="gpt-6-luna",
            prompt_version="surface-rewrite-v1",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
        ),
        authorization_receipt_id="consent-receipt",
        safe_payload={
            "context": "relationships",
            "scene_key": "psychology:missing-context:relationships",
            "action_key": "psychology:ask-one-clear-question",
            "requirements": [
                {
                    "key": "daily.missing-context",
                    "section": "manifestation",
                    "markers": ["tin nhắn", "chưa rõ"],
                    "min_matches": 1,
                }
            ],
            "evidence": [
                {
                    "label": "factor_1",
                    "source": "natal",
                    "kind": "planet_placement",
                    "domain": "communication",
                    "role": "primary",
                    "confidence": "high",
                    "labels": [{"name": "sign", "value": "Song Ngư"}],
                }
            ],
        },
    )


def _record(*, owner_key: str = "daily:anonymous") -> RewriteJobRecord:
    return RewriteJobRecord(
        id=uuid4(),
        request=_request(owner_key=owner_key),
        deletion_epoch=uuid4(),
        next_attempt_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
async def storage(tmp_path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'rewrite.db'}")
    await database.initialize()
    repository = PostgresContentRewriteRepository(
        database.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32)),
    )
    try:
        yield database, repository
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_enqueue_is_idempotent_and_stores_only_encrypted_request(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    record = _record()

    stored, replayed = await repository.enqueue(record)
    replay, replayed_again = await repository.enqueue(_record())

    assert replayed is False
    assert replayed_again is True
    assert replay.id == stored.id
    async with database.sessions() as session:
        row = await session.scalar(select(ContentRewriteJobRow))
        assert row is not None
        assert "missing-context" not in row.request_ciphertext
        assert "consent-receipt" not in row.request_ciphertext
        assert row.owner_fingerprint != record.request.key.owner.key


@pytest.mark.asyncio
async def test_lease_is_single_and_expired_sent_job_becomes_ambiguous(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    await repository.enqueue(_record())

    lease = await repository.lease(now=NOW, lease_for_seconds=30)
    assert lease is not None
    assert await repository.lease(now=NOW, lease_for_seconds=30) is None
    assert await repository.mark_request_started(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )

    assert await repository.lease(now=NOW + timedelta(seconds=31), lease_for_seconds=30) is None
    async with database.sessions() as session:
        row = await session.get(ContentRewriteJobRow, lease.id)
        assert row is not None
        assert row.status == RewriteJobStatus.FAILED.value
        assert row.last_result == RewriteJobResult.AMBIGUOUS.value


@pytest.mark.asyncio
async def test_owner_purge_is_idempotent_and_invalidates_stale_lease(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    record = _record(owner_key="daily:owner-1")
    await repository.enqueue(record)
    lease = await repository.lease(now=NOW, lease_for_seconds=30)
    assert lease is not None

    assert await repository.cancel_and_purge_owner(record.request.key.owner) == 1
    assert await repository.cancel_and_purge_owner(record.request.key.owner) == 0
    assert not await repository.succeed(
        lease=lease,
        gate_receipt_id="gate-receipt",
        output_fingerprint="f" * 64,
        completed_at=NOW,
    )


@pytest.mark.asyncio
async def test_service_checks_authorization_before_enqueue(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage

    with pytest.raises(PermissionError):
        await ContentRewriteService(repository, Authorization(False)).enqueue(
            _request(),
            now=NOW,
        )

    async with database.sessions() as session:
        assert await session.scalar(select(ContentRewriteJobRow)) is None

    stored, replayed = await ContentRewriteService(repository, Authorization(True)).enqueue(
        _request(),
        now=NOW,
    )
    assert replayed is False
    assert stored.request.safe_payload["scene_key"] == "psychology:missing-context:relationships"
