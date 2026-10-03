import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

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
        additional_consents: frozenset[tuple[str, str]] = frozenset(),
        ttl: timedelta = timedelta(days=30),
        replay_window: timedelta = timedelta(minutes=10),
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._envelope = envelope
        self._consent_version = consent_version
        self._consent_purpose = consent_purpose
        self._accepted_consents = additional_consents | {(consent_version, consent_purpose)}
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

    def session_epoch(self, guest: GuestSessionRecord) -> str:
        """Opaque client cache boundary; changes whenever a new guest session is created."""

        return self._hasher.digest("guest-session-epoch", str(guest.id)).hex()

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

    async def accept_deep_birth_consent(
        self, guest_id: UUID, *, version: str, now: datetime | None = None
    ) -> None:
        if version != "birth-profile-deep-v1":
            raise ConsentVersionInvalid
        await self._repository.save_consent(
            ConsentRecord(
                guest_id=guest_id,
                version=version,
                purpose="birth_profile_deep",
                accepted_at=now or datetime.now(UTC),
            )
        )

    async def accept_resonance_consent(
        self, guest_id: UUID, *, version: str, now: datetime | None = None
    ) -> None:
        if version != "reading-resonance-v1":
            raise ConsentVersionInvalid
        await self._repository.save_consent(
            ConsentRecord(
                guest_id=guest_id,
                version=version,
                purpose="reading_resonance",
                accepted_at=now or datetime.now(UTC),
            )
        )

    async def revoke_resonance_consent(
        self, guest_id: UUID, *, now: datetime | None = None
    ) -> None:
        await self._repository.revoke_consent(
            guest_id, "reading_resonance", now or datetime.now(UTC)
        )

    async def accept_content_rewrite_consent(
        self,
        guest_id: UUID,
        *,
        version: str,
        purpose: str = "external_content_rewrite",
        now: datetime | None = None,
    ) -> None:
        allowed = {
            ("external-content-rewrite-v1", "external_content_rewrite"),
            ("external-radar-rewrite-v1", "external_radar_rewrite"),
            ("external-matching-rewrite-v1", "external_matching_rewrite"),
        }
        if (version, purpose) not in allowed:
            raise ConsentVersionInvalid
        await self._repository.save_consent(
            ConsentRecord(
                guest_id=guest_id,
                version=version,
                purpose=purpose,
                accepted_at=now or datetime.now(UTC),
            )
        )

    async def revoke_content_rewrite_consent(
        self,
        guest_id: UUID,
        *,
        purpose: str = "external_content_rewrite",
        now: datetime | None = None,
    ) -> None:
        if purpose not in {
            "external_content_rewrite",
            "external_radar_rewrite",
            "external_matching_rewrite",
        }:
            raise ConsentPurposeInvalid
        await self._repository.revoke_consent(
            guest_id,
            purpose,
            now or datetime.now(UTC),
        )

    async def set_onboarding_status(self, guest_id: UUID, status: OnboardingStatus) -> None:
        await self._repository.update_onboarding(guest_id, status)

    def _validate_consent(self, version: str, purpose: str) -> None:
        if not any(version == accepted_version for accepted_version, _ in self._accepted_consents):
            raise ConsentVersionInvalid
        if (version, purpose) not in self._accepted_consents:
            raise ConsentPurposeInvalid
