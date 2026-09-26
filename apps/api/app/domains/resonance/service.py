from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domains.guest.errors import ConsentVersionInvalid
from app.domains.readings.models import BackgroundLens
from app.domains.resonance.models import ResonanceChoice, ResonanceRecord, ResonanceStatus
from app.domains.resonance.repository import ResonanceRepository


class ResonanceService:
    CONSENT_VERSION = "reading-resonance-v1"

    def __init__(self, repository: ResonanceRepository) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        guest_id: UUID,
        daily_note_id: UUID,
        revision_id: UUID | None,
        choice: ResonanceChoice,
        background_lens: BackgroundLens | None,
        consent_version: str,
        now: datetime | None = None,
    ) -> ResonanceRecord:
        if consent_version != self.CONSENT_VERSION:
            raise ConsentVersionInvalid
        current = now or datetime.now(UTC)
        return await self._repository.record_with_consent(
            ResonanceRecord(
                id=uuid4(),
                guest_id=guest_id,
                daily_note_id=daily_note_id,
                revision_id=revision_id,
                choice=choice,
                background_lens=background_lens,
                created_at=current,
                expires_at=current + timedelta(days=30),
            ),
            consent_version=consent_version,
        )

    async def status(self, guest_id: UUID, *, now: datetime | None = None) -> ResonanceStatus:
        return await self._repository.status(guest_id, now=now or datetime.now(UTC))

    async def clear(
        self,
        guest_id: UUID,
        *,
        revoke_consent: bool,
        now: datetime | None = None,
    ) -> None:
        await self._repository.clear_with_consent(
            guest_id,
            revoke_consent=revoke_consent,
            now=now or datetime.now(UTC),
        )

    async def cleanup(self, *, batch_size: int = 500, now: datetime | None = None) -> int:
        if batch_size < 1 or batch_size > 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        return await self._repository.purge_expired(
            now=now or datetime.now(UTC),
            batch_size=batch_size,
        )
