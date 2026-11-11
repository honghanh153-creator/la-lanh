"""Mood check-ins are stored encrypted (gap register PV-26); legacy plain rows keep working."""

from collections.abc import AsyncIterator
from importlib import import_module
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from cryptography.exceptions import InvalidTag

from app.db.session import Database
from app.domains.mood.models import MoodCheckInRecord, MoodValue
from app.domains.mood.postgres import PostgresMoodRepository
from app.domains.mood.tables import MoodCheckInRow
from tests.history.test_retention import NOW, cipher, note, owner

MIGRATION = "migrations.versions.20261111_0042_encrypt_mood_check_ins"


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'mood.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def test_new_check_in_stores_no_plain_mood_and_round_trips(storage: Database) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    moods = PostgresMoodRepository(storage.sessions, cipher())
    saved = await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.LAC_TROI,
            checked_in_at=NOW,
        )
    )
    async with storage.sessions() as session:
        row = await session.get(MoodCheckInRow, saved.id)
        assert row is not None
        assert row.mood is None
        assert row.mood_ciphertext is not None
        assert row.mood_ciphertext.startswith("aesgcm:")
        assert MoodValue.LAC_TROI.value not in row.mood_ciphertext
    found = await moods.find(guest_id, daily.id)
    assert found is not None and found.mood is MoodValue.LAC_TROI

    changed = await moods.upsert(
        MoodCheckInRecord(
            id=uuid4(),
            guest_id=guest_id,
            daily_note_id=daily.id,
            mood=MoodValue.RUC,
            checked_in_at=NOW,
        )
    )
    assert changed.id == saved.id and changed.mood is MoodValue.RUC
    found = await moods.find(guest_id, daily.id)
    assert found is not None and found.mood is MoodValue.RUC


async def test_ciphertext_is_bound_to_its_row(storage: Database) -> None:
    first_guest, second_guest = await owner(storage), await owner(storage)
    first = await note(storage, first_guest, NOW)
    second = await note(storage, second_guest, NOW)
    moods = PostgresMoodRepository(storage.sessions, cipher())
    a = await moods.upsert(MoodCheckInRecord(uuid4(), first_guest, first.id, MoodValue.CHILL, NOW))
    b = await moods.upsert(MoodCheckInRecord(uuid4(), second_guest, second.id, MoodValue.CANG, NOW))
    assert a.id != b.id
    async with storage.sessions() as session, session.begin():
        row_a = await session.get(MoodCheckInRow, a.id)
        row_b = await session.get(MoodCheckInRow, b.id)
        assert row_a is not None and row_b is not None
        row_b.mood_ciphertext = row_a.mood_ciphertext  # copied envelope must not decrypt
    with pytest.raises(InvalidTag):
        await moods.find(second_guest, second.id)


async def test_legacy_plain_row_stays_readable_and_is_encrypted_on_next_change(
    storage: Database,
) -> None:
    guest_id = await owner(storage)
    daily = await note(storage, guest_id, NOW)
    legacy_id = uuid4()
    async with storage.sessions() as session, session.begin():
        session.add(
            MoodCheckInRow(
                id=legacy_id,
                guest_id=guest_id,
                daily_note_id=daily.id,
                mood=MoodValue.DUOI.value,
                mood_ciphertext=None,
                checked_in_at=NOW,
                created_at=NOW,
            )
        )
    moods = PostgresMoodRepository(storage.sessions, cipher())
    found = await moods.find(guest_id, daily.id)
    assert found is not None and found.mood is MoodValue.DUOI

    await moods.upsert(MoodCheckInRecord(uuid4(), guest_id, daily.id, MoodValue.CHILL, NOW))
    async with storage.sessions() as session:
        row = await session.get(MoodCheckInRow, legacy_id)
        assert row is not None and row.mood is None and row.mood_ciphertext is not None
    found = await moods.find(guest_id, daily.id)
    assert found is not None and found.mood is MoodValue.CHILL


def test_migration_adds_ciphertext_and_relaxes_plain_column() -> None:
    migration = import_module(MIGRATION)
    assert migration.down_revision == "20261030_0041"
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context):
        migration.upgrade()
    sql = output.getvalue()
    assert "ALTER TABLE mood_check_ins ADD COLUMN mood_ciphertext TEXT" in sql
    assert "ALTER TABLE mood_check_ins ALTER COLUMN mood DROP NOT NULL" in sql
    assert "UPDATE" not in sql and "DELETE" not in sql


@pytest.mark.parametrize("encrypted_rows", [0, 2])
def test_migration_downgrade_never_drops_encrypted_moods(encrypted_rows: int) -> None:
    migration = import_module(MIGRATION)
    bind = MagicMock()
    bind.scalar.return_value = encrypted_rows
    with (
        patch.object(migration.op, "get_bind", return_value=bind),
        patch.object(migration.op, "alter_column") as alter,
        patch.object(migration.op, "drop_column") as drop,
    ):
        if encrypted_rows:
            with pytest.raises(RuntimeError, match="key-aware"):
                migration.downgrade()
            alter.assert_not_called()
            drop.assert_not_called()
        else:
            migration.downgrade()
            assert alter.call_args.kwargs["nullable"] is False
            drop.assert_called_once_with("mood_check_ins", "mood_ciphertext")
