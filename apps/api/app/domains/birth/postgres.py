import json
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.astro.models import ChartType, DateOnlySunResult, NatalChart
from app.domains.birth.models import BirthSnapshotRecord, BirthSupplement, BirthSupplementStored
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.readings.tables import ReadingPlanRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresBirthRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def save_or_replay(self, record: BirthSnapshotRecord) -> tuple[BirthSnapshotRecord, bool]:
        async with self._sessions() as session, session.begin():
            existing = await session.scalar(
                select(ChartSnapshotRow).where(
                    ChartSnapshotRow.guest_id == record.guest_id,
                    ChartSnapshotRow.input_hash == record.input_hash,
                )
            )
            if existing is not None:
                return _record(existing, self._envelope), True

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
                result_payload=None,
                result_ciphertext=_encrypt_result(record, self._envelope),
                created_at=record.created_at,
            )
            session.add(snapshot)
            await session.flush([snapshot])
            profile.current_snapshot_id = snapshot.id
            profile.updated_at = record.created_at
            await session.flush()
            return _record(snapshot, self._envelope), False

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
            return _record(row, self._envelope) if row is not None else None

    async def find_by_input_hash(
        self, guest_id: UUID, input_hash: bytes
    ) -> BirthSnapshotRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(ChartSnapshotRow).where(
                    ChartSnapshotRow.guest_id == guest_id,
                    ChartSnapshotRow.input_hash == input_hash,
                )
            )
            return _record(row, self._envelope) if row is not None else None

    async def save_supplement(
        self, guest_id: UUID, snapshot: BirthSnapshotRecord | None, supplement: BirthSupplement
    ) -> BirthSnapshotRecord | None:
        async with self._sessions() as session, session.begin():
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is None:
                raise RuntimeError("birth profile is required before supplement")
            active: ChartSnapshotRow | None = None
            if snapshot is not None:
                active = await session.scalar(
                    select(ChartSnapshotRow).where(
                        ChartSnapshotRow.guest_id == guest_id,
                        ChartSnapshotRow.input_hash == snapshot.input_hash,
                    )
                )
                if active is None:
                    active = ChartSnapshotRow(
                        id=snapshot.id,
                        guest_id=guest_id,
                        profile_id=profile.id,
                        input_hash=snapshot.input_hash,
                        birth_date_ciphertext=snapshot.birth_date_ciphertext,
                        schema_version="1.1.0",
                        engine_version=snapshot.result.provenance.version,
                        calculation_profile=snapshot.result.provenance.profile,
                        result_payload=None,
                        result_ciphertext=_encrypt_result(snapshot, self._envelope),
                        created_at=snapshot.created_at,
                    )
                    session.add(active)
                    await session.flush([active])
                profile.current_snapshot_id = active.id
            profile.profile_level = (
                3
                if supplement.birth_place_ciphertext
                and supplement.birth_time_mode.value != "unknown"
                else 2
            )
            if supplement.birth_time_mode.value == "unknown":
                profile.profile_level = 1
            profile.birth_time_ciphertext = supplement.birth_time_ciphertext
            profile.birth_place_ciphertext = supplement.birth_place_ciphertext
            profile.time_precision = (
                "approximate"
                if supplement.birth_time_mode.value == "approx_window"
                else supplement.birth_time_mode.value
            )
            profile.place_display_name = None
            profile.timezone_id = None
            profile.supplement_consent_version = supplement.consent_version
            profile.updated_at = snapshot.created_at if snapshot is not None else profile.updated_at
            await session.flush()
            return _record(active, self._envelope) if active is not None else None

    async def find_supplement(self, guest_id: UUID) -> BirthSupplementStored | None:
        async with self._sessions() as session:
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            return _supplement_record(profile) if profile is not None else None

    async def clear_supplement(
        self, guest_id: UUID, *, remove_time: bool, remove_place: bool
    ) -> BirthSupplementStored:
        async with self._sessions() as session, session.begin():
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
            )
            if profile is None:
                raise RuntimeError("birth profile is required before supplement removal")
            had_full_precision = profile.profile_level == 3
            if remove_time:
                profile.birth_time_ciphertext = None
                profile.time_precision = "unknown"
            if remove_place:
                profile.birth_place_ciphertext = None
                profile.place_display_name = None
                profile.timezone_id = None
            profile.profile_level = 2 if profile.birth_time_ciphertext is not None else 1
            if had_full_precision and profile.profile_level < 3:
                snapshots = await session.scalars(
                    select(ChartSnapshotRow)
                    .where(ChartSnapshotRow.profile_id == profile.id)
                    .order_by(ChartSnapshotRow.created_at.desc())
                )
                date_only = next(
                    (
                        row
                        for row in snapshots
                        if _record(row, self._envelope).result.chart_type
                        == ChartType.DATE_ONLY_NATAL
                    ),
                    None,
                )
                if date_only is None:
                    raise RuntimeError("date-only snapshot is required before supplement removal")
                profile.current_snapshot_id = date_only.id
                await session.flush([profile])

                # Precision withdrawal is also withdrawal of every artifact derived from
                # that precision. Daily-note deletion cascades to moods, saves and shares;
                # plan deletion cascades to revisions, projections and generation attempts.
                # Keeping only the date-only snapshot prevents old House/angle facts from
                # remaining recoverable after the user chose deletion.
                await session.execute(
                    delete(DailyExperimentRow).where(DailyExperimentRow.guest_id == guest_id)
                )
                await session.execute(delete(DailyNoteRow).where(DailyNoteRow.guest_id == guest_id))
                await session.execute(
                    delete(ReadingPlanRow).where(ReadingPlanRow.profile_id == profile.id)
                )
                await session.execute(
                    delete(ChartSnapshotRow).where(
                        ChartSnapshotRow.profile_id == profile.id,
                        ChartSnapshotRow.id != date_only.id,
                    )
                )
            await session.flush()
            return _supplement_record(profile)


def _record(row: ChartSnapshotRow, envelope: EnvelopeCipher) -> BirthSnapshotRecord:
    return BirthSnapshotRecord(
        id=row.id,
        guest_id=row.guest_id,
        profile_id=row.profile_id,
        input_hash=row.input_hash,
        birth_date_ciphertext=row.birth_date_ciphertext,
        result=_chart_result(_result_payload(row, envelope)),
        created_at=row.created_at,
    )


def _supplement_record(row: BirthProfileRow) -> BirthSupplementStored:
    return BirthSupplementStored(
        profile_id=row.id,
        profile_level=row.profile_level,
        birth_time_ciphertext=row.birth_time_ciphertext,
        birth_place_ciphertext=row.birth_place_ciphertext,
        time_precision=row.time_precision,
        supplement_consent_version=row.supplement_consent_version,
    )


def _chart_result(payload: dict[str, object]) -> DateOnlySunResult | NatalChart:
    chart_type = payload.get("chart_type")
    if chart_type == ChartType.NATAL.value:
        return NatalChart.model_validate(payload)
    return DateOnlySunResult.model_validate(payload)


def _chart_context(snapshot_id: UUID) -> bytes:
    return f"chart-snapshot:{snapshot_id}".encode()


def _encrypt_result(record: BirthSnapshotRecord, envelope: EnvelopeCipher) -> str:
    payload = json.dumps(
        record.result.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return envelope.encrypt(payload, context=_chart_context(record.id))


def _result_payload(row: ChartSnapshotRow, envelope: EnvelopeCipher) -> dict[str, object]:
    if row.result_ciphertext:
        decrypted = envelope.decrypt(
            row.result_ciphertext,
            context=_chart_context(row.id),
        )
        payload = json.loads(decrypted)
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted chart snapshot")
        return payload
    if row.result_payload is not None:
        return row.result_payload
    raise ValueError("chart snapshot has no result")
