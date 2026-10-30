"""Disposable PostgreSQL probe for the copy lifecycle (US-23 prerequisite; operator evidence).

Skipped unless ``LA_LANH_JOURNAL_PROBE_POSTGRES_URL`` names a migrated, disposable localhost
database whose name starts with ``lalanh_probe_`` (same guard and procedure as the journal probe:
docs/operations/disposable-postgres-journal-probe.md). Synthetic rows only. This release keeps the
source cascades (the compatibility release; migration 20261029_0039 drops them in the next one), so
it checks that birth time/place removal and guest deletion remove every copy, and that a share
create serialized behind a removal is rejected.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import delete, text

from app.db.session import Database
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.tables import BirthProfileRow
from app.domains.daily.models import DailyNoteRecord
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.tables import DailyNoteRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.errors import ShareArtifactUnavailable
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from tests.erasure_journal.test_postgres_restore_probe import (
    ENVELOPE,
    MIGRATIONS,
    PROBE_ENV,
    _bounded,
    _held,
    _lock_waiters,
    disposable_target,
)

NOW = datetime.now(UTC)


@pytest.fixture
async def probe() -> AsyncIterator[Database]:
    raw = os.environ.get(PROBE_ENV)
    if not raw:
        pytest.skip(f"set {PROBE_ENV} to run the disposable PostgreSQL copy-lifecycle probe")
    try:
        url = disposable_target(raw)
    except ValueError as error:
        pytest.fail(f"refusing to run the probe: {error}")
    database = Database(url.render_as_string(hide_password=False))
    try:
        async with database.engine.begin() as connection:
            head = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert head == ScriptDirectory(str(MIGRATIONS)).get_current_head()
            await connection.execute(text("TRUNCATE guest_sessions, erasure_journal CASCADE"))
        yield database
    finally:
        await database.dispose()


async def _seed(database: Database) -> dict[str, UUID]:
    guest_id, profile_id, saved_id, share_id = uuid4(), uuid4(), uuid4(), uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id, token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes, state="active",
                onboarding_status="basic_revealed", created_at=NOW, last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )  # fmt: skip
        await session.flush()
        session.add(
            BirthProfileRow(
                id=profile_id, guest_id=guest_id, profile_level=2, time_precision="exact",
                birth_time_ciphertext="synthetic", created_at=NOW, updated_at=NOW,
            )
        )  # fmt: skip
    note = await PostgresDailyNoteRepository(database.sessions, ENVELOPE).get_or_create(
        DailyNoteRecord(
            id=uuid4(), guest_id=guest_id, note_date=NOW.date(), title="synthetic",
            body="synthetic", context_label="probe", content_version="probe",
            chart_snapshot_id=None, created_at=NOW,
        )
    )  # fmt: skip
    async with database.sessions() as session, session.begin():
        session.add(
            SavedNoteRow(
                id=saved_id, guest_id=guest_id, daily_note_id=note.id, note_snapshot={},
                saved_at=NOW,
            )
        )  # fmt: skip
        session.add(
            ShareArtifactRow(
                id=share_id, guest_id=guest_id, daily_note_id=note.id,
                token_hash=uuid4().bytes + uuid4().bytes, safe_snapshot={}, format="story_9_16",
                created_at=NOW, expires_at=NOW + timedelta(days=14),
            )
        )  # fmt: skip
    return {"guest": guest_id, "note": note.id, "saved": saved_id, "share": share_id}


async def _present(database: Database, ids: dict[str, UUID]) -> tuple[bool, bool]:
    async with database.sessions() as session:
        return (
            await session.get(SavedNoteRow, ids["saved"]) is not None,
            await session.get(ShareArtifactRow, ids["share"]) is not None,
        )


async def test_time_removal_and_guest_deletion_still_remove_copies(probe: Database) -> None:
    removed, deleted = await _seed(probe), await _seed(probe)
    await PostgresBirthRepository(probe.sessions, ENVELOPE).clear_supplement(
        removed["guest"], remove_time=True, remove_place=False
    )
    assert await _present(probe, removed) == (False, False)
    async with probe.sessions() as session, session.begin():
        await session.execute(delete(DailyNoteRow).where(DailyNoteRow.id == deleted["note"]))
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == deleted["guest"]))
    assert await _present(probe, deleted) == (False, False)


def _link(ids: dict[str, UUID]) -> ShareArtifactRecord:
    return ShareArtifactRecord(
        id=uuid4(), guest_id=ids["guest"], daily_note_id=ids["note"],
        token_hash=uuid4().bytes + uuid4().bytes, safe_snapshot=SafeShareSnapshot(*(["s"] * 8)),
        format=ShareFormat.STORY_9_16, created_at=NOW, expires_at=NOW + timedelta(days=14),
    )  # fmt: skip


async def test_a_share_create_waiting_on_a_removal_is_rejected(probe: Database) -> None:
    """Codex r54 P2: remove-then-create. The removal holds the guest lock and has deleted the
    source; a create on another connection waits on that lock, then rechecks and fails."""

    ids = await _seed(probe)
    shares = PostgresShareArtifactRepository(probe.sessions, ENVELOPE)
    late = _link(ids)
    created: list[asyncio.Task[ShareArtifactRecord]] = []

    async def hold() -> None:
        created.append(asyncio.create_task(shares.create(late)))
        await _bounded(_lock_waiters(probe, 1))  # PostgreSQL says the create waits on the lock

    await PostgresBirthRepository(_held(probe.sessions, hold), ENVELOPE).clear_supplement(
        ids["guest"], remove_time=True, remove_place=False
    )
    with pytest.raises(ShareArtifactUnavailable):
        await _bounded(created[0])
    async with probe.sessions() as session:
        assert await session.get(ShareArtifactRow, late.id) is None


async def test_a_share_created_before_a_removal_is_deleted_by_it(probe: Database) -> None:
    """Create-then-remove: the link exists, and time removal deletes it with every copy."""

    ids = await _seed(probe)
    early = await PostgresShareArtifactRepository(probe.sessions, ENVELOPE).create(_link(ids))
    await PostgresBirthRepository(probe.sessions, ENVELOPE).clear_supplement(
        ids["guest"], remove_time=True, remove_place=False
    )
    async with probe.sessions() as session:
        assert await session.get(ShareArtifactRow, early.id) is None


async def test_the_probe_seed_and_checks_run_on_sqlite(tmp_path: Any) -> None:
    """The seed respects the schema before any PostgreSQL run; the lifecycle holds on SQLite."""

    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'probe-seed.db'}")
    await database.initialize()
    try:
        ids = await _seed(database)
        assert await _present(database, ids) == (True, True)
        await PostgresBirthRepository(database.sessions, ENVELOPE).clear_supplement(
            ids["guest"], remove_time=True, remove_place=False
        )
        assert await _present(database, ids) == (False, False)
        fresh = await _seed(database)
        await PostgresShareArtifactRepository(database.sessions, ENVELOPE).create(_link(fresh))
        async with database.sessions() as session, session.begin():
            await session.execute(delete(DailyNoteRow).where(DailyNoteRow.id == fresh["note"]))
        with pytest.raises(ShareArtifactUnavailable):
            await PostgresShareArtifactRepository(database.sessions, ENVELOPE).create(_link(fresh))
    finally:
        await database.dispose()
