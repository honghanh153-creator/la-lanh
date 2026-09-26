import json
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.daily.models import (
    DailyNoteRecord,
    FallbackReason,
    PersonaLabel,
    PersonaMode,
    SourceLevel,
)
from app.domains.daily.tables import DailyNoteRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresDailyNoteRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def get_or_create(self, record: DailyNoteRecord) -> DailyNoteRecord:
        async with self._sessions() as session, session.begin():
            existing = await session.scalar(
                select(DailyNoteRow).where(
                    DailyNoteRow.guest_id == record.guest_id,
                    DailyNoteRow.note_date == record.note_date,
                )
            )
            if existing is not None:
                _refresh(existing, record, self._envelope)
                return _record(existing, self._envelope)
            try:
                async with session.begin_nested():
                    row = DailyNoteRow(
                        id=record.id,
                        guest_id=record.guest_id,
                        note_date=record.note_date,
                        title="",
                        body="",
                        full_body="",
                        context_label="",
                        content_ciphertext=_encrypt_content(
                            record,
                            self._envelope,
                            record_id=record.id,
                        ),
                        content_version=record.content_version,
                        persona_mode=record.persona_mode.value,
                        persona_label=record.persona_label.value,
                        persona_version=record.persona_version,
                        source_level=record.source_level.value,
                        astrology_source_version=record.astrology_source_version,
                        fallback_used=record.fallback_used,
                        fallback_reason=(
                            record.fallback_reason.value if record.fallback_reason else None
                        ),
                        chart_snapshot_id=record.chart_snapshot_id,
                        created_at=record.created_at,
                    )
                    session.add(row)
                    await session.flush()
                    return _record(row, self._envelope)
            except IntegrityError:
                existing = await session.scalar(
                    select(DailyNoteRow).where(
                        DailyNoteRow.guest_id == record.guest_id,
                        DailyNoteRow.note_date == record.note_date,
                    )
                )
                if existing is None:
                    raise
                _refresh(existing, record, self._envelope)
                return _record(existing, self._envelope)

    async def find(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(DailyNoteRow).where(
                    DailyNoteRow.guest_id == guest_id,
                    DailyNoteRow.id == note_id,
                )
            )
            return _record(row, self._envelope) if row is not None else None


def _content_context(record_id: UUID) -> bytes:
    return f"daily-note:{record_id}".encode()


def _encrypt_content(
    record: DailyNoteRecord,
    envelope: EnvelopeCipher,
    *,
    record_id: UUID,
) -> str:
    payload = json.dumps(
        {
            "title": record.title,
            "body": record.body,
            "full_body": record.full_body,
            "context_label": record.context_label,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return envelope.encrypt(payload, context=_content_context(record_id))


def _content(row: DailyNoteRow, envelope: EnvelopeCipher) -> dict[str, object]:
    if row.content_ciphertext:
        decrypted = envelope.decrypt(
            row.content_ciphertext,
            context=_content_context(row.id),
        )
        payload: object = json.loads(decrypted)
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted daily note content")
        return cast(dict[str, object], payload)
    return {
        "title": row.title,
        "body": row.body,
        "full_body": row.full_body,
        "context_label": row.context_label,
    }


def _record(row: DailyNoteRow, envelope: EnvelopeCipher) -> DailyNoteRecord:
    content = _content(row, envelope)
    return DailyNoteRecord(
        id=row.id,
        guest_id=row.guest_id,
        note_date=row.note_date,
        title=str(content["title"]),
        body=str(content["body"]),
        full_body=str(content["full_body"]),
        context_label=str(content["context_label"]),
        content_version=row.content_version,
        persona_mode=PersonaMode(row.persona_mode),
        persona_label=PersonaLabel(row.persona_label),
        persona_version=row.persona_version,
        source_level=SourceLevel(row.source_level),
        astrology_source_version=row.astrology_source_version,
        fallback_used=row.fallback_used,
        fallback_reason=FallbackReason(row.fallback_reason) if row.fallback_reason else None,
        chart_snapshot_id=row.chart_snapshot_id,
        created_at=row.created_at,
    )


def _refresh(
    row: DailyNoteRow,
    record: DailyNoteRecord,
    envelope: EnvelopeCipher,
) -> None:
    if (
        row.content_version == record.content_version
        and row.persona_version == record.persona_version
        and row.chart_snapshot_id == record.chart_snapshot_id
    ):
        return
    row.title = ""
    row.body = ""
    row.full_body = ""
    row.context_label = ""
    row.content_ciphertext = _encrypt_content(record, envelope, record_id=row.id)
    row.content_version = record.content_version
    row.persona_mode = record.persona_mode.value
    row.persona_label = record.persona_label.value
    row.persona_version = record.persona_version
    row.source_level = record.source_level.value
    row.astrology_source_version = record.astrology_source_version
    row.fallback_used = record.fallback_used
    row.fallback_reason = record.fallback_reason.value if record.fallback_reason else None
    row.chart_snapshot_id = record.chart_snapshot_id
