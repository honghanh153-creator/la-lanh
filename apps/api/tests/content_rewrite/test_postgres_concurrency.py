"""Opt-in real PostgreSQL proof; never runs against a live or shared database."""

import asyncio
import calendar
import os
import ssl
import sys
from contextlib import asynccontextmanager
from contextvars import Context
from datetime import UTC, datetime, timedelta
from importlib import import_module
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.rewrite_scope import rewrite_session
from app.db.session import Database
from app.domains.content_rewrite.authorization import DatabaseRewriteAuthorization
from app.domains.content_rewrite.models import LeasedRewriteJob, RewriteRequestEnvelope
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.tables import (
    ContentRewriteJobRow,
    ContentRewriteSpendDayRow,
    ContentRewriteSpendMonthRow,
)
from app.domains.content_rewrite.worker import ContentRewriteWorker
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import GuestSessionRow
from app.domains.tarot.rewrite import TarotRewriteProjector
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.generation.base import RewriteGenerationSuccess
from app.infrastructure.generation.pricing import GenerationPricing, cents_to_nanos
from app.infrastructure.generation.schemas import surface_output_contract
from tests.content_rewrite import test_execution_fences as fence_checks
from tests.content_rewrite import test_radar_subject_consent as radar_checks
from tests.content_rewrite.test_execution_fences import seed_fence
from tests.content_rewrite.test_tarot_rewrite import _output


def _period_end(now: datetime, boundary: str) -> datetime:
    day = now.day if boundary == "day" else calendar.monthrange(now.year, now.month)[1]
    return now.replace(day=day, hour=23, minute=59, second=59, microsecond=0)


@pytest.mark.parametrize(
    "year,month,last_day,next_month",
    [(2026, 2, 28, 3), (2028, 2, 29, 3), (2026, 4, 30, 5), (2026, 10, 31, 11)],
)
def test_month_boundary_uses_actual_calendar_end(
    year: int, month: int, last_day: int, next_month: int
) -> None:
    now = datetime(year, month, 10, 12, tzinfo=UTC)
    boundary = _period_end(now, "month")
    assert boundary == datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)
    assert boundary + timedelta(seconds=2) == datetime(year, next_month, 1, 0, 0, 1, tzinfo=UTC)
    assert _period_end(now, "day") == datetime(year, month, 10, 23, 59, 59, tzinfo=UTC)


@pytest.mark.parametrize("boundary", ["day", "month"])
async def test_real_locked_transaction_crossing_period_does_not_send(postgres_fenced, boundary):  # type: ignore[no-untyped-def]
    db, repository, cipher, _, view, record = postgres_fenced
    clock = [_period_end(datetime.now(UTC), boundary)]
    async with db.sessions() as session, session.begin():
        await session.execute(update(ContentRewriteJobRow).values(created_at=clock[0]))
        await session.execute(
            update(GuestSessionRow).values(expires_at=clock[0] + timedelta(days=2))
        )
        await session.execute(
            update(TarotSessionRow).values(expires_at=clock[0] + timedelta(days=2))
        )
    guard = repository.execution_guard

    @asynccontextmanager
    async def delayed(lease):  # type: ignore[no-untyped-def]
        async with guard(lease) as allowed:
            assert allowed
            clock[0] += timedelta(seconds=2)
            yield allowed

    repository.execution_guard = delayed

    class Provider:
        calls = 0

        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            self.calls += 1
            return RewriteGenerationSuccess(key=request.key, output=_output(view))

    provider = Provider()
    await ContentRewriteWorker(
        repository,
        provider,
        DatabaseRewriteAuthorization(db.sessions),
        TarotRewriteProjector(db.sessions, cipher),
        daily_token_budget=100_000,
        daily_cost_budget_cents=100,
        monthly_cost_budget_cents=100,
        clock=lambda: clock[0],
    ).process_one()
    assert provider.calls == 0
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row.status == "failed" and row.last_result == "budget_blocked"
        previous_month = (clock[0] - timedelta(seconds=2)).strftime("%Y-%m")
        month = await session.get(ContentRewriteSpendMonthRow, previous_month)
        assert month.reserved_cost_nanos > 0


async def test_connection_termination_then_erasure_cannot_publish_or_resend(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, cipher, guest_id, view, _ = postgres_fenced
    entered = asyncio.Event()
    release = asyncio.Event()
    backend_pid = []

    class Provider:
        calls = 0

        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            self.calls += 1
            async with rewrite_session(db.sessions) as session:
                backend_pid.append(await session.scalar(text("SELECT pg_backend_pid()")))
                entered.set()
                await release.wait()
            return RewriteGenerationSuccess(key=request.key, output=_output(view))

    provider = Provider()
    worker = ContentRewriteWorker(
        repository,
        provider,
        DatabaseRewriteAuthorization(db.sessions),
        TarotRewriteProjector(db.sessions, cipher),
        daily_token_budget=100_000,
        daily_cost_budget_cents=100,
        monthly_cost_budget_cents=100,
    )
    task = asyncio.create_task(worker.process_one(), context=Context())
    try:
        await asyncio.wait_for(entered.wait(), 10)
        async with db.sessions() as session:
            assert await session.scalar(
                text("SELECT pg_terminate_backend(:pid)"), {"pid": backend_pid[0]}
            )
        erasure = asyncio.create_task(
            PostgresGuestRepository(db.sessions).delete_by_token_hash(
                guest_id.bytes * 2, datetime.now(UTC)
            ),
            context=Context(),
        )
        deadline = asyncio.get_running_loop().time() + 10
        while (
            await PostgresGuestRepository(db.sessions).find_by_token_hash(
                guest_id.bytes * 2, datetime.now(UTC)
            )
            is not None
        ):
            if asyncio.get_running_loop().time() >= deadline:
                pytest.fail("erasure did not commit its authorization revocation")
            await asyncio.sleep(0.01)
        assert not erasure.done(), "erasure must drain an already admitted disclosure"
        assert (
            await PostgresGuestRepository(db.sessions).find_by_token_hash(
                guest_id.bytes * 2, datetime.now(UTC)
            )
            is None
        )
        release.set()
        assert await asyncio.wait_for(erasure, 10)
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), 10)
        assert not await worker.process_one()
        assert provider.calls == 1
        async with db.sessions() as session:
            assert await session.get(TarotSessionRow, view.id) is None
            month = await session.get(
                ContentRewriteSpendMonthRow, datetime.now(UTC).strftime("%Y-%m")
            )
            assert month.reserved_cost_nanos > 0
    finally:
        release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_slow_provider_does_not_block_foreground_session(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, cipher, guest_id, view, _ = postgres_fenced
    entered, release = asyncio.Event(), asyncio.Event()

    class Provider:
        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            entered.set()
            await release.wait()
            return RewriteGenerationSuccess(key=request.key, output=_output(view))

    task = asyncio.create_task(
        ContentRewriteWorker(
            repository,
            Provider(),
            DatabaseRewriteAuthorization(db.sessions),
            TarotRewriteProjector(db.sessions, cipher),
            daily_token_budget=100_000,
            daily_cost_budget_cents=100,
            monthly_cost_budget_cents=100,
        ).process_one(),
        context=Context(),
    )
    try:
        await asyncio.wait_for(entered.wait(), 10)
        session = await asyncio.wait_for(
            PostgresGuestRepository(db.sessions).find_by_token_hash(
                guest_id.bytes * 2, datetime.now(UTC)
            ),
            1,
        )
        assert session is not None and session.guest.id == guest_id
    finally:
        release.set()
        await asyncio.wait_for(task, 10)


async def test_killed_worker_preserves_reservation_and_never_resends(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, _, _, _, record = postgres_fenced
    code = """
import asyncio, os
from datetime import UTC, datetime
from app.db.session import Database
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider
async def main():
    db = Database(os.environ["LA_LANH_TEST_POSTGRES_URL"])
    cipher = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32))
    repo = PostgresContentRewriteRepository(db.sessions, cipher)
    now = datetime.now(UTC)
    lease = await repo.lease(now=now, lease_for_seconds=1)
    assert lease is not None
    assert await repo.reserve_budget(job_id=lease.id, lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        since=now.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=100, daily_token_limit=1000, requested_cost_nanos=100,
        daily_cost_limit_nanos=1000, monthly_cost_limit_nanos=1000,
        pricing_version="synthetic", updated_at=now)
    async with repo.execution_guard(lease) as allowed:
        assert allowed
        assert await repo.mark_request_started(job_id=lease.id, lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch, started_at=now)
    print("synthetic-send-boundary", flush=True)
    await asyncio.sleep(60)
asyncio.run(main())
"""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        assert process.stdout is not None
        assert await asyncio.wait_for(process.stdout.readline(), 10) == b"synthetic-send-boundary\n"
        process.kill()
        await asyncio.wait_for(process.wait(), 10)
        assert process.returncode != 0
        assert (
            await repository.lease(
                now=datetime.now(UTC) + timedelta(seconds=2), lease_for_seconds=120
            )
            is None
        )
        async with db.sessions() as session:
            row = await session.get(ContentRewriteJobRow, record.id)
            assert row.status == "failed" and row.last_result == "ambiguous"
            month = await session.get(
                ContentRewriteSpendMonthRow, datetime.now(UTC).strftime("%Y-%m")
            )
            assert month.reserved_cost_nanos == 100
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.fixture
async def postgres_fenced():  # type: ignore[no-untyped-def]
    database_url = os.environ.get("LA_LANH_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("set LA_LANH_TEST_POSTGRES_URL for isolated PostgreSQL verification")
    url = make_url(database_url)
    if (
        url.drivername != "postgresql+asyncpg"
        or url.host != "127.0.0.1"
        or url.port not in (55432, 55434)
        or url.database != "la_lanh_security_test"
    ):
        pytest.fail("refusing to modify any database except the isolated localhost test database")
    db = Database(database_url)
    try:
        async with db.engine.begin() as connection:
            head = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert head == "20261011_0036"
            await connection.execute(
                text(
                    "TRUNCATE guest_sessions, content_rewrite_spend_days, "
                    "content_rewrite_spend_months, rewrite_send_fences CASCADE"
                )
            )
        yield await seed_fence(db)
    finally:
        await db.dispose()


@pytest.mark.parametrize("limit", ["monthly", "daily"])
async def test_parallel_reservations_never_cross_cap(postgres_fenced, limit):  # type: ignore[no-untyped-def]
    db, repository, _, guest_id, view, record = postgres_fenced
    now = datetime.now(UTC)
    for index in range(11):
        key = record.request.key.model_copy(update={"candidate_variant": f"race-{index}"})
        request = record.request.model_copy(update={"key": key})
        await repository.enqueue(record.model_copy(update={"id": uuid4(), "request": request}))
    leases = [await repository.lease(now=now, lease_for_seconds=120) for _ in range(12)]
    assert all(leases)

    async def reserve(lease: LeasedRewriteJob) -> bool:
        typed_repository: PostgresContentRewriteRepository = repository
        return await typed_repository.reserve_budget(
            job_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            since=now.replace(hour=0, minute=0, second=0, microsecond=0),
            requested_tokens=10,
            daily_token_limit=1000,
            requested_cost_nanos=60,
            daily_cost_limit_nanos=100 if limit == "daily" else 1000,
            monthly_cost_limit_nanos=100 if limit == "monthly" else 1000,
            pricing_version="offline-synthetic",
            updated_at=now,
        )

    results = await asyncio.wait_for(asyncio.gather(*(reserve(lease) for lease in leases)), 15)
    assert sum(results) == 1
    assert await PostgresGuestRepository(db.sessions).delete_by_token_hash(guest_id.bytes * 2, now)
    async with db.sessions() as session:
        monthly = await session.get(ContentRewriteSpendMonthRow, now.strftime("%Y-%m"))
        daily = await session.get(ContentRewriteSpendDayRow, now.strftime("%Y-%m-%d"))
        assert monthly.reserved_cost_nanos == daily.reserved_cost_nanos == 60
        assert daily.reserved_tokens == 10
        assert await session.get(TarotSessionRow, view.id) is None
        assert (await session.scalars(select(ContentRewriteJobRow))).all() == []


@pytest.mark.parametrize("limit", ["monthly", "daily"])
async def test_different_owner_workers_race_absent_ledgers_without_provider_overadmission(  # type: ignore[no-untyped-def]
    postgres_fenced, monkeypatch, limit
):
    db, repository, cipher, _, view, record = postgres_fenced
    fixtures = [postgres_fenced]
    for _ in range(3):
        fixtures.append(await seed_fence(db))
    owner_ids = {fixture[3] for fixture in fixtures}
    parent_ids = {fixture[4].id for fixture in fixtures}
    job_ids = {fixture[5].id for fixture in fixtures}
    assert len(owner_ids) == len(parent_ids) == len(job_ids) == 4
    assert db.engine.dialect.name == "postgresql"
    now = datetime.now(UTC)
    month_key, day_key = now.strftime("%Y-%m"), now.strftime("%Y-%m-%d")
    async with db.sessions() as session:
        assert await session.get(ContentRewriteSpendMonthRow, month_key) is None
        assert await session.get(ContentRewriteSpendDayRow, day_key) is None

    # Rendezvous after real, disjoint owner/parent locks, before any ledger insert.
    # Same-owner contenders would block here and time out instead of proving a race.
    barrier = asyncio.Barrier(len(owner_ids))
    entered_owners: set[UUID] = set()
    backend_pids: set[int] = set()
    typed_repository: PostgresContentRewriteRepository = repository
    parent_exists = typed_repository._parent_exists

    async def synchronized_parent(
        session: AsyncSession, request: RewriteRequestEnvelope, guest_id: UUID
    ) -> bool:
        valid = await parent_exists(session, request, guest_id)
        if guest_id not in entered_owners:
            assert valid and guest_id in owner_ids
            entered_owners.add(guest_id)
            pid = await session.scalar(text("SELECT pg_backend_pid()"))
            assert isinstance(pid, int)
            backend_pids.add(pid)
            assert await session.get(ContentRewriteSpendMonthRow, month_key) is None
            assert await session.get(ContentRewriteSpendDayRow, day_key) is None
            await barrier.wait()
        return valid

    monkeypatch.setattr(repository, "_parent_exists", synchronized_parent)
    contract = surface_output_contract(record.request.key.surface, record.request.safe_payload)
    # Synthetic prices make each reservation about 60 cents, with no paid provider.
    pricing = GenerationPricing(
        version="offline-synthetic-budget-race",
        input_nanos_per_token=0,
        output_nanos_per_token=cents_to_nanos(60) // contract.max_output_tokens,
    )
    reservation = pricing.cost_nanos(input_tokens=0, output_tokens=contract.max_output_tokens)
    ceiling = cents_to_nanos(100)
    assert ceiling == 1_000_000_000  # USD 1, not a 100-nanodollar test cap.
    assert ceiling // 2 < reservation <= ceiling
    provider_requests: list[RewriteRequestEnvelope] = []

    class Provider:
        async def generate_rewrite(
            self, request: RewriteRequestEnvelope
        ) -> RewriteGenerationSuccess:
            async with rewrite_session(db.sessions) as session:
                row = await session.scalar(
                    select(ContentRewriteJobRow).where(
                        ContentRewriteJobRow.generation_key == request.key.cache_key
                    )
                )
                assert row is not None and row.request_started_at == now
                assert row.budget_reserved_cost_nanos == reservation
            provider_requests.append(request)
            return RewriteGenerationSuccess(key=request.key, output=_output(view))

    worker = ContentRewriteWorker(
        repository,
        Provider(),
        DatabaseRewriteAuthorization(db.sessions),
        TarotRewriteProjector(db.sessions, cipher),
        daily_token_budget=1_000_000,
        daily_cost_budget_cents=100 if limit == "daily" else 1000,
        monthly_cost_budget_cents=100 if limit == "monthly" else 1000,
        pricing=pricing,
        clock=lambda: now,
    )
    tasks = [asyncio.create_task(worker.process_one(), context=Context()) for _ in owner_ids]
    try:
        assert all(await asyncio.wait_for(asyncio.gather(*tasks), 15))
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    assert entered_owners == owner_ids
    assert len(backend_pids) == len(owner_ids)
    assert len(provider_requests) == 1
    assert not await worker.process_one()
    assert len(provider_requests) == 1
    async with db.sessions() as session:
        monthly = await session.get(ContentRewriteSpendMonthRow, month_key)
        daily = await session.get(ContentRewriteSpendDayRow, day_key)
        assert monthly is not None and daily is not None
        assert monthly.reserved_cost_nanos == daily.reserved_cost_nanos == reservation
        assert monthly.reserved_cost_nanos <= ceiling
        assert daily.reserved_tokens > 0
        rows = (await session.scalars(select(ContentRewriteJobRow))).all()
        assert {row.id for row in rows} == job_ids
        admitted = [row for row in rows if row.status == "succeeded"]
        blocked = [row for row in rows if row.last_result == "budget_blocked"]
        assert len(admitted) == 1 and len(blocked) == len(owner_ids) - 1
        assert admitted[0].last_result == "accepted"
        assert admitted[0].cost_nanos == reservation
        assert admitted[0].input_tokens == daily.reserved_tokens
        assert admitted[0].pricing_version == pricing.version
        assert all(
            row.status == "failed" and row.last_result == "budget_blocked" for row in blocked
        )
        assert all(row.request_started_at is None and row.cost_nanos is None for row in blocked)
        assert all(row.budget_reserved_cost_nanos == 0 for row in blocked)
        assert provider_requests[0].key == next(
            fixture[5].request.key for fixture in fixtures if fixture[5].id == admitted[0].id
        )


async def test_erasure_waits_for_execution_then_fences_stale_worker(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, _, guest_id, view, record = postgres_fenced
    lease = await repository.lease(now=datetime.now(UTC), lease_for_seconds=120)
    assert lease
    deletion = None
    try:
        async with repository.execution_guard(lease) as allowed:
            assert allowed
            deletion = asyncio.create_task(
                PostgresGuestRepository(db.sessions).delete_by_token_hash(
                    guest_id.bytes * 2, datetime.now(UTC)
                ),
                # A concurrent task must not borrow the worker's transaction context.
                context=Context(),
            )
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(deletion), 0.2)
        assert await asyncio.wait_for(deletion, 5)
    finally:
        if deletion is not None and not deletion.done():
            deletion.cancel()
            await asyncio.gather(deletion, return_exceptions=True)
    async with repository.execution_guard(lease) as allowed:
        assert not allowed
    async with db.sessions() as session:
        assert await session.get(ContentRewriteJobRow, record.id) is None
        assert await session.get(TarotSessionRow, view.id) is None


async def test_verified_tls_accepts_test_ca_and_rejects_untrusted_server(postgres_fenced):  # type: ignore[no-untyped-def]
    db, _, _, _, _, _ = postgres_fenced
    assert await db.ping()
    async with db.sessions() as session:
        assert await session.scalar(text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()"))
    url = make_url(os.environ["LA_LANH_TEST_POSTGRES_URL"])
    untrusted = Database(
        url.difference_update_query(["sslrootcert"]).render_as_string(hide_password=False)
    )
    try:
        with pytest.raises(ssl.SSLCertVerificationError):
            await untrusted.ping()
    finally:
        await untrusted.dispose()


async def test_browser_role_has_no_privileges_and_rls_hides_private_rows(postgres_fenced):  # type: ignore[no-untyped-def]
    db, _, _, _, _, _ = postgres_fenced
    async with db.engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("CREATE ROLE la_lanh_browser_probe NOLOGIN"))
            tables = (
                "content_rewrite_jobs",
                "content_rewrite_spend_days",
                "content_rewrite_spend_months",
            )
            for table in tables:
                assert await connection.scalar(
                    text("SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:table)"),
                    {"table": f"public.{table}"},
                )
                assert not await connection.scalar(
                    text("SELECT has_table_privilege('la_lanh_browser_probe', :table, 'SELECT')"),
                    {"table": f"public.{table}"},
                )
            await connection.execute(
                text(
                    "GRANT SELECT ON content_rewrite_jobs, content_rewrite_spend_days, "
                    "content_rewrite_spend_months TO la_lanh_browser_probe"
                )
            )
            await connection.execute(text("SET LOCAL ROLE la_lanh_browser_probe"))
            # Even an accidental SELECT grant cannot expose backend-only queue rows.
            assert await connection.scalar(text("SELECT count(*) FROM content_rewrite_jobs")) == 0
        finally:
            # Test-only role and grants disappear with this rollback.
            await transaction.rollback()


async def test_legacy_paid_jobs_backfill_monthly_cap_on_real_postgres(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, _, _, _, record = postgres_fenced
    second = record.model_copy(
        update={
            "id": uuid4(),
            "request": record.request.model_copy(
                update={
                    "key": record.request.key.model_copy(update={"candidate_variant": "legacy"})
                }
            ),
        }
    )
    await repository.enqueue(second)
    async with db.engine.connect() as connection:
        transaction = await connection.begin()
        try:
            for job_id, timestamp, actual, reserved in (
                (record.id, datetime(2026, 9, 30, 23, 0, tzinfo=UTC), 300, 400),
                (second.id, datetime(2026, 10, 1, 0, 0, tzinfo=UTC), 500, 600),
            ):
                await connection.execute(
                    text(
                        "UPDATE content_rewrite_jobs SET cost_nanos=:actual, "
                        "budget_reserved_cost_nanos=:reserved, updated_at=:timestamp WHERE id=:id"
                    ),
                    {"actual": actual, "reserved": reserved, "timestamp": timestamp, "id": job_id},
                )
            await connection.execute(text("DROP TABLE content_rewrite_spend_months"))

            def apply_legacy_upgrade(sync_connection):  # type: ignore[no-untyped-def]
                migration = import_module("migrations.versions.20261008_0029_rewrite_monthly_spend")
                with Operations.context(MigrationContext.configure(sync_connection)):
                    migration.upgrade()

            await connection.run_sync(apply_legacy_upgrade)
            rows = (
                await connection.execute(
                    text(
                        "SELECT month, reserved_cost_nanos FROM "
                        "content_rewrite_spend_months ORDER BY month"
                    )
                )
            ).all()
            assert rows == [("2026-09", 700), ("2026-10", 1100)]
        finally:
            # Restore the current schema and synthetic fixture, even on failure.
            await transaction.rollback()


async def test_populated_daily_upgrade_keeps_both_ledgers_before_queue_erasure(postgres_fenced):  # type: ignore[no-untyped-def]
    db, repository, _, owner_id, _, record = postgres_fenced
    ids = [record.id]
    for variant in ("legacy-two", "legacy-three"):
        added = record.model_copy(
            update={
                "id": uuid4(),
                "request": record.request.model_copy(
                    update={
                        "key": record.request.key.model_copy(update={"candidate_variant": variant})
                    }
                ),
            }
        )
        await repository.enqueue(added)
        ids.append(added.id)
    async with db.engine.connect() as connection:
        transaction = await connection.begin()
        try:
            for job_id, stamp, cost, reserved, input_tokens, output_tokens, reserved_tokens in (
                (ids[0], "2026-10-01T06:59:59+07:00", 300, 400, 10, 20, 30),
                (ids[1], "2026-10-01T07:00:00+07:00", 500, 600, None, None, 20),
                (ids[2], "2026-10-01T07:00:01+07:00", None, 700, 5, None, 40),
            ):
                await connection.execute(
                    text(
                        "UPDATE content_rewrite_jobs SET updated_at=:stamp, "
                        "cost_nanos=:cost, budget_reserved_cost_nanos=:reserved, "
                        "input_tokens=:input, "
                        "output_tokens=:output, budget_reserved_tokens=:tokens WHERE id=:id"
                    ),
                    {
                        "id": job_id,
                        "stamp": datetime.fromisoformat(stamp),
                        "cost": cost,
                        "reserved": reserved,
                        "input": input_tokens,
                        "output": output_tokens,
                        "tokens": reserved_tokens,
                    },
                )
            await connection.execute(text("DROP TABLE content_rewrite_spend_days"))
            await connection.execute(text("DROP TABLE content_rewrite_spend_months"))
            for column in (
                "owner_guest_id",
                "reading_plan_id",
                "tarot_session_id",
                "radar_request_id",
            ):
                await connection.execute(
                    text(f"ALTER TABLE content_rewrite_jobs DROP COLUMN {column}")
                )

            def upgrade(sync_connection):  # type: ignore[no-untyped-def]
                with Operations.context(MigrationContext.configure(sync_connection)):
                    import_module(
                        "migrations.versions.20261008_0029_rewrite_monthly_spend"
                    ).upgrade()
                    import_module("migrations.versions.20261008_0030_rewrite_fences").upgrade()

            await connection.run_sync(upgrade)
            assert (
                await connection.execute(
                    text(
                        "SELECT month, reserved_cost_nanos FROM "
                        "content_rewrite_spend_months ORDER BY month"
                    )
                )
            ).all() == [("2026-09", 700), ("2026-10", 1800)]
            assert (
                await connection.execute(
                    text(
                        "SELECT day, reserved_cost_nanos, reserved_tokens "
                        "FROM content_rewrite_spend_days ORDER BY day"
                    )
                )
            ).all() == [("2026-09-30", 700, 60), ("2026-10-01", 1800, 65)]
            assert await connection.scalar(text("SELECT count(*) FROM content_rewrite_jobs")) == 0
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM guest_sessions WHERE id=:id"), {"id": owner_id}
                )
                == 1
            )
        finally:
            await transaction.rollback()


@pytest.mark.parametrize(
    "behavior", ["publish", "rollback", "withdraw_precision", "crash", "obsolete_birth"]
)
async def test_execution_contract_on_real_postgres(postgres_fenced, behavior):  # type: ignore[no-untyped-def]
    if behavior == "obsolete_birth":
        await fence_checks.test_obsolete_birth_reading_cannot_send_or_reserve_budget(
            postgres_fenced, True
        )
        return
    checks = {
        "publish": fence_checks.test_valid_birthless_tarot_projects_and_terminalizes_together,
        "rollback": fence_checks.test_projection_write_rolled_back_when_finalization_fails,
        "withdraw_precision": (
            fence_checks.test_precision_withdrawal_erases_both_radar_jobs_and_rejects_late_enqueue
        ),
        "crash": fence_checks.test_reserved_send_cannot_be_retried_after_projection_rollback,
    }
    await checks[behavior](postgres_fenced)  # type: ignore[no-untyped-call]


@pytest.mark.parametrize("withdrawal", ["legacy", "repository", "reconsent"])
@pytest.mark.parametrize(
    "other_consents,mode",
    [(False, "consented_invite"), (True, "private_check"), (True, "consented_invite")],
)
async def test_pair_consent_contract_on_real_postgres(  # type: ignore[no-untyped-def]
    postgres_fenced, other_consents, mode, withdrawal
):
    await radar_checks.test_radar_requires_both_subjects_before_enqueue_and_execution(
        postgres_fenced, other_consents, mode, withdrawal
    )
