"""`checked_in_at` follows the order in which saves are written (#627).

Clients apply an answer about a mood only if it is not older than the one they already hold, and
they decide "older" by `checked_in_at`. The request's time is taken before the owner lock, so a
save that arrived first can be written last; the stored time must still say it is the newest.
"""

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.db.session import Database
from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.postgres import PostgresMoodRepository
from tests.history.test_retention import NOW, cipher, note, owner


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'mood-order.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


def _save(
    guest_id: UUID, daily_note_id: UUID, mood: MoodValue, requested_at: datetime
) -> MoodCheckInRecord:
    return MoodCheckInRecord(uuid4(), guest_id, daily_note_id, mood, requested_at)


@pytest.mark.parametrize("encrypt_writes", [False, True])
async def test_a_save_requested_first_but_written_last_is_the_newest(
    storage: Database, encrypt_writes: bool
) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions, cipher(), encrypt_writes=encrypt_writes)
    # Request A was stamped first (it then waited for a connection); request B was stamped later
    # and is written first.
    requested_a = NOW
    requested_b = NOW + timedelta(seconds=2)

    written_b = await moods.upsert(_save(guest_id, daily.id, MoodValue.CHILL, requested_b))
    written_a = await moods.upsert(_save(guest_id, daily.id, MoodValue.DUOI, requested_a))

    # A is what the server holds, and its time says so: newer than B's by at least a millisecond,
    # the precision clients compare with.
    assert written_b.checked_in_at == requested_b
    assert written_a.checked_in_at - written_b.checked_in_at >= timedelta(milliseconds=1)
    found = await moods.find(guest_id, daily.id)
    assert found is not None
    assert found.mood is MoodValue.DUOI
    assert found.checked_in_at == written_a.checked_in_at


async def test_saves_with_the_same_request_time_still_get_increasing_times(
    storage: Database,
) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions, cipher())
    times = [
        (await moods.upsert(_save(guest_id, daily.id, mood, NOW))).checked_in_at
        for mood in (MoodValue.CHILL, MoodValue.DUOI, MoodValue.RUC)
    ]
    assert times[0] == NOW
    assert times[1] - times[0] >= timedelta(milliseconds=1)
    assert times[2] - times[1] >= timedelta(milliseconds=1)


async def test_a_later_request_keeps_its_own_time_and_other_notes_are_not_touched(
    storage: Database,
) -> None:
    guest_id = await owner(storage)
    first = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions, cipher())
    await moods.upsert(_save(guest_id, first.id, MoodValue.CHILL, NOW))
    later = NOW + timedelta(minutes=5)
    changed = await moods.upsert(_save(guest_id, first.id, MoodValue.DUOI, later))
    assert changed.checked_in_at == later

    other_guest = await owner(storage)
    other = await note(storage, other_guest, NOW)
    fresh = await moods.upsert(_save(other_guest, other.id, MoodValue.RUC, NOW))
    assert fresh.checked_in_at == NOW
