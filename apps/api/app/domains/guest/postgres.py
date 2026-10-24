import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from app.domains.accounts.models import ACCOUNT_DAYS, DEVICE_DAYS, AccountError
from app.domains.accounts.postgres import owned_credential
from app.domains.accounts.tables import (
    AccountDeviceRow,
    AccountRow,
    LoginChallengeRow,
    LoginQuotaRow,
)
from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    consent_definition,
    content_rewrite_receipt_id,
)
from app.domains.content_rewrite.postgres import authorization_fingerprint
from app.domains.content_rewrite.send_fence import drain_sends, pending_sends
from app.domains.content_rewrite.tables import ContentRewriteJobRow, RewriteSendFenceRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.guest.errors import AccountErasurePending, GuestExpired
from app.domains.guest.models import (
    ConsentRecord,
    CreationMaterial,
    GuestSessionRecord,
    GuestState,
    OnboardingStatus,
    StoredCreation,
)
from app.domains.guest.tables import ConsentRow, GuestCreationRow, GuestSessionRow
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.domains.radar.tables import RadarRequestRow
from app.domains.readings.tables import ReadingGenerationAttemptRow


class PostgresGuestRepository:
    """The only runtime guest repository; tests may inject an explicit test double."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        *,
        identity_eraser: Callable[[UUID], Awaitable[None]] | None = None,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._identity_eraser = identity_eraser
        self._erasure_journal = erasure_journal

    async def create_or_replay(self, material: CreationMaterial) -> StoredCreation:
        async with self._sessions() as session, session.begin():
            try:
                async with session.begin_nested():
                    guest = GuestSessionRow(
                        id=material.guest.id,
                        token_hash=material.guest.token_hash,
                        csrf_hash=material.guest.csrf_hash,
                        state=material.guest.state.value,
                        onboarding_status=material.guest.onboarding_status.value,
                        created_at=material.guest.created_at,
                        last_active_at=material.guest.last_active_at,
                        expires_at=material.guest.expires_at,
                    )
                    session.add_all(
                        [
                            guest,
                            ConsentRow(
                                guest_id=material.consent.guest_id,
                                version=material.consent.version,
                                purpose=material.consent.purpose,
                                accepted_at=material.consent.accepted_at,
                            ),
                            GuestCreationRow(
                                idempotency_hash=material.idempotency_hash,
                                request_hash=material.request_hash,
                                guest_id=material.guest.id,
                                credential_envelope=material.credential_envelope,
                                created_at=material.guest.created_at,
                                replay_expires_at=material.replay_expires_at,
                            ),
                        ]
                    )
                    await session.flush()
                    if material.history_consent_version is not None:
                        session.add(
                            HistoryRetentionPolicyRow(
                                guest_id=guest.id,
                                consent_version=material.history_consent_version,
                                activated_at=material.guest.created_at,
                            )
                        )
                        await session.flush()
            except IntegrityError:
                pass

            creation = await session.scalar(
                select(GuestCreationRow)
                .where(GuestCreationRow.idempotency_hash == material.idempotency_hash)
                .options(joinedload(GuestCreationRow.guest))
            )
            if creation is None:
                raise RuntimeError("idempotent guest creation could not be resolved")
            if (
                creation.credential_envelope is not None
                and creation.replay_expires_at <= material.guest.created_at
            ):
                creation.credential_envelope = None
                await session.flush()
            return _stored_creation(creation)

    async def find_by_token_hash(
        self, token_hash: bytes, now: datetime, *, touch_until: datetime | None = None
    ) -> StoredCreation | None:
        async with self._sessions() as session, session.begin():
            await session.connection(execution_options={"sqlite_write": True})
            owned = await owned_credential(session, token_hash, now)
            if owned is None:
                return None
            guest, device = owned
            if touch_until is not None:
                guest.last_active_at = max(guest.last_active_at, now)
                data_until = now + timedelta(days=ACCOUNT_DAYS) if device else touch_until
                guest.expires_at = max(guest.expires_at, data_until)
                if device is not None:
                    device.last_active_at = max(device.last_active_at, now)
                    device.expires_at = max(device.expires_at, now + timedelta(days=DEVICE_DAYS))
            record = _guest_record(guest)
            if device is not None:
                record = replace(
                    record,
                    token_hash=device.credential_digest,
                    csrf_hash=device.csrf_digest,
                    expires_at=min(guest.expires_at, device.expires_at),
                )
            return StoredCreation(
                guest=record,
                request_hash=b"",
                credential_envelope=None,
                replay_expires_at=guest.created_at,
            )

    async def delete_by_token_hash(self, token_hash: bytes, now: datetime) -> bool:
        guest_id: UUID | None = None
        async with self._sessions() as session, session.begin():
            await session.connection(execution_options={"sqlite_write": True})
            owned = await owned_credential(session, token_hash, now)
            if owned is None:
                return False
            guest = owned[0]
            guest_id = guest.id
            subject = await session.scalar(
                select(AccountRow.subject_id).where(AccountRow.guest_id == guest_id)
            )
            sends = await pending_sends(session, (guest_id,))
            guest.state = GuestState.DELETING.value
            if self._erasure_journal is not None:
                # Recorded with the DELETING marker, which is also what cleanup resumes from.
                self._erasure_journal.record(session, ErasureKind.GUEST_ERASED, guest_id, now)

            # Anything that has not crossed the durable provider-send marker is cancelled.
            # Attempts already sending are allowed to finish, and deletion does not report
            # success until they are terminal, so no provider disclosure can begin after 204.
            await session.execute(
                delete(ReadingGenerationAttemptRow).where(
                    ReadingGenerationAttemptRow.guest_id == guest_id,
                    ReadingGenerationAttemptRow.request_started_at.is_(None),
                )
            )

        await drain_sends(self._sessions, sends)
        while await self._started_generation_count(guest_id):  # noqa: ASYNC110 - cross-process DB state
            await asyncio.sleep(0.05)

        if subject is not None:
            if self._identity_eraser is None:
                raise AccountErasurePending
            try:
                await self._identity_eraser(subject)
            except AccountError:
                raise AccountErasurePending from None

        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(GuestSessionRow).where(
                    GuestSessionRow.id == guest_id,
                    GuestSessionRow.state == GuestState.DELETING.value,
                )
            )
            return bool(cast(CursorResult[Any], result).rowcount)

    async def _started_generation_count(self, guest_id: UUID) -> int:
        async with self._sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(ReadingGenerationAttemptRow)
                .where(
                    ReadingGenerationAttemptRow.guest_id == guest_id,
                    ReadingGenerationAttemptRow.request_started_at.is_not(None),
                )
            )
            return int(count or 0)

    async def purge_expired(self, now: datetime, batch_size: int) -> int:
        async with self._sessions() as session, session.begin():
            await session.connection(execution_options={"sqlite_write": True})
            # Lock owners first, in the same UUID order as account finalization.
            # Child replay/job cleanup must not hold a child while waiting for an
            # owner whose login transaction is scrubbing that same child.
            ids = list(
                await session.scalars(
                    select(GuestSessionRow.id)
                    .where(
                        # Resume a committed deletion even if its request was interrupted
                        # before erasure. DELETING owners no longer accept provider sends.
                        or_(
                            GuestSessionRow.expires_at <= now,
                            GuestSessionRow.state == GuestState.DELETING.value,
                        ),
                        ~select(ReadingGenerationAttemptRow.id)
                        .where(
                            ReadingGenerationAttemptRow.guest_id == GuestSessionRow.id,
                            ReadingGenerationAttemptRow.request_started_at.is_not(None),
                        )
                        .exists(),
                        ~select(RewriteSendFenceRow.job_id)
                        .where(
                            RewriteSendFenceRow.subject_id == GuestSessionRow.id,
                            RewriteSendFenceRow.expires_at > now,
                        )
                        .exists(),
                    )
                    .order_by(GuestSessionRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            linked = list(
                await session.execute(
                    select(AccountRow.guest_id, AccountRow.subject_id).where(
                        AccountRow.guest_id.in_(ids)
                    )
                )
            )
            linked_ids = {row[0] for row in linked}
            if linked_ids:
                await session.execute(
                    update(GuestSessionRow)
                    .where(
                        GuestSessionRow.id.in_(linked_ids),
                        GuestSessionRow.state != GuestState.DELETING.value,
                    )
                    .values(state=GuestState.DELETING.value)
                )
            removed = 0
            await session.execute(
                delete(RewriteSendFenceRow).where(RewriteSendFenceRow.expires_at <= now)
            )
            if ids:
                result = await session.execute(
                    delete(GuestSessionRow).where(GuestSessionRow.id.in_(set(ids) - linked_ids))
                )
                removed = int(cast(CursorResult[Any], result).rowcount or 0)
            stale_jobs = (
                select(ContentRewriteJobRow.id)
                .where(
                    ContentRewriteJobRow.created_at < now - timedelta(hours=24),
                    or_(
                        ContentRewriteJobRow.status != "leased",
                        ContentRewriteJobRow.lease_expires_at <= now,
                    ),
                )
                .order_by(ContentRewriteJobRow.id)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
            await session.execute(
                delete(ContentRewriteJobRow).where(ContentRewriteJobRow.id.in_(stale_jobs))
            )
            replay_ids = list(
                await session.scalars(
                    select(GuestCreationRow.id)
                    .where(
                        GuestCreationRow.replay_expires_at <= now,
                        GuestCreationRow.credential_envelope.is_not(None),
                    )
                    .order_by(GuestCreationRow.replay_expires_at, GuestCreationRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            if replay_ids:
                await session.execute(
                    update(GuestCreationRow)
                    .where(GuestCreationRow.id.in_(replay_ids))
                    .values(credential_envelope=None)
                )
            # Owner locks and erasure happen before credential cleanup. Never
            # hold a device lock then try to acquire its data-owner lock.
            for model, criterion in (
                (
                    AccountDeviceRow,
                    or_(
                        AccountDeviceRow.expires_at <= now, AccountDeviceRow.revoked_at.is_not(None)
                    ),
                ),
                (LoginChallengeRow, LoginChallengeRow.expires_at <= now),
            ):
                expired = (
                    select(model.id)
                    .where(criterion)
                    .order_by(model.expires_at, model.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
                await session.execute(delete(model).where(model.id.in_(expired)))
            quotas = (
                select(LoginQuotaRow.key_digest)
                .where(LoginQuotaRow.expires_at <= now)
                .order_by(LoginQuotaRow.expires_at, LoginQuotaRow.key_digest)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
            await session.execute(delete(LoginQuotaRow).where(LoginQuotaRow.key_digest.in_(quotas)))
        # Commit DELETING before external I/O: no restore, touch or new send can resurrect it.
        # Keep the linked subject until provider acknowledgement, so interrupted calls retry.
        for guest_id, subject in linked:
            if self._identity_eraser is None:
                continue
            try:
                await self._identity_eraser(subject)
            except AccountError:
                continue
            async with self._sessions() as session, session.begin():
                result = await session.execute(
                    delete(GuestSessionRow).where(
                        GuestSessionRow.id == guest_id,
                        GuestSessionRow.state == GuestState.DELETING.value,
                    )
                )
                removed += int(cast(CursorResult[Any], result).rowcount or 0)
        return removed

    async def has_consent(self, guest_id: UUID, version: str, purpose: str) -> bool:
        async with self._sessions() as session:
            return (
                await session.scalar(
                    select(ConsentRow.id).where(
                        ConsentRow.guest_id == guest_id,
                        ConsentRow.version == version,
                        ConsentRow.purpose == purpose,
                        ConsentRow.revoked_at.is_(None),
                    )
                )
                is not None
            )

    async def save_consent(self, consent: ConsentRecord) -> None:
        async with self._sessions() as session, session.begin():
            guest = await session.scalar(
                select(GuestSessionRow)
                .where(GuestSessionRow.id == consent.guest_id)
                .with_for_update()
            )
            if (
                guest is None
                or guest.state != GuestState.ACTIVE.value
                or guest.expires_at <= datetime.now(UTC)
            ):
                raise GuestExpired
            row = await session.scalar(
                select(ConsentRow).where(
                    ConsentRow.guest_id == consent.guest_id,
                    ConsentRow.purpose == consent.purpose,
                )
            )
            if row is None:
                session.add(
                    ConsentRow(
                        guest_id=consent.guest_id,
                        version=consent.version,
                        purpose=consent.purpose,
                        accepted_at=consent.accepted_at,
                    )
                )
            else:
                if row.version == consent.version and row.revoked_at is None:
                    return
                row.version = consent.version
                row.accepted_at = consent.accepted_at
                row.revoked_at = None

    async def revoke_consent(self, guest_id: UUID, purpose: str, revoked_at: datetime) -> None:
        async with self._sessions() as session, session.begin():
            # Same lock as rewrite execution: a completed withdrawal is a hard fence.
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
            )
            sends = await pending_sends(session, (guest_id,))
            await session.execute(
                update(ConsentRow)
                .where(ConsentRow.guest_id == guest_id, ConsentRow.purpose == purpose)
                .values(revoked_at=revoked_at)
            )
            if self._erasure_journal is not None:
                self._erasure_journal.record(
                    session, ErasureKind.CONSENT_REVOKED, guest_id, revoked_at, scope=purpose
                )
            for scope in RewriteConsentScope:
                if consent_definition(scope).purpose == purpose:
                    if scope is RewriteConsentScope.RADAR:
                        await session.execute(
                            delete(ContentRewriteJobRow).where(
                                ContentRewriteJobRow.radar_request_id.in_(
                                    select(RadarRequestRow.id).where(
                                        or_(
                                            RadarRequestRow.owner_guest_id == guest_id,
                                            RadarRequestRow.recipient_guest_id == guest_id,
                                        )
                                    )
                                )
                            )
                        )
                    receipt = content_rewrite_receipt_id(guest_id, scope=scope)
                    fingerprint = authorization_fingerprint(receipt)
                    await session.execute(
                        delete(ContentRewriteJobRow).where(
                            ContentRewriteJobRow.authorization_fingerprint == fingerprint
                        )
                    )

        await drain_sends(self._sessions, sends)

    async def update_onboarding(self, guest_id: UUID, status: OnboardingStatus) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(
                update(GuestSessionRow)
                .where(GuestSessionRow.id == guest_id)
                .values(onboarding_status=status.value)
            )


def _stored_creation(row: GuestCreationRow) -> StoredCreation:
    return StoredCreation(
        guest=_guest_record(row.guest),
        request_hash=row.request_hash,
        credential_envelope=row.credential_envelope,
        replay_expires_at=row.replay_expires_at,
    )


def _guest_record(row: GuestSessionRow) -> GuestSessionRecord:
    return GuestSessionRecord(
        id=row.id,
        token_hash=row.token_hash,
        csrf_hash=row.csrf_hash,
        state=GuestState(row.state),
        onboarding_status=OnboardingStatus(row.onboarding_status),
        created_at=row.created_at,
        last_active_at=row.last_active_at,
        expires_at=row.expires_at,
    )
