"""Saved month answers: explicit save, own list, delete (AK2, US-25 AC12).

Only the composed answer is stored (topic label, the three parts, the basis, the disclaimer and
the reframe line if any), encrypted with the row id as context. No typed text, no date window.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.postgres import account_transaction, lock_owner
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.month_answer.answer import MonthAnswer
from app.domains.month_answer.tables import SavedMonthAnswerRow
from app.infrastructure.crypto import EnvelopeCipher

# A person keeps a handful of these; the cap only stops a scripted flood of rows.
MAX_SAVED_PER_GUEST = 200


class SavedMonthAnswerLimit(Exception):
    """This guest already keeps the maximum number of saved month answers."""


@dataclass(frozen=True, slots=True)
class SavedMonthAnswer:
    id: UUID
    month: str
    topic: str
    content: dict[str, object]
    saved_at: datetime


def _context(row_id: UUID) -> bytes:
    return f"saved-month-answer:{row_id}".encode()


def snapshot_of(answer: MonthAnswer) -> dict[str, object]:
    return {
        "month": answer.month,
        "topic": answer.topic.value,
        "topic_label": answer.topic_label,
        "reframe": answer.reframe,
        "theme": answer.theme,
        "act": answer.act,
        "say": answer.say,
        "basis": {"line": answer.basis.line, "detail": answer.basis.detail},
        "disclaimer": answer.disclaimer,
    }


def decrypt_saved(row: SavedMonthAnswerRow, envelope: EnvelopeCipher) -> SavedMonthAnswer:
    payload: object = json.loads(
        envelope.decrypt(row.snapshot_ciphertext, context=_context(row.id))
    )
    if not isinstance(payload, dict):
        raise ValueError("invalid saved month answer")
    return SavedMonthAnswer(
        id=row.id,
        month=row.month,
        topic=row.topic,
        content=cast(dict[str, object], payload),
        saved_at=row.saved_at,
    )


class PostgresSavedMonthAnswers:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._erasure_journal = erasure_journal

    async def save(self, guest_id: UUID, answer: MonthAnswer) -> SavedMonthAnswer:
        """Idempotent per (guest, answer): saving the same answer twice keeps one row."""

        async with account_transaction(self._sessions) as session:
            await lock_owner(session, guest_id)
            existing = await session.scalar(
                select(SavedMonthAnswerRow).where(
                    SavedMonthAnswerRow.guest_id == guest_id,
                    SavedMonthAnswerRow.answer_key == answer.answer_key,
                )
            )
            if existing is not None:
                return decrypt_saved(existing, self._envelope)
            kept = await session.scalars(
                select(SavedMonthAnswerRow.id).where(SavedMonthAnswerRow.guest_id == guest_id)
            )
            if len(list(kept)) >= MAX_SAVED_PER_GUEST:
                raise SavedMonthAnswerLimit
            row_id = uuid4()
            payload = json.dumps(
                snapshot_of(answer), ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode()
            row = SavedMonthAnswerRow(
                id=row_id,
                guest_id=guest_id,
                answer_key=answer.answer_key,
                month=answer.month,
                topic=answer.topic.value,
                snapshot_ciphertext=self._envelope.encrypt(payload, context=_context(row_id)),
                saved_at=datetime.now(UTC),
            )
            session.add(row)
            await session.flush()
            return decrypt_saved(row, self._envelope)

    async def list_for_guest(self, guest_id: UUID) -> tuple[SavedMonthAnswer, ...]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(SavedMonthAnswerRow)
                .where(SavedMonthAnswerRow.guest_id == guest_id)
                .order_by(SavedMonthAnswerRow.saved_at.desc(), SavedMonthAnswerRow.id)
            )
            return tuple(decrypt_saved(row, self._envelope) for row in rows)

    async def delete(self, guest_id: UUID, saved_id: UUID) -> bool:
        async with self._sessions() as session, session.begin():
            removed = tuple(
                await session.scalars(
                    delete(SavedMonthAnswerRow)
                    .where(
                        SavedMonthAnswerRow.guest_id == guest_id,
                        SavedMonthAnswerRow.id == saved_id,
                    )
                    .returning(SavedMonthAnswerRow.id)
                )
            )
            if self._erasure_journal is not None:
                at = datetime.now(UTC)
                for row_id in removed:
                    self._erasure_journal.record(
                        session, ErasureKind.SAVED_MONTH_ANSWER_REMOVED, row_id, at
                    )
            return bool(removed)
