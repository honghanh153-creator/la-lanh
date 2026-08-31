from datetime import datetime
from typing import Any, cast

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from app.domains.guest.models import (
    CreationMaterial,
    GuestSessionRecord,
    GuestState,
    OnboardingStatus,
    StoredCreation,
)
from app.domains.guest.tables import ConsentRow, GuestCreationRow, GuestSessionRow


class PostgresGuestRepository:
    """The only runtime guest repository; tests may inject an explicit test double."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

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
            if touch_until is not None:
                await session.execute(
                    update(GuestSessionRow)
                    .where(
                        GuestSessionRow.token_hash == token_hash,
                        GuestSessionRow.state == GuestState.ACTIVE.value,
                        GuestSessionRow.expires_at > now,
                    )
                    .values(last_active_at=now, expires_at=touch_until)
                )
            guest = await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.token_hash == token_hash)
            )
            if guest is None:
                return None
            return StoredCreation(
                guest=_guest_record(guest),
                request_hash=b"",
                credential_envelope=None,
                replay_expires_at=guest.created_at,
            )

    async def delete_by_token_hash(self, token_hash: bytes, now: datetime) -> bool:
        del now
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(GuestSessionRow).where(GuestSessionRow.token_hash == token_hash)
            )
            return bool(cast(CursorResult[Any], result).rowcount)

    async def purge_expired(self, now: datetime, batch_size: int) -> int:
        async with self._sessions() as session, session.begin():
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
            ids = list(
                await session.scalars(
                    select(GuestSessionRow.id)
                    .where(GuestSessionRow.expires_at <= now)
                    .order_by(GuestSessionRow.expires_at, GuestSessionRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            if not ids:
                return 0
            result = await session.execute(
                delete(GuestSessionRow).where(GuestSessionRow.id.in_(ids))
            )
            return int(cast(CursorResult[Any], result).rowcount or 0)


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
