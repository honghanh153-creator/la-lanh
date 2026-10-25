"""Purge horizon edges (Codex #78 APPROVE @ 610c8ae, suggested as committed regressions)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.erasure_journal import replay as replay_module
from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.replay import export_entries, purge_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalHorizonRow, ErasureJournalRow
from app.domains.guest.tables import GuestSessionRow
from tests.erasure_journal.test_journal import ENVELOPE, JOURNAL, NOW, _guest

H = NOW - timedelta(days=15)


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def _horizon(database: Database) -> object:
    async with database.sessions() as session:
        row = await session.get(ErasureJournalHorizonRow, 1)
        return row.purged_before if row is not None else None


async def test_the_horizon_advances_holds_and_never_moves_back(storage: Database) -> None:
    assert await _horizon(storage) is None
    await purge_entries(storage.sessions, before=H)
    assert await _horizon(storage) == H
    await purge_entries(storage.sessions, before=H + timedelta(hours=1))
    assert await _horizon(storage) == H + timedelta(hours=1)
    await purge_entries(storage.sessions, before=H + timedelta(hours=1))  # equal: unchanged
    await purge_entries(storage.sessions, before=H)  # earlier: never moves back
    assert await _horizon(storage) == H + timedelta(hours=1)
    async with storage.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(ErasureJournalHorizonRow)) == 1


async def test_the_boundary_is_strict(storage: Database) -> None:
    guest_id = await _guest(storage)
    await purge_entries(storage.sessions, before=H)

    def entry(at: object) -> str:
        return json.dumps({
            "kind": ErasureKind.GUEST_ERASED.value,
            "subject_digest": JOURNAL.digest(ErasureKind.GUEST_ERASED, guest_id).hex(),
            "scope": "",
            "occurred_at": at.isoformat(),  # type: ignore[attr-defined]
        })  # fmt: skip

    older = await replay(
        storage.sessions, JOURNAL, ENVELOPE, [entry(H - timedelta(microseconds=1))]
    )
    assert older.reflected[ErasureKind.GUEST_ERASED.value] == 1 and not older.applied
    async with storage.sessions() as session:
        guest = await session.get(GuestSessionRow, guest_id)
        assert guest is not None and guest.state == "active"
    at_horizon = await replay(storage.sessions, JOURNAL, ENVELOPE, [entry(H)])
    assert at_horizon.applied[ErasureKind.GUEST_ERASED.value] == 1  # goes by row presence
    async with storage.sessions() as session:
        guest = await session.get(GuestSessionRow, guest_id)
        assert guest is not None and guest.state == "deleting"


async def test_a_failed_horizon_write_rolls_back_the_purge(
    storage: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    guest_id = await _guest(storage)
    async with storage.sessions() as session, session.begin():
        JOURNAL.record(session, ErasureKind.HISTORY_CLEARED, guest_id, H - timedelta(days=1))

    class Failing(ErasureJournalHorizonRow):
        def __init__(self, **_: object) -> None:
            raise RuntimeError("synthetic failure while recording the horizon")

    monkeypatch.setattr(replay_module, "ErasureJournalHorizonRow", Failing)
    with pytest.raises(RuntimeError):
        await purge_entries(storage.sessions, before=H)
    monkeypatch.undo()
    assert await _horizon(storage) is None
    assert len(await export_entries(storage.sessions)) == 1  # the DELETE rolled back too
    async with storage.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(ErasureJournalRow)) == 1
