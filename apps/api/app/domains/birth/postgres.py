from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.astro.models import DateOnlySunResult
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow


class PostgresBirthRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def save_or_replay(self, record: BirthSnapshotRecord) -> tuple[BirthSnapshotRecord, bool]:
        async with self._sessions() as session, session.begin():
            existing = await session.scalar(
                select(ChartSnapshotRow).where(
                    ChartSnapshotRow.guest_id == record.guest_id,
                    ChartSnapshotRow.input_hash == record.input_hash,
                )
            )
            if existing is not None:
                return _record(existing), True

            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == record.guest_id)
            )
            if profile is None:
                try:
                    async with session.begin_nested():
                        session.add(
                            BirthProfileRow(
                                id=record.profile_id,
                                guest_id=record.guest_id,
                                created_at=record.created_at,
                                updated_at=record.created_at,
                            )
                        )
                        await session.flush()
                except IntegrityError:
                    pass
                profile = await session.scalar(
                    select(BirthProfileRow).where(BirthProfileRow.guest_id == record.guest_id)
                )
                if profile is None:
                    raise RuntimeError("birth profile creation could not be resolved")

            snapshot = ChartSnapshotRow(
                id=record.id,
                guest_id=record.guest_id,
                profile_id=profile.id,
                input_hash=record.input_hash,
                birth_date_ciphertext=record.birth_date_ciphertext,
                schema_version="1.0.0",
                engine_version=record.result.provenance.version,
                calculation_profile=record.result.provenance.profile,
                result_payload=record.result.model_dump(mode="json"),
                created_at=record.created_at,
            )
            session.add(snapshot)
            profile.current_snapshot_id = snapshot.id
            profile.updated_at = record.created_at
            await session.flush()
            return _record(snapshot), False

    async def find_current(self, guest_id: UUID) -> BirthSnapshotRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(ChartSnapshotRow)
                .join(
                    BirthProfileRow,
                    BirthProfileRow.current_snapshot_id == ChartSnapshotRow.id,
                )
                .where(BirthProfileRow.guest_id == guest_id)
            )
            return _record(row) if row is not None else None


def _record(row: ChartSnapshotRow) -> BirthSnapshotRecord:
    return BirthSnapshotRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        input_hash=row.input_hash,
        birth_date_ciphertext=row.birth_date_ciphertext,
        result=DateOnlySunResult.model_validate(row.result_payload),
        created_at=row.created_at,
    )
