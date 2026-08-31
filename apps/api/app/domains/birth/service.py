from datetime import UTC, date, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from app.domains.astro.engine import NatalChartEngine
from app.domains.birth.errors import BirthDateOutOfRange, BirthProfileNotFound
from app.domains.birth.models import BirthReveal, BirthSnapshotRecord
from app.domains.birth.repository import BirthRepository
from app.infrastructure.crypto import EnvelopeCipher


class BirthChartService:
    def __init__(
        self,
        repository: BirthRepository,
        engine: NatalChartEngine,
        envelope: EnvelopeCipher,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._envelope = envelope

    async def create_date_only(
        self,
        *,
        guest_id: UUID,
        birth_date: date,
        now: datetime | None = None,
    ) -> BirthReveal:
        current = now or datetime.now(UTC)
        if birth_date < date(1800, 1, 1) or birth_date > min(date(2399, 12, 31), current.date()):
            raise BirthDateOutOfRange
        result = self._engine.calculate_date_only_sun(birth_date)
        canonical_input = f"date-only-v1:{birth_date.isoformat()}".encode()
        input_hash = sha256(canonical_input).digest()
        encrypted_date = self._envelope.encrypt(
            birth_date.isoformat().encode(),
            context=f"birth-date:{guest_id}".encode(),
        )
        stored, resumed = await self._repository.save_or_replay(
            BirthSnapshotRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=uuid4(),
                input_hash=input_hash,
                birth_date_ciphertext=encrypted_date,
                result=result,
                created_at=current,
            )
        )
        stored_date = date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{guest_id}".encode(),
            ).decode()
        )
        return BirthReveal(
            profile_id=stored.profile_id,
            snapshot_id=stored.id,
            birth_date=stored_date,
            result=stored.result,
            created_at=stored.created_at,
            resumed=resumed,
        )

    async def current(self, guest_id: UUID) -> BirthReveal:
        stored = await self._repository.find_current(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        birth_date = date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{guest_id}".encode(),
            ).decode()
        )
        return BirthReveal(
            profile_id=stored.profile_id,
            snapshot_id=stored.id,
            birth_date=birth_date,
            result=stored.result,
            created_at=stored.created_at,
            resumed=True,
        )
