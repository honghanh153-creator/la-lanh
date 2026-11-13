"""Disposable PostgreSQL probe for the human Tarot cap (US-24 AC01/AC02/AC05; operator evidence).

Skipped unless ``LA_LANH_JOURNAL_PROBE_POSTGRES_URL`` names a migrated, disposable database on
localhost (same guards as tests/erasure_journal/test_postgres_restore_probe.py). Synthetic rows
only. SQLite serializes writers with BEGIN IMMEDIATE; this checks the row locks and constraints
that PostgreSQL relies on instead. Not run in CI; a run needs the owner's separate approval.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.db.session import Database
from app.domains.human_tarot.errors import HumanTarotFull
from app.domains.human_tarot.tables import HumanTarotDayRow
from tests.erasure_journal.test_postgres_restore_probe import (
    MIGRATIONS,
    PROBE_ENV,
    disposable_target,
)
from tests.human_tarot import support
from tests.human_tarot.support import DAY, Clock, vn


@pytest.fixture
async def pg() -> AsyncIterator[Database]:
    raw = os.environ.get(PROBE_ENV)
    if not raw:
        pytest.skip(f"set {PROBE_ENV} to run the disposable PostgreSQL probe")
    try:
        url = disposable_target(raw)
    except ValueError as error:
        pytest.fail(f"refusing to run the probe: {error}")
    database = Database(url.render_as_string(hide_password=False))
    try:
        async with database.engine.begin() as connection:
            head = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert head == ScriptDirectory(str(MIGRATIONS)).get_current_head()
            await connection.execute(
                text(
                    "TRUNCATE human_tarot_slots, human_tarot_requests, human_tarot_days, "
                    "guest_sessions CASCADE"
                )
            )
        yield database
    finally:
        await database.dispose()


async def test_pg_twenty_guests_race_for_ten_slots(pg: Database) -> None:
    tarot = support.service(pg, Clock(vn(DAY, 7)))
    guests = [await support.guest(pg) for _ in range(20)]
    outcomes = await asyncio.wait_for(
        asyncio.gather(*(support.create(tarot, guest) for guest in guests), return_exceptions=True),
        60,
    )
    assert sum(not isinstance(item, BaseException) for item in outcomes) == 10
    assert sum(isinstance(item, HumanTarotFull) for item in outcomes) == 10
    async with pg.sessions() as session:
        day = await session.get(HumanTarotDayRow, DAY)
        assert day is not None and day.accepted_count == 10
    assert [slot.slot_no for slot in await support.slots(pg)] == list(range(1, 11))


async def test_pg_same_key_from_two_connections_debits_once(pg: Database) -> None:
    tarot = support.service(pg, Clock(vn(DAY, 7)))
    guest = await support.guest(pg)
    first, second = await asyncio.gather(
        support.create(tarot, guest, key="pg-same-key-" * 2),
        support.create(tarot, guest, key="pg-same-key-" * 2),
    )
    assert first.id == second.id
    async with pg.sessions() as session:
        day = await session.get(HumanTarotDayRow, DAY)
        assert day is not None and day.accepted_count == 1


async def test_pg_the_cap_constraint_rejects_an_eleventh_row(pg: Database) -> None:
    async with pg.engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO human_tarot_days (day, accepted_count, intake_closed, created_at) "
                "VALUES (:day, 10, false, now())"
            ),
            {"day": DAY},
        )
    with pytest.raises(Exception, match="ck_human_tarot_day_cap"):
        async with pg.engine.begin() as connection:
            await connection.execute(
                text("UPDATE human_tarot_days SET accepted_count = 11 WHERE day = :day"),
                {"day": DAY},
            )
