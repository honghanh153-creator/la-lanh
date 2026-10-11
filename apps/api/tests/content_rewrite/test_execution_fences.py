import asyncio
import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, update

from app.db.rewrite_scope import rewrite_session
from app.db.session import Database
from app.domains.content_rewrite.authorization import (
    DatabaseRewriteAuthorization,
    RewriteConsentScope,
    consent_definition,
)
from app.domains.content_rewrite.models import RewriteJobRecord
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.tables import (
    ContentRewriteJobRow,
    ContentRewriteSpendMonthRow,
    RewriteSendFenceRow,
)
from app.domains.content_rewrite.worker import ContentRewriteWorker
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.radar.rewrite import RadarPerspective
from app.domains.readings.models import ReadingPurpose
from app.domains.tarot.models import TarotSessionView
from app.domains.tarot.rewrite import (
    TAROT_REWRITE_RENDERER_VERSION,
    TarotRewriteProjector,
    compile_tarot_rewrite_request,
)
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider
from app.infrastructure.generation.base import RewriteGenerationSuccess
from tests.content_rewrite.test_tarot_rewrite import _output, _session


@pytest.mark.parametrize("target_send", [False, True])
async def test_tarot_erasure_waits_only_for_its_own_captured_send(fenced, target_send):  # type: ignore[no-untyped-def]
    from app.domains.tarot.service import TarotSessionService

    db, _, cipher, owner_id, view, record = fenced
    lease, unrelated = uuid4(), uuid4()
    async with db.sessions() as session, session.begin():
        session.add(
            RewriteSendFenceRow(
                job_id=unrelated,
                lease_token=lease,
                subject_id=owner_id,
                expires_at=datetime.now(UTC) + timedelta(minutes=3),
            )
        )
        if target_send:
            session.add(
                RewriteSendFenceRow(
                    job_id=record.id,
                    lease_token=lease,
                    subject_id=owner_id,
                    expires_at=datetime.now(UTC) + timedelta(minutes=3),
                )
            )
    service = TarotSessionService(db.sessions, cipher, SecretHasher(b"synthetic-hash-key" * 2))
    task = asyncio.create_task(service.delete(owner_id, view.id))
    try:
        if target_send:
            deadline = asyncio.get_running_loop().time() + 2
            while True:
                async with db.sessions() as session:
                    removed = await session.get(TarotSessionRow, view.id) is None
                if removed:
                    break
                if asyncio.get_running_loop().time() >= deadline:
                    pytest.fail("target source erasure did not commit")
                await asyncio.sleep(0.01)
            assert not task.done()
            async with db.sessions() as session, session.begin():
                await session.execute(
                    delete(RewriteSendFenceRow).where(RewriteSendFenceRow.job_id == record.id)
                )
        await asyncio.wait_for(task, 1)
        async with db.sessions() as session:
            assert await session.get(TarotSessionRow, view.id) is None
            assert await session.get(RewriteSendFenceRow, (unrelated, lease, owner_id)) is not None
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_reserved_send_cannot_be_retried_after_projection_rollback(fenced):  # type: ignore[no-untyped-def]
    db, repository, _, _, _, record = fenced
    now = datetime.now(UTC)
    lease = await repository.lease(now=now, lease_for_seconds=120)
    assert lease is not None
    assert await repository.reserve_budget(
        job_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        since=now.replace(hour=0, minute=0, second=0, microsecond=0),
        requested_tokens=100,
        daily_token_limit=1000,
        requested_cost_nanos=100,
        daily_cost_limit_nanos=1000,
        monthly_cost_limit_nanos=1000,
        pricing_version="offline",
        updated_at=now,
    )
    with pytest.raises(RuntimeError, match="after send"):
        async with repository.execution_guard(lease) as allowed:
            assert allowed
            assert await repository.mark_request_started(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                started_at=now,
            )
            raise RuntimeError("after send")
    assert await repository.lease(now=now + timedelta(seconds=121), lease_for_seconds=120) is None
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row.status == "failed" and row.last_result == "ambiguous"


@pytest.mark.parametrize("cleanup", ["worker", "guest"])
async def test_expired_leased_payload_erased_without_resend(fenced, cleanup):  # type: ignore[no-untyped-def]
    db, repository, _, _, _, record = fenced
    now = datetime.now(UTC)
    assert await repository.lease(now=now, lease_for_seconds=1)
    later = now + timedelta(days=2)
    if cleanup == "worker":
        assert await repository.lease(now=later, lease_for_seconds=120) is None
    else:
        # Keep the guest active so guest erasure cannot hide missing job cleanup.
        async with db.sessions() as session, session.begin():
            await session.execute(
                update(GuestSessionRow).values(expires_at=later + timedelta(days=1))
            )
        await PostgresGuestRepository(db.sessions).purge_expired(later, 100)
    async with db.sessions() as session:
        assert await session.get(ContentRewriteJobRow, record.id) is None


async def test_guard_rechecks_deadline_after_parent_lock(fenced, monkeypatch):  # type: ignore[no-untyped-def]
    from app.domains.content_rewrite import postgres

    _, repository, _, _, _, _ = fenced
    now = datetime.now(UTC)
    lease = await repository.lease(now=now, lease_for_seconds=120)
    assert lease
    parent_exists = repository._parent_exists

    class ExpiredClock:
        @staticmethod
        def now(_timezone):  # type: ignore[no-untyped-def]
            return lease.lease_expires_at + timedelta(seconds=1)

    async def delayed_parent(*args):  # type: ignore[no-untyped-def]
        result = await parent_exists(*args)
        monkeypatch.setattr(postgres, "datetime", ExpiredClock)
        return result

    monkeypatch.setattr(repository, "_parent_exists", delayed_parent)
    async with repository.execution_guard(lease) as allowed:
        assert allowed is False


async def test_publication_after_deadline_is_rejected(fenced):  # type: ignore[no-untyped-def]
    _, repository, _, _, _, _ = fenced
    lease = await repository.lease(now=datetime.now(UTC), lease_for_seconds=120)
    assert lease
    assert not await repository.succeed(
        lease=lease,
        gate_receipt_id="offline",
        output_fingerprint="f" * 64,
        input_tokens=1,
        output_tokens=1,
        cost_nanos=1,
        completed_at=lease.lease_expires_at,
    )


async def test_precision_withdrawal_erases_both_radar_jobs_and_rejects_late_enqueue(fenced):  # type: ignore[no-untyped-def]
    from app.domains.birth.postgres import PostgresBirthRepository
    from app.domains.birth.tables import BirthProfileRow
    from app.domains.identity.tables import PrincipalRow
    from app.domains.radar.rewrite import compile_radar_rewrite_request
    from app.domains.radar.tables import RadarRequestRow
    from tests.content_rewrite.test_radar_rewrite import _projection

    db, repository, cipher, owner_id, _, tarot_record = fenced
    now = datetime.now(UTC)
    recipient_id, principal_id, radar_id = uuid4(), uuid4(), uuid4()
    definition = consent_definition(RewriteConsentScope.RADAR)
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=recipient_id,
                token_hash=recipient_id.bytes * 2,
                csrf_hash=b"d" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
        await session.flush()
        session.add(PrincipalRow(id=principal_id, source_guest_id=owner_id, created_at=now))
        session.add(
            BirthProfileRow(
                guest_id=recipient_id,
                profile_level=2,
                birth_time_ciphertext="encrypted-test-time",
                time_precision="approximate",
                created_at=now,
                updated_at=now,
            )
        )
        for guest_id in (owner_id, recipient_id):
            session.add(
                ConsentRow(
                    guest_id=guest_id,
                    purpose=definition.purpose,
                    version=definition.version,
                    accepted_at=now,
                )
            )
        await session.flush()
        session.add(
            RadarRequestRow(
                id=radar_id,
                principal_id=principal_id,
                owner_guest_id=owner_id,
                recipient_guest_id=recipient_id,
                recipient_label_ciphertext="encrypted-label",
                context="crush",
                mode="consented_invite",
                status="completed",
                created_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
    records = []
    perspectives: tuple[tuple[UUID, RadarPerspective], ...] = (
        (owner_id, "owner"),
        (recipient_id, "recipient"),
    )
    for guest_id, perspective in perspectives:
        request = compile_radar_rewrite_request(
            guest_id,
            radar_id,
            perspective,
            _projection(),
            context="crush",
            model_version="gpt-6-luna",
            prompt_version="offline",
        )
        assert request
        record = RewriteJobRecord(
            id=uuid4(),
            request=request,
            deletion_epoch=uuid4(),
            created_at=now,
            updated_at=now,
            next_attempt_at=now,
        )
        await repository.enqueue(record)
        records.append(record)
    await PostgresBirthRepository(db.sessions, cipher).clear_supplement(
        recipient_id,
        remove_time=True,
        remove_place=False,
    )
    async with db.sessions() as session:
        assert await session.get(RadarRequestRow, radar_id) is None
        assert await session.get(ContentRewriteJobRow, tarot_record.id) is not None
        for record in records:
            assert await session.get(ContentRewriteJobRow, record.id) is None
    for record in records:
        with pytest.raises(PermissionError):
            await repository.enqueue(record)


@pytest.fixture
async def fenced(tmp_path):  # type: ignore[no-untyped-def]
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'fences.db'}")
    await db.initialize()
    try:
        yield await seed_fence(db)
    finally:
        await db.dispose()


async def seed_fence(
    db: Database,
) -> tuple[
    Database,
    PostgresContentRewriteRepository,
    AesGcmEnvelopeCipher,
    UUID,
    TarotSessionView,
    RewriteJobRecord,
]:
    cipher = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32))
    now = datetime.now(UTC)
    guest_id = uuid4()
    view = _session().model_copy(
        update={
            "id": uuid4(),
            "created_at": now,
            "updated_at": now,
            "expires_at": now + timedelta(days=1),
        }
    )
    definition = consent_definition(RewriteConsentScope.PERSONAL)
    assert view.reading is not None
    payload = json.dumps({"reading": view.reading.model_dump(mode="json")}).encode()
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=guest_id.bytes * 2,
                csrf_hash=b"c" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
        await session.flush()
        session.add(
            ConsentRow(
                guest_id=guest_id,
                version=definition.version,
                purpose=definition.purpose,
                accepted_at=now,
            )
        )
        session.add(
            TarotSessionRow(
                id=view.id,
                guest_id=guest_id,
                version=4,
                state="complete",
                context=view.context.value,
                spread=view.spread.value,
                voice=view.voice.value,
                origin=view.origin.value,
                idempotency_hash=b"i" * 32,
                payload_ciphertext=cipher.encrypt(
                    payload, context=f"tarot-session:{view.id}".encode()
                ),
                created_at=now,
                updated_at=now,
                expires_at=view.expires_at,
            )
        )
    request = compile_tarot_rewrite_request(
        guest_id, view, model_version="gpt-6-luna", prompt_version="surface-rewrite-v1"
    )
    assert request is not None
    record = RewriteJobRecord(
        id=uuid4(),
        request=request,
        deletion_epoch=uuid4(),
        next_attempt_at=now,
        created_at=now,
        updated_at=now,
    )
    repository = PostgresContentRewriteRepository(db.sessions, cipher)
    await repository.enqueue(record)
    return db, repository, cipher, guest_id, view, record


@pytest.mark.parametrize("with_budget", [False, True])
async def test_obsolete_birth_reading_cannot_send_or_reserve_budget(fenced, with_budget):  # type: ignore[no-untyped-def]
    from app.domains.astro.engine import NatalChartEngine
    from app.domains.birth.postgres import PostgresBirthRepository
    from app.domains.birth.service import BirthChartService
    from app.domains.readings.application import ReadingApplicationService
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.renderers import DeterministicVietnameseRenderer
    from app.domains.readings.rewrite import ReadingRewriteProjector, compile_daily_rewrite_request
    from app.domains.readings.tables import ReadingPlanRow
    from app.infrastructure.crypto import SecretHasher

    db, repository, cipher, guest_id, _, _ = fenced
    async with db.sessions() as session, session.begin():
        await session.execute(delete(ContentRewriteJobRow))
    birth_repository = PostgresBirthRepository(db.sessions, cipher)
    birth = BirthChartService(birth_repository, NatalChartEngine(), cipher, SecretHasher(b"h" * 32))
    await birth.create_date_only(guest_id=guest_id, birth_date=date(1990, 3, 15))
    snapshot = await birth_repository.find_current(guest_id)
    assert snapshot is not None
    readings = PostgresReadingRepository(db.sessions, cipher)
    view = await ReadingApplicationService(readings).project(
        guest_id=guest_id, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE
    )
    async with db.sessions() as session:
        plan_id = await session.scalar(select(ReadingPlanRow.id))
    assert plan_id is not None
    plan = await readings.get_plan(guest_id, snapshot.profile_id, plan_id)
    projection = await readings.get_projection(guest_id, snapshot.profile_id, view.scope_key)
    assert plan is not None and projection is not None
    request = compile_daily_rewrite_request(
        plan,
        projection,
        DeterministicVietnameseRenderer().render(plan.plan),
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )
    now = datetime.now(UTC)
    record = RewriteJobRecord(
        id=uuid4(),
        request=request,
        deletion_epoch=uuid4(),
        created_at=now,
        updated_at=now,
        next_attempt_at=now,
    )
    await repository.enqueue(record)
    # History remains, but it is no longer the user's live source.
    await birth.create_date_only(guest_id=guest_id, birth_date=date(1990, 11, 15))

    class Provider:
        calls = 0

        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            self.calls += 1
            raise AssertionError("obsolete personal data must not leave the system")

    provider = Provider()
    worker = ContentRewriteWorker(
        repository,
        provider,
        DatabaseRewriteAuthorization(db.sessions),
        ReadingRewriteProjector(readings),
        daily_token_budget=100_000 if with_budget else None,
        daily_cost_budget_cents=100 if with_budget else None,
        monthly_cost_budget_cents=100 if with_budget else None,
    )
    assert await worker.process_one()
    assert provider.calls == 0
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row is not None and row.status in {"failed", "cancelled"}
        assert row.budget_reserved_cost_nanos == 0
        assert await session.get(ContentRewriteSpendMonthRow, now.strftime("%Y-%m")) is None
    with pytest.raises(PermissionError):
        await repository.enqueue(record.model_copy(update={"id": uuid4()}))


async def test_valid_birthless_tarot_projects_and_terminalizes_together(fenced):  # type: ignore[no-untyped-def]
    db, repository, cipher, _, view, record = fenced

    class Provider:
        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            return RewriteGenerationSuccess(key=request.key, output=_output(view))

    await ContentRewriteWorker(
        repository,
        Provider(),
        DatabaseRewriteAuthorization(db.sessions),
        TarotRewriteProjector(db.sessions, cipher),
    ).process_one()
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row is not None and row.status == "succeeded"
        parent = await session.get(TarotSessionRow, view.id)
        assert parent is not None
        payload = json.loads(
            cipher.decrypt(parent.payload_ciphertext, context=f"tarot-session:{view.id}".encode())
        )
        assert (
            payload["reading"]["provenance"]["renderer_version"] == TAROT_REWRITE_RENDERER_VERSION
        )


async def test_unsafe_rewrite_keeps_local_revision_and_debit_without_resend(fenced):  # type: ignore[no-untyped-def]
    db, repository, cipher, _, view, record = fenced

    class Provider:
        calls = 0

        async def generate_rewrite(self, request):  # type: ignore[no-untyped-def]
            self.calls += 1
            output = _output(view)
            output["closing_question"] = "Người kia chắc chắn yêu bạn, bạn muốn hỏi gì?"
            return RewriteGenerationSuccess(key=request.key, output=output)

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
    assert await worker.process_one()
    assert not await worker.process_one()
    assert provider.calls == 1
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row is not None and row.status == "failed" and row.last_result == "gate_rejected"
        month = await session.get(ContentRewriteSpendMonthRow, datetime.now(UTC).strftime("%Y-%m"))
        assert month is not None and month.reserved_cost_nanos > 0
        parent = await session.get(TarotSessionRow, view.id)
        payload = json.loads(
            cipher.decrypt(parent.payload_ciphertext, context=f"tarot-session:{view.id}".encode())
        )
        assert payload["reading"] == view.reading.model_dump(mode="json")


@pytest.mark.parametrize("withdrawal", ["consent", "guest", "parent", "deleting"])
async def test_withdrawal_wins_no_provider_or_projection(fenced, withdrawal):  # type: ignore[no-untyped-def]
    db, repository, _cipher, guest_id, view, record = fenced
    lease = await repository.lease(now=datetime.now(UTC), lease_for_seconds=120)
    assert lease is not None
    if withdrawal == "consent":
        await PostgresGuestRepository(db.sessions).revoke_consent(
            guest_id, consent_definition(RewriteConsentScope.PERSONAL).purpose, datetime.now(UTC)
        )
    else:
        async with db.sessions() as session, session.begin():
            if withdrawal == "guest":
                await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest_id))
            elif withdrawal == "parent":
                await session.execute(delete(TarotSessionRow).where(TarotSessionRow.id == view.id))
            else:
                guest = await session.get(GuestSessionRow, guest_id)
                guest.state = "deleting"
    async with repository.execution_guard(lease) as allowed:
        assert allowed is False
    async with db.sessions() as session:
        row = await session.get(ContentRewriteJobRow, record.id)
        assert row is None or withdrawal == "deleting"
    if withdrawal != "deleting":
        with pytest.raises(PermissionError):
            await repository.enqueue(record)


async def test_projection_write_rolled_back_when_finalization_fails(fenced):  # type: ignore[no-untyped-def]
    db, repository, cipher, _, view, _ = fenced
    lease = await repository.lease(now=datetime.now(UTC), lease_for_seconds=120)
    assert lease is not None
    async with db.sessions() as session:
        original = (await session.get(TarotSessionRow, view.id)).payload_ciphertext
    with pytest.raises(RuntimeError, match="synthetic failure"):
        async with repository.execution_guard(lease) as allowed:
            assert allowed
            decision = await TarotRewriteProjector(db.sessions, cipher).validate_and_project(
                lease.request, _output(view), completed_at=datetime.now(UTC)
            )
            assert decision.accepted
            raise RuntimeError("synthetic failure")
    async with db.sessions() as session:
        assert (await session.get(TarotSessionRow, view.id)).payload_ciphertext == original


async def test_borrowed_rewrite_session_cannot_cross_factories(fenced):  # type: ignore[no-untyped-def]
    db, repository, _, _, _, _ = fenced
    lease = await repository.lease(now=datetime.now(UTC), lease_for_seconds=120)
    assert lease is not None
    async with repository.execution_guard(lease) as allowed:
        assert allowed
        from sqlalchemy.ext.asyncio import async_sessionmaker

        other = async_sessionmaker(db.engine)
        with pytest.raises(RuntimeError, match="crossed database"):
            async with rewrite_session(other):
                pass


@pytest.mark.parametrize("purpose", list(ReadingPurpose))
@pytest.mark.parametrize("rollback", [False, True])
async def test_reading_projectors_share_atomic_revision_and_publication(fenced, purpose, rollback):  # type: ignore[no-untyped-def]
    from app.domains.birth.tables import BirthProfileRow
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.renderers import DeterministicVietnameseRenderer
    from app.domains.readings.rewrite import (
        ReadingRewriteProjector,
        compile_daily_rewrite_request,
        compile_reading_rewrite_request,
    )
    from app.domains.readings.tables import ReadingRevisionRow
    from tests.content_rewrite.test_daily_rewrite import _good_output
    from tests.content_rewrite.test_daily_rewrite import _records as daily_records
    from tests.content_rewrite.test_reading_rewrite import _output as long_output
    from tests.content_rewrite.test_reading_rewrite import _records as long_records

    db, repository, cipher, _, _, _ = fenced
    # Drop the fixture's unrelated queued Tarot job so this lease selects the reading.
    async with db.sessions() as session, session.begin():
        await session.execute(delete(ContentRewriteJobRow))
    plan, projection, revision = (
        daily_records() if purpose == ReadingPurpose.DAILY_NOTE else long_records(purpose)
    )
    now = datetime.now(UTC)
    definition = consent_definition(RewriteConsentScope.PERSONAL)
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=plan.guest_id,
                token_hash=plan.guest_id.bytes * 2,
                csrf_hash=b"c" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
        await session.flush()
        session.add(
            ConsentRow(
                guest_id=plan.guest_id,
                version=definition.version,
                purpose=definition.purpose,
                accepted_at=now,
            )
        )
        session.add(
            BirthProfileRow(
                id=plan.profile_id, guest_id=plan.guest_id, created_at=now, updated_at=now
            )
        )
    readings = PostgresReadingRepository(db.sessions, cipher)
    await readings.save_or_replay_plan(plan)
    await readings.save_or_replay_revision(revision)
    await readings.get_or_create_projection(
        projection.model_copy(update={"active_revision_id": None})
    )
    await readings.publish_available(
        plan.guest_id, plan.profile_id, projection.scope_key, revision.id
    )
    baseline = DeterministicVietnameseRenderer().render(plan.plan)
    if purpose == ReadingPurpose.DAILY_NOTE:
        request = compile_daily_rewrite_request(
            plan,
            projection,
            baseline,
            model_version="gpt-6-luna",
            prompt_version="surface-rewrite-v1",
        )
        output = _good_output(baseline)
    else:
        request = compile_reading_rewrite_request(
            plan,
            projection,
            baseline,
            model_version="gpt-6-luna",
            prompt_version="surface-rewrite-v1",
        )
        output = long_output(plan)
        if purpose == ReadingPurpose.PERSONALIZED_SKY:
            output = {
                "hook": baseline.hook,
                "explanation": baseline.thesis,
                "everyday_example": baseline.manifestation,
                "bounded_action": baseline.micro_action,
            }
    assert request is not None
    await repository.enqueue(
        RewriteJobRecord(
            id=uuid4(),
            request=request,
            deletion_epoch=uuid4(),
            created_at=now,
            updated_at=now,
            next_attempt_at=now,
        )
    )
    lease = await repository.lease(now=now, lease_for_seconds=120)
    assert lease is not None

    async def project() -> None:
        async with repository.execution_guard(lease) as allowed:
            assert allowed
            decision = await ReadingRewriteProjector(readings).validate_and_project(
                request, output, completed_at=now
            )
            assert decision.accepted
            if rollback:
                raise RuntimeError("rollback")
            assert await repository.succeed(
                lease=lease,
                gate_receipt_id=decision.gate_receipt_id,
                output_fingerprint="f" * 64,
                input_tokens=10,
                output_tokens=10,
                cost_nanos=100,
                completed_at=now,
            )

    if rollback:
        with pytest.raises(RuntimeError, match="rollback"):
            await project()
    else:
        await project()
    updated = await readings.get_projection(plan.guest_id, plan.profile_id, projection.scope_key)
    assert updated is not None
    assert updated.active_revision_id == revision.id
    assert (updated.available_revision_id is None) == rollback
    async with db.sessions() as session:
        revisions = tuple(
            await session.scalars(
                select(ReadingRevisionRow).where(ReadingRevisionRow.plan_id == plan.id)
            )
        )
        assert len(revisions) == (1 if rollback else 2)
