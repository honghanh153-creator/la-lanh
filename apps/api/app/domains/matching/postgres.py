from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.identity.tables import PrincipalRow
from app.domains.matching.models import (
    GenderPreference,
    MatchingConsent,
    MatchingGender,
    MatchingIntent,
    MatchingProfile,
    MatchingVerification,
    VerificationStatus,
    WeeklyIntent,
)
from app.domains.matching.tables import (
    MatchingConsentRow,
    MatchingProfileRow,
    MatchingVerificationRow,
)
from app.infrastructure.crypto import EnvelopeCipher


class PostgresMatchingRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def get_profile(self, principal_id: UUID) -> MatchingProfile | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(MatchingProfileRow).where(MatchingProfileRow.principal_id == principal_id)
            )
            return self._profile(row) if row is not None else None

    async def save_profile(
        self,
        principal_id: UUID,
        *,
        display_name: str,
        gender_identity: MatchingGender,
        intent: MatchingIntent,
        gender_preference: GenderPreference,
        min_age: int,
        max_age: int,
        region_code: str,
        weekly_intent: WeeklyIntent,
        now: datetime,
    ) -> MatchingProfile:
        async with self._sessions() as session, session.begin():
            await self._lock_principal(session, principal_id)
            row = await session.scalar(
                select(MatchingProfileRow)
                .where(MatchingProfileRow.principal_id == principal_id)
                .with_for_update()
            )
            if row is None:
                row = MatchingProfileRow(
                    id=uuid4(),
                    principal_id=principal_id,
                    display_name_ciphertext=self._encrypt_display_name(principal_id, display_name),
                    gender_identity=gender_identity.value,
                    intent=intent.value,
                    gender_preference=gender_preference.value,
                    min_age=min_age,
                    max_age=max_age,
                    region_code=region_code,
                    weekly_intent=weekly_intent.value,
                    active=False,
                    joined_at=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.display_name_ciphertext = self._encrypt_display_name(principal_id, display_name)
                row.gender_identity = gender_identity.value
                row.intent = intent.value
                row.gender_preference = gender_preference.value
                row.min_age = min_age
                row.max_age = max_age
                row.region_code = region_code
                row.weekly_intent = weekly_intent.value
                row.updated_at = now
            await session.flush([row])
            return self._profile(row)

    async def get_active_consent(self, principal_id: UUID) -> MatchingConsent | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(MatchingConsentRow)
                .where(
                    MatchingConsentRow.principal_id == principal_id,
                    MatchingConsentRow.revoked_at.is_(None),
                )
                .order_by(MatchingConsentRow.accepted_at.desc())
            )
            return _consent(row) if row is not None else None

    async def grant_consent(
        self, principal_id: UUID, *, version: str, purpose: str, now: datetime
    ) -> MatchingConsent:
        async with self._sessions() as session, session.begin():
            await self._lock_principal(session, principal_id)
            await session.execute(
                update(MatchingConsentRow)
                .where(
                    MatchingConsentRow.principal_id == principal_id,
                    MatchingConsentRow.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            row = MatchingConsentRow(
                id=uuid4(),
                principal_id=principal_id,
                version=version,
                purpose=purpose,
                accepted_at=now,
                revoked_at=None,
            )
            session.add(row)
            await session.flush([row])
            return _consent(row)

    async def withdraw_consent(self, principal_id: UUID, *, now: datetime) -> None:
        async with self._sessions() as session, session.begin():
            await self._lock_principal(session, principal_id)
            await session.execute(
                update(MatchingConsentRow)
                .where(
                    MatchingConsentRow.principal_id == principal_id,
                    MatchingConsentRow.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.execute(
                update(MatchingProfileRow)
                .where(MatchingProfileRow.principal_id == principal_id)
                .values(active=False, joined_at=None, updated_at=now)
            )

    async def get_verification(self, principal_id: UUID) -> MatchingVerification | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(MatchingVerificationRow).where(
                    MatchingVerificationRow.principal_id == principal_id
                )
            )
            return _verification(row) if row is not None else None

    async def set_active(
        self, principal_id: UUID, *, active: bool, now: datetime
    ) -> MatchingProfile | None:
        async with self._sessions() as session, session.begin():
            await self._lock_principal(session, principal_id)
            row = await session.scalar(
                select(MatchingProfileRow)
                .where(MatchingProfileRow.principal_id == principal_id)
                .with_for_update()
            )
            if row is None:
                return None
            row.active = active
            row.joined_at = now if active else None
            row.updated_at = now
            await session.flush([row])
            return self._profile(row)

    async def _lock_principal(self, session: AsyncSession, principal_id: UUID) -> None:
        principal = await session.scalar(
            select(PrincipalRow.id).where(PrincipalRow.id == principal_id).with_for_update()
        )
        if principal is None:
            raise RuntimeError("matching principal no longer exists")

    def _profile(self, row: MatchingProfileRow) -> MatchingProfile:
        display_name = self._envelope.decrypt(
            row.display_name_ciphertext,
            context=f"matching-profile:{row.principal_id}".encode(),
        ).decode()
        return MatchingProfile(
            principal_id=row.principal_id,
            display_name=display_name,
            gender_identity=MatchingGender(row.gender_identity),
            intent=MatchingIntent(row.intent),
            gender_preference=GenderPreference(row.gender_preference),
            min_age=row.min_age,
            max_age=row.max_age,
            region_code=row.region_code,
            weekly_intent=WeeklyIntent(row.weekly_intent),
            active=row.active,
            joined_at=row.joined_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _encrypt_display_name(self, principal_id: UUID, display_name: str) -> str:
        return self._envelope.encrypt(
            display_name.encode(),
            context=f"matching-profile:{principal_id}".encode(),
        )


def _consent(row: MatchingConsentRow) -> MatchingConsent:
    return MatchingConsent(
        principal_id=row.principal_id,
        version=row.version,
        purpose=row.purpose,
        accepted_at=row.accepted_at,
        revoked_at=row.revoked_at,
    )


def _verification(row: MatchingVerificationRow) -> MatchingVerification:
    return MatchingVerification(
        principal_id=row.principal_id,
        status=VerificationStatus(row.status),
        reason_code=row.reason_code,
        updated_at=row.updated_at,
    )
