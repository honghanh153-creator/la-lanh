"""Human Tarot requests (US-24): admission, private reads, cancel and retention.

The database decides everything that matters for the person: the daily cap, who may read, when a
reading opens and what was erased. The owner's Google Sheet (see ``sheets``) is only where the
owner reads questions and writes readings; nothing read from it can grant access.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from hashlib import sha256
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.postgres import account_transaction, lock_owner
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.human_tarot import policy
from app.domains.human_tarot.errors import (
    HumanTarotAlreadyRequested,
    HumanTarotClosed,
    HumanTarotConflict,
    HumanTarotConsentRequired,
    HumanTarotDisabled,
    HumanTarotFull,
    HumanTarotKeyInvalid,
    HumanTarotNotFound,
)
from app.domains.human_tarot.models import (
    AvailabilityReason,
    HumanTarotAvailability,
    HumanTarotCardPosition,
    HumanTarotRequestView,
    HumanTarotResult,
    RequestStatus,
    SheetState,
    VisibleStatus,
)
from app.domains.human_tarot.tables import (
    HumanTarotDayRow,
    HumanTarotRequestRow,
    HumanTarotSlotRow,
)
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.errors import TarotQuestionRejected
from app.domains.tarot.knowledge import card_by_id
from app.domains.tarot.models import TarotContext, TarotSpread, TarotSpreadMap
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22,200}$")
logger = logging.getLogger(__name__)


class SheetBridge(Protocol):
    """Best-effort immediate Sheet work after a commit (US-24 R7). Failures stay in the DB."""

    async def export_now(self, slot_id: UUID) -> None: ...

    async def clear_now(self, slot_id: UUID) -> None: ...


def payload_context(request_id: UUID) -> bytes:
    return f"human-tarot-request:{request_id}".encode()


class HumanTarotService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        hasher: SecretHasher,
        *,
        enabled: bool = False,
        intake_closes_at: time = policy.RELEASE_TIME,
        engine: TarotReadingEngine | None = None,
        erasure_journal: ErasureJournal | None = None,
        bridge: SheetBridge | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if intake_closes_at > policy.RELEASE_TIME:
            raise ValueError("intake must close no later than the 10:00 release")
        self._sessions = sessions
        self._envelope = envelope
        self._hasher = hasher
        self._enabled = enabled
        self._intake_closes_at = intake_closes_at
        self._engine = engine or TarotReadingEngine()
        self._erasure_journal = erasure_journal
        self.bridge = bridge
        self._clock = clock or (lambda: datetime.now(UTC))

    def now(self) -> datetime:
        return self._clock()

    def closes_at(self, day: date) -> datetime:
        return policy.local_at(day, self._intake_closes_at)

    # ------------------------------------------------------------------ reads

    async def availability(self, guest_id: UUID) -> HumanTarotAvailability:
        now = self.now()
        day = policy.local_day(now)
        async with self._sessions() as database:
            day_row = await database.get(HumanTarotDayRow, day)
            mine = (
                await database.execute(
                    select(HumanTarotSlotRow.id, HumanTarotSlotRow.request_id).where(
                        HumanTarotSlotRow.day == day, HumanTarotSlotRow.guest_id == guest_id
                    )
                )
            ).one_or_none()
        accepted = day_row.accepted_count if day_row is not None else 0
        remaining = max(policy.DAILY_LIMIT - accepted, 0)
        if not self._enabled:
            reason = AvailabilityReason.DISABLED
        elif mine is not None:
            reason = AvailabilityReason.ALREADY_REQUESTED
        elif (day_row is not None and day_row.intake_closed) or now >= self.closes_at(day):
            reason = AvailabilityReason.CLOSED
        elif remaining == 0:
            reason = AvailabilityReason.FULL
        else:
            reason = AvailabilityReason.OPEN
        return HumanTarotAvailability(
            enabled=self._enabled,
            accepting=reason is AvailabilityReason.OPEN,
            reason=reason,
            local_date=day,
            closes_at=self.closes_at(day),
            release_at=policy.release_at(day),
            daily_limit=policy.DAILY_LIMIT,
            remaining=remaining,
            consent_version=policy.CONSENT_VERSION,
            current_request_id=mine.request_id if mine is not None else None,
        )

    async def get(self, guest_id: UUID, request_id: UUID) -> HumanTarotRequestView:
        now = self.now()
        async with self._sessions() as database:
            row = await database.scalar(
                select(HumanTarotRequestRow).where(
                    HumanTarotRequestRow.id == request_id,
                    HumanTarotRequestRow.guest_id == guest_id,
                    HumanTarotRequestRow.expires_at > now,
                )
            )
            if row is None:
                raise HumanTarotNotFound
            slot = await _slot_of(database, row.id)
        return self._view(row, slot, now)

    async def current(self, guest_id: UUID) -> HumanTarotRequestView:
        now = self.now()
        async with self._sessions() as database:
            row = await database.scalar(
                select(HumanTarotRequestRow)
                .where(
                    HumanTarotRequestRow.guest_id == guest_id,
                    HumanTarotRequestRow.expires_at > now,
                )
                .order_by(HumanTarotRequestRow.created_at.desc(), HumanTarotRequestRow.id)
                .limit(1)
            )
            if row is None:
                raise HumanTarotNotFound
            slot = await _slot_of(database, row.id)
        return self._view(row, slot, now)

    # ------------------------------------------------------------------ admission

    async def create(
        self,
        *,
        guest_id: UUID,
        context: TarotContext,
        question: str,
        spread: TarotSpread,
        consent_version: str,
        idempotency_key: str,
    ) -> HumanTarotRequestView:
        if not self._enabled:
            raise HumanTarotDisabled
        if consent_version != policy.CONSENT_VERSION:
            raise HumanTarotConsentRequired
        if not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
            raise HumanTarotKeyInvalid
        assessment = self._engine.assess_question(question, context)
        if not assessment.accepted or assessment.intent is None:
            raise TarotQuestionRejected(assessment)
        normalized = assessment.normalized_question
        spread_map = self._engine.choose_spread_map(spread, assessment.intent, normalized)
        idempotency_hash = self._hasher.digest("human-tarot-create", idempotency_key)
        request_hash = sha256(
            "\x00".join((context.value, normalized, spread.value, consent_version)).encode()
        ).hexdigest()

        # A retry of an accepted request answers with its receipt, even after the cut-off.
        replay = await self._replay(guest_id, idempotency_hash, request_hash)
        if replay is not None:
            return replay

        slot_id: UUID | None = None
        request_id: UUID | None = None
        async with account_transaction(self._sessions) as database:
            # Lock order (plan KTD2): the day row, then the guest row. No other path locks both.
            day_row = await _lock_day(database, policy.local_day(self.now()), self.now())
            await lock_owner(database, guest_id)
            # The clock is read again after waiting for the locks.
            now = self.now()
            existing = await database.scalar(
                select(HumanTarotRequestRow).where(
                    HumanTarotRequestRow.guest_id == guest_id,
                    HumanTarotRequestRow.idempotency_hash == idempotency_hash,
                )
            )
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise HumanTarotConflict
                request_id = existing.id
            else:
                day = day_row.day
                if (
                    policy.local_day(now) != day
                    or day_row.intake_closed
                    or now >= self.closes_at(day)
                ):
                    raise HumanTarotClosed
                taken = await database.scalar(
                    select(HumanTarotSlotRow.id).where(
                        HumanTarotSlotRow.day == day, HumanTarotSlotRow.guest_id == guest_id
                    )
                )
                if taken is not None:
                    raise HumanTarotAlreadyRequested
                if day_row.accepted_count >= policy.DAILY_LIMIT:
                    raise HumanTarotFull
                day_row.accepted_count += 1
                request_id = uuid4()
                release = policy.release_at(day)
                row = HumanTarotRequestRow(
                    id=request_id,
                    guest_id=guest_id,
                    day=day,
                    idempotency_hash=idempotency_hash,
                    request_hash=request_hash,
                    status=RequestStatus.ACCEPTED.value,
                    context=context.value,
                    spread=spread.value,
                    spread_map=spread_map.value,
                    consent_version=consent_version,
                    consented_at=now,
                    payload_ciphertext=self._encrypt(request_id, {"question": normalized}),
                    release_at=release,
                    expires_at=release + policy.RESULT_KEPT_AFTER_RELEASE,
                    created_at=now,
                    updated_at=now,
                )
                database.add(row)
                await database.flush([row])
                slot = HumanTarotSlotRow(
                    id=uuid4(),
                    day=day,
                    slot_no=day_row.accepted_count,
                    request_code=await _unused_code(database),
                    guest_id=guest_id,
                    request_id=request_id,
                    sheet_state=SheetState.PENDING_EXPORT.value,
                    attempts=0,
                    created_at=now,
                )
                database.add(slot)
                await database.flush([day_row, slot])
                slot_id = slot.id
        if slot_id is not None and self.bridge is not None:
            await self._best_effort(self.bridge.export_now, slot_id, "export")
        return await self.get(guest_id, request_id)

    async def _replay(
        self, guest_id: UUID, idempotency_hash: bytes, request_hash: str
    ) -> HumanTarotRequestView | None:
        async with self._sessions() as database:
            found = (
                await database.execute(
                    select(HumanTarotRequestRow.id, HumanTarotRequestRow.request_hash).where(
                        HumanTarotRequestRow.guest_id == guest_id,
                        HumanTarotRequestRow.idempotency_hash == idempotency_hash,
                    )
                )
            ).one_or_none()
        if found is None:
            return None
        if found.request_hash != request_hash:
            raise HumanTarotConflict
        return await self.get(guest_id, found.id)

    # ------------------------------------------------------------------ erasure

    async def cancel(self, guest_id: UUID, request_id: UUID) -> None:
        """Cancel a waiting request or delete a reading (R13). Reads and imports stop at commit."""

        slot_id: UUID | None = None
        async with account_transaction(self._sessions) as database:
            await lock_owner(database, guest_id)
            now = self.now()
            row = await database.scalar(
                select(HumanTarotRequestRow)
                .where(
                    HumanTarotRequestRow.id == request_id,
                    HumanTarotRequestRow.guest_id == guest_id,
                )
                .with_for_update()
            )
            if row is None:
                raise HumanTarotNotFound
            if row.status != RequestStatus.CANCELLED.value:
                tombstone(row, now)
                if self._erasure_journal is not None:
                    self._erasure_journal.record(
                        database, ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED, row.id, now
                    )
            slot = await _slot_of(database, row.id)
            if slot is not None and schedule_clear(slot):
                slot_id = slot.id
        if slot_id is not None and self.bridge is not None:
            await self._best_effort(self.bridge.clear_now, slot_id, "clear")

    async def close_intake(self, day: date) -> None:
        """Stop intake for ``day`` (after a restore, plan "cost"); the count is never reopened."""

        async with account_transaction(self._sessions) as database:
            row = await _lock_day(database, day, self.now())
            row.intake_closed = True

    async def finalize_and_purge(self, *, batch_size: int = 500) -> dict[str, int]:
        """Day end, question retention and expiry (US-24 OD2 proposal). Idempotent."""

        now = self.now()
        today = policy.local_day(now)
        counts: dict[str, int] = {}
        async with account_transaction(self._sessions) as database:
            # The day ended without an imported reading: no result, the question goes now.
            ended = await database.execute(
                update(HumanTarotRequestRow)
                .where(
                    HumanTarotRequestRow.status == RequestStatus.ACCEPTED.value,
                    HumanTarotRequestRow.day < today,
                )
                .values(
                    status=RequestStatus.UNFULFILLED.value,
                    payload_ciphertext=None,
                    question_purged_at=now,
                    updated_at=now,
                    expires_at=policy.day_end(today) + policy.TOMBSTONE_KEPT,
                )
            )
            counts["unfulfilled"] = _rowcount(ended)
            # A past day's rows, and rows whose request is gone, leave the Sheet.
            due = await database.execute(
                update(HumanTarotSlotRow)
                .where(
                    HumanTarotSlotRow.sheet_state.in_(
                        (SheetState.PENDING_EXPORT.value, SheetState.ON_SHEET.value)
                    ),
                    or_(HumanTarotSlotRow.day < today, HumanTarotSlotRow.request_id.is_(None)),
                )
                .values(
                    sheet_state=SheetState.CLEAR_DUE.value,
                    sheet_error=None,
                    attempts=0,
                    next_attempt_at=None,
                )
            )
            counts["clear_due"] = _rowcount(due)
            expired = await database.execute(
                delete(HumanTarotRequestRow).where(
                    HumanTarotRequestRow.id.in_(
                        select(HumanTarotRequestRow.id)
                        .where(HumanTarotRequestRow.expires_at <= now)
                        .limit(batch_size)
                    )
                )
            )
            counts["expired"] = _rowcount(expired)
            slots = await database.execute(
                delete(HumanTarotSlotRow).where(
                    HumanTarotSlotRow.sheet_state == SheetState.CLEARED.value,
                    HumanTarotSlotRow.day < today - timedelta(days=policy.SLOT_KEPT_AFTER_DAY.days),
                )
            )
            counts["slots_purged"] = _rowcount(slots)
            days = await database.execute(
                delete(HumanTarotDayRow).where(
                    HumanTarotDayRow.day < today - timedelta(days=policy.DAY_TALLY_KEPT.days),
                    ~select(HumanTarotSlotRow.id)
                    .where(HumanTarotSlotRow.day == HumanTarotDayRow.day)
                    .exists(),
                )
            )
            counts["days_purged"] = _rowcount(days)
        counts["questions_purged"] = await self._purge_questions(now, batch_size)
        return counts

    async def _purge_questions(self, now: datetime, batch_size: int) -> int:
        purged = 0
        async with account_transaction(self._sessions) as database:
            rows = (
                await database.scalars(
                    select(HumanTarotRequestRow)
                    .where(
                        HumanTarotRequestRow.status == RequestStatus.READY.value,
                        HumanTarotRequestRow.question_purged_at.is_(None),
                        HumanTarotRequestRow.release_at <= now - policy.QUESTION_KEPT_AFTER_RELEASE,
                    )
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            ).all()
            for row in rows:
                payload = self.decrypt(row)
                payload.pop("question", None)
                row.payload_ciphertext = self._encrypt(row.id, payload)
                row.question_purged_at = now
                row.updated_at = now
                purged += 1
        return purged

    # ------------------------------------------------------------------ helpers

    async def _best_effort(self, action: Callable[[UUID], Any], slot_id: UUID, name: str) -> None:
        try:
            await action(slot_id)
        except Exception as error:  # the durable state retries it
            logger.warning("human_tarot_%s_deferred error=%s", name, type(error).__name__)

    def _view(
        self, row: HumanTarotRequestRow, slot: HumanTarotSlotRow | None, now: datetime
    ) -> HumanTarotRequestView:
        status = _visible_status(row, now)
        payload = self.decrypt(row) if row.payload_ciphertext is not None else {}
        question = payload.get("question") if status in _QUESTION_VISIBLE else None
        if now >= row.release_at + policy.QUESTION_KEPT_AFTER_RELEASE:
            question = None
        result = None
        if status is VisibleStatus.READY:
            result = _result(payload.get("result"), TarotSpreadMap(row.spread_map))
        delivery = None
        if status in {VisibleStatus.WAITING, VisibleStatus.LATE} and slot is not None:
            delivery = _delivery(slot)
        copy_cleared = None
        if status is VisibleStatus.CANCELLED:
            copy_cleared = slot is None or slot.sheet_state == SheetState.CLEARED.value
        return HumanTarotRequestView(
            id=row.id,
            status=status,
            delivery=delivery,
            copy_cleared=copy_cleared,
            local_date=row.day,
            release_at=row.release_at,
            context=TarotContext(row.context),
            spread=TarotSpread(row.spread),
            question=question if isinstance(question, str) else None,
            result=result,
            expires_at=row.expires_at,
        )

    def _encrypt(self, request_id: UUID, payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
        return self._envelope.encrypt(encoded, context=payload_context(request_id))

    def encrypt(self, request_id: UUID, payload: dict[str, Any]) -> str:
        return self._encrypt(request_id, payload)

    def decrypt(self, row: HumanTarotRequestRow) -> dict[str, Any]:
        if row.payload_ciphertext is None:
            return {}
        payload = json.loads(
            self._envelope.decrypt(row.payload_ciphertext, context=payload_context(row.id))
        )
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted human Tarot payload")
        return cast(dict[str, Any], payload)


_QUESTION_VISIBLE = frozenset({VisibleStatus.WAITING, VisibleStatus.LATE, VisibleStatus.READY})


def _visible_status(row: HumanTarotRequestRow, now: datetime) -> VisibleStatus:
    if row.status == RequestStatus.CANCELLED.value:
        return VisibleStatus.CANCELLED
    if row.status == RequestStatus.UNFULFILLED.value:
        return VisibleStatus.UNFULFILLED
    if now < row.release_at:
        return VisibleStatus.WAITING
    if row.status == RequestStatus.READY.value:
        return VisibleStatus.READY
    if now >= policy.day_end(row.day):
        return VisibleStatus.UNFULFILLED  # the day-end job has not run yet
    return VisibleStatus.LATE


def _delivery(slot: HumanTarotSlotRow) -> str | None:
    if slot.sheet_state == SheetState.ON_SHEET.value:
        return "delivered"
    if slot.sheet_state == SheetState.PENDING_EXPORT.value:
        return "error" if slot.sheet_error is not None else "pending"
    return None


def _result(raw: object, spread_map: TarotSpreadMap) -> HumanTarotResult | None:
    if not isinstance(raw, dict):
        return None
    positions = dict(TarotReadingEngine.positions_for(spread_map))
    cards = tuple(
        HumanTarotCardPosition(
            position_key=item["position_key"],
            position_label=positions[item["position_key"]],
            card=card_by_id(item["card_id"]),
        )
        for item in raw["cards"]
    )
    return HumanTarotResult(
        cards=cards,
        reading=raw["reading"],
        step=raw["step"],
        imported_at=datetime.fromisoformat(raw["imported_at"]),
    )


def tombstone(row: HumanTarotRequestRow, now: datetime) -> None:
    row.status = RequestStatus.CANCELLED.value
    row.payload_ciphertext = None
    row.cancelled_at = now
    row.updated_at = now
    row.expires_at = now + policy.TOMBSTONE_KEPT


def schedule_clear(slot: HumanTarotSlotRow) -> bool:
    """Ask the bridge to clear the Sheet row and confirm it by reading it back."""

    if slot.sheet_state == SheetState.CLEARED.value:
        return False
    slot.sheet_state = SheetState.CLEAR_DUE.value
    slot.sheet_error = None
    slot.attempts = 0
    slot.next_attempt_at = None
    return True


async def _slot_of(database: AsyncSession, request_id: UUID) -> HumanTarotSlotRow | None:
    return cast(
        HumanTarotSlotRow | None,
        await database.scalar(
            select(HumanTarotSlotRow).where(HumanTarotSlotRow.request_id == request_id)
        ),
    )


async def _lock_day(database: AsyncSession, day: date, now: datetime) -> HumanTarotDayRow:
    dialect = database.get_bind().dialect.name
    if dialect == "postgresql":
        insert = postgresql_insert(HumanTarotDayRow)
    elif dialect == "sqlite":
        insert = sqlite_insert(HumanTarotDayRow)  # type: ignore[assignment]
    else:  # pragma: no cover - supported runtime databases are PostgreSQL and SQLite.
        raise RuntimeError(f"unsupported database dialect {dialect}")
    await database.execute(
        insert.values(
            day=day, accepted_count=0, intake_closed=False, created_at=now
        ).on_conflict_do_nothing(index_elements=[HumanTarotDayRow.day])
    )
    row = await database.scalar(
        select(HumanTarotDayRow)
        .where(HumanTarotDayRow.day == day)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:  # pragma: no cover - inserted above in this transaction
        raise RuntimeError("human Tarot day row missing")
    return row


async def _unused_code(database: AsyncSession) -> str:
    for _ in range(8):
        code = policy.new_request_code()
        taken = await database.scalar(
            select(HumanTarotSlotRow.id).where(HumanTarotSlotRow.request_code == code)
        )
        if taken is None:
            return code
    raise RuntimeError("could not allocate a request code")  # pragma: no cover


def _rowcount(result: object) -> int:
    return int(cast(CursorResult[Any], result).rowcount or 0)
