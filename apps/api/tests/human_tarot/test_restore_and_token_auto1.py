"""Codex auto-1 on #127: restore cleanup with nothing in flight, and the OAuth token across jobs.

1. A database restored to a copy with no human Tarot slot at all still clears the Sheet rows
   whose code it does not know (AC21), without waiting for a new request.
2. Each minute job is a new process. The access token is reused from the shared private cache
   while it is valid, so an active day costs about one grid read a minute and one OAuth call an
   hour, inside the 2,000-a-day budget (AC18), instead of two calls a minute.

Synthetic data only: no Google, no real question, no real credential.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select

from app.config import Settings
from app.db.session import Database
from app.domains.human_tarot import sheet_rows
from app.domains.human_tarot.service import RECONCILE_LEASE
from app.domains.human_tarot.sheets import (
    IDLE_RECONCILE,
    PER_DAY,
    GoogleBudget,
    HumanTarotSheetBridge,
)
from app.domains.human_tarot.tables import HumanTarotGoogleUsageRow, HumanTarotSyncLeaseRow
from app.infrastructure.google_sheets.client import (
    TOKEN_URI,
    FileTokenCache,
    GoogleSheetsClient,
    ServiceAccount,
    SheetsAccessDenied,
)
from tests.human_tarot import support
from tests.human_tarot.support import DAY, Clock, vn
from tests.human_tarot.test_sheets_sync import TAB, _owner_writes, _sheet, _wire

ORPHAN_A = ["LL-ABCDEF", "30/10/2026", "22:00", "Quan hệ", "Câu hỏi tổng hợp thứ nhất"]
ORPHAN_B = ["LL-GHJKMN", "30/10/2026", "22:00", "Công việc", "Câu hỏi tổng hợp thứ hai"]

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = KEY.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
)
ACCOUNT = ServiceAccount(client_email="synthetic-reader@example.invalid", private_key_pem=PEM)
SHEET_ID = "synthetic-sheet-id-0000000000"


def _data_rows_blank(grid: list[list[Any]]) -> bool:
    return all(cell == "" for row in grid[1:] for cell in row)


# --------------------------------------------------------------------------- 1. restore cleanup


async def test_a_restore_with_no_slot_at_all_still_clears_unknown_rows(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 9)), _sheet()
    _, bridge = _wire(database, clock, sheet)
    # The restored copy predates every human Tarot request; the Sheet still holds two later
    # questions, one of them with a reading the owner had started.
    sheet.set_row(TAB, 2, ORPHAN_A)
    sheet.set_row(TAB, 3, ORPHAN_B)
    _owner_writes(sheet, 3)
    assert await support.slots(database) == []
    report = await bridge.sync_once()
    assert report.error is None and report.counts.get("orphan_cleared") == 2, report.line()
    assert _data_rows_blank(sheet.grid(TAB))
    # The next pass reads once more to confirm the rows stayed empty, then the job goes quiet.
    calls = len(sheet.calls)
    assert "orphan_cleared" not in (await bridge.sync_once()).counts
    assert sheet.calls[calls:] == ["read"]
    calls = len(sheet.calls)
    await bridge.sync_once()
    assert sheet.calls[calls:] == []


async def test_only_long_cleared_slots_still_clear_a_late_row(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 7)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    row = list(sheet.grid(TAB)[1])
    await tarot.cancel(guest, view.id)
    clock.advance(minutes=30)  # past the clear verification window: no slot is in flight
    await bridge.sync_once()
    sheet.set_row(TAB, 2, row)  # a write that timed out long ago lands now
    clock.advance(minutes=IDLE_RECONCILE.total_seconds() / 60)
    report = await bridge.sync_once()
    assert report.counts.get("reappeared") == 1 and report.counts.get("cleared") == 1
    assert _data_rows_blank(sheet.grid(TAB))


async def test_an_idle_sheet_is_checked_at_most_once_per_window(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 9)), _sheet()
    _, bridge = _wire(database, clock, sheet)
    await bridge.sync_once()
    assert sheet.calls == ["read"]
    sheet.set_row(TAB, 4, ORPHAN_A)
    for _ in range(14):
        clock.advance(minutes=1)
        await bridge.sync_once()
    assert sheet.calls == ["read"]  # inside the window: no Google call while nothing is in flight
    clock.advance(minutes=1)
    report = await bridge.sync_once()
    assert report.counts.get("orphan_cleared") == 1
    assert _data_rows_blank(sheet.grid(TAB))


async def test_the_restore_replay_asks_for_a_check_at_once(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 9)), _sheet()
    tarot, bridge = _wire(database, clock, sheet)
    await bridge.sync_once()  # a clean check just before the snapshot
    sheet.set_row(TAB, 2, ORPHAN_A)
    await tarot.close_intake(DAY)  # run by `erasure_journal replay` and `close-today`
    report = await bridge.sync_once()
    assert report.counts.get("orphan_cleared") == 1
    async with database.sessions() as session:
        marker = await session.scalar(
            select(HumanTarotSyncLeaseRow).where(HumanTarotSyncLeaseRow.name == RECONCILE_LEASE)
        )
    assert marker is not None and marker.holder is None


# --------------------------------------------------------------------------- 2. the token


class _Google:
    """Google over a mock transport: OAuth mints a token, values reads serve the FakeSheet."""

    def __init__(self, grid: list[list[Any]]) -> None:
        self.grid = grid
        self.oauth = 0
        self.sheets = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URI:
            self.oauth += 1
            return httpx.Response(
                200, json={"access_token": f"synthetic-{self.oauth}", "expires_in": 3600}
            )
        self.sheets += 1
        if request.method == "GET":
            rows = [list(row) for row in self.grid]
            for row in rows:
                while row and row[-1] in ("", None):
                    row.pop()
            while rows and not rows[-1]:
                rows.pop()
            return httpx.Response(200, json={"values": rows})
        return httpx.Response(200, json={})


async def _used_today(database: Database) -> int:
    async with database.sessions() as session:
        used = await session.scalar(
            select(HumanTarotGoogleUsageRow.used).where(
                HumanTarotGoogleUsageRow.bucket == f"d:{DAY.isoformat()}"
            )
        )
    return int(used or 0)


async def test_minute_jobs_reuse_the_token_and_fit_the_daily_budget(
    database: Database, tmp_path: Path
) -> None:
    clock, sheet = Clock(vn(DAY, 0, 1)), _sheet()
    tarot, _ = _wire(database, clock, sheet)
    await support.create(tarot, await support.guest(database))  # one slot in flight all day
    google = _Google(sheet.grid(TAB))
    before = await _used_today(database)
    minutes = 120
    for _ in range(minutes):
        # A new process each minute: new budget object, new client, new bridge, same cache dir.
        budget = GoogleBudget(database.sessions, clock)
        client = GoogleSheetsClient(
            SHEET_ID,
            ACCOUNT,
            transport=httpx.MockTransport(google),
            clock=lambda: clock().timestamp(),
            reserve=budget.reserve,
            token_cache=FileTokenCache(tmp_path / "token-cache"),
        )
        report = await HumanTarotSheetBridge(
            database.sessions, tarot, client, budget=budget
        ).sync_once()
        assert report.error is None, report.line()
        clock.advance(minutes=1)
    # One grid read a minute; a token about once an hour (valid 60 minutes, renewed 1 early).
    assert google.sheets == minutes
    assert google.oauth == 3
    used = await _used_today(database) - before
    assert used == minutes + google.oauth
    # A whole active day at this rate stays well inside the cap, leaving room for the writes.
    assert used * (24 * 60) / minutes < PER_DAY * 0.8


def _credentials(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic-service-account.json"
    path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "token_uri": TOKEN_URI,
                "client_email": ACCOUNT.client_email,
                "private_key": PEM.decode(),
            }
        ),
        encoding="utf-8",
    )
    return path


async def test_the_job_wiring_shares_the_token_between_invocations(tmp_path: Path) -> None:
    from scripts import sync_human_tarot

    settings = Settings(
        environment="test",
        human_tarot_sheet_sync_enabled=True,
        human_tarot_sheet_id=SHEET_ID,
        human_tarot_google_credentials_file=str(_credentials(tmp_path)),
        human_tarot_google_token_cache_dir=str(tmp_path / "cache"),
    )
    google = _Google(sheet_rows.padded([list(sheet_rows.HEADER)]))
    reserved: list[int] = []

    class _Budget:
        async def reserve(self, calls: int = 1) -> None:
            reserved.append(calls)

    for _ in range(3):  # three separate job invocations
        gateway = sync_human_tarot.gateway(
            settings,
            _Budget(),  # type: ignore[arg-type]
            transport=httpx.MockTransport(google),
        )
        await gateway.read(sheet_rows.GRID)
    assert google.oauth == 1 and google.sheets == 3
    assert reserved == [1]  # only the one token request; the caller reserves each read itself


def _client(google: _Google, cache: FileTokenCache, now: list[float]) -> GoogleSheetsClient:
    return GoogleSheetsClient(
        SHEET_ID,
        ACCOUNT,
        transport=httpx.MockTransport(google),
        clock=lambda: now[0],
        token_cache=cache,
    )


async def test_the_cache_file_is_private_and_holds_no_account_name(tmp_path: Path) -> None:
    google, now = _Google([]), [1_800_000_000.0]
    directory = tmp_path / "cache"
    await _client(google, FileTokenCache(directory), now).read(sheet_rows.GRID)
    token_file = directory / "google-token.json"
    assert stat.S_IMODE(os.stat(directory).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(token_file).st_mode) == 0o600
    body = token_file.read_text(encoding="utf-8")
    assert ACCOUNT.client_email not in body and "BEGIN" not in body
    assert [path.name for path in directory.iterdir()] == ["google-token.json"]


async def test_an_expiring_token_is_renewed_once(tmp_path: Path) -> None:
    google, now = _Google([]), [1_800_000_000.0]
    cache = FileTokenCache(tmp_path / "cache")
    await _client(google, cache, now).read(sheet_rows.GRID)
    now[0] += 3600 - 59  # inside the renewal margin
    await _client(google, cache, now).read(sheet_rows.GRID)
    await _client(google, cache, now).read(sheet_rows.GRID)
    assert google.oauth == 2


async def test_another_account_never_gets_the_cached_token(tmp_path: Path) -> None:
    google, now = _Google([]), [1_800_000_000.0]
    cache = FileTokenCache(tmp_path / "cache")
    await _client(google, cache, now).read(sheet_rows.GRID)
    other = GoogleSheetsClient(
        SHEET_ID,
        ServiceAccount(client_email="other-reader@example.invalid", private_key_pem=PEM),
        transport=httpx.MockTransport(google),
        clock=lambda: now[0],
        token_cache=cache,
    )
    await other.read(sheet_rows.GRID)
    assert google.oauth == 2


@pytest.mark.parametrize("unsafe", ["symlink", "readable_by_others"])
async def test_an_unsafe_cache_file_is_ignored(tmp_path: Path, unsafe: str) -> None:
    google, now = _Google([]), [1_800_000_000.0]
    directory = tmp_path / "cache"
    cache = FileTokenCache(directory)
    await _client(google, cache, now).read(sheet_rows.GRID)
    token_file = directory / "google-token.json"
    if unsafe == "symlink":
        target = tmp_path / "elsewhere.json"
        token_file.rename(target)
        token_file.symlink_to(target)
    else:
        token_file.chmod(0o644)
    await _client(google, cache, now).read(sheet_rows.GRID)
    assert google.oauth == 2


async def test_a_rejected_token_is_dropped_from_the_cache(tmp_path: Path) -> None:
    now = [1_800_000_000.0]
    directory = tmp_path / "cache"
    cache = FileTokenCache(directory)
    await _client(_Google([]), cache, now).read(sheet_rows.GRID)
    assert (directory / "google-token.json").exists()

    def revoked(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={})

    client = GoogleSheetsClient(
        SHEET_ID,
        ACCOUNT,
        transport=httpx.MockTransport(revoked),
        clock=lambda: now[0],
        token_cache=cache,
    )
    with pytest.raises(SheetsAccessDenied):
        await client.read(sheet_rows.GRID)
    assert not (directory / "google-token.json").exists()


def test_the_default_cache_lives_in_the_temp_directory() -> None:
    import tempfile

    cache = FileTokenCache.default()
    assert str(cache._directory).startswith(tempfile.gettempdir())
    assert FileTokenCache.default("/run/synthetic")._directory == Path("/run/synthetic")


async def test_a_failing_idle_check_waits_for_the_next_window(database: Database) -> None:
    clock, sheet = Clock(vn(DAY, 9)), _sheet()
    _, bridge = _wire(database, clock, sheet)
    sheet.set_row(TAB, 1, ["Mã sai"])  # the owner broke the header
    sheet.set_row(TAB, 2, ORPHAN_A)
    assert (await bridge.sync_once()).error == "SHEET_LAYOUT_INVALID"
    for _ in range(14):
        clock.advance(minutes=1)
        assert (await bridge.sync_once()).error is None
    assert sheet.calls == ["read"]
    sheet.set_row(TAB, 1, list(sheet_rows.HEADER))  # fixed
    clock.advance(minutes=1)
    assert (await bridge.sync_once()).counts.get("orphan_cleared") == 1
