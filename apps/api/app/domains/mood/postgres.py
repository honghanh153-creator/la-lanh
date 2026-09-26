from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.tables import MoodCheckInRow


class PostgresMoodRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def upsert(self, record: MoodCheckInRecord) -> MoodCheckInRecord:
        async with self._sessions() as session, session.begin():
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
                )
                session.add(row)
            else:
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
