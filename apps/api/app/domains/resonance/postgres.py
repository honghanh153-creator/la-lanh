import json
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.daily.tables import DailyNoteRow
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.readings.models import BackgroundLens
from app.domains.readings.tables import ReadingRevisionRow
from app.domains.resonance.errors import ResonanceTargetNotFound
from app.domains.resonance.models import ResonanceChoice, ResonanceRecord, ResonanceStatus
from app.domains.resonance.tables import ResonanceFeedbackRow
from app.infrastructure.crypto import EnvelopeCipher

RESONANCE_PURPOSE = "reading_resonance"


class PostgresResonanceRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def record_with_consent(
        self,
        record: ResonanceRecord,
        *,
        consent_version: str,
    ) -> ResonanceRecord:
        revision_key = str(record.revision_id or "legacy")
        async with self._sessions() as session, session.begin():
            # Authorization is deliberately first: an invalid owner cannot create
            # or refresh consent, even if a later feedback write would fail.
            await self._require_owned_target(session, record)
            await self._accept_consent(
                session,
                guest_id=record.guest_id,
                version=consent_version,
                accepted_at=record.created_at,
            )
            await self._after_consent()

            row = await session.scalar(
                select(ResonanceFeedbackRow).where(
                    ResonanceFeedbackRow.guest_id == record.guest_id,
                    ResonanceFeedbackRow.daily_note_id == record.daily_note_id,
                    ResonanceFeedbackRow.revision_key == revision_key,
                )
            )
            if row is None:
                row = ResonanceFeedbackRow(
                    id=record.id,
                    guest_id=record.guest_id,
                    daily_note_id=record.daily_note_id,
                    revision_id=record.revision_id,
                    revision_key=revision_key,
                    payload_ciphertext="",
                    created_at=record.created_at,
                    updated_at=record.created_at,
                    expires_at=record.expires_at,
                )
                row.payload_ciphertext = self._encrypt_payload(row.id, record)
                try:
                    async with session.begin_nested():
                        session.add(row)
                        await session.flush([row])
                except IntegrityError:
                    row = await session.scalar(
                        select(ResonanceFeedbackRow).where(
                            ResonanceFeedbackRow.guest_id == record.guest_id,
                            ResonanceFeedbackRow.daily_note_id == record.daily_note_id,
                            ResonanceFeedbackRow.revision_key == revision_key,
                        )
                    )
                    if row is None:
                        raise
            row.payload_ciphertext = self._encrypt_payload(row.id, record)
            row.created_at = record.created_at
            row.updated_at = record.created_at
            row.expires_at = record.expires_at
            await session.flush([row])
            return self._record(row)

    async def status(self, guest_id: UUID, *, now: datetime) -> ResonanceStatus:
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(ResonanceFeedbackRow).where(
                    ResonanceFeedbackRow.guest_id == guest_id,
                    ResonanceFeedbackRow.expires_at <= now,
                )
            )
            consented = bool(
                await session.scalar(
                    select(func.count())
                    .select_from(ConsentRow)
                    .where(
                        ConsentRow.guest_id == guest_id,
                        ConsentRow.purpose == RESONANCE_PURPOSE,
                        ConsentRow.version == "reading-resonance-v1",
                        ConsentRow.revoked_at.is_(None),
                    )
                )
            )
            rows = tuple(
                await session.scalars(
                    select(ResonanceFeedbackRow)
                    .where(
                        ResonanceFeedbackRow.guest_id == guest_id,
                        ResonanceFeedbackRow.expires_at > now,
                    )
                    .order_by(ResonanceFeedbackRow.created_at.desc())
                )
            )
            return ResonanceStatus(
                consented=consented,
                feedback_count=len(rows),
                last_choice=self._record(rows[0]).choice if rows else None,
            )

    async def clear_with_consent(
        self,
        guest_id: UUID,
        *,
        revoke_consent: bool,
        now: datetime,
    ) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(ResonanceFeedbackRow).where(ResonanceFeedbackRow.guest_id == guest_id)
            )
            await self._after_clear()
            if revoke_consent:
                await session.execute(
                    update(ConsentRow)
                    .where(
                        ConsentRow.guest_id == guest_id,
                        ConsentRow.purpose == RESONANCE_PURPOSE,
                    )
                    .values(revoked_at=now)
                )

    async def purge_expired(self, *, now: datetime, batch_size: int) -> int:
        async with self._sessions() as session, session.begin():
            ids = tuple(
                await session.scalars(
                    select(ResonanceFeedbackRow.id)
                    .where(ResonanceFeedbackRow.expires_at <= now)
                    .order_by(ResonanceFeedbackRow.expires_at, ResonanceFeedbackRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            if not ids:
                return 0
            result = await session.execute(
                delete(ResonanceFeedbackRow).where(ResonanceFeedbackRow.id.in_(ids))
            )
            return int(cast(CursorResult[Any], result).rowcount or 0)

    async def _require_owned_target(self, session: AsyncSession, record: ResonanceRecord) -> None:
        owner_id = await session.scalar(
            select(GuestSessionRow.id)
            .where(GuestSessionRow.id == record.guest_id)
            .with_for_update()
        )
        if owner_id is None:
            raise ResonanceTargetNotFound
        note_id = await session.scalar(
            select(DailyNoteRow.id).where(
                DailyNoteRow.id == record.daily_note_id,
                DailyNoteRow.guest_id == record.guest_id,
            )
        )
        if note_id is None:
            raise ResonanceTargetNotFound
        if record.revision_id is not None:
            revision_id = await session.scalar(
                select(ReadingRevisionRow.id).where(
                    ReadingRevisionRow.id == record.revision_id,
                    ReadingRevisionRow.guest_id == record.guest_id,
                )
            )
            if revision_id is None:
                raise ResonanceTargetNotFound

    async def _accept_consent(
        self,
        session: AsyncSession,
        *,
        guest_id: UUID,
        version: str,
        accepted_at: datetime,
    ) -> None:
        row = await session.scalar(
            select(ConsentRow).where(
                ConsentRow.guest_id == guest_id,
                ConsentRow.purpose == RESONANCE_PURPOSE,
            )
        )
        if row is None:
            row = ConsentRow(
                guest_id=guest_id,
                version=version,
                purpose=RESONANCE_PURPOSE,
                accepted_at=accepted_at,
            )
            session.add(row)
            await session.flush([row])
        row.version = version
        row.accepted_at = accepted_at
        row.revoked_at = None

    async def _after_consent(self) -> None:
        """Fault-injection seam used to prove transaction rollback."""

    async def _after_clear(self) -> None:
        """Fault-injection seam used to prove transaction rollback."""

    def _encrypt_payload(self, row_id: UUID, record: ResonanceRecord) -> str:
        payload = json.dumps(
            {
                "choice": record.choice.value,
                "background_lens": (
                    record.background_lens.value if record.background_lens else None
                ),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return self._envelope.encrypt(payload, context=_payload_context(row_id))

    def _record(self, row: ResonanceFeedbackRow) -> ResonanceRecord:
        payload = json.loads(
            self._envelope.decrypt(
                row.payload_ciphertext,
                context=_payload_context(row.id),
            )
        )
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted resonance payload")
        lens = payload.get("background_lens")
        return ResonanceRecord(
            id=row.id,
            guest_id=row.guest_id,
            daily_note_id=row.daily_note_id,
            revision_id=row.revision_id,
            choice=ResonanceChoice(payload["choice"]),
            background_lens=BackgroundLens(lens) if lens is not None else None,
            created_at=row.created_at,
            expires_at=row.expires_at,
        )


def _payload_context(record_id: UUID) -> bytes:
    return f"resonance-feedback:{record_id}".encode()
