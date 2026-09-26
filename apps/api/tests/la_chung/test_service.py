import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from cryptography.exceptions import InvalidTag
from sqlalchemy import select

from app.db.session import Database
from app.domains.guest.tables import GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.la_chung.service import LaChungInvalid, LaChungService, LaChungUnavailable
from app.domains.la_chung.tables import LaChungRequestRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

# Public preview intentionally evaluates real wall-clock expiry. Anchor fixtures to
# the test run so this suite does not start failing as its original fixed date ages.
NOW = datetime.now(UTC).replace(microsecond=0)
Storage = tuple[Database, LaChungService, SecretHasher, AesGcmEnvelopeCipher]


async def _principal(database: Database) -> UUID:
    guest_id = uuid4()
    principal_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes,
                state="claimed",
                onboarding_status="birth_ready",
                created_at=NOW,
                last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )
        await session.flush()
        session.add(PrincipalRow(id=principal_id, source_guest_id=guest_id, created_at=NOW))
    return principal_id


@pytest.fixture
async def la_chung_storage(tmp_path: Path) -> AsyncIterator[Storage]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'la-chung-service.db'}")
    await database.initialize()
    hasher = SecretHasher(b"h" * 32)
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))
    try:
        yield database, LaChungService(database.sessions, hasher, envelope), hasher, envelope
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_create_replays_owner_and_draft_bound_invite_with_encrypted_label(
    la_chung_storage: Storage,
) -> None:
    database, service, _, _ = la_chung_storage
    principal_id = await _principal(database)

    first, first_token = await service.create(
        principal_id=principal_id,
        recipient_label="  người   bạn riêng  ",
        context="friend",
        idempotency_key="invite-service-idempotency-123456",
        now=NOW,
    )
    replay, replay_token = await service.create(
        principal_id=principal_id,
        recipient_label="người bạn riêng",
        context="friend",
        idempotency_key="invite-service-idempotency-123456",
        now=NOW + timedelta(minutes=1),
    )

    assert replay.id == first.id
    assert replay_token == first_token
    assert replay.recipient_label == "người bạn riêng"
    assert (await service.list_owned(principal_id))[0].recipient_label == "người bạn riêng"
    assert (await service.preview(first_token)).recipient_label == "người bạn riêng"
    async with database.sessions() as session:
        rows = tuple(await session.scalars(select(LaChungRequestRow)))
    assert len(rows) == 1
    assert rows[0].recipient_label is None
    ciphertext = rows[0].recipient_label_ciphertext
    assert ciphertext is not None and ciphertext.startswith("aesgcm:")
    with pytest.raises(InvalidTag):
        la_chung_storage[3].decrypt(
            ciphertext,
            context=f"la-chung-recipient-label:{uuid4()}".encode(),
        )


@pytest.mark.asyncio
async def test_concurrent_create_retries_resolve_one_invite(
    la_chung_storage: Storage,
) -> None:
    database, service, _, _ = la_chung_storage
    principal_id = await _principal(database)

    results = await asyncio.gather(
        *(
            service.create(
                principal_id=principal_id,
                recipient_label="người bạn",
                context="bff",
                idempotency_key="invite-concurrent-idempotency-123456",
                now=NOW,
            )
            for _ in range(2)
        )
    )

    assert results[0][0].id == results[1][0].id
    assert results[0][1] == results[1][1]
    async with database.sessions() as session:
        rows = tuple(await session.scalars(select(LaChungRequestRow)))
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_create_key_cannot_change_draft_or_recover_terminal_invite(
    la_chung_storage: Storage,
) -> None:
    database, service, _, _ = la_chung_storage
    principal_id = await _principal(database)
    key = "invite-conflict-idempotency-123456"
    await service.create(
        principal_id=principal_id,
        recipient_label="bạn cũ",
        context="friend",
        idempotency_key=key,
        now=NOW,
    )

    with pytest.raises(LaChungInvalid):
        await service.create(
            principal_id=principal_id,
            recipient_label="bạn mới",
            context="friend",
            idempotency_key=key,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(LaChungUnavailable):
        await service.create(
            principal_id=principal_id,
            recipient_label="bạn cũ",
            context="friend",
            idempotency_key=key,
            now=NOW + timedelta(days=8),
        )


@pytest.mark.asyncio
async def test_same_client_key_is_isolated_between_owners_and_legacy_label_is_readable(
    la_chung_storage: Storage,
) -> None:
    database, service, hasher, envelope = la_chung_storage
    principal_a = await _principal(database)
    principal_b = await _principal(database)
    key = "invite-owner-bound-idempotency-123456"
    invite_a, _ = await service.create(
        principal_id=principal_a,
        recipient_label="owner a",
        context="friend",
        idempotency_key=key,
        now=NOW,
    )
    invite_b, _ = await service.create(
        principal_id=principal_b,
        recipient_label="owner b",
        context="friend",
        idempotency_key=key,
        now=NOW,
    )
    assert invite_a.id != invite_b.id

    legacy_id = uuid4()
    legacy_token = "a" * 43
    async with database.sessions() as session, session.begin():
        session.add(
            LaChungRequestRow(
                id=legacy_id,
                principal_id=principal_a,
                recipient_label="legacy friend",
                recipient_label_ciphertext=None,
                context="bff",
                status="pending",
                bank_version="la-chung-v1",
                token_hash=hasher.digest("la-chung-capability", legacy_token),
                token_ciphertext=envelope.encrypt(
                    legacy_token.encode(),
                    context=f"la-chung-capability:{legacy_id}".encode(),
                ),
                idempotency_hash=None,
                draft_hash=None,
                created_at=NOW,
                expires_at=NOW + timedelta(days=7),
            )
        )

    legacy = next(item for item in await service.list_owned(principal_a) if item.id == legacy_id)
    assert legacy.recipient_label == "legacy friend"
    assert (await service.preview(legacy_token)).recipient_label == "legacy friend"
