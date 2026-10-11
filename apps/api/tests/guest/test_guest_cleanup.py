import asyncio
from collections.abc import AsyncIterator
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.birth.tables import BirthProfileRow
from app.domains.guest.models import GuestState
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import ConsentRow, GuestCreationRow, GuestSessionRow
from app.domains.readings.models import GenerationAttemptResult
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.tables import (
    ReadingGenerationAttemptRow,
    ReadingPlanRow,
    ReadingProjectionRow,
    ReadingRevisionRow,
)
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider
from tests.readings.test_worker import NOW, _queued_attempt


@pytest.fixture
async def storage(
    tmp_path: Path,
) -> AsyncIterator[tuple[Database, PostgresGuestRepository, PostgresReadingRepository]]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'guest-cleanup.db'}")
    await database.initialize()
    try:
        yield (
            database,
            PostgresGuestRepository(database.sessions),
            PostgresReadingRepository(
                database.sessions,
                AesGcmEnvelopeCipher(StaticDataKeyProvider(b"g" * 32)),
            ),
        )
    finally:
        await database.dispose()


@pytest.mark.parametrize("started", [False, True], ids=["unsent", "provider-started"])
@pytest.mark.parametrize("days_later", [0, 31], ids=["unexpired", "expired"])
async def test_cleanup_recovers_interrupted_committed_deletion(
    storage: tuple[Database, PostgresGuestRepository, PostgresReadingRepository],
    monkeypatch: pytest.MonkeyPatch,
    started: bool,
    days_later: int,
) -> None:
    database, guests, readings = storage
    guest_id, _, attempt, _ = await _queued_attempt(database, readings)
    lease = await readings.lease_generation_attempt(now=NOW, lease_for_seconds=30)
    assert lease is not None and lease.id == attempt.id
    other_id, _, _, _ = await _queued_attempt(database, readings)
    async with database.sessions() as session, session.begin():
        guest = await session.get(GuestSessionRow, guest_id)
        other = await session.get(GuestSessionRow, other_id)
        assert guest is not None and other is not None
        token_hash = guest.token_hash
        other.expires_at = NOW + timedelta(days=60)
        session.add_all(
            [
                ConsentRow(
                    guest_id=guest_id,
                    version="birth-profile-v1",
                    purpose="birth_profile_basic",
                    accepted_at=NOW,
                ),
                GuestCreationRow(
                    guest_id=guest_id,
                    idempotency_hash=b"i" * 32,
                    request_hash=b"r" * 32,
                    credential_envelope="synthetic-encrypted-credential",
                    created_at=NOW,
                    replay_expires_at=NOW + timedelta(minutes=10),
                ),
            ]
        )

    if started:
        assert await readings.mark_generation_request_started(
            attempt_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            started_at=NOW,
        )

    async def interrupt_after_commit(_guest_id: UUID) -> int:
        raise asyncio.CancelledError

    with monkeypatch.context() as patch:
        patch.setattr(guests, "_started_generation_count", interrupt_after_commit)
        with pytest.raises(asyncio.CancelledError):
            await guests.delete_by_token_hash(token_hash, NOW)

    async with database.sessions() as session:
        deleting = await session.get(GuestSessionRow, guest_id)
        assert deleting is not None and deleting.state == GuestState.DELETING.value
        retained_attempt = await session.get(ReadingGenerationAttemptRow, lease.id)
        assert (retained_attempt is not None) is started
    assert await guests.find_by_token_hash(token_hash, NOW) is None
    assert not await readings.mark_generation_request_started(
        attempt_id=lease.id,
        lease_token=lease.lease_token,
        deletion_epoch=lease.deletion_epoch,
        started_at=NOW,
    )

    cleanup_at = NOW + timedelta(days=days_later)
    if started:
        assert await guests.purge_expired(cleanup_at, batch_size=1) == 0
        async with database.sessions() as session:
            assert await session.get(GuestSessionRow, guest_id) is not None
            retained_attempt = await session.get(ReadingGenerationAttemptRow, lease.id)
            assert retained_attempt is not None and retained_attempt.request_started_at == NOW
            assert (
                await session.scalar(select(ConsentRow.id).where(ConsentRow.guest_id == guest_id))
                is not None
            )
        assert await readings.fail_generation_attempt(
            attempt_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            result=GenerationAttemptResult.PERMANENT,
            updated_at=cleanup_at,
        )

    assert await guests.purge_expired(cleanup_at, batch_size=1) == 1
    assert await guests.purge_expired(cleanup_at, batch_size=1) == 0
    async with database.sessions() as session:
        assert await session.get(GuestSessionRow, guest_id) is None
        assert await session.get(GuestSessionRow, other_id) is not None
        for model in (
            ConsentRow,
            GuestCreationRow,
            BirthProfileRow,
            ReadingPlanRow,
            ReadingRevisionRow,
            ReadingProjectionRow,
            ReadingGenerationAttemptRow,
        ):
            assert (
                await session.scalar(
                    select(func.count()).select_from(model).where(model.guest_id == guest_id)
                )
                == 0
            )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ReadingGenerationAttemptRow)
                .where(ReadingGenerationAttemptRow.guest_id == other_id)
            )
            == 1
        )


async def test_cleanup_batches_deleting_and_expired_owners_in_uuid_order(
    storage: tuple[Database, PostgresGuestRepository, PostgresReadingRepository],
) -> None:
    database, guests, _ = storage
    async with database.sessions() as session, session.begin():
        for number, state, expires_at in (
            (3, GuestState.DELETING, NOW + timedelta(days=30)),
            (2, GuestState.ACTIVE, NOW),
            (1, GuestState.DELETING, NOW + timedelta(days=30)),
            (4, GuestState.ACTIVE, NOW + timedelta(days=30)),
        ):
            session.add(
                GuestSessionRow(
                    id=UUID(int=number),
                    token_hash=uuid4().bytes + uuid4().bytes,
                    csrf_hash=b"c" * 32,
                    state=state.value,
                    onboarding_status="birth_pending",
                    created_at=NOW - timedelta(days=1),
                    last_active_at=NOW - timedelta(days=1),
                    expires_at=expires_at,
                )
            )

    for removed, expected in (
        (2, [UUID(int=3), UUID(int=4)]),
        (1, [UUID(int=4)]),
        (0, [UUID(int=4)]),
    ):
        assert await guests.purge_expired(NOW, batch_size=2) == removed
        async with database.sessions() as session:
            assert (
                list(await session.scalars(select(GuestSessionRow.id).order_by(GuestSessionRow.id)))
                == expected
            )
