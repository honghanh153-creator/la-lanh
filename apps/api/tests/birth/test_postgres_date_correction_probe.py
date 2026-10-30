"""Disposable PostgreSQL probe for the birth-date correction (US-23 AC2, AC4, AC8, AC11).

Skipped unless ``LA_LANH_JOURNAL_PROBE_POSTGRES_URL`` names a migrated, disposable localhost
database whose name starts with ``lalanh_probe_`` (guard, tools and procedure as in
docs/operations/disposable-postgres-journal-probe.md). Synthetic rows only. Checks what SQLite
cannot: two connections racing on the revision fence, the immediate current-snapshot FK during the
replacement, a send drain across connections, and pg_dump/pg_restore on both sides of a correction.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.astro.engine import NatalChartEngine
from app.domains.birth.errors import BirthProfileChanged
from app.domains.birth.models import BirthTimeMode
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.service import BirthChartService
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.content_rewrite.tables import RewriteSendFenceRow
from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.replay import export_entries, replay
from tests.erasure_journal.test_postgres_restore_probe import (
    ENVELOPE,
    HASHER,
    JOURNAL,
    _bounded,
    _guest,
    _tool,
    probe,
)

__all__ = ["probe"]
FIRST, SECOND, THIRD = date(1990, 3, 15), date(1991, 11, 15), date(1993, 6, 1)


def _service(database: Database) -> BirthChartService:
    repository = PostgresBirthRepository(database.sessions, ENVELOPE, JOURNAL)
    return BirthChartService(repository, NatalChartEngine(), ENVELOPE, HASHER)


async def _full_subject(database: Database) -> tuple[BirthChartService, UUID]:
    guest_id = await _guest(database)
    service = _service(database)
    await service.create_date_only(guest_id=guest_id, birth_date=FIRST)
    await service.add_supplement(
        guest_id=guest_id, birth_time_mode=BirthTimeMode.EXACT, birth_time_local="08:15",
        approx_window=None, place_id="vn-hanoi", consent_version="birth-profile-deep-v1",
    )  # fmt: skip
    return service, guest_id


async def _correct(service: BirthChartService, guest_id: UUID, value: date, revision: Any) -> Any:
    return await service.correct_date(
        guest_id=guest_id, birth_date=value, confirm_birth_date=value, expected_revision=revision
    )


async def test_an_active_natal_subject_is_replaced_without_fk_error(probe: Any) -> None:
    database, _, _ = probe
    service, guest_id = await _full_subject(database)
    current = await service.current(guest_id)
    replaced = await _correct(service, guest_id, SECOND, current.profile_revision)
    async with database.sessions() as session:
        snapshots = await session.scalar(
            select(func.count()).select_from(ChartSnapshotRow).where(
                ChartSnapshotRow.guest_id == guest_id
            )
        )  # fmt: skip
        profile = await session.scalar(
            select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
        )
    assert snapshots == 1
    assert profile is not None and profile.current_snapshot_id == replaced.snapshot_id
    assert profile.birth_time_ciphertext is None and profile.supplement_consent_version is None


async def _await_commit(task: asyncio.Task[Any], committed: Callable[[], Awaitable[bool]]) -> None:
    """Wait, bounded, until the correction has committed (Codex r55).

    A correction that fails before committing surfaces its own error at once; one that never
    commits times out instead of polling forever, and its task is cancelled so teardown runs.
    """

    async def poll() -> None:
        while not await committed():
            if task.done():
                task.result()  # raises the correction's error
                raise AssertionError("the correction finished without committing")
            await asyncio.sleep(0.05)

    try:
        await _bounded(poll())
    except BaseException:
        task.cancel()
        with contextlib.suppress(BaseException):
            await task
        raise


async def test_two_tabs_race_on_the_revision_fence(probe: Any) -> None:
    database, _, _ = probe
    guest_id = await _guest(database)
    first, second = _service(database), _service(database)
    await first.create_date_only(guest_id=guest_id, birth_date=FIRST)
    revision = (await first.current(guest_id)).profile_revision
    results = await asyncio.gather(
        _bounded(_correct(first, guest_id, SECOND, revision)),
        _bounded(_correct(second, guest_id, THIRD, revision)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, BirthProfileChanged) for result in results) == 1
    assert sum(not isinstance(result, BaseException) for result in results) == 1


async def test_success_waits_for_an_admitted_send(probe: Any) -> None:
    database, _, _ = probe
    service, guest_id = await _full_subject(database)
    job_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            RewriteSendFenceRow(
                job_id=job_id, lease_token=uuid4(), subject_id=guest_id,
                expires_at=datetime.now(UTC) + timedelta(minutes=3),
            )
        )  # fmt: skip
    revision = (await service.current(guest_id)).profile_revision
    task = asyncio.create_task(_correct(service, guest_id, SECOND, revision))

    async def committed() -> bool:
        return (await service.current(guest_id)).birth_date == SECOND

    await _await_commit(task, committed)
    assert not task.done()
    async with database.sessions() as session, session.begin():
        row = await session.scalar(
            select(RewriteSendFenceRow).where(RewriteSendFenceRow.job_id == job_id)
        )
        assert row is not None
        await session.delete(row)
    assert (await _bounded(task)).birth_date == SECOND


async def test_restore_on_both_sides_of_a_correction(probe: Any, tmp_path: Path) -> None:
    database, url, env = probe
    service, guest_id = await _full_subject(database)
    before, after = tmp_path / "before.dump", tmp_path / "after.dump"
    dump = ("pg_dump", "--format=custom", "--schema=public", f"--dbname={url.database}")
    await _tool(env, *dump, f"--file={before}")
    revision = (await service.current(guest_id)).profile_revision
    replaced = await _correct(service, guest_id, SECOND, revision)
    await _tool(env, *dump, f"--file={after}")
    lines = await export_entries(database.sessions)
    kind = ErasureKind.BIRTH_DATE_REPLACED.value
    restore = f"{url.database}_restore"
    for path, applied in ((after, False), (before, True)):
        await _tool(env, "dropdb", "--if-exists", restore)
        await _tool(env, "createdb", restore)
        await _tool(env, "pg_restore", "--no-owner", f"--dbname={restore}", str(path))
        restored = Database(url.set(database=restore).render_as_string(hide_password=False))
        try:
            report = await replay(restored.sessions, JOURNAL, ENVELOPE, lines)
            assert report.applied[kind] == (1 if applied else 0)
            assert report.reflected[kind] == (0 if applied else 1)
            async with restored.sessions() as session:
                profile = await session.scalar(
                    select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
                )
                snapshots = await session.scalar(
                    select(func.count()).select_from(ChartSnapshotRow).where(
                        ChartSnapshotRow.guest_id == guest_id
                    )
                )  # fmt: skip
            assert profile is not None
            if applied:
                assert profile.current_snapshot_id is None and snapshots == 0
                assert profile.birth_time_ciphertext is None
            else:
                assert profile.current_snapshot_id == replaced.snapshot_id and snapshots == 1
        finally:
            await restored.dispose()
    assert all(SECOND.isoformat() not in line and FIRST.isoformat() not in line for line in lines)


@pytest.mark.parametrize("value", [FIRST])
def test_probe_constants_are_adult_dates(value: date) -> None:
    """The synthetic dates pass the 18+ rule, so the probe never meets an age refusal."""

    today = date.today()
    assert value < today.replace(year=today.year - 18)


async def test_the_probe_seed_and_replacement_run_on_sqlite(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'probe-seed.db'}")
    await database.initialize()
    try:
        service, guest_id = await _full_subject(database)
        revision = (await service.current(guest_id)).profile_revision
        replaced = await _correct(service, guest_id, SECOND, revision)
        assert (await service.current(guest_id)).snapshot_id == replaced.snapshot_id
    finally:
        await database.dispose()
