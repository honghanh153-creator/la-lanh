import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.astro.models import ChartType, DateOnlySunResult, NatalChart
from app.domains.birth.errors import (
    BirthDateChangeLimited,
    BirthDateChangeRequiresEdit,
    BirthDateUnchanged,
    BirthProfileChanged,
    BirthProfileNotFound,
)
from app.domains.birth.models import BirthSnapshotRecord, BirthSupplement, BirthSupplementStored
from app.domains.birth.tables import BirthDateChangeRow, BirthProfileRow, ChartSnapshotRow
from app.domains.content_rewrite.send_fence import drain_sends, pending_sends
from app.domains.content_rewrite.tables import ContentRewriteJobRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.models import OnboardingStatus
from app.domains.guest.tables import GuestSessionRow
from app.domains.radar.tables import RadarRequestRow
from app.domains.readings.tables import ReadingPlanRow, ReadingProjectionRow
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresBirthRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._erasure_journal = erasure_journal

    async def save_or_replay(self, record: BirthSnapshotRecord) -> tuple[BirthSnapshotRecord, bool]:
        async with self._sessions() as session, session.begin():
            await session.scalar(
                select(GuestSessionRow)
                .where(GuestSessionRow.id == record.guest_id)
                .with_for_update()
            )
            existing = await session.scalar(
                select(ChartSnapshotRow).where(
                    ChartSnapshotRow.guest_id == record.guest_id,
                    ChartSnapshotRow.input_hash == record.input_hash,
                )
            )
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == record.guest_id)
            )
            if profile is None:
                try:
                    async with session.begin_nested():
                        session.add(
                            BirthProfileRow(
                                id=record.profile_id,
                                guest_id=record.guest_id,
                                created_at=record.created_at,
                                updated_at=record.created_at,
                            )
                        )
                        await session.flush()
                except IntegrityError:
                    pass
                profile = await session.scalar(
                    select(BirthProfileRow).where(BirthProfileRow.guest_id == record.guest_id)
                )
                if profile is None:
                    raise RuntimeError("birth profile creation could not be resolved")

            current_snapshot = (
                await session.scalar(
                    select(ChartSnapshotRow).where(
                        ChartSnapshotRow.id == profile.current_snapshot_id,
                        ChartSnapshotRow.guest_id == record.guest_id,
                        ChartSnapshotRow.profile_id == profile.id,
                    )
                )
                if profile.current_snapshot_id is not None
                else None
            )
            date_context = f"birth-date:{record.guest_id}".encode()
            requested_date = self._envelope.decrypt(
                record.birth_date_ciphertext, context=date_context
            )
            if current_snapshot is not None:
                current_date = self._envelope.decrypt(
                    current_snapshot.birth_date_ciphertext, context=date_context
                )
                if current_date == requested_date:
                    # Retrying the date is not permission to downgrade a complete chart.
                    return _record(
                        current_snapshot, self._envelope, profile_revision=profile.updated_at
                    ), True
                # US-23 D4: a different date replaces the subject, which only the explicit,
                # confirmed and fenced edit may do. A retry or crafted request never does.
                raise BirthDateChangeRequiresEdit

            if existing is not None:
                profile.current_snapshot_id = existing.id
                profile.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(existing, self._envelope, profile_revision=profile.updated_at), True

            snapshot = ChartSnapshotRow(
                id=record.id,
                guest_id=record.guest_id,
                profile_id=profile.id,
                input_hash=record.input_hash,
                birth_date_ciphertext=record.birth_date_ciphertext,
                schema_version="1.0.0",
                engine_version=record.result.provenance.version,
                calculation_profile=record.result.provenance.profile,
                result_payload=None,
                result_ciphertext=_encrypt_result(record, self._envelope),
                created_at=record.created_at,
            )
            session.add(snapshot)
            await session.flush([snapshot])
            profile.current_snapshot_id = snapshot.id
            profile.updated_at = datetime.now(UTC)
            await session.flush()
            return _record(snapshot, self._envelope, profile_revision=profile.updated_at), False

    async def find_current(self, guest_id: UUID) -> BirthSnapshotRecord | None:
        async with self._sessions() as session:
            pair = (
                await session.execute(
                    select(ChartSnapshotRow, BirthProfileRow.updated_at)
                    .join(
                        BirthProfileRow,
                        BirthProfileRow.current_snapshot_id == ChartSnapshotRow.id,
                    )
                    .where(BirthProfileRow.guest_id == guest_id)
                )
            ).one_or_none()
            return _record(pair[0], self._envelope, profile_revision=pair[1]) if pair else None

    async def find_by_input_hash(
        self, guest_id: UUID, input_hash: bytes
    ) -> BirthSnapshotRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(ChartSnapshotRow).where(
                    ChartSnapshotRow.guest_id == guest_id,
                    ChartSnapshotRow.input_hash == input_hash,
                )
            )
            return _record(row, self._envelope) if row is not None else None

    async def save_supplement(
        self,
        guest_id: UUID,
        snapshot: BirthSnapshotRecord | None,
        supplement: BirthSupplement,
        *,
        expected_snapshot_id: UUID,
        expected_updated_at: datetime | None,
    ) -> BirthSnapshotRecord | None:
        async with self._sessions() as session, session.begin():
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            sends = await pending_sends(session, (guest_id,)) if snapshot is None else ()
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is None:
                raise RuntimeError("birth profile is required before supplement")
            if (
                profile.current_snapshot_id != expected_snapshot_id
                or profile.updated_at != expected_updated_at
            ):
                raise BirthProfileChanged
            if snapshot is None:
                await self._erase_precision(session, profile)
                if self._erasure_journal is not None:
                    self._erasure_journal.record(
                        session, ErasureKind.BIRTH_TIME_DOWNGRADED, guest_id, datetime.now(UTC)
                    )
            active: ChartSnapshotRow | None = None
            if snapshot is not None:
                active = await session.scalar(
                    select(ChartSnapshotRow).where(
                        ChartSnapshotRow.guest_id == guest_id,
                        ChartSnapshotRow.input_hash == snapshot.input_hash,
                    )
                )
                if active is None:
                    active = ChartSnapshotRow(
                        id=snapshot.id,
                        guest_id=guest_id,
                        profile_id=profile.id,
                        input_hash=snapshot.input_hash,
                        birth_date_ciphertext=snapshot.birth_date_ciphertext,
                        schema_version="1.1.0",
                        engine_version=snapshot.result.provenance.version,
                        calculation_profile=snapshot.result.provenance.profile,
                        result_payload=None,
                        result_ciphertext=_encrypt_result(snapshot, self._envelope),
                        created_at=snapshot.created_at,
                    )
                    session.add(active)
                    await session.flush([active])
                profile.current_snapshot_id = active.id
            profile.profile_level = (
                3
                if supplement.birth_place_ciphertext
                and supplement.birth_time_mode.value != "unknown"
                else 2
            )
            if supplement.birth_time_mode.value == "unknown":
                profile.profile_level = 1
            profile.birth_time_ciphertext = supplement.birth_time_ciphertext
            profile.birth_place_ciphertext = supplement.birth_place_ciphertext
            profile.time_precision = (
                "approximate"
                if supplement.birth_time_mode.value == "approx_window"
                else supplement.birth_time_mode.value
            )
            profile.place_display_name = None
            profile.timezone_id = None
            profile.supplement_consent_version = supplement.consent_version
            profile.updated_at = datetime.now(UTC)
            await session.flush()
            stored = _record(active, self._envelope) if active is not None else None
        await drain_sends(self._sessions, sends)
        return stored

    async def find_supplement(self, guest_id: UUID) -> BirthSupplementStored | None:
        async with self._sessions() as session:
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            return _supplement_record(profile) if profile is not None else None

    async def clear_supplement(
        self, guest_id: UUID, *, remove_time: bool, remove_place: bool
    ) -> BirthSupplementStored:
        async with self._sessions() as session, session.begin():
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            sends = await pending_sends(session, (guest_id,)) if remove_time or remove_place else ()
            if remove_time or remove_place:
                # Both perspectives contain facts derived from either participant.
                # Erase the parent before cascading to its jobs, matching execution order.
                await session.execute(
                    delete(RadarRequestRow).where(
                        or_(
                            RadarRequestRow.owner_guest_id == guest_id,
                            RadarRequestRow.recipient_guest_id == guest_id,
                        )
                    )
                )
                await session.execute(
                    delete(ContentRewriteJobRow).where(
                        ContentRewriteJobRow.owner_guest_id == guest_id,
                        ContentRewriteJobRow.owner_namespace.in_(("readings", "radar")),
                    )
                )
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is None:
                raise RuntimeError("birth profile is required before supplement removal")
            if remove_time:
                profile.birth_time_ciphertext = None
                profile.time_precision = "unknown"
            if remove_place:
                profile.birth_place_ciphertext = None
                profile.place_display_name = None
                profile.timezone_id = None
            profile.profile_level = (
                3
                if profile.birth_time_ciphertext and profile.birth_place_ciphertext
                else 2
                if profile.birth_time_ciphertext
                else 1
            )
            if remove_time or remove_place:
                await self._erase_precision(session, profile)
                profile.updated_at = datetime.now(UTC)
                if self._erasure_journal is not None:
                    self._erasure_journal.record(
                        session,
                        ErasureKind.BIRTH_SUPPLEMENT_REMOVED,
                        guest_id,
                        profile.updated_at,
                        scope=",".join(
                            name
                            for name, removed in (("time", remove_time), ("place", remove_place))
                            if removed
                        ),
                    )
            await session.flush()
            stored = _supplement_record(profile)
        await drain_sends(self._sessions, sends)
        return stored

    async def recent_date_changes(self, guest_id: UUID, *, since: datetime) -> int:
        async with self._sessions() as session:
            used = await session.scalar(
                select(func.count())
                .select_from(BirthDateChangeRow)
                .where(
                    BirthDateChangeRow.guest_id == guest_id, BirthDateChangeRow.changed_at > since
                )
            )
        return int(used or 0)

    async def replace_date(
        self,
        record: BirthSnapshotRecord,
        *,
        expected_revision: datetime,
        now: datetime,
        limit: int,
        window: timedelta,
    ) -> BirthSnapshotRecord:
        """Phase 2 of a birth-date correction (US-23): one transaction under the guest lock.

        The new date-only chart was computed and encrypted beforehand, outside any lock. Here the
        revision fence, the unchanged-date rule and the rolling limit are checked again, the
        admitted provider sends are captured, the old subject and everything derived from it are
        deleted (saved notes and share links stay, D2), time/place/deep consent are cleared, the
        new snapshot becomes current, and the change and its data-free journal entry are written.
        Phase 3 drains the captured sends after commit, before the caller reports success.
        """

        guest_id = record.guest_id
        async with self._sessions() as session, session.begin():
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is None or profile.current_snapshot_id is None:
                raise BirthProfileNotFound
            if profile.updated_at != expected_revision:
                raise BirthProfileChanged
            current = await session.get(ChartSnapshotRow, profile.current_snapshot_id)
            if current is None:
                raise RuntimeError("current snapshot could not be resolved")
            date_context = f"birth-date:{guest_id}".encode()
            if self._envelope.decrypt(
                current.birth_date_ciphertext, context=date_context
            ) == self._envelope.decrypt(record.birth_date_ciphertext, context=date_context):
                raise BirthDateUnchanged
            await session.execute(
                delete(BirthDateChangeRow).where(
                    BirthDateChangeRow.guest_id == guest_id,
                    BirthDateChangeRow.changed_at <= now - window,
                )
            )
            used = await session.scalar(
                select(func.count())
                .select_from(BirthDateChangeRow)
                .where(BirthDateChangeRow.guest_id == guest_id)
            )
            if int(used or 0) >= limit:
                raise BirthDateChangeLimited
            sends = await pending_sends(session, (guest_id,))
            await _replace_subject(session, profile)
            snapshot = ChartSnapshotRow(
                id=record.id,
                guest_id=guest_id,
                profile_id=profile.id,
                input_hash=record.input_hash,
                birth_date_ciphertext=record.birth_date_ciphertext,
                schema_version="1.0.0",
                engine_version=record.result.provenance.version,
                calculation_profile=record.result.provenance.profile,
                result_payload=None,
                result_ciphertext=_encrypt_result(record, self._envelope),
                created_at=record.created_at,
            )
            session.add(snapshot)
            await session.flush([snapshot])
            profile.current_snapshot_id = snapshot.id
            profile.updated_at = datetime.now(UTC)
            session.add(BirthDateChangeRow(guest_id=guest_id, changed_at=now))
            if self._erasure_journal is not None:
                self._erasure_journal.record(
                    session, ErasureKind.BIRTH_DATE_REPLACED, guest_id, now
                )
            await session.flush()
            stored = _record(snapshot, self._envelope, profile_revision=profile.updated_at)
        await drain_sends(self._sessions, sends)
        return stored

    async def replay_date_replacement(self, guest_id: UUID) -> None:
        """Re-apply a journaled date correction to a restored copy that predates it.

        The restored copy holds only the old subject and no replacement value exists to restore,
        so this fails closed: the old subject and its dependents go and no active birth subject
        remains. The guest returns to ``birth_pending``; the app asks for the date again and
        ``POST /v1/birth-profile`` accepts it because no subject exists. Saved notes and share
        links stay, as after the live correction. Idempotent.
        """

        async with self._sessions() as session, session.begin():
            guest = await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            sends = await pending_sends(session, (guest_id,))
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is not None:
                await _replace_subject(session, profile)
                profile.updated_at = datetime.now(UTC)
            if guest is not None:
                guest.onboarding_status = OnboardingStatus.BIRTH_PENDING.value
        await drain_sends(self._sessions, sends)

    async def replay_time_downgrade(self, guest_id: UUID) -> None:
        """Re-apply a journaled switch to an unknown birth time after a restore."""

        async with self._sessions() as session, session.begin():
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            sends = await pending_sends(session, (guest_id,))
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is not None:
                await self._erase_precision(session, profile)
                profile.birth_time_ciphertext = None
                profile.time_precision = "unknown"
                profile.profile_level = 1
                profile.updated_at = datetime.now(UTC)
        await drain_sends(self._sessions, sends)

    async def _erase_precision(self, session: AsyncSession, profile: BirthProfileRow) -> None:
        snapshots = list(
            await session.scalars(
                select(ChartSnapshotRow)
                .where(ChartSnapshotRow.profile_id == profile.id)
                .order_by(ChartSnapshotRow.created_at.desc())
            )
        )
        results = [(row, _record(row, self._envelope).result.chart_type) for row in snapshots]
        current_snapshot = next(
            (row for row in snapshots if row.id == profile.current_snapshot_id), None
        )
        if current_snapshot is None and snapshots:
            raise RuntimeError("current snapshot is required before supplement removal")
        date_context = f"birth-date:{profile.guest_id}".encode()
        current_date = (
            self._envelope.decrypt(current_snapshot.birth_date_ciphertext, context=date_context)
            if current_snapshot is not None
            else None
        )
        date_only = next(
            (
                row
                for row, chart_type in results
                if chart_type == ChartType.DATE_ONLY_NATAL
                and self._envelope.decrypt(row.birth_date_ciphertext, context=date_context)
                == current_date
            ),
            None,
        )
        if date_only is None and snapshots:
            raise RuntimeError("date-only snapshot is required before supplement removal")
        if date_only is not None:
            profile.current_snapshot_id = date_only.id
            await session.flush([profile])
        # Removing time or place deletes every saved note and share link of this person, as its
        # confirmation promises ("mọi note, bản lưu, link chia sẻ hiện có"). Delete them here
        # rather than through the source cascades, which migration 20261029_0039 drops in the next
        # release; this also covers copies a birth-date correction detaches.
        await delete_copies(session, profile.guest_id)
        await delete_derived(session, profile)
        if date_only is not None:
            await session.execute(
                delete(ChartSnapshotRow).where(
                    ChartSnapshotRow.profile_id == profile.id,
                    ChartSnapshotRow.id != date_only.id,
                )
            )


async def _replace_subject(session: AsyncSession, profile: BirthProfileRow) -> None:
    """Delete the profile's birth subject and everything derived from it (US-23 D1, D3).

    Leaves the profile with no current snapshot, date-only level and no time, place or deep
    consent. Saved notes and share links are kept (D2); they no longer cascade from their source.
    """

    await delete_derived(session, profile)
    await session.execute(
        delete(ReadingProjectionRow).where(ReadingProjectionRow.profile_id == profile.id)
    )
    profile.current_snapshot_id = None
    await session.flush([profile])
    await session.execute(delete(ChartSnapshotRow).where(ChartSnapshotRow.profile_id == profile.id))
    profile.profile_level = 1
    profile.birth_time_ciphertext = None
    profile.birth_place_ciphertext = None
    profile.time_precision = "unknown"
    profile.place_display_name = None
    profile.timezone_id = None
    profile.supplement_consent_version = None


async def delete_copies(session: AsyncSession, guest_id: UUID) -> None:
    """Every saved note and share link the guest owns, attached to a source or not."""

    await session.execute(delete(SavedNoteRow).where(SavedNoteRow.guest_id == guest_id))
    await session.execute(delete(ShareArtifactRow).where(ShareArtifactRow.guest_id == guest_id))


async def delete_derived(session: AsyncSession, profile: BirthProfileRow) -> None:
    """Content derived from the profile's birth data, saved and shared copies excepted.

    Radar rows of both perspectives go first, then their and the Reading rewrite jobs, so no job
    outlives its parent; then experiments, Daily notes (their mood, feedback and attempts cascade)
    and reading plans (their revisions, attempts and pointing projections cascade).
    """

    guest_id = profile.guest_id
    await session.execute(
        delete(RadarRequestRow).where(
            or_(
                RadarRequestRow.owner_guest_id == guest_id,
                RadarRequestRow.recipient_guest_id == guest_id,
            )
        )
    )
    await session.execute(
        delete(ContentRewriteJobRow).where(
            ContentRewriteJobRow.owner_guest_id == guest_id,
            ContentRewriteJobRow.owner_namespace.in_(("readings", "radar")),
        )
    )
    await session.execute(delete(DailyExperimentRow).where(DailyExperimentRow.guest_id == guest_id))
    await session.execute(delete(DailyNoteRow).where(DailyNoteRow.guest_id == guest_id))
    await session.execute(delete(ReadingPlanRow).where(ReadingPlanRow.profile_id == profile.id))


def _record(
    row: ChartSnapshotRow, envelope: EnvelopeCipher, *, profile_revision: datetime | None = None
) -> BirthSnapshotRecord:
    return BirthSnapshotRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        input_hash=row.input_hash,
        birth_date_ciphertext=row.birth_date_ciphertext,
        result=_chart_result(_result_payload(row, envelope)),
        created_at=row.created_at,
        profile_revision=profile_revision,
    )


def _supplement_record(row: BirthProfileRow) -> BirthSupplementStored:
    return BirthSupplementStored(
        profile_id=row.id,
        profile_level=row.profile_level,
        birth_time_ciphertext=row.birth_time_ciphertext,
        birth_place_ciphertext=row.birth_place_ciphertext,
        time_precision=row.time_precision,
        supplement_consent_version=row.supplement_consent_version,
        updated_at=row.updated_at,
    )


def _chart_result(payload: dict[str, object]) -> DateOnlySunResult | NatalChart:
    chart_type = payload.get("chart_type")
    if chart_type == ChartType.NATAL.value:
        return NatalChart.model_validate(payload)
    return DateOnlySunResult.model_validate(payload)


def _chart_context(snapshot_id: UUID) -> bytes:
    return f"chart-snapshot:{snapshot_id}".encode()


def _encrypt_result(record: BirthSnapshotRecord, envelope: EnvelopeCipher) -> str:
    payload = json.dumps(
        record.result.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return envelope.encrypt(payload, context=_chart_context(record.id))


def _result_payload(row: ChartSnapshotRow, envelope: EnvelopeCipher) -> dict[str, object]:
    if row.result_ciphertext:
        decrypted = envelope.decrypt(
            row.result_ciphertext,
            context=_chart_context(row.id),
        )
        payload = json.loads(decrypted)
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted chart snapshot")
        return payload
    if row.result_payload is not None:
        return row.result_payload
    raise ValueError("chart snapshot has no result")
