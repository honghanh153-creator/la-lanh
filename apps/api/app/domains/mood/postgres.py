from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.postgres import account_transaction, lock_owner
from app.domains.daily.tables import DailyNoteRow
from app.domains.history.errors import HistoryUnavailable
from app.domains.history.postgres import expired_history, unavailable_daily
from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.tables import MoodCheckInRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresMoodRepository:
    """Reads plain and encrypted moods. Writes stay plain until `encrypt_writes` is on, because an
    image older than this one cannot read an encrypted row (its `mood` column is NULL). Turn it on
    only when every running image and the rollback image can read encrypted rows."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        *,
        encrypt_writes: bool = False,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._encrypt_writes = encrypt_writes

    def _stored(self, row_id: UUID, mood: MoodValue) -> tuple[str | None, str | None]:
        if not self._encrypt_writes:
            return mood.value, None
        return None, _encrypt(row_id, mood, self._envelope)

    async def upsert(self, record: MoodCheckInRecord) -> MoodCheckInRecord:
        async with account_transaction(self._sessions) as session:
            await lock_owner(session, record.guest_id)
            source = await session.scalar(
                select(DailyNoteRow.id).where(
                    DailyNoteRow.id == record.daily_note_id,
                    DailyNoteRow.guest_id == record.guest_id,
                    ~unavailable_daily(record.checked_in_at),
                )
            )
            if source is None:
                raise HistoryUnavailable
            row = await session.scalar(
                select(MoodCheckInRow).where(
                    MoodCheckInRow.guest_id == record.guest_id,
                    MoodCheckInRow.daily_note_id == record.daily_note_id,
                )
            )
            if row is None:
                plain, ciphertext = self._stored(record.id, record.mood)
                row = MoodCheckInRow(
                    id=record.id,
                    guest_id=record.guest_id,
                    daily_note_id=record.daily_note_id,
                    mood=plain,
                    mood_ciphertext=ciphertext,
                    checked_in_at=record.checked_in_at,
                    created_at=record.checked_in_at,
                )
                session.add(row)
            else:
                expired = await session.scalar(
                    select(MoodCheckInRow.id).where(
                        MoodCheckInRow.id == row.id,
                        expired_history(
                            MoodCheckInRow.guest_id, MoodCheckInRow.created_at, record.checked_in_at
                        ),
                    )
                )
                if expired is not None:
                    raise HistoryUnavailable
                # With encrypted writes on, a legacy plain value is cleared here.
                row.mood, row.mood_ciphertext = self._stored(row.id, record.mood)
                row.checked_in_at = record.checked_in_at
            await session.flush()
            return _record(row, self._envelope)

    async def find(self, guest_id: UUID, daily_note_id: UUID) -> MoodCheckInRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(MoodCheckInRow).where(
                    MoodCheckInRow.guest_id == guest_id,
                    MoodCheckInRow.daily_note_id == daily_note_id,
                    ~expired_history(
                        MoodCheckInRow.guest_id, MoodCheckInRow.created_at, datetime.now(UTC)
                    ),
                )
            )
            return _record(row, self._envelope) if row is not None else None


def _context(row_id: UUID) -> bytes:
    return f"mood-check-in:{row_id}".encode()


# AES-GCM keeps the plaintext length, so every mood is padded to one size before encryption;
# otherwise the ciphertext length alone would tell the longer choices apart.
_PADDED_BYTES = 16


def _encrypt(row_id: UUID, mood: MoodValue, envelope: EnvelopeCipher) -> str:
    raw = mood.value.encode()
    if len(raw) > _PADDED_BYTES:
        raise ValueError("mood value is longer than its padded size")
    return envelope.encrypt(raw.ljust(_PADDED_BYTES, b"\0"), context=_context(row_id))


def mood_value(row: MoodCheckInRow, envelope: EnvelopeCipher) -> MoodValue:
    """The stored mood. A plain value wins when present: it is either a legacy row, a write made
    while encrypted writes are off, or a newer change from an older image."""
    if row.mood is not None:
        return MoodValue(row.mood)
    if row.mood_ciphertext is None:
        raise ValueError("mood check-in has no stored value")
    raw = envelope.decrypt(row.mood_ciphertext, context=_context(row.id))
    return MoodValue(raw.rstrip(b"\0").decode())


def _record(row: MoodCheckInRow, envelope: EnvelopeCipher) -> MoodCheckInRecord:
    return MoodCheckInRecord(
        id=row.id,
        guest_id=row.guest_id,
        daily_note_id=row.daily_note_id,
        mood=mood_value(row, envelope),
        checked_in_at=row.checked_in_at,
    )
