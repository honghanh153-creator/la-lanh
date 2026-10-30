"""US-24 U5: the two-way Sheet bridge against an in-memory Sheet (no Google, synthetic data)."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import delete

from app.db.session import Database
from app.domains.guest.tables import GuestSessionRow
from app.domains.human_tarot import sheet_rows
from app.domains.human_tarot.models import VisibleStatus
from app.domains.human_tarot.sheets import GoogleBudget, HumanTarotSheetBridge
from app.infrastructure.google_sheets.client import (
    SheetsAccessDenied,
    SheetsError,
    SheetsRateLimited,
    SheetsUnavailable,
)
from tests.human_tarot import support
from tests.human_tarot.fake_sheet import FakeSheet
from tests.human_tarot.support import DAY, QUESTION, Clock, vn

TAB = sheet_rows.TAB
LONG = "Bài đọc này đủ dài để không bị báo là quá ngắn."


def _sheet() -> FakeSheet:
    sheet = FakeSheet()
    sheet.set_row(TAB, 1, list(sheet_rows.HEADER))
    return sheet


def _wire(
    database: Database, clock: Clock, sheet: FakeSheet, **budget: int
) -> tuple[Any, HumanTarotSheetBridge]:
    tarot = support.service(database, clock)
    bridge = HumanTarotSheetBridge(
        database.sessions, tarot, sheet, budget=GoogleBudget(database.sessions, clock, **budget)
    )
    tarot.bridge = bridge
    return tarot, bridge


def _owner_writes(sheet: FakeSheet, row: int, **overrides: Any) -> None:
    values: dict[str, Any] = {
        "cards": ["Ngôi Sao", "Năm Cốc", "Át Gậy"],
        "reading": "Bài đọc tổng hợp cho kiểm thử: điều đã rõ là bạn cần nghỉ một nhịp "
        "trước khi nhận.",
        "step": "Viết ra ba việc đang ôm.",
        "ready": True,
    } | overrides
    chosen: list[str] = values["cards"]
    cards = [*chosen, *[""] * (5 - len(chosen))]
    sheet.set_row(TAB, row, [*cards, values["reading"], values["step"], values["ready"]], "H")


def _titles() -> dict[str, str]:
    from app.domains.tarot.knowledge import card_by_id

    return {card: card_by_id(card).title_vi for card in ("major-star", "cups-5", "wands-ace")}


async def test_export_writes_the_assigned_row_as_text(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, _ = _wire(database, clock, sheet)
    guest = await support.guest(database)
    formula_like = '=IMPORTXML("x") mình có nên nhận việc này không?'
    view = await support.create(tarot, guest, question=formula_like)
    assert view.delivery == "delivered"
    (slot,) = await support.slots(database)
    row = sheet.grid(TAB)[1]
    assert row[0] == slot.request_code and row[1] == "30/10/2026" and row[2] == "10:00"
    assert row[3] == "Công việc" and row[4] == formula_like and row[5] == "3"
    assert row[6] == "1. Điều đã rõ · 2. Điều dễ bỏ sót · 3. Một bước nhỏ có thể thử"
    assert row[15] == sheet_rows.STATUS_WAITING
    assert all(cell == "" for cell in row[7:15])
    # Nothing identifying beyond the request itself (AC23).
    assert str(guest) not in str(sheet.grid(TAB)) and str(view.id) not in str(sheet.grid(TAB))


async def test_ready_row_is_validated_frozen_and_opens_at_ten(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    titles = _titles()
    _owner_writes(sheet, 2, cards=[titles["major-star"], titles["cups-5"], titles["wands-ace"]])
    clock.moment = vn(DAY, 9)
    report = await bridge.sync_once()
    assert report.counts.get("imported") == 1, report.line()
    assert sheet.cell(TAB, "P2") == sheet_rows.STATUS_IMPORTED
    assert (await tarot.get(guest, view.id)).result is None  # still before 10:00
    # A later edit of the Sheet never replaces the frozen reading (AC16).
    sheet.set_row(TAB, 2, ["Một bài khác hẳn, viết lại sau khi app đã nhận bài đọc rồi."], "M")
    await bridge.sync_once()
    clock.moment = vn(DAY, 10)
    opened = await tarot.get(guest, view.id)
    assert opened.status is VisibleStatus.READY and opened.result is not None
    assert opened.result.reading.startswith("Bài đọc tổng hợp")
    assert [item.card.id for item in opened.result.cards] == ["major-star", "cups-5", "wands-ace"]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"cards": ["Ngôi Sao", "Năm Cốc"]}, "SO_LA_SAI"),
        ({"cards": ["Ngôi Sao", "Năm Cốc", "Át Gậy", "Mặt Trời"]}, "SO_LA_SAI"),
        ({"cards": ["Ngôi Sao", "Lá Bịa", "Át Gậy"]}, "LA_2_KHONG_CO"),
        ({"cards": ["Ngôi Sao", "Ngôi Sao", "Át Gậy"]}, "LA_TRUNG"),
        ({"reading": "Ngắn quá."}, "BAI_DOC_QUA_NGAN"),
        ({"step": "x" * 300}, "BUOC_NHO_QUA_DAI"),
        (
            {"reading": '=HYPERLINK("https://example.com") bài đọc đủ dài để không bị báo ngắn.'},
            "CO_LINK_HOAC_CONG_THUC",
        ),
        (
            {"reading": "Xem thêm ở www.example.com nhé, bài đọc này đủ dài để qua giới hạn."},
            "CO_LINK_HOAC_CONG_THUC",
        ),
        (
            {"reading": "Chắc chắn người kia đang nhớ bạn, bài đọc này đủ dài để qua giới hạn."},
            "CAU_KHANG_DINH_KHONG_AN_TOAN",
        ),
    ],
)
async def test_invalid_ready_rows_are_not_imported_and_get_a_code(
    database: Database, overrides: dict[str, Any], code: str
) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    titles = _titles()
    defaults = {"cards": [titles["major-star"], titles["cups-5"], titles["wands-ace"]]}
    _owner_writes(sheet, 2, **(defaults | overrides))
    report = await bridge.sync_once()
    assert report.counts.get("import_rejected") == 1
    assert sheet.cell(TAB, "P2") == sheet_rows.STATUS_FIX
    assert code in str(sheet.cell(TAB, "Q2")).split(",")
    assert "nhận" not in str(sheet.cell(TAB, "Q2"))  # codes only, never content
    row = await support.request_row(database, view.id)
    assert row is not None and row.status == "accepted"
    writes = sheet.calls.count("write")
    await bridge.sync_once()
    assert sheet.calls.count("write") == writes  # the same feedback is not rewritten


async def test_unticked_rows_are_left_alone(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    view = await support.create(tarot, await support.guest(database))
    _owner_writes(sheet, 2, ready=False)
    await bridge.sync_once()
    row = await support.request_row(database, view.id)
    assert row is not None and row.status == "accepted"


async def test_ambiguous_timeout_after_the_write_does_not_duplicate(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    sheet.fail_after_write.append(SheetsUnavailable())
    tarot, bridge = _wire(database, clock, sheet)
    view = await support.create(tarot, await support.guest(database))
    assert view.delivery == "error"
    (slot,) = await support.slots(database)
    assert slot.sheet_state == "pending_export" and slot.sheet_error == "SHEETS_UNAVAILABLE"
    clock.advance(minutes=3)  # past the back-off
    await bridge.sync_once()
    (slot,) = await support.slots(database)
    assert slot.sheet_state == "on_sheet"
    codes = [row[0] for row in sheet.grid(TAB)[1:] if row[0]]
    assert codes == [slot.request_code]


@pytest.mark.parametrize(
    "failure", [SheetsRateLimited(), SheetsAccessDenied(), SheetsUnavailable()]
)
async def test_google_failures_keep_the_request_and_log_no_content(
    database: Database, failure: SheetsError, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    sheet.fail_before.append(failure)
    tarot, _ = _wire(database, clock, sheet)
    view = await support.create(tarot, await support.guest(database))
    assert view.status is VisibleStatus.WAITING and view.delivery == "error"
    (slot,) = await support.slots(database)
    assert slot.attempts == 1 and slot.next_attempt_at is not None
    text = caplog.text
    assert QUESTION not in text and slot.request_code not in text
    assert failure.code in text


async def test_a_row_holding_another_code_is_never_overwritten(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    sheet.set_row(TAB, 2, ["Ghi chú tay của owner"])
    tarot, _ = _wire(database, clock, sheet)
    view = await support.create(tarot, await support.guest(database))
    assert view.delivery == "error"
    assert sheet.cell(TAB, "A2") == "Ghi chú tay của owner" and sheet.cell(TAB, "E2") == ""
    (slot,) = await support.slots(database)
    assert slot.sheet_error == "SLOT_OCCUPIED"


async def test_a_wrong_header_stops_every_write(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), FakeSheet()
    sheet.set_row(TAB, 1, ["Mã", *sheet_rows.HEADER[1:]])
    tarot, bridge = _wire(database, clock, sheet)
    await support.create(tarot, await support.guest(database))
    report = await bridge.sync_once()
    assert report.error == "SHEET_LAYOUT_INVALID"
    assert "write" not in sheet.calls and "clear" not in sheet.calls


async def test_cancel_clears_the_row_and_confirms_by_reading_back(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, _ = _wire(database, clock, sheet)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    _owner_writes(sheet, 2, ready=False)
    await tarot.cancel(guest, view.id)
    assert all(cell == "" for cell in sheet.grid(TAB)[1])
    receipt = await tarot.get(guest, view.id)
    assert receipt.status is VisibleStatus.CANCELLED and receipt.copy_cleared is True


async def test_a_cancel_during_an_export_in_flight_still_clears_the_row(
    database: Database,
) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    guest = await support.guest(database)
    original = sheet.write
    cancelled: list[bool] = []

    async def write_then_cancel(updates: Any) -> None:
        await original(updates)
        if not cancelled:
            cancelled.append(True)
            request_id = (await tarot.current(guest)).id
            await tarot.cancel(guest, request_id)  # commits while the export holds the lease

    sheet.write = write_then_cancel  # type: ignore[method-assign]
    view = await support.create(tarot, guest)
    assert view.status is VisibleStatus.CANCELLED
    (slot,) = await support.slots(database)
    assert slot.sheet_state == "clear_due"  # the export did not overwrite the cancel
    assert sheet.cell(TAB, "A2") == slot.request_code  # the question landed after the cancel
    clock.advance(seconds=31)  # the export's lease has expired
    await bridge.sync_once()
    assert all(cell == "" for cell in sheet.grid(TAB)[1])
    (slot,) = await support.slots(database)
    assert slot.sheet_state == "cleared"


async def test_guest_deletion_and_unknown_codes_leave_no_copy(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    guest = await support.guest(database)
    await support.create(tarot, guest)
    sheet.set_row(TAB, 5, ["LL-ABCDEF", "30/10/2026", "10:00", "Quan hệ", "Một câu hỏi lạ"])
    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest))
    report = await bridge.sync_once()
    assert report.counts.get("orphan_cleared") == 1
    assert report.counts.get("cleared") == 1
    assert all(cell == "" for row in sheet.grid(TAB)[1:] for cell in row)


async def test_a_request_admitted_during_the_grid_read_is_not_taken_for_an_orphan(
    database: Database,
) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    await support.create(tarot, await support.guest(database))
    late_guest = await support.guest(database)
    original = sheet.read
    admitted: list[bool] = []

    async def read_while_admitting(range_a1: str) -> list[list[Any]]:
        if not admitted:
            admitted.append(True)
            # A new request commits and lands on the Sheet after the pass listed its slots.
            await support.create(tarot, late_guest)
        return await original(range_a1)

    sheet.read = read_while_admitting  # type: ignore[method-assign]
    report = await bridge.sync_once()
    assert "orphan_cleared" not in report.counts, report.line()
    codes = [row[0] for row in sheet.grid(TAB)[1:] if row[0]]
    assert len(codes) == 2


async def test_day_end_clears_yesterday_and_frees_rows_for_today(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    first = await support.guest(database)
    yesterday = await support.create(tarot, first)
    clock.moment = vn(DAY + timedelta(days=1), 0, 1)
    report = await bridge.sync_once()
    assert report.counts.get("retention_unfulfilled") == 1 and report.counts.get("cleared") == 1
    assert (await tarot.get(first, yesterday.id)).status is VisibleStatus.UNFULFILLED
    second = await support.guest(database)
    today = await support.create(tarot, second)
    assert today.delivery == "delivered"
    assert sheet.cell(TAB, "B2") == "31/10/2026"


async def test_duplicate_codes_after_a_sort_block_the_import(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    view = await support.create(tarot, await support.guest(database))
    titles = _titles()
    _owner_writes(sheet, 2, cards=[titles["major-star"], titles["cups-5"], titles["wands-ace"]])
    sheet.set_row(TAB, 7, list(sheet.grid(TAB)[1]))
    report = await bridge.sync_once()
    assert report.counts.get("duplicate_code") == 1
    row = await support.request_row(database, view.id)
    assert row is not None and row.status == "accepted"


async def test_the_google_budget_fails_closed(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet, per_minute=3)
    guests = [await support.guest(database) for _ in range(3)]
    views = [await support.create(tarot, guest) for guest in guests]
    # Each export reads the grid and writes once: the third export finds the minute spent.
    assert [view.delivery for view in views] == ["delivered", "error", "error"]
    (_, second, _) = await support.slots(database)
    assert second.sheet_error == "GOOGLE_BUDGET_EXHAUSTED"
    clock.advance(minutes=5)
    # Next minute: one grid read, then the second export (read + write), then the third export
    # finds the minute spent again and the pass stops without any further call.
    report = await bridge.sync_once()
    assert report.error == "GOOGLE_BUDGET_EXHAUSTED" and report.counts.get("exported") == 1
    assert sheet.calls.count("read") + sheet.calls.count("write") == 3 + 3


async def test_no_google_call_when_nothing_is_in_flight(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    _, bridge = _wire(database, clock, sheet)
    report = await bridge.sync_once()
    assert sheet.calls == [] and report.error is None


async def test_one_pass_at_a_time(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    await support.create(tarot, await support.guest(database))
    entered, release = asyncio.Event(), asyncio.Event()
    original = sheet.read

    async def held_read(range_a1: str) -> list[list[Any]]:
        entered.set()
        await release.wait()  # the first pass holds the sync lease here
        return await original(range_a1)

    sheet.read = held_read  # type: ignore[method-assign]
    first = asyncio.create_task(bridge.sync_once())
    await asyncio.wait_for(entered.wait(), 5)
    second = await bridge.sync_once()
    release.set()
    assert second.skipped is True and (await first).skipped is False
