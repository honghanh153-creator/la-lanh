"""Codex #78 P2-1: the real history-clear entry point journals in its own transaction.

The HTTP route calls HistoryService.request("clear"), not repository.clear(). These tests go
through that service with a synthetic credential and CSRF token, and through HTTP, then restore a
snapshot taken before the clear and check that unexpired history does not come back.
"""

from __future__ import annotations

import shutil
import sqlite3
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.daily.tables import DailyNoteRow
from app.domains.erasure_journal.replay import export_entries, purge_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.guest.errors import CsrfRejected
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.postgres import PostgresHistoryRepository
from app.domains.history.service import HistoryService
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.domains.tarot.tables import TarotSessionRow
from tests.accounts.support import FakeTransport, headers
from tests.accounts.support import client as make_client
from tests.erasure_journal.test_journal import (
    ENVELOPE,
    HASHER,
    JOURNAL,
    NOW,
    OLD,
    _guest,
    _note,
)
from tests.history.test_api import disclosed_guest

TOKEN, CSRF = "synthetic-guest-credential", "synthetic-csrf-token"


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def _owner_with_history(database: Database) -> tuple[object, object, object]:
    guest_id = await _guest(database, HASHER.digest("guest-credential", TOKEN))
    note_id = await _note(database, guest_id)
    tarot_id = uuid4()
    async with database.sessions() as session, session.begin():
        guest = await session.get(GuestSessionRow, guest_id)
        assert guest is not None
        guest.csrf_hash = HASHER.digest("guest-csrf", CSRF)
        # Completed Tarot history that is far from expiry: only the manual clear removes it.
        session.add(
            TarotSessionRow(
                id=tarot_id, guest_id=guest_id, state="complete", context="self_care",
                spread="one_card", voice="straight_warm", origin="direct",
                idempotency_hash=b"s" * 32, payload_ciphertext="synthetic-opaque-reading",
                created_at=OLD, updated_at=OLD, expires_at=NOW + timedelta(days=29),
            )
        )  # fmt: skip
    return guest_id, note_id, tarot_id


def _tarot(guest_id: object, tarot_id: object, created: datetime) -> TarotSessionRow:
    return TarotSessionRow(
        id=tarot_id, guest_id=guest_id, state="complete", context="self_care", spread="one_card",
        voice="straight_warm", origin="direct", idempotency_hash=uuid4().bytes * 2,
        payload_ciphertext="synthetic-opaque-reading", created_at=created, updated_at=created,
        expires_at=created + timedelta(days=30),
    )  # fmt: skip


def _service(database: Database) -> HistoryService:
    return HistoryService(PostgresHistoryRepository(database.sessions, ENVELOPE, JOURNAL), HASHER)


async def _journal_count(database: Database) -> int:
    async with database.sessions() as session:
        return int(await session.scalar(select(func.count()).select_from(ErasureJournalRow)) or 0)


async def test_service_clear_journals_once_and_survives_restore_with_both_cleanups(
    tmp_path: Path,
) -> None:
    live, dump = tmp_path / "live.db", tmp_path / "dump.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    guest_id, note_id, tarot_id = await _owner_with_history(database)
    await database.dispose()
    shutil.copyfile(live, dump)
    database = Database(f"sqlite+aiosqlite:///{live}")
    assert await _service(database).request("clear", TOKEN, CSRF) is None
    assert await _journal_count(database) == 1
    async with database.sessions() as session:
        assert await session.get(TarotSessionRow, tarot_id) is None
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(dump, live)
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert report.applied["history_cleared"] == 1
        await PostgresGuestRepository(database.sessions).purge_expired(datetime.now(UTC), 500)
        history = PostgresHistoryRepository(database.sessions, ENVELOPE)
        for _ in range(100):
            if not await history.purge_expired(datetime.now(UTC)):
                break
        async with database.sessions() as session:
            assert await session.get(GuestSessionRow, guest_id) is not None
            assert await session.get(DailyNoteRow, note_id) is None
            assert await session.get(TarotSessionRow, tarot_id) is None
    finally:
        await database.dispose()


async def test_a_failed_clear_rolls_back_the_deletion_and_its_journal_entry(
    storage: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, note_id, tarot_id = await _owner_with_history(storage)
    original = PostgresHistoryRepository._erase

    async def erase_then_fail(*args: object, **kwargs: object) -> int:
        await original(*args, **kwargs)  # type: ignore[arg-type]
        raise RuntimeError("synthetic failure after the deletion statements")

    monkeypatch.setattr(PostgresHistoryRepository, "_erase", erase_then_fail)
    with pytest.raises(RuntimeError):
        await _service(storage).request("clear", TOKEN, CSRF)
    assert await _journal_count(storage) == 0
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, note_id) is not None
        assert await session.get(TarotSessionRow, tarot_id) is not None


async def test_rejected_csrf_journals_nothing(storage: Database) -> None:
    await _owner_with_history(storage)
    with pytest.raises(CsrfRejected):
        await _service(storage).request("clear", TOKEN, "wrong-csrf")
    assert await _journal_count(storage) == 0


def test_http_history_clear_writes_exactly_one_entry(tmp_path: Path) -> None:
    path = tmp_path / "http.db"
    with make_client(path, FakeTransport(), enabled=False) as client:
        owner = disclosed_guest(client)
        assert client.delete("/v1/session/history", headers=headers("wrong")).status_code == 403
        cleared = client.delete("/v1/session/history", headers=headers(owner["csrf_token"]))
        assert cleared.status_code == 204
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT kind, scope FROM erasure_journal").fetchall()
    assert rows == [("history_cleared", "")]


async def test_a_purged_checkpoint_does_not_reapply_an_old_clear_to_later_history(
    tmp_path: Path,
) -> None:
    """Codex #78 P1 @ 5579600: the hourly copy exports before it purges, so an old export can
    hold a clear whose journal row a later snapshot no longer has. The purge horizon recorded in
    the same transaction marks such entries as reflected; newer history must survive replay."""

    live, snapshot = tmp_path / "live.db", tmp_path / "snapshot.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    owner = await _guest(database)
    clear_at = NOW - timedelta(days=15, minutes=1)
    newer = uuid4()
    async with database.sessions() as session, session.begin():
        guest = await session.get(GuestSessionRow, owner)
        policy = await session.get(HistoryRetentionPolicyRow, owner)
        assert guest is not None and policy is not None
        guest.created_at = policy.activated_at = clear_at - timedelta(days=1)
        session.add(_tarot(owner, uuid4(), clear_at - timedelta(hours=1)))
    assert await PostgresHistoryRepository(database.sessions, ENVELOPE, JOURNAL).clear(
        owner, clear_at
    )
    retained_file = await export_entries(database.sessions)  # the hourly copy, before its purge
    assert len(retained_file) == 1
    async with database.sessions() as session, session.begin():
        session.add(_tarot(owner, newer, NOW - timedelta(days=1)))
    assert await purge_entries(database.sessions, before=NOW - timedelta(days=15)) == 1
    latest_file = await export_entries(database.sessions)
    assert latest_file == []
    await database.dispose()
    shutil.copyfile(live, snapshot)  # a valid dump taken after the purge
    shutil.copyfile(snapshot, live)
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        report = await replay(database.sessions, JOURNAL, ENVELOPE, [*retained_file, *latest_file])
        assert report.reflected["history_cleared"] == 1 and not report.applied
        await PostgresGuestRepository(database.sessions).purge_expired(NOW, 500)
        history = PostgresHistoryRepository(database.sessions, ENVELOPE)
        for _ in range(100):
            if not await history.purge_expired(NOW):
                break
        async with database.sessions() as session:
            assert await session.get(TarotSessionRow, newer) is not None
    finally:
        await database.dispose()


async def test_an_entry_newer_than_the_purge_horizon_is_still_applied(tmp_path: Path) -> None:
    """The horizon only covers what was purged: a newer erasure missing from the snapshot (the
    original pre-dump/post-commit case) is still re-applied."""

    live, snapshot = tmp_path / "live.db", tmp_path / "snapshot.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    _, note_id, tarot_id = await _owner_with_history(database)
    await purge_entries(database.sessions, before=NOW - timedelta(days=15))  # horizon in snapshot
    await database.dispose()
    shutil.copyfile(live, snapshot)
    database = Database(f"sqlite+aiosqlite:///{live}")
    assert await _service(database).request("clear", TOKEN, CSRF) is None
    exported = await export_entries(database.sessions)
    await database.dispose()
    shutil.copyfile(snapshot, live)
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert report.applied["history_cleared"] == 1
        async with database.sessions() as session:
            assert await session.get(TarotSessionRow, tarot_id) is None
            assert await session.get(DailyNoteRow, note_id) is None
    finally:
        await database.dispose()
