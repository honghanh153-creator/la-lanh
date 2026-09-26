import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select, text

from app.db.session import Database
from app.domains.astro.models import DateOnlySunResult, EngineProvenance, ZodiacSign
from app.domains.birth.tables import BirthProfileRow
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    GenerationAttemptRecord,
    GenerationAttemptResult,
    GenerationAttemptStatus,
    LeasedGenerationAttempt,
    ReadingPlan,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_gate_policy_version,
    canonical_generation_key,
    canonical_projection_scope_key,
    canonical_reading_plan_key,
    canonical_reading_revision_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.tables import ReadingGenerationAttemptRow
from app.domains.readings.worker import ReadingGenerationWorker
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider
from app.infrastructure.generation.base import (
    GenerationResult,
    GenerationSuccess,
    GenerationTransient,
)

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)


def _lease(*, attempt_count: int = 1, max_attempts: int = 2) -> LeasedGenerationAttempt:
    plan = ReadingPlanner().plan(
        DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=EngineProvenance(version="2.10.03", profile="test"),
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
    )
    plan_record = ReadingPlanRecord(
        id=uuid4(),
        guest_id=uuid4(),
        profile_id=uuid4(),
        plan_key=canonical_reading_plan_key(plan),
        plan=plan,
        created_at=NOW,
    )
    return LeasedGenerationAttempt(
        id=uuid4(),
        plan_record=plan_record,
        scope_key="s" * 64,
        generation_key="g" * 64,
        provider="openai",
        model="gpt-5.4-mini-2026-03-17",
        prompt_version="chart-synthesis-v1",
        deletion_epoch=uuid4(),
        lease_token=uuid4(),
        lease_expires_at=NOW + timedelta(minutes=1),
        attempt_count=attempt_count,
        max_attempts=max_attempts,
    )


class FakeRepository:
    def __init__(self, lease: LeasedGenerationAttempt, *, finalize: bool = True) -> None:
        self.lease = lease
        self.finalize = finalize
        self.events: list[str] = []
        self.retried = False
        self.failed = False

    async def lease_generation_attempt(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append("lease_committed")
        lease, self.lease = self.lease, None  # type: ignore[assignment]
        return lease

    async def mark_generation_request_started(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append("request_marker_committed")
        return True

    async def retry_generation_attempt(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append("retry_committed")
        self.retried = True
        return True

    async def fail_generation_attempt(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append("failure_committed")
        self.failed = True
        return True

    async def finalize_generation_success(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append("finalize_committed")
        return self.finalize


class FakeProvider:
    def __init__(self, result: GenerationResult) -> None:
        self.result = result
        self.calls = 0
        self.repository: FakeRepository | None = None

    async def generate(self, plan: ReadingPlan) -> GenerationResult:
        del plan
        assert self.repository is not None
        assert self.repository.events == ["lease_committed", "request_marker_committed"]
        self.repository.events.append("network")
        self.calls += 1
        return self.result


class ExplodingProvider:
    async def generate(self, plan: ReadingPlan) -> GenerationResult:
        del plan
        raise RuntimeError("provider payload must not be logged")


@pytest.mark.asyncio
async def test_worker_calls_network_after_marker_and_publishes_available() -> None:
    lease = _lease()
    candidate = (
        DeterministicVietnameseRenderer()
        .render(lease.plan_record.plan)
        .model_copy(update={"renderer_version": "openai-responses-v1"})
    )
    repository = FakeRepository(lease)
    provider = FakeProvider(GenerationSuccess(candidate=candidate))
    provider.repository = repository
    worker = ReadingGenerationWorker(repository, provider, clock=lambda: NOW)

    assert await worker.process_one() is True

    assert provider.calls == 1
    assert repository.events == [
        "lease_committed",
        "request_marker_committed",
        "network",
        "finalize_committed",
    ]
    assert repository.retried is False
    assert repository.failed is False


@pytest.mark.asyncio
async def test_worker_closes_unexpected_post_marker_failure_without_retry() -> None:
    repository = FakeRepository(_lease())

    worker = ReadingGenerationWorker(repository, ExplodingProvider(), clock=lambda: NOW)

    assert await worker.process_one()

    assert repository.failed is True
    assert repository.retried is False
    assert repository.events == [
        "lease_committed",
        "request_marker_committed",
        "failure_committed",
    ]


@pytest.mark.asyncio
async def test_worker_loop_recovers_after_iteration_failure(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FlakyRepository:
        def __init__(self) -> None:
            self.calls = 0

        async def lease_generation_attempt(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary database failure")
            return None

    sleeps = 0

    async def bounded_sleep(delay: float) -> None:
        nonlocal sleeps
        assert delay > 0
        sleeps += 1
        if sleeps == 2:
            raise asyncio.CancelledError

    repository = FlakyRepository()
    monkeypatch.setattr(asyncio, "sleep", bounded_sleep)
    worker = ReadingGenerationWorker(repository, ExplodingProvider())  # type: ignore[arg-type]

    with pytest.raises(asyncio.CancelledError):
        await worker.run_forever(poll_seconds=0.01)

    assert repository.calls == 2


@pytest.mark.asyncio
async def test_worker_owns_only_bounded_safe_retry() -> None:
    lease = _lease(attempt_count=1, max_attempts=2)
    repository = FakeRepository(lease)
    provider = FakeProvider(GenerationTransient(code="rate_limited", retry_safe=True))
    provider.repository = repository

    assert await ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()

    assert provider.calls == 1
    assert repository.retried is True
    assert repository.failed is False


@pytest.mark.asyncio
async def test_timeout_after_send_is_terminal_and_never_retried() -> None:
    lease = _lease(attempt_count=1, max_attempts=3)
    repository = FakeRepository(lease)
    provider = FakeProvider(GenerationTransient(code="timeout", retry_safe=False))
    provider.repository = repository

    assert await ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()

    assert provider.calls == 1
    assert repository.retried is False
    assert repository.failed is True


@pytest.mark.asyncio
async def test_late_worker_after_deletion_cannot_finalize() -> None:
    lease = _lease()
    candidate = (
        DeterministicVietnameseRenderer()
        .render(lease.plan_record.plan)
        .model_copy(update={"renderer_version": "openai-responses-v1"})
    )
    repository = FakeRepository(lease, finalize=False)
    provider = FakeProvider(GenerationSuccess(candidate=candidate))
    provider.repository = repository

    assert await ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()

    assert repository.events[-1] == "finalize_committed"
    assert repository.finalize is False
    assert repository.retried is False


def test_attempt_status_is_closed() -> None:
    assert {item.value for item in GenerationAttemptStatus} == {
        "pending",
        "leased",
        "retry_wait",
        "succeeded",
        "failed",
    }


@pytest.fixture
async def storage(tmp_path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    await database.initialize()
    repository = PostgresReadingRepository(
        database.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"w" * 32)),
    )
    try:
        yield database, repository
    finally:
        await database.dispose()


async def _queued_attempt(
    database: Database,
    repository: PostgresReadingRepository,
    *,
    prompt_version: str = "chart-synthesis-v1",
    max_attempts: int = 2,
) -> tuple[UUID, UUID, GenerationAttemptRecord, UUID]:
    guest_id = uuid4()
    profile_id = uuid4()
    async with database.sessions() as session, session.begin():
        guest = GuestSessionRow(
            id=guest_id,
            token_hash=uuid4().bytes + uuid4().bytes,
            csrf_hash=uuid4().bytes + uuid4().bytes,
            state="active",
            onboarding_status="birth_ready",
            created_at=NOW,
            last_active_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
        session.add(guest)
        await session.flush([guest])
        session.add(
            BirthProfileRow(
                id=profile_id,
                guest_id=guest_id,
                current_snapshot_id=None,
                profile_level=1,
                time_precision="unknown",
                created_at=NOW,
                updated_at=NOW,
            )
        )
    plan = ReadingPlanner().plan(
        DateOnlySunResult(
            status="certain",
            sign=ZodiacSign.PISCES,
            candidates=(ZodiacSign.PISCES,),
            provenance=EngineProvenance(version="2.10.03", profile="test"),
        ),
        purpose=ReadingPurpose.DAILY_NOTE,
    )
    plan_record, _ = await repository.save_or_replay_plan(
        ReadingPlanRecord(
            id=uuid4(),
            guest_id=guest_id,
            profile_id=profile_id,
            plan_key=canonical_reading_plan_key(plan),
            plan=plan,
            created_at=NOW,
        )
    )
    candidate = DeterministicVietnameseRenderer().render(plan)
    evaluation = evaluate_candidate(plan, candidate)
    gate_policy = canonical_gate_policy_version(evaluation)
    fallback, _ = await repository.save_or_replay_revision(
        ReadingRevisionRecord(
            id=uuid4(),
            guest_id=guest_id,
            profile_id=profile_id,
            plan_id=plan_record.id,
            revision_key=canonical_reading_revision_key(
                plan_key=plan_record.plan_key,
                source=ReadingRevisionSource.DETERMINISTIC,
                renderer_version=candidate.renderer_version,
                content_version="fallback-v1",
                schema_version=candidate.schema_version,
                rules_version=plan.rules_version,
                gate_policy_version=gate_policy,
            ),
            source=ReadingRevisionSource.DETERMINISTIC,
            renderer_version=candidate.renderer_version,
            content_version="fallback-v1",
            schema_version=candidate.schema_version,
            rules_version=plan.rules_version,
            gate_policy_version=gate_policy,
            evaluation=evaluation,
            created_at=NOW,
        )
    )
    scope_key = canonical_projection_scope_key(
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=plan.tradition,
        config_hash=plan.config_hash,
        local_date=NOW.date(),
        timezone_name="UTC",
        observed_at=NOW,
    )
    projection, _ = await repository.get_or_create_projection(
        ReadingProjectionRecord(
            id=uuid4(),
            guest_id=guest_id,
            profile_id=profile_id,
            scope_key=scope_key,
            purpose=ReadingPurpose.DAILY_NOTE,
            tradition=plan.tradition,
            config_hash=plan.config_hash,
            local_date=NOW.date(),
            timezone_name="UTC",
            observed_at=NOW,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    await repository.publish_available(guest_id, profile_id, scope_key, fallback.id)
    generation_key = canonical_generation_key(
        plan_key=plan_record.plan_key,
        scope_key=scope_key,
        provider="openai",
        model="gpt-5.4-mini-2026-03-17",
        prompt_version=prompt_version,
    )
    attempt, _ = await repository.enqueue_generation_attempt(
        GenerationAttemptRecord(
            id=uuid4(),
            guest_id=guest_id,
            profile_id=profile_id,
            plan_id=plan_record.id,
            scope_key=scope_key,
            generation_key=generation_key,
            provider="openai",
            model="gpt-5.4-mini-2026-03-17",
            prompt_version=prompt_version,
            deletion_epoch=uuid4(),
            max_attempts=max_attempts,
            next_attempt_at=NOW,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    return guest_id, profile_id, attempt, projection.id


@pytest.mark.asyncio
async def test_repository_recovers_only_a_lease_that_never_crossed_send_boundary(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    _, _, attempt, _ = await _queued_attempt(database, repository)

    first = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=30)
    assert first is not None and first.id == attempt.id
    recovered = await repository.lease_generation_attempt(
        now=NOW + timedelta(seconds=31), lease_for_seconds=30
    )

    assert recovered is not None and recovered.id == attempt.id
    assert recovered.attempt_count == 2
    assert recovered.lease_token != first.lease_token


@pytest.mark.asyncio
async def test_concurrent_lease_claim_has_one_winner(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    await _queued_attempt(database, repository)

    claims = await asyncio.gather(
        repository.lease_generation_attempt(now=NOW, lease_for_seconds=30),
        repository.lease_generation_attempt(now=NOW, lease_for_seconds=30),
    )

    assert sum(claim is not None for claim in claims) == 1


@pytest.mark.asyncio
async def test_expired_post_send_lease_is_failed_without_ambiguous_retry(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    await _queued_attempt(database, repository)
    lease = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=30)
    assert lease is not None
    assert await repository.mark_generation_request_started(
        attempt_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )

    assert (
        await repository.lease_generation_attempt(
            now=NOW + timedelta(seconds=31), lease_for_seconds=30
        )
        is None
    )
    async with database.sessions() as session:
        row = (
            await session.execute(
                text("SELECT status, last_result FROM reading_generation_attempts WHERE id = :id"),
                {"id": lease.id.hex},
            )
        ).one()
    assert row == (GenerationAttemptStatus.FAILED.value, GenerationAttemptResult.AMBIGUOUS.value)


@pytest.mark.asyncio
async def test_real_worker_cas_keeps_generated_candidate_available_not_active(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id, _, _ = await _queued_attempt(database, repository)
    lease_preview = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=30)
    assert lease_preview is not None
    # Return the unstarted lease to eligibility through expiry; no network boundary was crossed.
    candidate = (
        DeterministicVietnameseRenderer()
        .render(lease_preview.plan_record.plan)
        .model_copy(update={"renderer_version": "openai-responses-v1"})
    )
    provider = FakeProvider(GenerationSuccess(candidate=candidate))
    provider.repository = None

    class ProviderWithoutFakeEvents:
        async def generate(self, plan):  # type: ignore[no-untyped-def]
            return GenerationSuccess(candidate=candidate)

    worker = ReadingGenerationWorker(
        repository,
        ProviderWithoutFakeEvents(),
        lease_seconds=30,
        clock=lambda: NOW + timedelta(seconds=31),
    )
    assert await worker.process_one()

    async with database.sessions() as session:
        projection = (
            await session.execute(
                text(
                    "SELECT active_revision_id, available_revision_id "
                    "FROM reading_projections "
                    "WHERE guest_id = :guest_id AND profile_id = :profile_id"
                ),
                {"guest_id": guest_id.hex, "profile_id": profile_id.hex},
            )
        ).one()
        generated_count = await session.scalar(
            text("SELECT COUNT(*) FROM reading_revisions WHERE source = 'generated'")
        )
        attempt_status = await session.scalar(
            text("SELECT status FROM reading_generation_attempts")
        )
    assert projection.active_revision_id != projection.available_revision_id
    assert projection.available_revision_id is not None
    assert generated_count == 1
    assert attempt_status == GenerationAttemptStatus.SUCCEEDED.value
    assert (
        await repository.finalize_generation_success(
            lease=lease_preview,
            revision=cast(ReadingRevisionRecord, object()),
            completed_at=NOW + timedelta(seconds=32),
        )
        is False
    )


@pytest.mark.asyncio
async def test_real_late_worker_after_cascade_deletion_cannot_write(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)

    class DeletingProvider:
        async def generate(self, plan):  # type: ignore[no-untyped-def]
            async with database.sessions() as session, session.begin():
                await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest_id))
            candidate = (
                DeterministicVietnameseRenderer()
                .render(plan)
                .model_copy(update={"renderer_version": "openai-responses-v1"})
            )
            return GenerationSuccess(candidate=candidate)

    worker = ReadingGenerationWorker(repository, DeletingProvider(), clock=lambda: NOW)
    assert await worker.process_one()

    async with database.sessions() as session:
        counts = []
        for table in (
            "reading_plans",
            "reading_revisions",
            "reading_projections",
            "reading_generation_attempts",
        ):
            count = await session.scalar(
                text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - closed table list
            )
            counts.append(int(count or 0))
    assert tuple(counts) == (0, 0, 0, 0)


@pytest.mark.asyncio
async def test_completed_deletion_prevents_stale_lease_from_reaching_provider(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)
    lease = await repository.lease_generation_attempt(now=NOW, lease_for_seconds=30)
    assert lease is not None
    async with database.sessions() as session:
        token_hash = await session.scalar(
            select(GuestSessionRow.token_hash).where(GuestSessionRow.id == guest_id)
        )
    assert token_hash is not None
    assert await PostgresGuestRepository(database.sessions).delete_by_token_hash(token_hash, NOW)

    class StaleLeaseRepository(FakeRepository):
        async def mark_generation_request_started(self, **kwargs):  # type: ignore[no-untyped-def]
            self.events.append("request_marker_rejected")
            return await repository.mark_generation_request_started(**kwargs)

    stale_repository = StaleLeaseRepository(lease)
    provider = FakeProvider(GenerationTransient(code="should_not_run", retry_safe=False))
    provider.repository = stale_repository

    assert await ReadingGenerationWorker(
        stale_repository,
        provider,
        clock=lambda: NOW,
    ).process_one()
    assert provider.calls == 0
    assert stale_repository.events == ["lease_committed", "request_marker_rejected"]


@pytest.mark.asyncio
async def test_deletion_waits_for_an_already_started_provider_send(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)
    async with database.sessions() as session:
        token_hash = await session.scalar(
            select(GuestSessionRow.token_hash).where(GuestSessionRow.id == guest_id)
        )
    assert token_hash is not None

    entered_provider = asyncio.Event()
    release_provider = asyncio.Event()

    class BlockingProvider:
        async def generate(self, plan):  # type: ignore[no-untyped-def]
            entered_provider.set()
            await release_provider.wait()
            candidate = (
                DeterministicVietnameseRenderer()
                .render(plan)
                .model_copy(update={"renderer_version": "openai-responses-v1"})
            )
            return GenerationSuccess(candidate=candidate)

    worker_task = asyncio.create_task(
        ReadingGenerationWorker(repository, BlockingProvider(), clock=lambda: NOW).process_one()
    )
    await entered_provider.wait()
    deletion_task = asyncio.create_task(
        PostgresGuestRepository(database.sessions).delete_by_token_hash(token_hash, NOW)
    )
    await asyncio.sleep(0.01)
    assert deletion_task.done() is False

    release_provider.set()
    assert await worker_task is True
    assert await deletion_task is True

    async with database.sessions() as session:
        guest_count = await session.scalar(select(func.count()).select_from(GuestSessionRow))
        attempt_count = await session.scalar(
            select(func.count()).select_from(ReadingGenerationAttemptRow)
        )
    assert (guest_count, attempt_count) == (0, 0)
