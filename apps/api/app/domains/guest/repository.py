from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.guest.models import (
    ConsentRecord,
    CreationMaterial,
    OnboardingStatus,
    StoredCreation,
)


class GuestRepository(Protocol):
    async def create_or_replay(self, material: CreationMaterial) -> StoredCreation: ...

    async def find_by_token_hash(
        self, token_hash: bytes, now: datetime, *, touch_until: datetime | None = None
    ) -> StoredCreation | None: ...

    async def delete_by_token_hash(self, token_hash: bytes, now: datetime) -> bool: ...

    async def purge_expired(self, now: datetime, batch_size: int) -> int: ...

    async def save_consent(self, consent: ConsentRecord) -> None: ...

    async def revoke_consent(self, guest_id: UUID, purpose: str, revoked_at: datetime) -> None: ...

    async def update_onboarding(self, guest_id: UUID, status: OnboardingStatus) -> None: ...


RepositoryFactory = Callable[[], GuestRepository]
