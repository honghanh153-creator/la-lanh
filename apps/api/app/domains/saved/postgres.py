import json
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.readings.models import ReadingContentProjection
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.tables import SavedNoteRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresSavedNoteRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def save(self, record: SavedNoteRecord) -> SavedNoteRecord:
        async with self._sessions() as session, session.begin():
            existing = await session.scalar(
                select(SavedNoteRow).where(
                    SavedNoteRow.guest_id == record.guest_id,
                    SavedNoteRow.daily_note_id == record.daily_note_id,
                )
            )
            if existing is not None:
                return _record(existing, self._envelope)
            try:
                async with session.begin_nested():
                    row = SavedNoteRow(
                        id=record.id,
                        guest_id=record.guest_id,
                        daily_note_id=record.daily_note_id,
                        note_snapshot={},
                        snapshot_ciphertext=_encrypt_snapshot(record, self._envelope),
                        profile_id=record.profile_id,
                        revision_id=record.revision_id,
                        reading_snapshot={} if record.reading_snapshot is not None else None,
                        saved_at=record.saved_at,
                    )
                    session.add(row)
                    await session.flush()
                    return _record(row, self._envelope)
            except IntegrityError:
                existing = await session.scalar(
                    select(SavedNoteRow).where(
                        SavedNoteRow.guest_id == record.guest_id,
                        SavedNoteRow.daily_note_id == record.daily_note_id,
                    )
                )
                if existing is None:
                    raise
                return _record(existing, self._envelope)

    async def list_for_guest(self, guest_id: UUID) -> tuple[SavedNoteRecord, ...]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(SavedNoteRow)
                .where(SavedNoteRow.guest_id == guest_id)
                .order_by(SavedNoteRow.saved_at.desc())
            )
            return tuple(_record(row, self._envelope) for row in rows)

    async def delete(self, guest_id: UUID, daily_note_id: UUID) -> bool:
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                delete(SavedNoteRow).where(
                    SavedNoteRow.guest_id == guest_id,
                    SavedNoteRow.daily_note_id == daily_note_id,
                )
            )
            return bool(cast(CursorResult[Any], result).rowcount)


def _snapshot_context(record_id: UUID) -> bytes:
    return f"saved-note:{record_id}".encode()


def _encrypt_snapshot(record: SavedNoteRecord, envelope: EnvelopeCipher) -> str:
    payload = json.dumps(
        {
            "note_snapshot": record.note_snapshot,
            "reading_snapshot": (
                record.reading_snapshot.model_dump(mode="json")
                if record.reading_snapshot is not None
                else None
            ),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return envelope.encrypt(payload, context=_snapshot_context(record.id))


def _snapshot_payload(row: SavedNoteRow, envelope: EnvelopeCipher) -> dict[str, object]:
    if row.snapshot_ciphertext:
        decrypted = envelope.decrypt(
            row.snapshot_ciphertext,
            context=_snapshot_context(row.id),
        )
        payload: object = json.loads(decrypted)
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted saved note snapshot")
        return cast(dict[str, object], payload)
    return {
        "note_snapshot": row.note_snapshot,
        "reading_snapshot": row.reading_snapshot,
    }


def _record(row: SavedNoteRow, envelope: EnvelopeCipher) -> SavedNoteRecord:
    payload = _snapshot_payload(row, envelope)
    note_snapshot = payload.get("note_snapshot")
    if not isinstance(note_snapshot, dict):
        raise ValueError("invalid saved note snapshot")
    reading_snapshot = payload.get("reading_snapshot")
    return SavedNoteRecord(
        id=row.id,
        guest_id=row.guest_id,
        daily_note_id=row.daily_note_id,
        note_snapshot=cast(dict[str, object], note_snapshot),
        saved_at=row.saved_at,
        profile_id=row.profile_id,
        revision_id=row.revision_id,
        reading_snapshot=(
            ReadingContentProjection.model_validate(reading_snapshot)
            if reading_snapshot is not None
            else None
        ),
    )
