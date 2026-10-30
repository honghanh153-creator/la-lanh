"""The bounded two-way bridge to the owner's Google Sheet (US-24 U5, plan KTD3/KTD4/KTD6/KTD7).

Export: right after admission commits, and again from the minute job until it lands, the request
is written to its own DB-assigned row, never appended. Import: a row the owner ticked is matched by
code and date, validated, and frozen once in the database. Clear: a cancelled, deleted, finished
or orphaned request's row is cleared and confirmed by reading it back.

Every Google call first takes a slot of the application budget (30 a minute, 2,000 a day,
retries included) and fails closed when none is left. Writes to one row hold that slot's lease, so
a cancel that commits while an export is in flight is cleared only after the write finished.
Nothing here logs a question, a reading, a code or a cell value; only counts and closed codes.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.postgres import account_transaction
from app.domains.guest.models import GuestState
from app.domains.guest.tables import GuestSessionRow
from app.domains.human_tarot import policy, sheet_rows
from app.domains.human_tarot.models import RequestStatus, SheetState
from app.domains.human_tarot.service import HumanTarotService
from app.domains.human_tarot.tables import (
    HumanTarotGoogleUsageRow,
    HumanTarotRequestRow,
    HumanTarotSlotRow,
    HumanTarotSyncLeaseRow,
)
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import TarotContext, TarotSpreadMap
from app.infrastructure.google_sheets.client import SheetsError, SheetsGateway

logger = logging.getLogger(__name__)

PER_MINUTE = 30
PER_DAY = 2000
SLOT_LEASE = timedelta(seconds=30)
SYNC_LEASE = timedelta(seconds=55)
MAX_BACKOFF = timedelta(minutes=15)
CLEAR_VERIFY = timedelta(minutes=15)


class BudgetExhausted(Exception):
    code = "GOOGLE_BUDGET_EXHAUSTED"


class LayoutInvalid(Exception):
    code = "SHEET_LAYOUT_INVALID"


@dataclass
class SyncReport:
    skipped: bool = False
    error: str | None = None
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount

    def line(self) -> str:
        parts = [f"{key}={value}" for key, value in sorted(self.counts.items())]
        if self.skipped:
            parts.insert(0, "skipped=lease")
        if self.error is not None:
            parts.insert(0, f"error={self.error}")
        return "human_tarot_sync " + " ".join(parts)


class GoogleBudget:
    """Durable per-minute and per-day call counters shared by every process."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Callable[[], datetime],
        *,
        per_minute: int = PER_MINUTE,
        per_day: int = PER_DAY,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._limits = {"m": per_minute, "d": per_day}

    async def reserve(self, calls: int = 1) -> None:
        now = self._clock()
        local = now.astimezone(policy.PRODUCT_TIMEZONE)
        buckets = {
            "m": (f"m:{local:%Y-%m-%dT%H:%M}", now + timedelta(minutes=2)),
            "d": (f"d:{local:%Y-%m-%d}", now + timedelta(days=2)),
        }
        async with account_transaction(self._sessions) as database:
            for kind, (bucket, expires_at) in buckets.items():
                used = await _increment(database, bucket, calls, expires_at)
                if used > self._limits[kind]:
                    raise BudgetExhausted  # rolls back both increments
            await database.execute(
                delete(HumanTarotGoogleUsageRow).where(HumanTarotGoogleUsageRow.expires_at <= now)
            )


class HumanTarotSheetBridge:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        service: HumanTarotService,
        gateway: SheetsGateway,
        *,
        budget: GoogleBudget | None = None,
    ) -> None:
        self._sessions = sessions
        self._service = service
        self._gateway = gateway
        self._budget = budget or GoogleBudget(sessions, service.now)

    # ------------------------------------------------------------------ SheetBridge protocol

    async def export_now(self, slot_id: UUID) -> None:
        await self._export(slot_id, SyncReport())

    async def clear_now(self, slot_id: UUID) -> None:
        await self._clear(slot_id, SyncReport())

    # ------------------------------------------------------------------ the minute job

    async def sync_once(self) -> SyncReport:
        report = SyncReport()
        holder = uuid4()
        if not await self._take_sync_lease(holder):
            report.skipped = True
            return report
        try:
            report.counts.update(
                {
                    f"retention_{key}": value
                    for key, value in (await self._service.finalize_and_purge()).items()
                    if value
                }
            )
            await self._pass(report)
        except (SheetsError, BudgetExhausted, LayoutInvalid) as error:
            report.error = error.code
        finally:
            await self._release_sync_lease(holder)
        logger.info(report.line())
        return report

    async def _pass(self, report: SyncReport) -> None:
        now = self._service.now()
        today = policy.local_day(now)
        async with self._sessions() as database:
            active = list(
                await database.scalars(
                    select(HumanTarotSlotRow).where(
                        or_(
                            HumanTarotSlotRow.sheet_state != SheetState.CLEARED.value,
                            # Keep looking for a while after a clear: a write that timed out on
                            # our side may still land at Google afterwards.
                            HumanTarotSlotRow.cleared_at > now - CLEAR_VERIFY,
                        )
                    )
                )
            )
        if not active:
            return  # nothing in flight: no Google call at all
        grid = await self._grid()
        rows = sheet_rows.code_rows(grid)
        # Read the known codes only after the grid: a slot always commits before its row is
        # written, so every code the grid shows is already in this set unless it is truly unknown.
        async with self._sessions() as database:
            found = await database.execute(
                select(HumanTarotSlotRow.request_code, HumanTarotSlotRow.id).where(
                    HumanTarotSlotRow.request_code.in_(list(rows))
                )
            )
            known = {code: slot_id for code, slot_id in found.tuples()}
            cleared = set(
                await database.scalars(
                    select(HumanTarotSlotRow.id).where(
                        HumanTarotSlotRow.id.in_(list(known.values())),
                        HumanTarotSlotRow.sheet_state == SheetState.CLEARED.value,
                    )
                )
            )
        for code, numbers in rows.items():
            if sheet_rows.is_app_code(code) and code not in known:
                # A well-formed app code this database does not know (for example after a
                # restore) holds a question with no purpose left.
                await self._clear_rows(numbers)
                report.add("orphan_cleared", len(numbers))
            elif code in known and known[code] in cleared:
                # Back after it was cleared (a late write): clear it again.
                await self._reopen_clear(known[code])
                report.add("reappeared")
                active.append(
                    HumanTarotSlotRow(
                        id=known[code], request_code=code, sheet_state=SheetState.CLEAR_DUE.value
                    )
                )
        for slot in active:
            if slot.sheet_state == SheetState.CLEAR_SENT.value:
                await self._confirm_clear(slot, grid, report)
        for slot in active:
            if slot.sheet_state == SheetState.CLEAR_DUE.value:
                await self._clear(slot.id, report)
        for slot in active:
            if slot.sheet_state == SheetState.PENDING_EXPORT.value and slot.day == today:
                await self._export(slot.id, report)
        for slot in active:
            if slot.sheet_state == SheetState.ON_SHEET.value and slot.day == today:
                numbers = rows.get(slot.request_code, [])
                own = sheet_rows.row_number(slot.slot_no)
                if numbers == [own]:
                    await self._import(slot, grid[own - 1], own, report)
                elif len(numbers) > 1:
                    report.add("duplicate_code")
                elif numbers:
                    # Codex r56: the code left the row the DB assigned (a sort of A:G only), so the
                    # owner columns beside it may belong to someone else. Never import from there.
                    report.add("row_moved")

    # ------------------------------------------------------------------ export

    async def _export(self, slot_id: UUID, report: SyncReport) -> None:
        token = await self._claim(slot_id, SheetState.PENDING_EXPORT)
        if token is None:
            return
        try:
            async with self._sessions() as database:
                slot = await database.get(HumanTarotSlotRow, slot_id)
                request = (
                    await database.get(HumanTarotRequestRow, slot.request_id)
                    if slot is not None and slot.request_id is not None
                    else None
                )
                owner = (
                    (
                        await database.execute(
                            select(GuestSessionRow.state, GuestSessionRow.expires_at).where(
                                GuestSessionRow.id == request.guest_id
                            )
                        )
                    ).one_or_none()
                    if request is not None
                    else None
                )
            if slot is None:
                return
            now = self._service.now()
            # Consent, owner and day are checked again right before anything leaves (KTD6).
            if (
                request is None
                or request.status != RequestStatus.ACCEPTED.value
                or request.consent_version != policy.CONSENT_VERSION
                or owner is None
                or owner.state != GuestState.ACTIVE.value
                or owner.expires_at <= now
                or request.day != policy.local_day(now)
            ):
                await self._finish(slot_id, token, SheetState.PENDING_EXPORT, SheetState.CLEAR_DUE)
                report.add("export_withdrawn")
                return
            question = self._service.decrypt(request).get("question")
            if not isinstance(question, str):
                await self._finish(slot_id, token, SheetState.PENDING_EXPORT, SheetState.CLEAR_DUE)
                return
            grid = await self._grid()
            number = sheet_rows.row_number(slot.slot_no)
            occupant = str(grid[number - 1][sheet_rows.CODE] or "").strip()
            # Codex r56: write only into a row that is empty in every column, or that already
            # carries this request's own code (a retry). Owner content left without a code may
            # be a previous person's reading and must never be bound to this request.
            if occupant != slot.request_code and not sheet_rows.row_blank(grid[number - 1]):
                await self._fail(slot_id, token, "SLOT_OCCUPIED")
                report.add("export_blocked")
                return
            cells = sheet_rows.request_cells(
                slot.request_code,
                request.day,
                TarotContext(request.context),
                question,
                TarotSpreadMap(request.spread_map),
            )
            await self._budget.reserve()
            await self._gateway.write(
                [
                    (sheet_rows.row_range(slot.slot_no, "A", "G"), [cells]),
                    (
                        sheet_rows.row_range(slot.slot_no, "P", "Q"),
                        [[sheet_rows.STATUS_WAITING, ""]],
                    ),
                ]
            )
            await self._finish(
                slot_id, token, SheetState.PENDING_EXPORT, SheetState.ON_SHEET, exported_at=now
            )
            report.add("exported")
        except (SheetsError, BudgetExhausted, LayoutInvalid) as error:
            # Ambiguous outcome (a timeout after Google applied the write) is fine: the retry
            # finds its own code in its own row and writes the same cells again (AC13).
            await self._fail(slot_id, token, error.code)
            report.add("export_failed")
            if isinstance(error, BudgetExhausted | LayoutInvalid):
                raise
        finally:
            await self._release(slot_id, token)

    # ------------------------------------------------------------------ clear

    async def _clear(self, slot_id: UUID, report: SyncReport) -> None:
        token = await self._claim(slot_id, SheetState.CLEAR_DUE)
        if token is None:
            return
        try:
            async with self._sessions() as database:
                slot = await database.get(HumanTarotSlotRow, slot_id)
            if slot is None:
                return
            grid = await self._grid()
            decision = sheet_rows.clear_decision(grid, slot.request_code, slot.slot_no)
            if decision in {"moved", "unverified"}:
                # Fail closed (Codex r56): the code sits in another row, or the assigned row now
                # belongs to another request. Nothing is cleared blindly; the owner fixes it.
                await self._fail(
                    slot_id, token, "SLOT_MOVED" if decision == "moved" else "ROW_UNVERIFIED"
                )
                report.add(f"clear_{decision}")
                return
            if decision == "clear":
                await self._clear_rows([sheet_rows.row_number(slot.slot_no)])
                grid = await self._grid()
            # Read back the whole assigned row: a missing code alone never proves deletion (R13).
            if sheet_rows.clear_decision(grid, slot.request_code, slot.slot_no) != "gone":
                await self._finish(slot_id, token, SheetState.CLEAR_DUE, SheetState.CLEAR_SENT)
                report.add("clear_unconfirmed")
            else:
                await self._finish(
                    slot_id,
                    token,
                    SheetState.CLEAR_DUE,
                    SheetState.CLEARED,
                    cleared_at=self._service.now(),
                )
                report.add("cleared")
        except (SheetsError, BudgetExhausted, LayoutInvalid) as error:
            await self._fail(slot_id, token, error.code)
            report.add("clear_failed")
            if isinstance(error, BudgetExhausted | LayoutInvalid):
                raise
        finally:
            await self._release(slot_id, token)

    async def _reopen_clear(self, slot_id: UUID) -> None:
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSlotRow)
                .where(
                    HumanTarotSlotRow.id == slot_id,
                    HumanTarotSlotRow.sheet_state == SheetState.CLEARED.value,
                )
                .values(
                    sheet_state=SheetState.CLEAR_DUE.value, cleared_at=None, next_attempt_at=None
                )
            )

    async def _confirm_clear(
        self, slot: HumanTarotSlotRow, grid: list[list[Any]], report: SyncReport
    ) -> None:
        gone = sheet_rows.clear_decision(grid, slot.request_code, slot.slot_no) == "gone"
        state = SheetState.CLEARED if gone else SheetState.CLEAR_DUE
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSlotRow)
                .where(
                    HumanTarotSlotRow.id == slot.id,
                    HumanTarotSlotRow.sheet_state == SheetState.CLEAR_SENT.value,
                )
                .values(
                    sheet_state=state.value,
                    cleared_at=self._service.now() if state is SheetState.CLEARED else None,
                )
            )
        slot.sheet_state = state.value
        report.add("clear_confirmed" if state is SheetState.CLEARED else "clear_retry")

    async def _clear_rows(self, numbers: list[int]) -> None:
        await self._budget.reserve()
        await self._gateway.clear(
            [f"'{sheet_rows.TAB}'!A{number}:{sheet_rows.LAST_COLUMN}{number}" for number in numbers]
        )

    # ------------------------------------------------------------------ import

    async def _import(
        self, slot: HumanTarotSlotRow, row: list[Any], number: int, report: SyncReport
    ) -> None:
        if not sheet_rows.is_ready(row[sheet_rows.READY]):
            return
        async with self._sessions() as database:
            request = (
                await database.get(HumanTarotRequestRow, slot.request_id)
                if slot.request_id is not None
                else None
            )
        if request is None or request.status != RequestStatus.ACCEPTED.value:
            return
        spread_map = TarotSpreadMap(request.spread_map)
        checked = sheet_rows.validate_row(row, day=request.day, spread_map=spread_map)
        if checked.errors:
            await self._feedback(slot, number, sheet_rows.STATUS_FIX, ",".join(checked.errors))
            report.add("import_rejected")
            return
        if await self._freeze(slot, request.id, checked, spread_map):
            await self._feedback(slot, number, sheet_rows.STATUS_IMPORTED, "")
            report.add("imported")

    async def _freeze(
        self,
        slot: HumanTarotSlotRow,
        request_id: UUID,
        checked: sheet_rows.Validation,
        spread_map: TarotSpreadMap,
    ) -> bool:
        """Freeze once (KTD5): only an accepted request of today whose slot is still on the Sheet.

        A cancel committed first wins; a later edit of the Sheet never replaces the frozen copy.
        """

        now = self._service.now()
        positions = TarotReadingEngine.positions_for(spread_map)
        async with account_transaction(self._sessions) as database:
            request = await database.scalar(
                select(HumanTarotRequestRow)
                .where(
                    HumanTarotRequestRow.id == request_id,
                    HumanTarotRequestRow.status == RequestStatus.ACCEPTED.value,
                    HumanTarotRequestRow.day == policy.local_day(now),
                )
                .with_for_update()
            )
            current = await database.scalar(
                select(HumanTarotSlotRow.sheet_state).where(
                    HumanTarotSlotRow.id == slot.id,
                    HumanTarotSlotRow.request_id == request_id,
                    HumanTarotSlotRow.request_code == slot.request_code,
                )
            )
            if request is None or current != SheetState.ON_SHEET.value:
                return False
            payload = self._service.decrypt(request)
            payload["result"] = {
                "schema": policy.RESULT_SCHEMA,
                "reader": policy.READER,
                "cards": [
                    {"position_key": key, "card_id": card}
                    for (key, _), card in zip(positions, checked.cards, strict=True)
                ],
                "reading": checked.reading,
                "step": checked.step,
                "imported_at": now.astimezone(UTC).isoformat(),
            }
            request.payload_ciphertext = self._service.encrypt(request.id, payload)
            request.status = RequestStatus.READY.value
            request.imported_at = now
            request.updated_at = now
        return True

    async def _feedback(
        self, slot: HumanTarotSlotRow, number: int, status: str, codes: str
    ) -> None:
        digest = hashlib.sha256(f"{status}|{codes}".encode()).hexdigest()
        if slot.feedback_digest == digest:
            return
        try:
            await self._budget.reserve()
            await self._gateway.write(
                [(f"'{sheet_rows.TAB}'!P{number}:Q{number}", [[status, codes]])]
            )
        except (SheetsError, BudgetExhausted):
            return  # feedback is advisory; the import state lives in the database
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSlotRow)
                .where(HumanTarotSlotRow.id == slot.id)
                .values(feedback_digest=digest)
            )
        slot.feedback_digest = digest

    # ------------------------------------------------------------------ shared

    async def _grid(self) -> list[list[Any]]:
        await self._budget.reserve()
        grid = sheet_rows.padded(await self._gateway.read(sheet_rows.GRID))
        if not sheet_rows.header_ok(grid):
            raise LayoutInvalid
        return grid

    async def _claim(self, slot_id: UUID, state: SheetState) -> UUID | None:
        now = self._service.now()
        token = uuid4()
        async with account_transaction(self._sessions) as database:
            result = await database.execute(
                update(HumanTarotSlotRow)
                .where(
                    HumanTarotSlotRow.id == slot_id,
                    HumanTarotSlotRow.sheet_state == state.value,
                    or_(
                        HumanTarotSlotRow.lease_until.is_(None),
                        HumanTarotSlotRow.lease_until <= now,
                    ),
                    or_(
                        HumanTarotSlotRow.next_attempt_at.is_(None),
                        HumanTarotSlotRow.next_attempt_at <= now,
                    ),
                )
                .values(lease_token=token, lease_until=now + SLOT_LEASE)
            )
        return token if _rowcount(result) == 1 else None

    async def _finish(
        self,
        slot_id: UUID,
        token: UUID,
        expected: SheetState,
        state: SheetState,
        **values: Any,
    ) -> None:
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSlotRow)
                .where(
                    HumanTarotSlotRow.id == slot_id,
                    HumanTarotSlotRow.lease_token == token,
                    # A cancel that committed meanwhile moved the state on: keep its decision.
                    HumanTarotSlotRow.sheet_state == expected.value,
                )
                .values(
                    sheet_state=state.value,
                    sheet_error=None,
                    attempts=0,
                    next_attempt_at=None,
                    **values,
                )
            )

    async def _fail(self, slot_id: UUID, token: UUID, code: str) -> None:
        now = self._service.now()
        async with account_transaction(self._sessions) as database:
            slot = await database.scalar(
                select(HumanTarotSlotRow).where(
                    HumanTarotSlotRow.id == slot_id, HumanTarotSlotRow.lease_token == token
                )
            )
            if slot is None:
                return
            slot.attempts += 1
            slot.sheet_error = code
            # Bounded before building the duration: 2**attempts overflows after a long outage.
            delay = MAX_BACKOFF if slot.attempts >= 4 else timedelta(minutes=2**slot.attempts)
            slot.next_attempt_at = now + min(delay, MAX_BACKOFF)
        logger.warning("human_tarot_sheet_error code=%s", code)

    async def _release(self, slot_id: UUID, token: UUID) -> None:
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSlotRow)
                .where(HumanTarotSlotRow.id == slot_id, HumanTarotSlotRow.lease_token == token)
                .values(lease_token=None, lease_until=None)
            )

    async def _take_sync_lease(self, holder: UUID) -> bool:
        now = self._service.now()
        async with account_transaction(self._sessions) as database:
            await _insert_ignore(
                database,
                HumanTarotSyncLeaseRow,
                {"name": "sync", "holder": None, "lease_until": now},
            )
            result = await database.execute(
                update(HumanTarotSyncLeaseRow)
                .where(
                    HumanTarotSyncLeaseRow.name == "sync",
                    HumanTarotSyncLeaseRow.lease_until <= now,
                )
                .values(holder=holder, lease_until=now + SYNC_LEASE)
            )
        return _rowcount(result) == 1

    async def _release_sync_lease(self, holder: UUID) -> None:
        async with account_transaction(self._sessions) as database:
            await database.execute(
                update(HumanTarotSyncLeaseRow)
                .where(
                    HumanTarotSyncLeaseRow.name == "sync", HumanTarotSyncLeaseRow.holder == holder
                )
                .values(holder=None, lease_until=self._service.now())
            )


async def _increment(database: AsyncSession, bucket: str, calls: int, expires_at: datetime) -> int:
    dialect = database.get_bind().dialect.name
    insert = postgresql_insert if dialect == "postgresql" else sqlite_insert
    statement = (
        insert(HumanTarotGoogleUsageRow)
        .values(bucket=bucket, used=calls, expires_at=expires_at)
        .on_conflict_do_update(
            index_elements=[HumanTarotGoogleUsageRow.bucket],
            set_={"used": HumanTarotGoogleUsageRow.used + calls},
        )
        .returning(HumanTarotGoogleUsageRow.used)
    )
    return int((await database.execute(statement)).scalar_one())


async def _insert_ignore(database: AsyncSession, model: Any, values: dict[str, Any]) -> None:
    dialect = database.get_bind().dialect.name
    insert = postgresql_insert if dialect == "postgresql" else sqlite_insert
    await database.execute(insert(model).values(**values).on_conflict_do_nothing())


def _rowcount(result: object) -> int:
    return int(cast(CursorResult[Any], result).rowcount or 0)
