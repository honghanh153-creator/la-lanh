import json
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, or_, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from app.domains.accounts.postgres import account_transaction, lock_owner
from app.domains.content_rewrite.tables import RewriteSendFenceRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.errors import GuestExpired
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.errors import HistoryBusy
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.domains.human_tarot.tables import HumanTarotRequestRow
from app.domains.mood.tables import MoodCheckInRow
from app.domains.radar.tables import RadarRequestRow
from app.domains.readings.tables import (
    ReadingGenerationAttemptRow,
    ReadingPlanRow,
    ReadingProjectionRow,
    ReadingRevisionRow,
)
from app.domains.resonance.tables import ResonanceFeedbackRow
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import EnvelopeCipher

CONSENT_VERSION = "history-retention-v1"
HISTORY_WINDOW = timedelta(days=30)
PURGE_WINDOW = timedelta(days=29, hours=18)
# Owner decision 2026-10-20: automatic Daily-note history (notes, Daily projections and plans with
# their rewrite revisions) is hidden 24 hours after creation and becomes eligible for physical
# deletion from 18 hours. Physical deletion happens at the first six-hour cleanup run after the
# row is eligible, so it is not a proven 24-hour bound: today's note stays until the local day
# ends, an owner's send fence defers a run, and a live child below keeps its root.
# Saved notes and today's note are exempt as before; a note's mood is attached and goes with it.
DAILY_HISTORY_WINDOW = timedelta(hours=24)
DAILY_PURGE_WINDOW = timedelta(hours=18)
PRODUCT_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


async def activate_policy(session: AsyncSession, guest_id: UUID, now: datetime) -> datetime:
    """Caller owns the guest lock. Never reset activation or shorten legacy grace."""
    row = await session.get(HistoryRetentionPolicyRow, guest_id)
    if row is None:
        row = HistoryRetentionPolicyRow(
            guest_id=guest_id, consent_version=CONSENT_VERSION, activated_at=now
        )
        session.add(row)
        await session.flush()
    return row.activated_at


def expired_history(
    guest_id: InstrumentedAttribute[UUID],
    created_at: InstrumentedAttribute[datetime],
    now: datetime,
    *,
    physical: bool = False,
    daily: bool = False,
) -> ColumnElement[bool]:
    if daily:
        window = DAILY_PURGE_WINDOW if physical else DAILY_HISTORY_WINDOW
    else:
        window = PURGE_WINDOW if physical else HISTORY_WINDOW
    return (created_at <= now - window) & select(HistoryRetentionPolicyRow.guest_id).where(
        HistoryRetentionPolicyRow.guest_id == guest_id,
        or_(
            created_at >= HistoryRetentionPolicyRow.activated_at,
            # Existing content receives a full 30-day disclosure transition.
            HistoryRetentionPolicyRow.activated_at <= now - HISTORY_WINDOW,
        ),
    ).exists()


def live_daily_children(now: datetime) -> ColumnElement[bool]:
    """A Daily note that a child with its own unexpired contract still references: a small
    experiment awaiting review, resonance feedback, or an unrevoked share link. Automatic cleanup
    keeps that root (hidden) until the child expires, instead of cascading the child away early."""

    experiment = (
        select(DailyExperimentRow.id)
        .where(DailyExperimentRow.daily_note_id == DailyNoteRow.id)
        .where(DailyExperimentRow.expires_at > now)
        .exists()
    )
    feedback = (
        select(ResonanceFeedbackRow.id)
        .where(ResonanceFeedbackRow.daily_note_id == DailyNoteRow.id)
        .where(ResonanceFeedbackRow.expires_at > now)
        .exists()
    )
    share = (
        select(ShareArtifactRow.id)
        .where(ShareArtifactRow.daily_note_id == DailyNoteRow.id)
        .where(ShareArtifactRow.expires_at > now, ShareArtifactRow.revoked_at.is_(None))
        .exists()
    )
    return experiment | feedback | share


def saved_daily_source() -> ColumnElement[bool]:
    return (
        select(SavedNoteRow.id)
        .where(
            SavedNoteRow.guest_id == DailyNoteRow.guest_id,
            SavedNoteRow.daily_note_id == DailyNoteRow.id,
        )
        .exists()
    )


def unavailable_daily(now: datetime) -> ColumnElement[bool]:
    return (
        expired_history(DailyNoteRow.guest_id, DailyNoteRow.created_at, now, daily=True)
        & (DailyNoteRow.note_date < now.astimezone(PRODUCT_TIMEZONE).date())
        & ~saved_daily_source()
    )


def unavailable_projection(now: datetime) -> ColumnElement[bool]:
    return (
        (ReadingProjectionRow.purpose == "daily_note")
        & (ReadingProjectionRow.local_date < now.astimezone(PRODUCT_TIMEZONE).date())
        & expired_history(
            ReadingProjectionRow.guest_id, ReadingProjectionRow.created_at, now, daily=True
        )
    )


async def require_available_projection(
    session: AsyncSession,
    projection: ReadingProjectionRow,
) -> None:
    from app.domains.history.errors import HistoryUnavailable

    if (
        await session.scalar(
            select(ReadingProjectionRow.id).where(
                ReadingProjectionRow.id == projection.id,
                unavailable_projection(datetime.now(UTC)),
            )
        )
        is not None
    ):
        raise HistoryUnavailable


class PostgresHistoryRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._erasure_journal = erasure_journal

    async def status(self, guest_id: UUID) -> datetime | None:
        async with self._sessions() as session:
            return cast(
                datetime | None,
                await session.scalar(
                    select(HistoryRetentionPolicyRow.activated_at).where(
                        HistoryRetentionPolicyRow.guest_id == guest_id
                    )
                ),
            )

    async def activate(self, guest_id: UUID, now: datetime) -> datetime:
        async with account_transaction(self._sessions) as session:
            await self._active_owner(session, guest_id, now)
            return await activate_policy(session, guest_id, now)

    @staticmethod
    async def _active_owner(session: AsyncSession, guest_id: UUID, now: datetime) -> None:
        guest = await lock_owner(session, guest_id)
        if guest is None or guest.state != "active" or guest.expires_at <= now:
            raise GuestExpired

    @staticmethod
    async def _busy(session: AsyncSession, guest_id: UUID, now: datetime) -> bool:
        job = await session.scalar(
            select(RewriteSendFenceRow.job_id)
            .where(
                RewriteSendFenceRow.subject_id == guest_id,
                RewriteSendFenceRow.expires_at > now,
            )
            .limit(1)
            .with_for_update()
        )
        attempt = await session.scalar(
            select(ReadingGenerationAttemptRow.id)
            .where(
                ReadingGenerationAttemptRow.guest_id == guest_id,
                ReadingGenerationAttemptRow.status == "leased",
                ReadingGenerationAttemptRow.request_started_at.is_not(None),
                ReadingGenerationAttemptRow.lease_expires_at > now - timedelta(seconds=60),
            )
            .limit(1)
            .with_for_update()
        )
        return job is not None or attempt is not None

    async def clear(self, guest_id: UUID, now: datetime) -> int:
        async with account_transaction(self._sessions) as session:
            await self._active_owner(session, guest_id, now)
            if await self._busy(session, guest_id, now):
                raise HistoryBusy
            return await self.clear_in_session(session, guest_id, now)

    async def clear_in_session(self, session: AsyncSession, guest_id: UUID, now: datetime) -> int:
        """A manual clear inside the caller's owner-locked, authorized transaction.

        The journal fact and the deletion commit or roll back together (audit P07, option A).
        Every manual clear path, the HTTP service included, goes through here.
        """

        if self._erasure_journal is not None:
            self._erasure_journal.record(session, ErasureKind.HISTORY_CLEARED, guest_id, now)
        return await self._erase(session, guest_id, now, manual=True, batch_size=None)

    async def replay_clear(self, guest_id: UUID, cleared_at: datetime) -> int:
        """Re-apply a journaled manual clear after a restore, judged at its original time."""

        async with account_transaction(self._sessions) as session:
            return await self._erase(session, guest_id, cleared_at, manual=True, batch_size=None)

    async def purge_expired(self, now: datetime, batch_size: int = 500) -> int:
        """Bound each transaction to one owner's batch, visiting owners in UUID order."""
        if not 1 <= batch_size <= 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        # Keyset iteration avoids starving later owners behind protected/current sources.
        last: UUID | None = None
        removed = 0
        while removed < batch_size:
            async with account_transaction(self._sessions) as session:
                query = select(GuestSessionRow.id).order_by(GuestSessionRow.id).limit(1)
                if last is not None:
                    query = query.where(GuestSessionRow.id > last)
                guest_id = await session.scalar(query.with_for_update(skip_locked=True))
                if guest_id is None:
                    break
                last = guest_id
                if await self._busy(session, guest_id, now):
                    continue
                removed += await self._erase(
                    session, guest_id, now, manual=False, batch_size=batch_size - removed
                )
        return removed

    async def remaining(self, now: datetime) -> int:
        """Count eligible roots, including busy owners, without deleting or decrypting outputs."""
        total = 0
        async with self._sessions() as session:
            owners = await session.scalars(select(GuestSessionRow.id))
            for guest_id in owners:
                for model, criteria in self._criteria(guest_id, now, manual=False):
                    total += int(
                        await session.scalar(
                            select(func.count()).select_from(model).where(criteria)
                        )
                        or 0
                    )
                total += len(await self._daily_plan_ids(session, guest_id, now, manual=False))
        return total

    @staticmethod
    def _criteria(
        guest_id: UUID,
        now: datetime,
        *,
        manual: bool,
    ) -> list[tuple[Any, ColumnElement[bool]]]:
        today = now.astimezone(PRODUCT_TIMEZONE).date()
        daily = (
            (DailyNoteRow.guest_id == guest_id)
            & (DailyNoteRow.note_date < today)
            & ~saved_daily_source()
        )
        moods = MoodCheckInRow.guest_id == guest_id
        tarot = TarotSessionRow.guest_id == guest_id
        # US-24: removing a request also clears its Google Sheet row (the slot loses its link).
        human_tarot = HumanTarotRequestRow.guest_id == guest_id
        radar = RadarRequestRow.owner_guest_id == guest_id
        resonance = ResonanceFeedbackRow.guest_id == guest_id
        experiments = DailyExperimentRow.guest_id == guest_id
        # A revoked or expired link already answers like an unknown one; its encrypted snapshot
        # has no further use, even when the note it came from is saved (audit P05). Live links
        # stay, in both modes.
        shares = (ShareArtifactRow.guest_id == guest_id) & (
            ShareArtifactRow.revoked_at.is_not(None) | (ShareArtifactRow.expires_at <= now)
        )
        if manual:
            tarot &= TarotSessionRow.state == "complete"
            # Finished ones only; a request still waiting for its reading is cancelled explicitly.
            human_tarot &= HumanTarotRequestRow.status.in_(
                ("ready", "unfulfilled", "cancelled")
            ) & (HumanTarotRequestRow.release_at <= now)
            radar &= RadarRequestRow.completed_at.is_not(None)
        else:
            daily &= expired_history(
                DailyNoteRow.guest_id, DailyNoteRow.created_at, now, physical=True, daily=True
            ) & ~live_daily_children(now)
            moods &= expired_history(
                MoodCheckInRow.guest_id, MoodCheckInRow.created_at, now, physical=True
            )
            tarot &= TarotSessionRow.expires_at <= now
            human_tarot &= HumanTarotRequestRow.expires_at <= now
            radar &= RadarRequestRow.expires_at <= now
            resonance &= ResonanceFeedbackRow.expires_at <= now
            experiments &= DailyExperimentRow.expires_at <= now
        # Delete feedback first, without affecting its source or consent.
        return [
            (MoodCheckInRow, moods),
            (ResonanceFeedbackRow, resonance),
            (DailyExperimentRow, experiments),
            (ShareArtifactRow, shares),
            (TarotSessionRow, tarot),
            (HumanTarotRequestRow, human_tarot),
            (RadarRequestRow, radar),
            (DailyNoteRow, daily),
        ]

    async def _daily_plan_ids(
        self,
        session: AsyncSession,
        guest_id: UUID,
        now: datetime,
        *,
        manual: bool,
        limit: int | None = None,
    ) -> list[UUID]:
        today = now.astimezone(PRODUCT_TIMEZONE).date()
        revisions = (
            select(ReadingRevisionRow.id)
            .where(ReadingRevisionRow.plan_id == ReadingPlanRow.id)
            .correlate(ReadingPlanRow)
        )
        protected_projection = (
            select(ReadingProjectionRow.id)
            .where(
                or_(
                    ReadingProjectionRow.purpose != "daily_note",
                    ReadingProjectionRow.local_date >= today,
                ),
                or_(
                    ReadingProjectionRow.active_revision_id.in_(revisions),
                    ReadingProjectionRow.available_revision_id.in_(revisions),
                ),
            )
            .exists()
        )
        saved = select(SavedNoteRow.id).where(SavedNoteRow.revision_id.in_(revisions)).exists()
        # Unsent attempts are not a retention exemption. Deleting their plan under
        # the owner lock cascades the attempt; a waiting worker must then fail its
        # send-boundary recheck. _busy guards actual provider sends before erasure.
        # Do not filter busy plans here: remaining() must report blocked backlog.
        query = select(ReadingPlanRow).where(
            ReadingPlanRow.guest_id == guest_id,
            ~protected_projection,
            ~saved,
        )
        if not manual:
            # Revisions of a plan carry experiment, feedback and share children with their own
            # expiry; keep the plan until they expire rather than cascading them away early.
            live_children = or_(
                select(DailyExperimentRow.id)
                .where(DailyExperimentRow.revision_id.in_(revisions))
                .where(DailyExperimentRow.expires_at > now)
                .exists(),
                select(ResonanceFeedbackRow.id)
                .where(ResonanceFeedbackRow.revision_id.in_(revisions))
                .where(ResonanceFeedbackRow.expires_at > now)
                .exists(),
                select(ShareArtifactRow.id)
                .where(ShareArtifactRow.revision_id.in_(revisions))
                .where(ShareArtifactRow.expires_at > now, ShareArtifactRow.revoked_at.is_(None))
                .exists(),
            )
            query = query.where(~live_children)
            query = query.where(
                expired_history(
                    ReadingPlanRow.guest_id,
                    ReadingPlanRow.created_at,
                    now,
                    physical=True,
                    daily=True,
                )
            )
        ids: list[UUID] = []
        last: UUID | None = None
        # Purpose lives in the existing encrypted plan. Page through it without changing IDs
        # or adding a second metadata authority. Non-daily plans never expire as history.
        while limit is None or len(ids) < limit:
            page = query.order_by(ReadingPlanRow.id).limit(100)
            if last is not None:
                page = page.where(ReadingPlanRow.id > last)
            rows = list(await session.scalars(page))
            if not rows:
                break
            for row in rows:
                last = row.id
                payload = json.loads(
                    self._envelope.decrypt(
                        row.plan_ciphertext, context=f"reading-plan:{row.id}".encode()
                    )
                )
                if payload["purpose"] == "daily_note":
                    ids.append(row.id)
                    if limit is not None and len(ids) >= limit:
                        return ids
        return ids

    async def _erase(
        self,
        session: AsyncSession,
        guest_id: UUID,
        now: datetime,
        *,
        manual: bool,
        batch_size: int | None,
    ) -> int:
        removed = 0
        for model, criteria in self._criteria(guest_id, now, manual=manual):
            remaining = None if batch_size is None else batch_size - removed
            if remaining == 0:
                return removed
            if remaining is None:
                result = await session.execute(delete(model).where(criteria))
                removed += int(cast(CursorResult[Any], result).rowcount or 0)
                continue
            query = select(model.id).where(criteria).order_by(model.id)
            if remaining is not None:
                query = query.limit(remaining)
            ids = list(await session.scalars(query))
            if ids:
                result = await session.execute(delete(model).where(model.id.in_(ids)))
                removed += int(cast(CursorResult[Any], result).rowcount or 0)
        remaining = None if batch_size is None else batch_size - removed
        if remaining == 0:
            return removed
        ids = await self._daily_plan_ids(
            session,
            guest_id,
            now,
            manual=manual,
            limit=remaining,
        )
        if ids:
            result = await session.execute(delete(ReadingPlanRow).where(ReadingPlanRow.id.in_(ids)))
            removed += int(cast(CursorResult[Any], result).rowcount or 0)
        return removed
