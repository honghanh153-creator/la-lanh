import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.identity.models import OwnerIdentity, OwnerSession
from app.domains.identity.tables import OwnerSessionRow, PrincipalRow
from app.infrastructure.crypto import SecretHasher


class OwnerSessionUnavailable(RuntimeError):
    pass


class OwnerIdentityService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        hasher: SecretHasher,
        *,
        ttl: timedelta = timedelta(days=30),
    ) -> None:
        self._sessions = sessions
        self._hasher = hasher
        self._ttl = ttl

    async def claim_guest(self, guest_id: UUID, *, now: datetime | None = None) -> OwnerSession:
        current = now or datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        async with self._sessions() as session, session.begin():
            principal = await session.scalar(
                select(PrincipalRow).where(PrincipalRow.source_guest_id == guest_id)
            )
            resumed = principal is not None
            if principal is None:
                principal = PrincipalRow(id=uuid4(), source_guest_id=guest_id, created_at=current)
                session.add(principal)
                await session.flush()
            owner_session = OwnerSessionRow(
                id=uuid4(),
                principal_id=principal.id,
                token_hash=self._hasher.digest("owner-session", token),
                created_at=current,
                expires_at=current + self._ttl,
            )
            session.add(owner_session)
            await session.flush()
            return OwnerSession(
                principal_id=principal.id,
                source_guest_id=principal.source_guest_id,
                token=token,
                expires_at=owner_session.expires_at,
                resumed=resumed,
            )

    async def resume(self, token: str | None, *, now: datetime | None = None) -> OwnerIdentity:
        if not token:
            raise OwnerSessionUnavailable
        current = now or datetime.now(UTC)
        digest = self._hasher.digest("owner-session", token)
        async with self._sessions() as session:
            row = await session.scalar(
                select(OwnerSessionRow).where(OwnerSessionRow.token_hash == digest)
            )
            if row is None or row.revoked_at is not None or row.expires_at <= current:
                raise OwnerSessionUnavailable
            principal = await session.get(PrincipalRow, row.principal_id)
            if principal is None:
                raise OwnerSessionUnavailable
            return OwnerIdentity(
                principal_id=principal.id,
                source_guest_id=principal.source_guest_id,
                expires_at=row.expires_at,
            )
