import asyncio
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import aiosqlite
import pytest
from sqlalchemy import delete, event, func, select, text

from app.db.session import Database
from app.domains.astro.models import DateOnlySunResult, EngineProvenance, ZodiacSign
from app.domains.birth.tables import BirthProfileRow
from app.domains.content_rewrite.send_fence import pending_sends
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


# Codex r36: on local SQLite a deferred transaction that has read cannot upgrade to a write while
# another connection holds the write lock; SQLite answers SQLITE_BUSY at once (no busy wait) to
# avoid deadlock. Guest deletion takes the write lock up front (BEGIN IMMEDIATE), so a worker
# transaction that read before deletion locked and wrote after failed with "database is locked".
# These tests pin both orders with barriers inside the real deletion transaction. They release a
# barrier only after SQLite itself reports that the other side's BEGIN IMMEDIATE arrived while the
# write lock was held (Codex r41: a signal from SQLAlchemy's cursor events fires before aiosqlite
# has even created the cursor, so it cannot show that the request reached SQLite).


async def _observed(signal: asyncio.Event) -> None:
    # A bound for failing, never for ordering: on code without the write lock up front the
    # expected request never comes, and the test should fail rather than hang.
    await asyncio.wait_for(signal.wait(), 10)


def _write_lock_held_elsewhere(connection: sqlite3.Connection) -> bool:
    """Ask SQLite, on its own thread, whether another connection holds the write lock now.

    Tries BEGIN IMMEDIATE with a zero busy timeout: SQLITE_BUSY means it is held elsewhere. A
    successful try is rolled back at once, so the real statement starts from the same state.
    """
    timeout = int(connection.execute("PRAGMA busy_timeout").fetchone()[0])
    connection.execute("PRAGMA busy_timeout = 0")
    try:
        connection.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as error:
        if "database is locked" not in str(error):
            raise
        return True
    else:
        connection.execute("ROLLBACK")
        return False
    finally:
        connection.execute(f"PRAGMA busy_timeout = {timeout}")


@dataclass
class _LockRequest:
    loop: asyncio.AbstractEventLoop
    entered: asyncio.Event = field(default_factory=asyncio.Event)
    acquired: asyncio.Event = field(default_factory=asyncio.Event)
    contended: bool | None = None

    def _enter(self, contended: bool) -> None:
        self.contended = contended
        self.entered.set()

    def wrap(self, execute: Callable[..., Any]) -> Callable[..., Any]:
        # Runs on aiosqlite's thread, after the cursor exists, immediately before sqlite3 executes.
        def run(*args: Any, **kwargs: Any) -> Any:
            connection = cast(sqlite3.Cursor, execute.__self__).connection  # type: ignore[attr-defined]
            self.loop.call_soon_threadsafe(self._enter, _write_lock_held_elsewhere(connection))
            result = execute(*args, **kwargs)
            self.loop.call_soon_threadsafe(self.acquired.set)
            return result

        return run


class _WriteLockProbe:
    """Observes a task's next BEGIN IMMEDIATE where aiosqlite hands it to SQLite.

    The task is identified on the event loop when aiosqlite queues the statement; the check and
    the signals then run on aiosqlite's thread around the real sqlite3 call. `entered` with
    `contended=True` and no `acquired` means the request reached SQLite while another connection
    held the write lock, and the task is waiting for it.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._armed: dict[asyncio.Task[Any], _LockRequest] = {}
        original = cast(Callable[..., Awaitable[Any]], aiosqlite.Connection._execute)
        armed = self._armed

        async def execute(
            connection: aiosqlite.Connection, fn: Any, *args: Any, **kwargs: Any
        ) -> Any:
            task = asyncio.current_task()
            request = armed.get(task) if task is not None else None
            if request is not None and args and args[0] == "BEGIN IMMEDIATE":
                del armed[task]  # type: ignore[arg-type]
                fn = request.wrap(fn)
            return await original(connection, fn, *args, **kwargs)

        monkeypatch.setattr(aiosqlite.Connection, "_execute", execute)

    def arm(self, task: asyncio.Task[Any]) -> _LockRequest:
        request = _LockRequest(asyncio.get_running_loop())
        self._armed[task] = request
        return request


def _hold_deletion_inside_its_write_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[asyncio.Event, asyncio.Event]:
    holding = asyncio.Event()
    release = asyncio.Event()

    async def paused(*args: Any, **kwargs: Any) -> Any:
        holding.set()
        await release.wait()
        return await pending_sends(*args, **kwargs)

    monkeypatch.setattr("app.domains.guest.postgres.pending_sends", paused)
    return holding, release


class _GateProvider:
    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def generate(self, plan):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.entered.set()
        await self.release.wait()
        candidate = (
            DeterministicVietnameseRenderer()
            .render(plan)
            .model_copy(update={"renderer_version": "openai-responses-v1"})
        )
        return GenerationSuccess(candidate=candidate)


async def _token_hash(database: Database, guest_id: UUID) -> bytes:
    async with database.sessions() as session:
        token_hash = await session.scalar(
            select(GuestSessionRow.token_hash).where(GuestSessionRow.id == guest_id)
        )
    assert token_hash is not None
    return token_hash


async def _counts(database: Database) -> tuple[int, int]:
    async with database.sessions() as session:
        guests = await session.scalar(select(func.count()).select_from(GuestSessionRow))
        attempts = await session.scalar(
            select(func.count()).select_from(ReadingGenerationAttemptRow)
        )
    return int(guests or 0), int(attempts or 0)


async def test_finalize_that_read_before_deletion_locked_still_commits(  # type: ignore[no-untyped-def]
    storage, monkeypatch
) -> None:
    # Order A: the worker's finalize has started reading when deletion takes the write lock.
    import app.domains.readings.postgres as readings_postgres

    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)
    token_hash = await _token_hash(database, guest_id)
    holding, release_deletion = _hold_deletion_inside_its_write_transaction(monkeypatch)
    provider = _GateProvider()
    probe = _WriteLockProbe(monkeypatch)
    deletion: list[asyncio.Task[bool]] = []
    deletion_pending: list[bool] = []
    original_find_plan = readings_postgres._find_plan
    armed = asyncio.Event()

    async def find_plan_then_let_deletion_lock(*args):  # type: ignore[no-untyped-def]
        if armed.is_set() and not deletion:
            task = asyncio.create_task(
                PostgresGuestRepository(database.sessions).delete_by_token_hash(token_hash, NOW)
            )
            deletion.append(task)
            request = probe.arm(task)
            if finalize.acquired.is_set():
                # Finalize already holds the write lock: deletion must queue behind it.
                await _observed(request.entered)
                deletion_pending.append(request.contended is True and not request.acquired.is_set())
            else:
                # Finalize read without the lock: let deletion take it before finalize writes.
                await _observed(holding)
        return await original_find_plan(*args)

    monkeypatch.setattr(readings_postgres, "_find_plan", find_plan_then_let_deletion_lock)
    worker = asyncio.create_task(
        ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()
    )
    await provider.entered.wait()
    finalize = probe.arm(worker)
    armed.set()
    provider.release.set()
    worker_result = list(await asyncio.gather(worker, return_exceptions=True))
    release_deletion.set()
    assert worker_result == [True]
    assert deletion_pending == [True]
    assert await deletion[0] is True
    assert await _counts(database) == (0, 0)


async def test_finalize_waits_for_a_deletion_that_already_holds_the_write_lock(  # type: ignore[no-untyped-def]
    storage, monkeypatch
) -> None:
    # Order B: deletion holds the write lock before the worker finalizes its started send.
    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)
    token_hash = await _token_hash(database, guest_id)
    holding, release_deletion = _hold_deletion_inside_its_write_transaction(monkeypatch)
    provider = _GateProvider()
    probe = _WriteLockProbe(monkeypatch)
    worker = asyncio.create_task(
        ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()
    )
    await provider.entered.wait()
    deletion = asyncio.create_task(
        PostgresGuestRepository(database.sessions).delete_by_token_hash(token_hash, NOW)
    )
    await holding.wait()
    finalize = probe.arm(worker)
    provider.release.set()
    # Released only once finalize's BEGIN IMMEDIATE reached SQLite while deletion held the lock.
    await _observed(finalize.entered)
    assert finalize.contended is True
    assert finalize.acquired.is_set() is False
    assert deletion.done() is False
    release_deletion.set()
    assert list(await asyncio.gather(worker, return_exceptions=True)) == [True]
    assert await deletion is True
    assert await _counts(database) == (0, 0)


async def test_send_fence_waits_for_deletion_and_then_never_sends(  # type: ignore[no-untyped-def]
    storage, monkeypatch
) -> None:
    # The pre-send marker reads ACTIVE then writes. If deletion locks in between, the worker must
    # wait for it and then refuse to send, not crash or send for a deleted guest.
    database, repository = storage
    guest_id, _, _, _ = await _queued_attempt(database, repository)
    token_hash = await _token_hash(database, guest_id)
    holding, release_deletion = _hold_deletion_inside_its_write_transaction(monkeypatch)
    provider = _GateProvider()
    provider.release.set()
    probe = _WriteLockProbe(monkeypatch)
    deletion: list[asyncio.Task[bool]] = []
    mark_lock: list[_LockRequest] = []
    mark_armed = asyncio.Event()
    original_mark = repository.mark_generation_request_started

    async def mark_after_deletion_locks(**kwargs):  # type: ignore[no-untyped-def]
        deletion.append(
            asyncio.create_task(
                PostgresGuestRepository(database.sessions).delete_by_token_hash(token_hash, NOW)
            )
        )
        await holding.wait()
        mark_lock.append(probe.arm(asyncio.current_task()))  # type: ignore[arg-type]
        mark_armed.set()
        return await original_mark(**kwargs)

    monkeypatch.setattr(repository, "mark_generation_request_started", mark_after_deletion_locks)
    worker = asyncio.create_task(
        ReadingGenerationWorker(repository, provider, clock=lambda: NOW).process_one()
    )
    await holding.wait()
    await _observed(mark_armed)
    mark = mark_lock[0]
    # Released only once the pre-send marker's BEGIN IMMEDIATE reached SQLite while deletion held
    # the lock.
    await _observed(mark.entered)
    assert mark.contended is True
    assert mark.acquired.is_set() is False
    release_deletion.set()
    assert list(await asyncio.gather(worker, return_exceptions=True)) == [True]
    assert provider.calls == 0
    assert await deletion[0] is True
    assert await _counts(database) == (0, 0)


async def test_write_lock_probe_rejects_a_request_that_reaches_sqlite_after_the_holder_commits(  # type: ignore[no-untyped-def]
    storage, monkeypatch
) -> None:
    # Negative control for Codex r41's schedule: SQLAlchemy has started BEGIN IMMEDIATE (its cursor
    # event fired) while the holder owns the lock, but aiosqlite's cursor creation is held until
    # the holder commits. The probe must not report contention, so the tests above would fail.
    database, _ = storage
    probe = _WriteLockProbe(monkeypatch)
    sqlalchemy_began = asyncio.Event()
    at_cursor = asyncio.Event()
    holder_committed = asyncio.Event()
    contender: list[asyncio.Task[None]] = []
    begin_next: set[asyncio.Task[Any]] = set()

    def note_begin(_conn, _cursor, statement, *_args) -> None:  # type: ignore[no-untyped-def]
        task = asyncio.current_task()
        if statement == "BEGIN IMMEDIATE" and contender and task is contender[0]:
            begin_next.add(task)
            sqlalchemy_began.set()

    event.listen(database.engine.sync_engine, "before_cursor_execute", note_begin)
    original_cursor = aiosqlite.Connection.cursor

    async def late_cursor(connection: aiosqlite.Connection) -> aiosqlite.Cursor:
        task = asyncio.current_task()
        if task in begin_next:
            begin_next.discard(task)
            at_cursor.set()
            await holder_committed.wait()
        return await original_cursor(connection)

    monkeypatch.setattr(aiosqlite.Connection, "cursor", late_cursor)

    async def take_write_lock() -> None:
        async with database.sessions() as session, session.begin():
            await session.connection(execution_options={"sqlite_write": True})

    async with database.sessions() as holder, holder.begin():
        await holder.connection(execution_options={"sqlite_write": True})
        contender.append(asyncio.create_task(take_write_lock()))
        request = probe.arm(contender[0])
        await _observed(at_cursor)
        assert sqlalchemy_began.is_set() is True
        assert request.entered.is_set() is False
    holder_committed.set()
    await asyncio.wait_for(contender[0], 10)
    assert request.contended is False
    assert request.acquired.is_set() is True
