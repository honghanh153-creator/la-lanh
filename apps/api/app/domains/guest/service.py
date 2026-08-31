import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.domains.guest.errors import (
    ConsentPurposeInvalid,
    ConsentVersionInvalid,
    GuestExpired,
    GuestSessionMissing,
    IdempotencyConflict,
    IdempotencyKeyInvalid,
    IdempotencyReplayExpired,
)
from app.domains.guest.models import (
    ConsentRecord,
    CreationMaterial,
    CreationResult,
    GuestSessionRecord,
    GuestState,
    OnboardingStatus,
)
from app.domains.guest.repository import GuestRepository
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22,200}$")


class GuestSessionService:
    def __init__(
        self,
        repository: GuestRepository,
        hasher: SecretHasher,
        envelope: EnvelopeCipher,
        *,
        consent_version: str,
        consent_purpose: str,
        ttl: timedelta = timedelta(days=30),
        replay_window: timedelta = timedelta(minutes=10),
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._envelope = envelope
        self._consent_version = consent_version
        self._consent_purpose = consent_purpose
        self._ttl = ttl
        self._replay_window = replay_window

    async def create(
        self,
        *,
        consent_version: str,
        purpose: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> CreationResult:
        current = now or datetime.now(UTC)
        self._validate_consent(consent_version, purpose)
        if not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
            raise IdempotencyKeyInvalid

        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        guest_id = secrets.SystemRandom().getrandbits(128)
        from uuid import UUID

        guest = GuestSessionRecord(
            id=UUID(int=guest_id),
            token_hash=self._hasher.digest("guest-credential", token),
            csrf_hash=self._hasher.digest("guest-csrf", csrf_token),
            state=GuestState.ACTIVE,
            onboarding_status=OnboardingStatus.BIRTH_PENDING,
            created_at=current,
            last_active_at=current,
            expires_at=current + self._ttl,
        )
        request_hash = sha256(f"{consent_version}\x00{purpose}".encode()).digest()
        replay_expires_at = current + self._replay_window
        credential_envelope = self._envelope.encrypt(
            json.dumps({"token": token, "csrf_token": csrf_token}).encode(),
            context=b"guest-issuance-v1",
        )
        stored = await self._repository.create_or_replay(
            CreationMaterial(
                guest=guest,
                consent=ConsentRecord(
                    guest_id=guest.id,
                    version=consent_version,
                    purpose=purpose,
                    accepted_at=current,
                ),
                idempotency_hash=self._hasher.digest("guest-idempotency", idempotency_key),
                request_hash=request_hash,
                credential_envelope=credential_envelope,
                replay_expires_at=replay_expires_at,
            )
        )
        if not secrets.compare_digest(stored.request_hash, request_hash):
            raise IdempotencyConflict
        if stored.credential_envelope is None or stored.replay_expires_at <= current:
            raise IdempotencyReplayExpired
        raw = self._envelope.decrypt(stored.credential_envelope, context=b"guest-issuance-v1")
        credentials = json.loads(raw)
        return CreationResult(
            guest=stored.guest,
            token=str(credentials["token"]),
            csrf_token=str(credentials["csrf_token"]),
            resumed=stored.guest.id != guest.id,
        )

    async def resume(self, token: str | None, *, now: datetime | None = None) -> GuestSessionRecord:
        if not token:
            raise GuestSessionMissing
        current = now or datetime.now(UTC)
        stored = await self._repository.find_by_token_hash(
            self._hasher.digest("guest-credential", token),
            current,
            touch_until=current + self._ttl,
        )
        if stored is None or not stored.guest.is_active(current):
            raise GuestExpired
        return stored.guest

    async def delete(self, token: str | None, *, now: datetime | None = None) -> None:
        if not token:
            raise GuestSessionMissing
        current = now or datetime.now(UTC)
        deleted = await self._repository.delete_by_token_hash(
            self._hasher.digest("guest-credential", token), current
        )
        if not deleted:
            raise GuestExpired

    async def verify_csrf(
        self, token: str | None, csrf_token: str | None, *, now: datetime | None = None
    ) -> GuestSessionRecord:
        guest = await self.resume(token, now=now)
        if not csrf_token or not self._hasher.verify("guest-csrf", csrf_token, guest.csrf_hash):
            from app.domains.guest.errors import CsrfRejected

            raise CsrfRejected
        return guest

    async def cleanup(self, *, batch_size: int, now: datetime | None = None) -> int:
        if batch_size < 1 or batch_size > 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        return await self._repository.purge_expired(now or datetime.now(UTC), batch_size)

    def _validate_consent(self, version: str, purpose: str) -> None:
        if version != self._consent_version:
            raise ConsentVersionInvalid
        if purpose != self._consent_purpose:
            raise ConsentPurposeInvalid
