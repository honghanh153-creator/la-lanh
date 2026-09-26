import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domains.guest.errors import (
    ConsentVersionInvalid,
    GuestExpired,
    IdempotencyReplayExpired,
)
from app.domains.guest.models import (
    ConsentRecord,
    CreationMaterial,
    OnboardingStatus,
    StoredCreation,
)
from app.domains.guest.service import GuestSessionService
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider


class MemoryGuestRepository:
    def __init__(self) -> None:
        self.creations: dict[bytes, StoredCreation] = {}
        self.guests: dict[bytes, StoredCreation] = {}
        self._lock = asyncio.Lock()
        self.consents: dict[tuple[UUID, str], ConsentRecord] = {}

    async def create_or_replay(self, material: CreationMaterial) -> StoredCreation:
        async with self._lock:
            existing = self.creations.get(material.idempotency_hash)
            if existing is not None:
                if existing.replay_expires_at <= material.guest.created_at:
                    existing = replace(existing, credential_envelope=None)
                    self.creations[material.idempotency_hash] = existing
                return existing
            stored = StoredCreation(
                guest=material.guest,
                request_hash=material.request_hash,
                credential_envelope=material.credential_envelope,
                replay_expires_at=material.replay_expires_at,
            )
            self.creations[material.idempotency_hash] = stored
            self.guests[material.guest.token_hash] = stored
            return stored

    async def find_by_token_hash(
        self,
        token_hash: bytes,
        now: datetime,
        *,
        touch_until: datetime | None = None,
    ) -> StoredCreation | None:
        stored = self.guests.get(token_hash)
        if stored is None:
            return None
        if touch_until is not None and stored.guest.expires_at > now:
            stored = replace(
                stored,
                guest=replace(stored.guest, last_active_at=now, expires_at=touch_until),
            )
            self.guests[token_hash] = stored
        return stored

    async def delete_by_token_hash(self, token_hash: bytes, now: datetime) -> bool:
        del now
        return self.guests.pop(token_hash, None) is not None

    async def purge_expired(self, now: datetime, batch_size: int) -> int:
        expired = [
            token_hash
            for token_hash, stored in self.guests.items()
            if stored.guest.expires_at <= now
        ][:batch_size]
        for token_hash in expired:
            del self.guests[token_hash]
        return len(expired)

    async def save_consent(self, consent: ConsentRecord) -> None:
        self.consents[(consent.guest_id, consent.purpose)] = consent

    async def revoke_consent(self, guest_id: UUID, purpose: str, revoked_at: datetime) -> None:
        del revoked_at
        self.consents.pop((guest_id, purpose), None)

    async def update_onboarding(self, guest_id: UUID, status: OnboardingStatus) -> None:
        for token_hash, stored in list(self.guests.items()):
            if stored.guest.id == guest_id:
                updated = replace(stored, guest=replace(stored.guest, onboarding_status=status))
                self.guests[token_hash] = updated


@pytest.fixture
def repository() -> MemoryGuestRepository:
    return MemoryGuestRepository()


@pytest.fixture
def service(repository: MemoryGuestRepository) -> GuestSessionService:
    key = b"k" * 32
    return GuestSessionService(
        repository,
        SecretHasher(key),
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32)),
        consent_version="birth-profile-v1",
        consent_purpose="birth_profile_basic",
    )


@pytest.mark.asyncio
async def test_concurrent_idempotent_creation_returns_one_guest_and_credential(
    service: GuestSessionService, repository: MemoryGuestRepository
) -> None:
    now = datetime(2026, 8, 30, 12, tzinfo=UTC)
    first, second = await asyncio.gather(
        service.create(
            consent_version="birth-profile-v1",
            purpose="birth_profile_basic",
            idempotency_key="guest-create-key-1234567890",
            now=now,
        ),
        service.create(
            consent_version="birth-profile-v1",
            purpose="birth_profile_basic",
            idempotency_key="guest-create-key-1234567890",
            now=now,
        ),
    )

    assert first.guest.id == second.guest.id
    assert first.token == second.token
    assert first.csrf_token == second.csrf_token
    assert len(repository.guests) == 1


@pytest.mark.asyncio
async def test_stale_consent_is_rejected_before_persistence(
    service: GuestSessionService, repository: MemoryGuestRepository
) -> None:
    with pytest.raises(ConsentVersionInvalid):
        await service.create(
            consent_version="old-version",
            purpose="birth_profile_basic",
            idempotency_key="guest-create-key-1234567890",
        )
    assert repository.guests == {}


@pytest.mark.asyncio
async def test_idempotency_key_cannot_recover_credential_after_replay_window(
    service: GuestSessionService,
) -> None:
    now = datetime(2026, 8, 30, 12, tzinfo=UTC)
    await service.create(
        consent_version="birth-profile-v1",
        purpose="birth_profile_basic",
        idempotency_key="guest-create-key-1234567890",
        now=now,
    )
    with pytest.raises(IdempotencyReplayExpired):
        await service.create(
            consent_version="birth-profile-v1",
            purpose="birth_profile_basic",
            idempotency_key="guest-create-key-1234567890",
            now=now + timedelta(minutes=11),
        )


@pytest.mark.asyncio
async def test_expired_guest_cannot_resume(service: GuestSessionService) -> None:
    now = datetime(2026, 8, 30, 12, tzinfo=UTC)
    created = await service.create(
        consent_version="birth-profile-v1",
        purpose="birth_profile_basic",
        idempotency_key="guest-create-key-1234567890",
        now=now,
    )
    with pytest.raises(GuestExpired):
        await service.resume(created.token, now=now + timedelta(days=31))


@pytest.mark.asyncio
async def test_database_hash_is_not_an_http_credential(
    service: GuestSessionService, repository: MemoryGuestRepository
) -> None:
    created = await service.create(
        consent_version="birth-profile-v1",
        purpose="birth_profile_basic",
        idempotency_key="guest-create-key-1234567890",
    )
    token_hash = next(iter(repository.guests)).hex()
    assert await service.resume(created.token)
    with pytest.raises(GuestExpired):
        await service.resume(token_hash)
