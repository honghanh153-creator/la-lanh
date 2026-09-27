import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from app.domains.birth.service import BirthChartService
from app.domains.geo.service import CURRENT_ADMIN_CODES
from app.domains.matching.errors import (
    MatchingConsentInvalid,
    MatchingNotReady,
    MatchingProfileInvalid,
    MatchingProfileRequired,
)
from app.domains.matching.models import (
    GenderPreference,
    MatchingGender,
    MatchingIntent,
    MatchingProfile,
    MatchingReadiness,
    MatchingVerification,
    VerificationStatus,
    WeeklyIntent,
)
from app.domains.matching.repository import MatchingRepository

MATCHING_CONSENT_VERSION = "matching-v1"
MATCHING_CONSENT_PURPOSE = "weekly_relationship_matching"


class MatchingService:
    def __init__(
        self,
        repository: MatchingRepository,
        birth_service: BirthChartService,
    ) -> None:
        self._repository = repository
        self._birth_service = birth_service

    async def readiness(
        self, principal_id: UUID, source_guest_id: UUID, *, now: datetime | None = None
    ) -> MatchingReadiness:
        current = now or datetime.now(UTC)
        reveal, supplement, verification, profile, consent = await asyncio.gather(
            self._birth_service.current(source_guest_id),
            self._birth_service.supplement_state(source_guest_id),
            self._repository.get_verification(principal_id),
            self._repository.get_profile(principal_id),
            self._repository.get_active_consent(principal_id),
        )
        age = _age_on(reveal.birth_date, current.date())
        if verification is None:
            verification = MatchingVerification(
                principal_id=principal_id,
                status=VerificationStatus.NOT_STARTED,
                reason_code=None,
                updated_at=current,
            )
        return MatchingReadiness(
            profile=profile,
            consent=consent,
            verification=verification,
            age_eligible=age >= 18,
            birth_profile_level=supplement.profile_level,
        )

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
        now: datetime | None = None,
    ) -> MatchingProfile:
        normalized_name = display_name.strip()
        normalized_region = region_code.strip().lower()
        allowed_regions = {place_id.removeprefix("vn-") for place_id in CURRENT_ADMIN_CODES}
        if (
            len(normalized_name) < 2
            or len(normalized_name) > 32
            or not normalized_region
            or normalized_region not in allowed_regions
            or min_age < 18
            or max_age > 120
            or min_age > max_age
        ):
            raise MatchingProfileInvalid
        return await self._repository.save_profile(
            principal_id,
            display_name=normalized_name,
            gender_identity=gender_identity,
            intent=intent,
            gender_preference=gender_preference,
            min_age=min_age,
            max_age=max_age,
            region_code=normalized_region,
            weekly_intent=weekly_intent,
            now=now or datetime.now(UTC),
        )

    async def grant_consent(
        self, principal_id: UUID, *, version: str, now: datetime | None = None
    ) -> None:
        if version != MATCHING_CONSENT_VERSION:
            raise MatchingConsentInvalid
        await self._repository.grant_consent(
            principal_id,
            version=version,
            purpose=MATCHING_CONSENT_PURPOSE,
            now=now or datetime.now(UTC),
        )

    async def withdraw_consent(self, principal_id: UUID, *, now: datetime | None = None) -> None:
        await self._repository.withdraw_consent(principal_id, now=now or datetime.now(UTC))

    async def set_pool_membership(
        self,
        principal_id: UUID,
        source_guest_id: UUID,
        *,
        active: bool,
        now: datetime | None = None,
    ) -> MatchingProfile:
        current = now or datetime.now(UTC)
        if active:
            readiness = await self.readiness(principal_id, source_guest_id, now=current)
            if not readiness.ready:
                raise MatchingNotReady
        profile = await self._repository.set_active(principal_id, active=active, now=current)
        if profile is None:
            raise MatchingProfileRequired
        return profile


def _age_on(birth_date: date, on_date: date) -> int:
    return (
        on_date.year
        - birth_date.year
        - ((on_date.month, on_date.day) < (birth_date.month, birth_date.day))
    )
