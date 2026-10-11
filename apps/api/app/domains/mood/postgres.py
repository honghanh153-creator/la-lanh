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


class PostgresMoodRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

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
                    mood=record.mood.value,
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
                row.mood = record.mood.value
                row.checked_in_at = record.checked_in_at
            await session.flush()
            return _record(row)

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
            return _record(row) if row is not None else None


def _record(row: MoodCheckInRow) -> MoodCheckInRecord:
    return MoodCheckInRecord(
        id=row.id,
        guest_id=row.guest_id,
        daily_note_id=row.daily_note_id,
        mood=MoodValue(row.mood),
        checked_in_at=row.checked_in_at,
    )
