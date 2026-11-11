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
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], envelope: EnvelopeCipher
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

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
                row = MoodCheckInRow(
                    id=record.id,
                    guest_id=record.guest_id,
                    daily_note_id=record.daily_note_id,
                    mood=None,
                    mood_ciphertext=_encrypt(record.id, record.mood, self._envelope),
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
                # Re-encrypt under this row's id; a legacy plain value is cleared here.
                row.mood = None
                row.mood_ciphertext = _encrypt(row.id, record.mood, self._envelope)
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


def _encrypt(row_id: UUID, mood: MoodValue, envelope: EnvelopeCipher) -> str:
    return envelope.encrypt(mood.value.encode(), context=_context(row_id))


def mood_value(row: MoodCheckInRow, envelope: EnvelopeCipher) -> MoodValue:
    """The stored mood. A plain value wins when present: this image never writes one, so it is
    either a legacy row or a newer change from a previous image during a rolling deploy."""
    if row.mood is not None:
        return MoodValue(row.mood)
    if row.mood_ciphertext is None:
        raise ValueError("mood check-in has no stored value")
    return MoodValue(envelope.decrypt(row.mood_ciphertext, context=_context(row.id)).decode())


def _record(row: MoodCheckInRow, envelope: EnvelopeCipher) -> MoodCheckInRecord:
    return MoodCheckInRecord(
        id=row.id,
        guest_id=row.guest_id,
        daily_note_id=row.daily_note_id,
        mood=mood_value(row, envelope),
        checked_in_at=row.checked_in_at,
    )
