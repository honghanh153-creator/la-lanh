"""Codex r56 on #127: a Sheet row is bound to its request by the DB-assigned row *and* its code.

1. A missing code never proves the question is gone: a cancel clears the request's own row and
   confirms only when the whole row reads back empty.
2. An export never reuses a row that still holds owner content without a code (a previous reading
   must not reach the next person).
3. A ready row is imported only from its own row: a partial sort of A:G is refused, not swapped.
4. Every Google HTTP request is in the durable budget, the OAuth token request included.
5. The retry back-off stays bounded after a long outage.
"""

from __future__ import annotations

from datetime import timedelta

import httpx
import pytest

from app.db.session import Database
from app.domains.human_tarot.sheets import BudgetExhausted, GoogleBudget, HumanTarotSheetBridge
from app.infrastructure.google_sheets import client as google_client
from app.infrastructure.google_sheets.client import SheetsAccessDenied
from tests.human_tarot import support
from tests.human_tarot.support import DAY, QUESTION, Clock, vn
from tests.human_tarot.test_sheets_sync import TAB, _owner_writes, _sheet, _wire

PRIVATE = "Bài riêng tổng hợp của người thứ nhất, không được gửi cho người khác dù mã hàng đã mất."


async def test_a_missing_code_does_not_prove_the_question_is_gone(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, _ = _wire(database, clock, sheet)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    sheet.set_row(TAB, 2, [""])  # the owner deleted only the code
    await tarot.cancel(guest, view.id)
    receipt = await tarot.get(guest, view.id)
    assert receipt.copy_cleared is True
    assert all(cell == "" for cell in sheet.grid(TAB)[1])  # question and all cells really gone
    assert sheet.cell(TAB, "E2") != QUESTION


async def test_an_export_never_reuses_a_row_with_leftover_owner_content(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    _owner_writes(sheet, 2, reading=PRIVATE)  # a ready reading left without a code
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    assert view.delivery == "error"
    (slot,) = await support.slots(database)
    assert slot.sheet_error == "SLOT_OCCUPIED" and sheet.cell(TAB, "A2") == ""
    await bridge.sync_once()
    clock.moment = vn(DAY, 22)
    assert (await tarot.get(guest, view.id)).result is None


async def test_a_cancelled_reading_never_reaches_the_next_days_guest(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    first = await support.guest(database)
    old = await support.create(tarot, first)
    _owner_writes(sheet, 2, reading=PRIVATE)
    sheet.set_row(TAB, 2, [""])
    await tarot.cancel(first, old.id)
    assert (await tarot.get(first, old.id)).copy_cleared is True
    clock.moment = vn(DAY + timedelta(days=1), 7)
    second = await support.guest(database)
    new = await support.create(tarot, second)
    await bridge.sync_once()
    clock.moment = vn(DAY + timedelta(days=1), 22)
    opened = await tarot.get(second, new.id)
    assert opened.result is None or opened.result.reading != PRIVATE


async def test_a_partial_sort_cannot_swap_two_peoples_readings(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    first, second = await support.guest(database), await support.guest(database)
    a = await support.create(tarot, first)
    b = await support.create(tarot, second)
    _owner_writes(
        sheet, 2, reading="Bài riêng của người thứ nhất, đủ dài cho kiểm thử ràng buộc hàng."
    )
    _owner_writes(sheet, 3, reading="Bài riêng của người thứ hai, khác hẳn, đủ dài cho kiểm thử.")
    grid = sheet.grid(TAB)
    grid[1][:7], grid[2][:7] = grid[2][:7], grid[1][:7]  # only A:G sorted
    report = await bridge.sync_once()
    assert report.counts.get("row_moved") == 2 and "imported" not in report.counts
    clock.moment = vn(DAY, 22)
    assert (await tarot.get(first, a.id)).result is None
    assert (await tarot.get(second, b.id)).result is None


async def test_the_oauth_request_is_in_the_budget(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = Clock(vn(DAY, 7))
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "synthetic", "expires_in": 3600})
        return httpx.Response(200, json={"values": []})

    monkeypatch.setattr(google_client, "signed_assertion", lambda account, now: "synthetic")
    budget = GoogleBudget(database.sessions, clock, per_minute=1, per_day=2000)
    client = google_client.GoogleSheetsClient(
        "synthetic-spreadsheet-id-000000",
        google_client.ServiceAccount("synthetic@example.invalid", b"synthetic"),
        transport=httpx.MockTransport(handler),
        reserve=budget.reserve,
    )
    tarot = support.service(database, clock)
    bridge = HumanTarotSheetBridge(database.sessions, tarot, client, budget=budget)
    await support.create(tarot, await support.guest(database))
    report = await bridge.sync_once()
    # One call allowed this minute: the grid read is reserved, the token request finds the
    # minute spent, so nothing at all reaches Google.
    assert report.error == "GOOGLE_BUDGET_EXHAUSTED"
    assert calls == []
    with pytest.raises(BudgetExhausted):
        await budget.reserve()


async def test_the_back_off_stays_bounded_after_a_long_outage(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 0)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    sheet.fail_before = [SheetsAccessDenied()]
    await support.create(tarot, await support.guest(database))
    (slot,) = await support.slots(database)
    for _ in range(45):
        clock.advance(minutes=16)
        sheet.fail_before = [SheetsAccessDenied()]
        await bridge.export_now(slot.id)
    (slot,) = await support.slots(database)
    assert slot.attempts >= 45
    assert slot.next_attempt_at is not None
    assert slot.next_attempt_at - clock() <= timedelta(minutes=15)
