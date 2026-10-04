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
            "title_meaning": "Chưa rõ thì chưa cần kết luận.",
            "scene_meaning": "Một tin nhắn ngắn khiến ý của người kia chưa rõ.",
            "action_meaning": "Hỏi lại một câu rõ ràng trước khi kết luận.",
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
    assert await repository.reserve_budget(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        since=NOW.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=700,
        daily_token_limit=1_000,
        requested_cost_nanos=700_000,
        daily_cost_limit_nanos=1_000_000,
        pricing_version="test-price-v1",
        updated_at=NOW,
    )
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
        assert row.input_tokens == 700
        assert row.cost_nanos == 700_000
        assert row.budget_reserved_tokens == 0
        assert row.budget_reserved_cost_nanos == 0


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
        input_tokens=100,
        output_tokens=20,
        cost_nanos=20_000,
        completed_at=NOW,
    )


@pytest.mark.asyncio
async def test_authorization_revocation_purges_every_linked_job(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    first = _record(owner_key="daily:owner-1")
    second = _record(owner_key="daily:owner-2")
    await repository.enqueue(first)
    await repository.enqueue(second)

    assert await repository.cancel_and_purge_authorization("consent-receipt") == 2
    assert await repository.cancel_and_purge_authorization("consent-receipt") == 0


@pytest.mark.asyncio
async def test_success_persists_aggregate_usage_without_payload(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    await repository.enqueue(_record())
    lease = await repository.lease(now=NOW, lease_for_seconds=30)
    assert lease is not None
    assert await repository.mark_request_started(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )

    assert await repository.succeed(
        lease=lease,
        gate_receipt_id="gate-receipt",
        output_fingerprint="f" * 64,
        input_tokens=321,
        output_tokens=87,
        cost_nanos=75_600,
        completed_at=NOW,
    )

    assert await repository.tokens_used_since(NOW - timedelta(minutes=1)) == 408
    assert await repository.cost_used_since(NOW - timedelta(minutes=1)) == 75_600
    item = (await repository.list_review_records())[0]
    assert item.input_tokens == 321
    assert item.output_tokens == 87
    assert item.cost_nanos == 75_600


@pytest.mark.asyncio
async def test_budget_reservation_counts_in_flight_jobs_and_releases_on_success(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    await repository.enqueue(_record(owner_key="daily:owner-1"))
    second = _record(owner_key="daily:owner-2")
    second = second.model_copy(
        update={
            "request": second.request.model_copy(
                update={"key": second.request.key.model_copy(update={"blueprint_hash": "b" * 64})}
            )
        }
    )
    await repository.enqueue(second)

    first_lease = await repository.lease(now=NOW, lease_for_seconds=30)
    second_lease = await repository.lease(now=NOW, lease_for_seconds=30)
    assert first_lease is not None
    assert second_lease is not None
    assert await repository.reserve_budget(
        job_id=first_lease.id,
        lease_token=first_lease.lease_token,
        deletion_epoch=first_lease.deletion_epoch,
        since=NOW.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=700,
        daily_token_limit=1_000,
        requested_cost_nanos=700_000,
        daily_cost_limit_nanos=1_000_000,
        pricing_version="test-price-v1",
        updated_at=NOW,
    )
    assert not await repository.reserve_budget(
        job_id=second_lease.id,
        lease_token=second_lease.lease_token,
        deletion_epoch=second_lease.deletion_epoch,
        since=NOW.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=400,
        daily_token_limit=1_000,
        requested_cost_nanos=400_000,
        daily_cost_limit_nanos=1_000_000,
        pricing_version="test-price-v1",
        updated_at=NOW,
    )

    assert await repository.succeed(
        lease=first_lease,
        gate_receipt_id="gate-receipt",
        output_fingerprint="f" * 64,
        input_tokens=500,
        output_tokens=100,
        cost_nanos=600_000,
        completed_at=NOW,
    )
    assert await repository.reserve_budget(
        job_id=second_lease.id,
        lease_token=second_lease.lease_token,
        deletion_epoch=second_lease.deletion_epoch,
        since=NOW.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=400,
        daily_token_limit=1_000,
        requested_cost_nanos=400_000,
        daily_cost_limit_nanos=1_000_000,
        pricing_version="test-price-v1",
        updated_at=NOW,
    )


@pytest.mark.asyncio
async def test_ambiguous_sent_request_consumes_its_conservative_reservation(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    await repository.enqueue(_record())
    lease = await repository.lease(now=NOW, lease_for_seconds=30)
    assert lease is not None
    assert await repository.reserve_budget(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        since=NOW.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=700,
        daily_token_limit=1_000,
        requested_cost_nanos=700_000,
        daily_cost_limit_nanos=1_000_000,
        pricing_version="test-price-v1",
        updated_at=NOW,
    )
    assert await repository.mark_request_started(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )
    assert await repository.fail(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        result=RewriteJobResult.AMBIGUOUS,
        updated_at=NOW,
    )

    assert await repository.tokens_used_since(NOW - timedelta(minutes=1)) == 700
    assert await repository.cost_used_since(NOW - timedelta(minutes=1)) == 700_000


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


@pytest.mark.asyncio
async def test_review_queue_exposes_metadata_without_owner_or_payload(storage) -> None:  # type: ignore[no-untyped-def]
    _database, repository = storage
    record = _record(owner_key="daily:private-owner")
    await repository.enqueue(record)

    items = await repository.list_review_records()

    assert len(items) == 1
    item = items[0]
    assert item.id == record.id
    assert item.surface is RewriteSurface.DAILY_HOME
    serialized = item.model_dump_json()
    assert "private-owner" not in serialized
    assert "scene_meaning" not in serialized
    assert "consent-receipt" not in serialized
