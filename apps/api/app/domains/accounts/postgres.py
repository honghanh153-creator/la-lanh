from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from hashlib import sha256
from typing import cast
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.models import AccountError
from app.domains.accounts.tables import AccountDeviceRow, LoginQuotaRow
from app.domains.guest.models import GuestState
from app.domains.guest.tables import GuestSessionRow
from app.infrastructure.crypto import SecretHasher


@asynccontextmanager
async def account_transaction(
    sessions: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessions() as session, session.begin():
        # SQLite's FOR UPDATE is a no-op. Acquire the writer reservation before
        # reading, including on file-backed connections in separate processes.
        await session.connection(execution_options={"sqlite_write": True})
        yield session


async def lock_subject(session: AsyncSession, subject: UUID) -> None:
    if session.get_bind().dialect.name == "postgresql":
        key = int.from_bytes(sha256(b"account-subject\0" + subject.bytes).digest()[:8], signed=True)
        await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


async def lock_owner(session: AsyncSession, guest_id: UUID) -> GuestSessionRow | None:
    return cast(
        GuestSessionRow | None,
        await session.scalar(
            select(GuestSessionRow)
            .where(GuestSessionRow.id == guest_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ),
    )


async def lock_owners(session: AsyncSession, guest_ids: Iterable[UUID | None]) -> None:
    for guest_id in sorted({item for item in guest_ids if item is not None}):
        await lock_owner(session, guest_id)


async def owned_credential(
    session: AsyncSession, digest: bytes | None, now: datetime
) -> tuple[GuestSessionRow, AccountDeviceRow | None] | None:
    """Owner-before-device lock order agrees with erasure and session renewal."""
    if digest is None:
        return None
    guest_id = await session.scalar(
        select(GuestSessionRow.id).where(GuestSessionRow.token_hash == digest)
    )
    device_id = None
    if guest_id is None:
        discovery = (
            await session.execute(
                select(AccountDeviceRow.guest_id, AccountDeviceRow.id).where(
                    AccountDeviceRow.credential_digest == digest
                )
            )
        ).one_or_none()
        if discovery is None:
            return None
        guest_id, device_id = discovery
    guest = await lock_owner(session, guest_id)
    if guest is None or guest.state != GuestState.ACTIVE.value or guest.expires_at <= now:
        return None
    if device_id is None:
        # The discovery read may have preceded first-link invalidation.
        return (guest, None) if guest.token_hash == digest else None
    device = await session.scalar(
        select(AccountDeviceRow)
        .where(
            AccountDeviceRow.id == device_id,
            AccountDeviceRow.guest_id == guest.id,
            AccountDeviceRow.credential_digest == digest,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if device is None or device.revoked_at is not None or device.expires_at <= now:
        return None
    return guest, device


async def admit(
    session: AsyncSession,
    hasher: SecretHasher,
    action: str,
    peer: str,
    email_digest: bytes,
    now: datetime,
) -> AccountError | None:
    # The global row is locked first on every process, including its initial
    # INSERT ON CONFLICT, which also serializes empty-table / missing-row races.
    limits = (
        [("global", "all", 100), ("email", email_digest.hex(), 5), ("peer", peer, 10)]
        if action == "send"
        else [("global", "all", 1000), ("email", email_digest.hex(), 30), ("peer", peer, 120)]
    )
    rows: list[tuple[LoginQuotaRow, int]] = []
    if action == "send":
        limits.append(("resend", email_digest.hex(), 1))
    for scope, identity, limit in limits:
        duration = 60 if scope == "resend" else 3600
        digest = hasher.digest(f"account-quota-{action}-{scope}", identity)
        insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
        await session.execute(
            insert(LoginQuotaRow)
            .values(key_digest=digest, used=0, expires_at=now + timedelta(seconds=duration))
            .on_conflict_do_nothing(index_elements=["key_digest"])
        )
        row = await session.scalar(
            select(LoginQuotaRow).where(LoginQuotaRow.key_digest == digest).with_for_update()
        )
        if row is None:
            raise RuntimeError("login quota could not be reserved")
        if row.expires_at <= now:
            row.used = 0
            row.expires_at = now + timedelta(seconds=duration)
        if row.used >= limit:
            return AccountError(
                "LOGIN_LIMITED",
                429,
                retry_after=max(1, int((row.expires_at - now).total_seconds())),
            )
        rows.append((row, limit))
    for row, _ in rows:
        row.used += 1
    return None
