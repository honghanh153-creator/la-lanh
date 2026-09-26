import json
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.astro.models import TimePrecision
from app.domains.birth.tables import BirthProfileRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.experiments.errors import (
    ExperimentConflict,
    ExperimentReplaceRequired,
    ExperimentTargetNotFound,
)
from app.domains.experiments.models import (
    DailyExperiment,
    ExperimentDraft,
    ExperimentOutcome,
    ExperimentState,
)
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.readings.models import (
    BackgroundLens,
    ExperimentProjection,
    PlanMode,
    ReadingPurpose,
    canonical_lens_variant,
    experiment_projection_for,
)
from app.domains.readings.postgres import _plan_record, _revision_record
from app.domains.readings.tables import ReadingPlanRow, ReadingProjectionRow, ReadingRevisionRow
from app.infrastructure.crypto import EnvelopeCipher

EXPERIMENT_PURPOSE = "action_experiment"


class PostgresExperimentRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def choose_with_consent(
        self,
        draft: ExperimentDraft,
        *,
        consent_version: str,
        expected_experiment_id: UUID | None,
        expected_version: int | None,
    ) -> DailyExperiment:
        async with self._sessions() as session, session.begin():
            projection = await self._require_owned_active_target(session, draft)
            await self._delete_expired_for_guest(session, draft.guest_id, draft.created_at)
            current = await self._open_row(session, draft.guest_id, lock=True)
            if current is not None and self._same_target(current, draft):
                return await self._record(session, current)
            if current is not None:
                if expected_experiment_id is None or expected_version is None:
                    raise ExperimentReplaceRequired
                if current.id != expected_experiment_id or current.version != expected_version:
                    raise ExperimentConflict
            elif expected_experiment_id is not None or expected_version is not None:
                raise ExperimentConflict

            await self._accept_consent(
                session,
                guest_id=draft.guest_id,
                version=consent_version,
                accepted_at=draft.created_at,
            )
            await self._after_consent()
            version = current.version + 1 if current is not None else 1
            if current is not None:
                await session.delete(current)
                await session.flush()
            row = DailyExperimentRow(
                id=draft.id,
                version=version,
                guest_id=draft.guest_id,
                daily_note_id=draft.daily_note_id,
                revision_id=draft.revision_id,
                state=ExperimentState.CHOSEN.value,
                payload_ciphertext="",
                created_at=draft.created_at,
                updated_at=draft.created_at,
                expires_at=draft.expires_at,
                reflected_at=None,
            )
            row.payload_ciphertext = self._encrypt_payload(
                row.id,
                background_lens=draft.background_lens,
                action_key=draft.action_key,
                outcome=None,
            )
            try:
                async with session.begin_nested():
                    session.add(row)
                    await session.flush([row])
            except IntegrityError as error:
                raise ExperimentConflict from error
            return self._record_from_projection(row, projection, outcome=None)

    async def current(self, guest_id: UUID, *, now: datetime) -> DailyExperiment | None:
        async with self._sessions() as session, session.begin():
            await self._delete_expired_for_guest(session, guest_id, now)
            row = await self._open_row(session, guest_id, lock=True)
            if row is not None and await self._delete_if_stale_chart(session, row):
                return None
            return await self._record(session, row) if row is not None else None

    async def undo(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        now: datetime,
    ) -> bool:
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(DailyExperimentRow).where(
                    DailyExperimentRow.id == experiment_id,
                    DailyExperimentRow.guest_id == guest_id,
                    DailyExperimentRow.version == expected_version,
                    DailyExperimentRow.state == ExperimentState.CHOSEN.value,
                    DailyExperimentRow.expires_at > now,
                )
            )
            return cast(CursorResult[Any], result).rowcount == 1

    async def reflect(
        self,
        guest_id: UUID,
        *,
        experiment_id: UUID,
        expected_version: int,
        outcome: ExperimentOutcome,
        now: datetime,
    ) -> DailyExperiment | None:
        async with self._sessions() as session, session.begin():
            row = await session.scalar(
                select(DailyExperimentRow)
                .where(
                    DailyExperimentRow.id == experiment_id,
                    DailyExperimentRow.guest_id == guest_id,
                    DailyExperimentRow.version == expected_version,
                    DailyExperimentRow.state == ExperimentState.CHOSEN.value,
                    DailyExperimentRow.expires_at > now,
                )
                .with_for_update()
            )
            if row is None:
                return None
            if await self._delete_if_stale_chart(session, row):
                return None
            lens, action_key, _ = self._payload(row)
            row.state = ExperimentState.REFLECTED.value
            row.updated_at = now
            row.reflected_at = now
            row.payload_ciphertext = self._encrypt_payload(
                row.id,
                background_lens=lens,
                action_key=action_key,
                outcome=outcome,
            )
            await session.flush([row])
            return await self._record(session, row)

    async def purge_expired(self, *, now: datetime, batch_size: int) -> int:
        async with self._sessions() as session, session.begin():
            ids = tuple(
                await session.scalars(
                    select(DailyExperimentRow.id)
                    .where(DailyExperimentRow.expires_at <= now)
                    .order_by(DailyExperimentRow.expires_at, DailyExperimentRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            if not ids:
                return 0
            result = await session.execute(
                delete(DailyExperimentRow).where(DailyExperimentRow.id.in_(ids))
            )
            return int(cast(CursorResult[Any], result).rowcount or 0)

    async def _require_owned_active_target(
        self,
        session: AsyncSession,
        draft: ExperimentDraft,
    ) -> ExperimentProjection:
        owner_id = await session.scalar(
            select(GuestSessionRow.id).where(GuestSessionRow.id == draft.guest_id).with_for_update()
        )
        if owner_id is None:
            raise ExperimentTargetNotFound
        note = await session.scalar(
            select(DailyNoteRow).where(
                DailyNoteRow.id == draft.daily_note_id,
                DailyNoteRow.guest_id == draft.guest_id,
            )
        )
        revision_row = await session.scalar(
            select(ReadingRevisionRow).where(
                ReadingRevisionRow.id == draft.revision_id,
                ReadingRevisionRow.guest_id == draft.guest_id,
            )
        )
        if note is None or revision_row is None:
            raise ExperimentTargetNotFound
        plan_row = await session.scalar(
            select(ReadingPlanRow).where(
                ReadingPlanRow.id == revision_row.plan_id,
                ReadingPlanRow.guest_id == draft.guest_id,
            )
        )
        if plan_row is None:
            raise ExperimentTargetNotFound
        plan = _plan_record(plan_row, self._envelope).plan
        normalized_lens = plan.background_lens or BackgroundLens.AUTO
        if (
            plan.mode is not PlanMode.FULL_SYNTHESIS
            or plan.precision is not TimePrecision.EXACT
            or plan.purpose is not ReadingPurpose.DAILY_NOTE
            or normalized_lens is not draft.background_lens
        ):
            raise ExperimentTargetNotFound
        current_snapshot_id = await session.scalar(
            select(BirthProfileRow.current_snapshot_id).where(
                BirthProfileRow.id == plan_row.profile_id,
                BirthProfileRow.guest_id == draft.guest_id,
            )
        )
        if plan_row.chart_snapshot_id is None or current_snapshot_id != plan_row.chart_snapshot_id:
            raise ExperimentTargetNotFound
        active_projection_id = await session.scalar(
            select(ReadingProjectionRow.id).where(
                ReadingProjectionRow.guest_id == draft.guest_id,
                ReadingProjectionRow.profile_id == plan_row.profile_id,
                ReadingProjectionRow.purpose == ReadingPurpose.DAILY_NOTE.value,
                ReadingProjectionRow.local_date == note.note_date,
                ReadingProjectionRow.lens_variant == canonical_lens_variant(draft.background_lens),
                ReadingProjectionRow.active_revision_id == draft.revision_id,
            )
        )
        if active_projection_id is None:
            raise ExperimentTargetNotFound
        revision = _revision_record(revision_row, self._envelope)
        candidate = revision.evaluation.publishable_candidate
        if candidate is None:
            raise ExperimentTargetNotFound
        projection = experiment_projection_for(revision.id, candidate.micro_action)
        if projection.action_key != draft.action_key:
            raise ExperimentTargetNotFound
        return projection

    async def _record(self, session: AsyncSession, row: DailyExperimentRow) -> DailyExperiment:
        revision_row = await session.scalar(
            select(ReadingRevisionRow).where(
                ReadingRevisionRow.id == row.revision_id,
                ReadingRevisionRow.guest_id == row.guest_id,
            )
        )
        if revision_row is None:
            raise ExperimentTargetNotFound
        revision = _revision_record(revision_row, self._envelope)
        candidate = revision.evaluation.publishable_candidate
        if candidate is None:
            raise ExperimentTargetNotFound
        projection = experiment_projection_for(revision.id, candidate.micro_action)
        lens, action_key, outcome = self._payload(row)
        if action_key != projection.action_key:
            raise ValueError("stored experiment action does not match its accepted revision")
        return self._record_from_projection(row, projection, outcome=outcome, lens=lens)

    def _record_from_projection(
        self,
        row: DailyExperimentRow,
        projection: ExperimentProjection,
        *,
        outcome: ExperimentOutcome | None,
        lens: BackgroundLens | None = None,
    ) -> DailyExperiment:
        stored_lens, action_key, _ = self._payload(row)
        return DailyExperiment(
            id=row.id,
            version=row.version,
            daily_note_id=row.daily_note_id,
            revision_id=row.revision_id,
            state=ExperimentState(row.state),
            background_lens=lens or stored_lens,
            action_key=action_key,
            projection=projection,
            outcome=outcome,
            created_at=row.created_at,
            updated_at=row.updated_at,
            expires_at=row.expires_at,
            reflected_at=row.reflected_at,
        )

    async def _open_row(
        self, session: AsyncSession, guest_id: UUID, *, lock: bool
    ) -> DailyExperimentRow | None:
        statement = select(DailyExperimentRow).where(
            DailyExperimentRow.guest_id == guest_id,
            DailyExperimentRow.state == ExperimentState.CHOSEN.value,
        )
        if lock:
            statement = statement.with_for_update()
        return cast(DailyExperimentRow | None, await session.scalar(statement))

    async def _delete_expired_for_guest(
        self, session: AsyncSession, guest_id: UUID, now: datetime
    ) -> None:
        await session.execute(
            delete(DailyExperimentRow).where(
                DailyExperimentRow.guest_id == guest_id,
                DailyExperimentRow.expires_at <= now,
            )
        )

    async def _delete_if_stale_chart(
        self,
        session: AsyncSession,
        row: DailyExperimentRow,
    ) -> bool:
        current_plan_id = await session.scalar(
            select(ReadingPlanRow.id)
            .join(ReadingRevisionRow, ReadingRevisionRow.plan_id == ReadingPlanRow.id)
            .join(BirthProfileRow, BirthProfileRow.id == ReadingPlanRow.profile_id)
            .where(
                ReadingRevisionRow.id == row.revision_id,
                ReadingRevisionRow.guest_id == row.guest_id,
                ReadingPlanRow.guest_id == row.guest_id,
                BirthProfileRow.guest_id == row.guest_id,
                ReadingPlanRow.chart_snapshot_id.is_not(None),
                ReadingPlanRow.chart_snapshot_id == BirthProfileRow.current_snapshot_id,
            )
        )
        if current_plan_id is not None:
            return False
        await session.delete(row)
        await session.flush([row])
        return True

    def _same_target(self, row: DailyExperimentRow, draft: ExperimentDraft) -> bool:
        lens, action_key, _ = self._payload(row)
        return (
            row.daily_note_id == draft.daily_note_id
            and row.revision_id == draft.revision_id
            and lens is draft.background_lens
            and action_key == draft.action_key
        )

    async def _accept_consent(
        self,
        session: AsyncSession,
        *,
        guest_id: UUID,
        version: str,
        accepted_at: datetime,
    ) -> None:
        row = await session.scalar(
            select(ConsentRow).where(
                ConsentRow.guest_id == guest_id,
                ConsentRow.purpose == EXPERIMENT_PURPOSE,
            )
        )
        if row is None:
            row = ConsentRow(
                guest_id=guest_id,
                version=version,
                purpose=EXPERIMENT_PURPOSE,
                accepted_at=accepted_at,
            )
            session.add(row)
            await session.flush([row])
        row.version = version
        row.accepted_at = accepted_at
        row.revoked_at = None

    async def _after_consent(self) -> None:
        """Fault-injection seam proving consent and experiment writes are atomic."""

    def _encrypt_payload(
        self,
        row_id: UUID,
        *,
        background_lens: BackgroundLens,
        action_key: str,
        outcome: ExperimentOutcome | None,
    ) -> str:
        payload = json.dumps(
            {
                "action_key": action_key,
                "background_lens": background_lens.value,
                "outcome": outcome.value if outcome is not None else None,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        if len(payload) > 256:
            raise ValueError("experiment payload exceeds its bounded contract")
        return self._envelope.encrypt(payload, context=_payload_context(row_id))

    def _payload(
        self, row: DailyExperimentRow
    ) -> tuple[BackgroundLens, str, ExperimentOutcome | None]:
        payload = json.loads(
            self._envelope.decrypt(
                row.payload_ciphertext,
                context=_payload_context(row.id),
            )
        )
        if not isinstance(payload, dict) or set(payload) != {
            "action_key",
            "background_lens",
            "outcome",
        }:
            raise ValueError("invalid encrypted experiment payload")
        action_key = payload["action_key"]
        if not isinstance(action_key, str) or len(action_key) != 64:
            raise ValueError("invalid encrypted experiment action key")
        raw_outcome = payload["outcome"]
        return (
            BackgroundLens(payload["background_lens"]),
            action_key,
            ExperimentOutcome(raw_outcome) if raw_outcome is not None else None,
        )


def _payload_context(record_id: UUID) -> bytes:
    return f"daily-experiment:{record_id}".encode()
