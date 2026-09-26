from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.matching.models import (
    GenderPreference,
    MatchingConsent,
    MatchingGender,
    MatchingIntent,
    MatchingProfile,
    MatchingVerification,
    WeeklyIntent,
)


class MatchingRepository(Protocol):
    async def get_profile(self, principal_id: UUID) -> MatchingProfile | None: ...

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
    ) -> MatchingProfile: ...

    async def get_active_consent(self, principal_id: UUID) -> MatchingConsent | None: ...

    async def grant_consent(
        self, principal_id: UUID, *, version: str, purpose: str, now: datetime
    ) -> MatchingConsent: ...

    async def withdraw_consent(self, principal_id: UUID, *, now: datetime) -> None: ...

    async def get_verification(self, principal_id: UUID) -> MatchingVerification | None: ...

    async def set_active(
        self, principal_id: UUID, *, active: bool, now: datetime
    ) -> MatchingProfile | None: ...
