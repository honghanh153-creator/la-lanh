from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.resonance.models import ResonanceRecord, ResonanceStatus


class ResonanceRepository(Protocol):
    async def record_with_consent(
        self,
        record: ResonanceRecord,
        *,
        consent_version: str,
    ) -> ResonanceRecord: ...

    async def status(self, guest_id: UUID, *, now: datetime) -> ResonanceStatus: ...

    async def clear_with_consent(
        self,
        guest_id: UUID,
        *,
        revoke_consent: bool,
        now: datetime,
    ) -> None: ...

    async def purge_expired(self, *, now: datetime, batch_size: int) -> int: ...
