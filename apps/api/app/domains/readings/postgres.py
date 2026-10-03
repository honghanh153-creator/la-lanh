import json
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import Select, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.astro.models import TimePrecision, Tradition
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.guest.models import GuestState
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.models import (
    CandidateEvaluation,
    GenerationAttemptRecord,
    GenerationAttemptResult,
    GenerationAttemptStatus,
    LeasedGenerationAttempt,
    PlanMode,
    ReadingPlan,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_generation_key,
    canonical_reading_revision_key,
)
from app.domains.readings.tables import (
    ReadingGenerationAttemptRow,
    ReadingPlanRow,
    ReadingProjectionRow,
    ReadingRevisionRow,
)
from app.infrastructure.crypto import EnvelopeCipher


class ImmutableReadingConflictError(ValueError):
    """An idempotency identity was reused for different immutable content."""


class ReadingOwnershipError(ValueError):
    """A requested profile, plan, revision, or projection is outside the owner scope."""


class PostgresReadingRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def save_or_replay_plan(
        self, record: ReadingPlanRecord
    ) -> tuple[ReadingPlanRecord, bool]:
        async with self._sessions() as session, session.begin():
            await _require_profile(session, record.guest_id, record.profile_id)
            if record.chart_snapshot_id is not None:
                await _require_snapshot(
                    session,
                    record.guest_id,
                    record.profile_id,
                    record.chart_snapshot_id,
                )
            existing = await _find_plan_by_key(
                session, record.guest_id, record.profile_id, record.plan_key
            )
            if existing is not None:
                stored = _plan_record(existing, self._envelope)
                _assert_same_plan(stored, record)
                return stored, True

            try:
                async with session.begin_nested():
                    row = ReadingPlanRow(
                        id=record.id,
                        guest_id=record.guest_id,
                        profile_id=record.profile_id,
                        chart_snapshot_id=record.chart_snapshot_id,
                        plan_key=record.plan_key,
                        plan_ciphertext=self._envelope.encrypt(
                            record.plan.model_dump_json(exclude_none=False).encode(),
                            context=_plan_context(record.id),
                        ),
                        created_at=record.created_at,
                    )
                    session.add(row)
                    await session.flush([row])
            except IntegrityError:
                existing = await _find_plan_by_key(
                    session, record.guest_id, record.profile_id, record.plan_key
                )
                if existing is None:
                    raise
                stored = _plan_record(existing, self._envelope)
                _assert_same_plan(stored, record)
                return stored, True
            return _plan_record(row, self._envelope), False

    async def get_plan(
        self, guest_id: UUID, profile_id: UUID, plan_id: UUID
    ) -> ReadingPlanRecord | None:
        async with self._sessions() as session:
            row = await _find_plan(session, guest_id, profile_id, plan_id)
            return _plan_record(row, self._envelope) if row is not None else None

    async def save_or_replay_revision(
        self, record: ReadingRevisionRecord
    ) -> tuple[ReadingRevisionRecord, bool]:
        async with self._sessions() as session, session.begin():
            plan_row = await _find_plan(session, record.guest_id, record.profile_id, record.plan_id)
            if plan_row is None:
                raise ReadingOwnershipError("reading plan does not belong to this profile")
            plan = _plan_record(plan_row, self._envelope)
            _validate_revision_against_plan(record, plan)
            existing = await _find_revision_by_key(
                session, record.guest_id, record.profile_id, record.revision_key
            )
            if existing is not None:
                stored = _revision_record(existing, self._envelope)
                _assert_same_revision(stored, record)
                return stored, True

            try:
                async with session.begin_nested():
                    row = _new_revision_row(record, self._envelope)
                    session.add(row)
                    await session.flush([row])
            except IntegrityError:
                existing = await _find_revision_by_key(
                    session, record.guest_id, record.profile_id, record.revision_key
                )
                if existing is None:
                    raise
                stored = _revision_record(existing, self._envelope)
                _assert_same_revision(stored, record)
                return stored, True
            return _revision_record(row, self._envelope), False

    async def get_revision(
        self, guest_id: UUID, profile_id: UUID, revision_id: UUID
    ) -> ReadingRevisionRecord | None:
        async with self._sessions() as session:
            row = await _find_revision(session, guest_id, profile_id, revision_id)
            return _revision_record(row, self._envelope) if row is not None else None

    async def get_or_create_projection(
        self, record: ReadingProjectionRecord
    ) -> tuple[ReadingProjectionRecord, bool]:
        if record.active_revision_id is not None or record.available_revision_id is not None:
            raise ValueError("new projections must begin without revision pointers")
        async with self._sessions() as session, session.begin():
            await _require_profile(session, record.guest_id, record.profile_id)
            existing = await _find_projection(
                session, record.guest_id, record.profile_id, record.scope_key
            )
            if existing is not None:
                stored = _projection_record(existing)
                _assert_same_projection_scope(stored, record)
                return stored, True

            try:
                async with session.begin_nested():
                    row = ReadingProjectionRow(
                        id=record.id,
                        guest_id=record.guest_id,
                        profile_id=record.profile_id,
                        scope_key=record.scope_key,
                        purpose=record.purpose.value,
                        tradition=record.tradition.value,
                        config_hash=record.config_hash,
                        lens_variant=record.lens_variant,
                        local_date=record.local_date,
                        timezone_name=record.timezone_name,
                        observed_at=record.observed_at,
                        active_revision_id=record.active_revision_id,
                        available_revision_id=record.available_revision_id,
                        acknowledged_aura_transition_id=(record.acknowledged_aura_transition_id),
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                    )
                    session.add(row)
                    await session.flush([row])
            except IntegrityError:
                existing = await _find_projection(
                    session, record.guest_id, record.profile_id, record.scope_key
                )
                if existing is None:
                    raise
                stored = _projection_record(existing)
                _assert_same_projection_scope(stored, record)
                return stored, True
            return _projection_record(row), False

    async def get_projection(
        self, guest_id: UUID, profile_id: UUID, scope_key: str
    ) -> ReadingProjectionRecord | None:
        async with self._sessions() as session:
            row = await _find_projection(session, guest_id, profile_id, scope_key)
            return _projection_record(row) if row is not None else None

    async def publish_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        revision_id: UUID,
    ) -> ReadingProjectionRecord:
        async with self._sessions() as session, session.begin():
            projection = await _find_projection(session, guest_id, profile_id, scope_key)
            revision = await _find_revision(session, guest_id, profile_id, revision_id)
            if projection is None or revision is None:
                raise ReadingOwnershipError("projection and revision must share the owner scope")
            await self._validate_revision_for_projection(session, projection, revision)

            if projection.active_revision_id is None:
                if revision.source != ReadingRevisionSource.DETERMINISTIC.value:
                    raise ValueError("the first active revision must be deterministic")
                activated = await session.execute(
                    update(ReadingProjectionRow)
                    .where(
                        ReadingProjectionRow.id == projection.id,
                        ReadingProjectionRow.guest_id == guest_id,
                        ReadingProjectionRow.profile_id == profile_id,
                        ReadingProjectionRow.active_revision_id.is_(None),
                    )
                    .values(
                        active_revision_id=revision.id,
                        available_revision_id=None,
                        updated_at=max(projection.updated_at, revision.created_at),
                    )
                )
                if cast(CursorResult[Any], activated).rowcount == 1:
                    refreshed = await _find_projection(session, guest_id, profile_id, scope_key)
                    if refreshed is None:  # pragma: no cover - updated in this transaction.
                        raise RuntimeError("projection disappeared after activation")
                    return _projection_record(refreshed)
                await session.refresh(projection)

            if projection.active_revision_id != revision.id:
                active_revision = await _find_revision(
                    session,
                    guest_id,
                    profile_id,
                    cast(UUID, projection.active_revision_id),
                )
                if (
                    active_revision is not None
                    and active_revision.source == ReadingRevisionSource.GENERATED.value
                    and revision.source == ReadingRevisionSource.DETERMINISTIC.value
                ):
                    # Once a user activates a generated reading, routine refetches must not
                    # advertise the deterministic fallback as a newer (and weaker) update.
                    return _projection_record(projection)
                projection.available_revision_id = revision.id
                projection.updated_at = max(projection.updated_at, revision.created_at)
                await session.flush([projection])
            return _projection_record(projection)

    async def activate_available(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        updated_at: datetime,
        expected_chart_snapshot_id: UUID | None = None,
    ) -> ReadingProjectionRecord | None:
        async with self._sessions() as session, session.begin():
            projection = await _find_projection(session, guest_id, profile_id, scope_key)
            if projection is None or projection.available_revision_id != expected_revision_id:
                return None
            revision = await _find_revision(session, guest_id, profile_id, expected_revision_id)
            if revision is None:  # The composite pointer FK makes this data corruption only.
                raise RuntimeError("available reading revision is missing")
            await self._validate_revision_for_projection(session, projection, revision)
            plan_row = await _find_plan(
                session,
                revision.guest_id,
                revision.profile_id,
                revision.plan_id,
            )
            profile = await session.scalar(_profile_for_activation_query(guest_id, profile_id))
            if plan_row is None:
                return None
            if profile is None:
                return None
            if (
                plan_row.chart_snapshot_id is not None
                and profile.current_snapshot_id != plan_row.chart_snapshot_id
            ):
                return None
            if expected_chart_snapshot_id is not None and (
                plan_row.chart_snapshot_id is None
                or expected_chart_snapshot_id != plan_row.chart_snapshot_id
            ):
                return None
            if expected_chart_snapshot_id is not None:
                plan = _plan_record(plan_row, self._envelope).plan
                if (
                    plan.mode is not PlanMode.FULL_SYNTHESIS
                    or plan.precision is not TimePrecision.EXACT
                ):
                    return None
            result = await session.execute(
                update(ReadingProjectionRow)
                .where(
                    ReadingProjectionRow.id == projection.id,
                    ReadingProjectionRow.guest_id == guest_id,
                    ReadingProjectionRow.profile_id == profile_id,
                    ReadingProjectionRow.scope_key == scope_key,
                    ReadingProjectionRow.available_revision_id == expected_revision_id,
                )
                .values(
                    active_revision_id=expected_revision_id,
                    available_revision_id=None,
                    updated_at=updated_at,
                )
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                return None
            refreshed = await _find_projection(session, guest_id, profile_id, scope_key)
            if refreshed is None:  # pragma: no cover - the updated row cannot disappear here.
                return None
            return _projection_record(refreshed)

    async def acknowledge_aura_transition(
        self,
        guest_id: UUID,
        profile_id: UUID,
        scope_key: str,
        *,
        expected_revision_id: UUID,
        transition_id: str,
        updated_at: datetime,
    ) -> ReadingProjectionRecord | None:
        async with self._sessions() as session, session.begin():
            projection = await _find_projection(session, guest_id, profile_id, scope_key)
            if projection is None or projection.available_revision_id != expected_revision_id:
                return None
            result = await session.execute(
                update(ReadingProjectionRow)
                .where(
                    ReadingProjectionRow.id == projection.id,
                    ReadingProjectionRow.guest_id == guest_id,
                    ReadingProjectionRow.profile_id == profile_id,
                    ReadingProjectionRow.scope_key == scope_key,
                    ReadingProjectionRow.available_revision_id == expected_revision_id,
                )
                .values(
                    acknowledged_aura_transition_id=transition_id,
                    updated_at=max(projection.updated_at, updated_at),
                )
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                return None
            refreshed = await _find_projection(session, guest_id, profile_id, scope_key)
            if refreshed is None:  # pragma: no cover - the updated row cannot disappear here.
                return None
            return _projection_record(refreshed)

    async def enqueue_generation_attempt(
        self, record: GenerationAttemptRecord
    ) -> tuple[GenerationAttemptRecord, bool]:
        if record.status is not GenerationAttemptStatus.PENDING:
            raise ValueError("new generation attempts must be pending")
        async with self._sessions() as session, session.begin():
            plan_row = await _find_plan(session, record.guest_id, record.profile_id, record.plan_id)
            projection = await _find_projection(
                session, record.guest_id, record.profile_id, record.scope_key
            )
            if plan_row is None or projection is None:
                raise ReadingOwnershipError("generation plan and projection must share an owner")
            plan_record = _plan_record(plan_row, self._envelope)
            if plan_record.plan.tradition is not Tradition.WESTERN:
                raise ValueError("generated Jyotish is disabled")
            if (
                plan_record.plan.purpose.value != projection.purpose
                or plan_record.plan.tradition.value != projection.tradition
                or plan_record.plan.config_hash != projection.config_hash
            ):
                raise ValueError("generation plan does not match projection scope")
            if projection.active_revision_id is None:
                raise ValueError("deterministic fallback must be active before enqueue")
            active = await _find_revision(
                session,
                record.guest_id,
                record.profile_id,
                projection.active_revision_id,
            )
            if (
                active is None
                or active.source != ReadingRevisionSource.DETERMINISTIC.value
                or active.plan_id != record.plan_id
            ):
                raise ValueError("generation requires an active deterministic fallback")
            expected_key = canonical_generation_key(
                plan_key=plan_record.plan_key,
                scope_key=record.scope_key,
                provider=record.provider,
                model=record.model,
                prompt_version=record.prompt_version,
            )
            if record.generation_key != expected_key:
                raise ValueError("generation_key does not match its immutable inputs")
            existing = await _find_attempt_by_key(
                session, record.guest_id, record.profile_id, record.generation_key
            )
            if existing is not None:
                stored = _attempt_record(existing)
                _assert_same_attempt(stored, record)
                return stored, True

            try:
                async with session.begin_nested():
                    row = _attempt_row(record)
                    session.add(row)
                    await session.flush([row])
            except IntegrityError:
                existing = await _find_attempt_by_key(
                    session, record.guest_id, record.profile_id, record.generation_key
                )
                if existing is None:
                    raise
                stored = _attempt_record(existing)
                _assert_same_attempt(stored, record)
                return stored, True
            return _attempt_record(row), False

    async def lease_generation_attempt(
        self, *, now: datetime, lease_for_seconds: int
    ) -> LeasedGenerationAttempt | None:
        async with self._sessions() as session, session.begin():
            # A lease that expired after the durable pre-send marker is ambiguous.
            # It is terminal and must never be delivered to the provider again.
            await session.execute(
                update(ReadingGenerationAttemptRow)
                .where(
                    ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                    ReadingGenerationAttemptRow.lease_expires_at <= now,
                    ReadingGenerationAttemptRow.request_started_at.is_not(None),
                )
                .values(
                    status=GenerationAttemptStatus.FAILED.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    last_result=GenerationAttemptResult.AMBIGUOUS.value,
                    updated_at=now,
                )
            )
            await session.execute(
                update(ReadingGenerationAttemptRow)
                .where(
                    ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                    ReadingGenerationAttemptRow.lease_expires_at <= now,
                    ReadingGenerationAttemptRow.request_started_at.is_(None),
                    ReadingGenerationAttemptRow.attempt_count
                    >= ReadingGenerationAttemptRow.max_attempts,
                )
                .values(
                    status=GenerationAttemptStatus.FAILED.value,
                    lease_token=None,
                    lease_expires_at=None,
                    last_result=GenerationAttemptResult.TRANSIENT.value,
                    updated_at=now,
                )
            )
            row = cast(
                ReadingGenerationAttemptRow | None,
                await session.scalar(
                    select(ReadingGenerationAttemptRow)
                    .where(
                        ReadingGenerationAttemptRow.attempt_count
                        < ReadingGenerationAttemptRow.max_attempts,
                        or_(
                            (
                                ReadingGenerationAttemptRow.status.in_(
                                    (
                                        GenerationAttemptStatus.PENDING.value,
                                        GenerationAttemptStatus.RETRY_WAIT.value,
                                    )
                                )
                                & (ReadingGenerationAttemptRow.next_attempt_at <= now)
                            ),
                            (
                                (
                                    ReadingGenerationAttemptRow.status
                                    == GenerationAttemptStatus.LEASED.value
                                )
                                & (ReadingGenerationAttemptRow.lease_expires_at <= now)
                                & ReadingGenerationAttemptRow.request_started_at.is_(None)
                            ),
                        ),
                    )
                    .order_by(
                        ReadingGenerationAttemptRow.next_attempt_at,
                        ReadingGenerationAttemptRow.created_at,
                        ReadingGenerationAttemptRow.id,
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                ),
            )
            if row is None:
                return None
            row.status = GenerationAttemptStatus.LEASED.value
            row.lease_token = uuid4()
            row.lease_expires_at = now + timedelta(seconds=lease_for_seconds)
            row.request_started_at = None
            row.attempt_count += 1
            row.updated_at = now
            await session.flush([row])
            plan_row = await _find_plan(session, row.guest_id, row.profile_id, row.plan_id)
            if plan_row is None:  # Cascades make this unreachable in a valid transaction.
                return None
            return LeasedGenerationAttempt(
                id=row.id,
                plan_record=_plan_record(plan_row, self._envelope),
                scope_key=row.scope_key,
                generation_key=row.generation_key,
                provider=row.provider,
                model=row.model,
                prompt_version=row.prompt_version,
                deletion_epoch=row.deletion_epoch,
                lease_token=row.lease_token,
                lease_expires_at=row.lease_expires_at,
                attempt_count=row.attempt_count,
                max_attempts=row.max_attempts,
            )

    async def mark_generation_request_started(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        started_at: datetime,
    ) -> bool:
        async with self._sessions() as session, session.begin():
            guest_id = await session.scalar(
                select(ReadingGenerationAttemptRow.guest_id).where(
                    ReadingGenerationAttemptRow.id == attempt_id,
                    ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                    ReadingGenerationAttemptRow.lease_token == lease_token,
                    ReadingGenerationAttemptRow.deletion_epoch == deletion_epoch,
                    ReadingGenerationAttemptRow.request_started_at.is_(None),
                    ReadingGenerationAttemptRow.lease_expires_at > started_at,
                )
            )
            if guest_id is None:
                return False

            # Serialize the irreversible provider-send boundary with guest deletion.
            # Whichever transaction holds the guest row first establishes whether the
            # send is allowed or deletion owns the session from this point onward.
            guest = await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            if (
                guest is None
                or guest.state != GuestState.ACTIVE.value
                or guest.expires_at <= started_at
            ):
                return False

            result = await session.execute(
                update(ReadingGenerationAttemptRow)
                .where(
                    ReadingGenerationAttemptRow.id == attempt_id,
                    ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                    ReadingGenerationAttemptRow.lease_token == lease_token,
                    ReadingGenerationAttemptRow.deletion_epoch == deletion_epoch,
                    ReadingGenerationAttemptRow.request_started_at.is_(None),
                    ReadingGenerationAttemptRow.lease_expires_at > started_at,
                )
                .values(request_started_at=started_at, updated_at=started_at)
            )
            return cast(CursorResult[Any], result).rowcount == 1

    async def retry_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        next_attempt_at: datetime,
        updated_at: datetime,
    ) -> bool:
        return await self._finish_attempt(
            attempt_id=attempt_id,
            lease_token=lease_token,
            deletion_epoch=deletion_epoch,
            status=GenerationAttemptStatus.RETRY_WAIT,
            result=result,
            updated_at=updated_at,
            next_attempt_at=next_attempt_at,
        )

    async def fail_generation_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        result: GenerationAttemptResult,
        updated_at: datetime,
    ) -> bool:
        return await self._finish_attempt(
            attempt_id=attempt_id,
            lease_token=lease_token,
            deletion_epoch=deletion_epoch,
            status=GenerationAttemptStatus.FAILED,
            result=result,
            updated_at=updated_at,
            next_attempt_at=updated_at,
        )

    async def _finish_attempt(
        self,
        *,
        attempt_id: UUID,
        lease_token: UUID,
        deletion_epoch: UUID,
        status: GenerationAttemptStatus,
        result: GenerationAttemptResult,
        updated_at: datetime,
        next_attempt_at: datetime,
    ) -> bool:
        async with self._sessions() as session, session.begin():
            statement = (
                update(ReadingGenerationAttemptRow)
                .where(
                    ReadingGenerationAttemptRow.id == attempt_id,
                    ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                    ReadingGenerationAttemptRow.lease_token == lease_token,
                    ReadingGenerationAttemptRow.deletion_epoch == deletion_epoch,
                    ReadingGenerationAttemptRow.request_started_at.is_not(None),
                )
                .values(
                    status=status.value,
                    lease_token=None,
                    lease_expires_at=None,
                    request_started_at=None,
                    next_attempt_at=next_attempt_at,
                    last_result=result.value,
                    updated_at=updated_at,
                )
            )
            if status is GenerationAttemptStatus.RETRY_WAIT:
                statement = statement.where(
                    ReadingGenerationAttemptRow.attempt_count
                    < ReadingGenerationAttemptRow.max_attempts
                )
            executed = await session.execute(statement)
            return cast(CursorResult[Any], executed).rowcount == 1

    async def finalize_generation_success(
        self,
        *,
        lease: LeasedGenerationAttempt,
        revision: ReadingRevisionRecord,
        completed_at: datetime,
    ) -> bool:
        async with self._sessions() as session, session.begin():
            attempt = cast(
                ReadingGenerationAttemptRow | None,
                await session.scalar(
                    select(ReadingGenerationAttemptRow)
                    .where(
                        ReadingGenerationAttemptRow.id == lease.id,
                        ReadingGenerationAttemptRow.status == GenerationAttemptStatus.LEASED.value,
                        ReadingGenerationAttemptRow.lease_token == lease.lease_token,
                        ReadingGenerationAttemptRow.deletion_epoch == lease.deletion_epoch,
                        ReadingGenerationAttemptRow.request_started_at.is_not(None),
                    )
                    .with_for_update()
                ),
            )
            if attempt is None:
                return False
            plan_row = await _find_plan(
                session, attempt.guest_id, attempt.profile_id, attempt.plan_id
            )
            projection = await _find_projection(
                session, attempt.guest_id, attempt.profile_id, attempt.scope_key
            )
            if plan_row is None or projection is None or projection.active_revision_id is None:
                return False
            active = await _find_revision(
                session, attempt.guest_id, attempt.profile_id, projection.active_revision_id
            )
            if (
                active is None
                or active.source != ReadingRevisionSource.DETERMINISTIC.value
                or active.plan_id != attempt.plan_id
            ):
                return False
            plan = _plan_record(plan_row, self._envelope)
            if plan.plan.config_hash != projection.config_hash:
                return False
            _validate_revision_against_plan(revision, plan)
            if (
                revision.source is not ReadingRevisionSource.GENERATED
                or revision.guest_id != attempt.guest_id
                or revision.profile_id != attempt.profile_id
                or revision.plan_id != attempt.plan_id
            ):
                raise ValueError("generated revision does not match its leased attempt")
            existing = await _find_revision_by_key(
                session, revision.guest_id, revision.profile_id, revision.revision_key
            )
            if existing is None:
                revision_row = _new_revision_row(revision, self._envelope)
                session.add(revision_row)
                await session.flush([revision_row])
            else:
                stored = _revision_record(existing, self._envelope)
                _assert_same_revision(stored, revision)
                revision_row = existing

            # Generated content is only advertised as available; it never changes active.
            projection.available_revision_id = revision_row.id
            projection.updated_at = max(projection.updated_at, completed_at)
            attempt.status = GenerationAttemptStatus.SUCCEEDED.value
            attempt.lease_token = None
            attempt.lease_expires_at = None
            attempt.request_started_at = None
            attempt.accepted_revision_id = revision_row.id
            attempt.last_result = GenerationAttemptResult.SUCCESS.value
            attempt.updated_at = completed_at
            await session.flush([projection, attempt])
            return True

    async def _validate_revision_for_projection(
        self,
        session: AsyncSession,
        projection: ReadingProjectionRow,
        revision: ReadingRevisionRow,
    ) -> None:
        plan_row = await _find_plan(
            session, revision.guest_id, revision.profile_id, revision.plan_id
        )
        if plan_row is None:
            raise ReadingOwnershipError("revision plan is outside the projection owner scope")
        plan = _plan_record(plan_row, self._envelope).plan
        if (
            plan.purpose.value != projection.purpose
            or plan.tradition.value != projection.tradition
            or plan.config_hash != projection.config_hash
        ):
            raise ValueError(
                "revision plan does not match the projection purpose, tradition, and config"
            )


async def _require_profile(session: AsyncSession, guest_id: UUID, profile_id: UUID) -> None:
    profile = await session.scalar(
        select(BirthProfileRow.id).where(
            BirthProfileRow.id == profile_id,
            BirthProfileRow.guest_id == guest_id,
        )
    )
    if profile is None:
        raise ReadingOwnershipError("birth profile does not belong to this guest")


def _profile_for_activation_query(
    guest_id: UUID, profile_id: UUID
) -> Select[tuple[BirthProfileRow]]:
    return (
        select(BirthProfileRow)
        .where(
            BirthProfileRow.id == profile_id,
            BirthProfileRow.guest_id == guest_id,
        )
        .with_for_update()
    )


async def _require_snapshot(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, snapshot_id: UUID
) -> None:
    snapshot = await session.scalar(
        select(ChartSnapshotRow.id).where(
            ChartSnapshotRow.id == snapshot_id,
            ChartSnapshotRow.guest_id == guest_id,
            ChartSnapshotRow.profile_id == profile_id,
        )
    )
    if snapshot is None:
        raise ReadingOwnershipError("chart snapshot does not belong to this profile")


async def _find_plan_by_key(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, plan_key: str
) -> ReadingPlanRow | None:
    return cast(
        ReadingPlanRow | None,
        await session.scalar(
            select(ReadingPlanRow).where(
                ReadingPlanRow.guest_id == guest_id,
                ReadingPlanRow.profile_id == profile_id,
                ReadingPlanRow.plan_key == plan_key,
            )
        ),
    )


async def _find_plan(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, plan_id: UUID
) -> ReadingPlanRow | None:
    return cast(
        ReadingPlanRow | None,
        await session.scalar(
            select(ReadingPlanRow).where(
                ReadingPlanRow.id == plan_id,
                ReadingPlanRow.guest_id == guest_id,
                ReadingPlanRow.profile_id == profile_id,
            )
        ),
    )


async def _find_revision_by_key(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, revision_key: str
) -> ReadingRevisionRow | None:
    return cast(
        ReadingRevisionRow | None,
        await session.scalar(
            select(ReadingRevisionRow).where(
                ReadingRevisionRow.guest_id == guest_id,
                ReadingRevisionRow.profile_id == profile_id,
                ReadingRevisionRow.revision_key == revision_key,
            )
        ),
    )


async def _find_revision(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, revision_id: UUID
) -> ReadingRevisionRow | None:
    return cast(
        ReadingRevisionRow | None,
        await session.scalar(
            select(ReadingRevisionRow).where(
                ReadingRevisionRow.id == revision_id,
                ReadingRevisionRow.guest_id == guest_id,
                ReadingRevisionRow.profile_id == profile_id,
            )
        ),
    )


async def _find_projection(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, scope_key: str
) -> ReadingProjectionRow | None:
    return cast(
        ReadingProjectionRow | None,
        await session.scalar(
            select(ReadingProjectionRow).where(
                ReadingProjectionRow.guest_id == guest_id,
                ReadingProjectionRow.profile_id == profile_id,
                ReadingProjectionRow.scope_key == scope_key,
            )
        ),
    )


async def _find_attempt_by_key(
    session: AsyncSession, guest_id: UUID, profile_id: UUID, generation_key: str
) -> ReadingGenerationAttemptRow | None:
    return cast(
        ReadingGenerationAttemptRow | None,
        await session.scalar(
            select(ReadingGenerationAttemptRow).where(
                ReadingGenerationAttemptRow.guest_id == guest_id,
                ReadingGenerationAttemptRow.profile_id == profile_id,
                ReadingGenerationAttemptRow.generation_key == generation_key,
            )
        ),
    )


def _plan_context(record_id: UUID) -> bytes:
    return f"reading-plan:{record_id}".encode()


def _revision_context(record_id: UUID) -> bytes:
    return f"reading-revision:{record_id}".encode()


def _plan_record(row: ReadingPlanRow, envelope: EnvelopeCipher) -> ReadingPlanRecord:
    payload = envelope.decrypt(row.plan_ciphertext, context=_plan_context(row.id))
    return ReadingPlanRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        chart_snapshot_id=row.chart_snapshot_id,
        plan_key=row.plan_key,
        plan=ReadingPlan.model_validate(_json_object(payload)),
        created_at=row.created_at,
    )


def _revision_record(row: ReadingRevisionRow, envelope: EnvelopeCipher) -> ReadingRevisionRecord:
    payload = envelope.decrypt(row.evaluation_ciphertext, context=_revision_context(row.id))
    return ReadingRevisionRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        plan_id=row.plan_id,
        revision_key=row.revision_key,
        source=ReadingRevisionSource(row.source),
        renderer_version=row.renderer_version,
        content_version=row.content_version,
        schema_version=row.schema_version,
        rules_version=row.rules_version,
        gate_policy_version=row.gate_policy_version,
        evaluation=CandidateEvaluation.model_validate(_json_object(payload)),
        created_at=row.created_at,
    )


def _new_revision_row(
    record: ReadingRevisionRecord, envelope: EnvelopeCipher
) -> ReadingRevisionRow:
    return ReadingRevisionRow(
        id=record.id,
        guest_id=record.guest_id,
        profile_id=record.profile_id,
        plan_id=record.plan_id,
        revision_key=record.revision_key,
        source=record.source.value,
        renderer_version=record.renderer_version,
        content_version=record.content_version,
        schema_version=record.schema_version,
        rules_version=record.rules_version,
        gate_policy_version=record.gate_policy_version,
        accepted=True,
        evaluation_ciphertext=envelope.encrypt(
            record.evaluation.model_dump_json(exclude_none=False).encode(),
            context=_revision_context(record.id),
        ),
        created_at=record.created_at,
    )


def _projection_record(row: ReadingProjectionRow) -> ReadingProjectionRecord:
    return ReadingProjectionRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        scope_key=row.scope_key,
        purpose=ReadingPurpose(row.purpose),
        tradition=Tradition(row.tradition),
        config_hash=row.config_hash,
        lens_variant=row.lens_variant,
        local_date=row.local_date,
        timezone_name=row.timezone_name,
        observed_at=row.observed_at,
        active_revision_id=row.active_revision_id,
        available_revision_id=row.available_revision_id,
        acknowledged_aura_transition_id=row.acknowledged_aura_transition_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _attempt_row(record: GenerationAttemptRecord) -> ReadingGenerationAttemptRow:
    return ReadingGenerationAttemptRow(
        id=record.id,
        guest_id=record.guest_id,
        profile_id=record.profile_id,
        plan_id=record.plan_id,
        scope_key=record.scope_key,
        generation_key=record.generation_key,
        provider=record.provider,
        model=record.model,
        prompt_version=record.prompt_version,
        deletion_epoch=record.deletion_epoch,
        status=record.status.value,
        lease_token=record.lease_token,
        lease_expires_at=record.lease_expires_at,
        request_started_at=record.request_started_at,
        attempt_count=record.attempt_count,
        max_attempts=record.max_attempts,
        next_attempt_at=record.next_attempt_at,
        accepted_revision_id=record.accepted_revision_id,
        last_result=record.last_result.value if record.last_result is not None else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _attempt_record(row: ReadingGenerationAttemptRow) -> GenerationAttemptRecord:
    return GenerationAttemptRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        plan_id=row.plan_id,
        scope_key=row.scope_key,
        generation_key=row.generation_key,
        provider=row.provider,
        model=row.model,
        prompt_version=row.prompt_version,
        deletion_epoch=row.deletion_epoch,
        status=GenerationAttemptStatus(row.status),
        lease_token=row.lease_token,
        lease_expires_at=row.lease_expires_at,
        request_started_at=row.request_started_at,
        attempt_count=row.attempt_count,
        max_attempts=row.max_attempts,
        next_attempt_at=row.next_attempt_at,
        accepted_revision_id=row.accepted_revision_id,
        last_result=(
            GenerationAttemptResult(row.last_result) if row.last_result is not None else None
        ),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _json_object(payload: bytes) -> dict[str, object]:
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("encrypted reading payload must be a JSON object")
    return decoded


def _validate_revision_against_plan(
    revision: ReadingRevisionRecord, plan: ReadingPlanRecord
) -> None:
    candidate = revision.evaluation.publishable_candidate
    if candidate is None:  # Protected again at the storage boundary.
        raise ValueError("accepted revision requires publishable content")
    expected_key = canonical_reading_revision_key(
        plan_key=plan.plan_key,
        source=revision.source,
        renderer_version=revision.renderer_version,
        content_version=revision.content_version,
        schema_version=revision.schema_version,
        rules_version=revision.rules_version,
        gate_policy_version=revision.gate_policy_version,
    )
    if revision.revision_key != expected_key:
        raise ValueError("revision_key does not match the canonical revision identity")
    if candidate.plan_hash != plan.plan.plan_hash:
        raise ValueError("accepted candidate does not belong to this reading plan")
    if revision.rules_version != plan.plan.rules_version:
        raise ValueError("revision rules version does not match the reading plan")


def _assert_same_plan(stored: ReadingPlanRecord, requested: ReadingPlanRecord) -> None:
    if stored.chart_snapshot_id != requested.chart_snapshot_id or stored.plan != requested.plan:
        raise ImmutableReadingConflictError("plan_key already belongs to different content")


def _assert_same_revision(stored: ReadingRevisionRecord, requested: ReadingRevisionRecord) -> None:
    comparable_fields = (
        "plan_id",
        "source",
        "renderer_version",
        "content_version",
        "schema_version",
        "rules_version",
        "gate_policy_version",
        "evaluation",
    )
    if any(getattr(stored, field) != getattr(requested, field) for field in comparable_fields):
        raise ImmutableReadingConflictError(
            "revision_key already belongs to different accepted content"
        )


def _assert_same_projection_scope(
    stored: ReadingProjectionRecord, requested: ReadingProjectionRecord
) -> None:
    fields = (
        "purpose",
        "tradition",
        "config_hash",
        "lens_variant",
        "local_date",
        "timezone_name",
        "observed_at",
    )
    if any(getattr(stored, field) != getattr(requested, field) for field in fields):
        raise ImmutableReadingConflictError("scope_key already belongs to a different projection")


def _assert_same_attempt(
    stored: GenerationAttemptRecord, requested: GenerationAttemptRecord
) -> None:
    fields = (
        "plan_id",
        "scope_key",
        "provider",
        "model",
        "prompt_version",
        "max_attempts",
    )
    if any(getattr(stored, field) != getattr(requested, field) for field in fields):
        raise ImmutableReadingConflictError(
            "generation_key already belongs to a different immutable attempt"
        )
