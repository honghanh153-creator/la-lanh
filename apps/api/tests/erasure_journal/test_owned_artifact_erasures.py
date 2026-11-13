"""Deletion journal, batch 1 of the deferred kinds (audit P07, option A).

Tarot session delete, share-link revoke and saved-note unsave. Each records a keyed digest of the
row's own id in the erasure's transaction, and replay re-applies it to a restored copy. Synthetic
SQLite stand-in for a restore: the database file is copied as the dump.
"""

from __future__ import annotations

import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.session import Database
from app.domains.daily.models import DailyNoteRecord
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.erasure_journal.replay import export_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from app.domains.tarot.errors import TarotSessionNotFound
from app.domains.tarot.service import TarotSessionService
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

NOW = datetime.now(UTC)
OLD = NOW - timedelta(days=3)
HASHER = SecretHasher(b"j" * 32)
JOURNAL = ErasureJournal(HASHER)
ENVELOPE = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"h" * 32))
KINDS = (
    ErasureKind.TAROT_SESSION_DELETED,
    ErasureKind.SHARE_REVOKED,
    ErasureKind.SAVED_NOTE_REMOVED,
)


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def _guest(database: Database) -> UUID:
    guest_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id, token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes, state="active",
                onboarding_status="birth_ready", created_at=OLD, last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )  # fmt: skip
    return guest_id


async def _note(database: Database, guest_id: UUID, day: int) -> UUID:
    record = await PostgresDailyNoteRepository(database.sessions, ENVELOPE).get_or_create(
        DailyNoteRecord(
            id=uuid4(), guest_id=guest_id, note_date=(OLD - timedelta(days=day)).date(),
            title="synthetic", body="private", context_label="test", content_version="test",
            chart_snapshot_id=None, created_at=OLD,
        )
    )  # fmt: skip
    return record.id


async def _seed(database: Database) -> dict[str, UUID]:
    """One guest with two of each artifact: one to erase, one that must stay."""

    guest_id = await _guest(database)
    ids = {"guest": guest_id}
    async with database.sessions() as session, session.begin():
        for name in ("tarot", "tarot_kept"):
            ids[name] = uuid4()
            session.add(
                TarotSessionRow(
                    id=ids[name], guest_id=guest_id, state="completed", context="general",
                    spread="one_card", voice="calm", origin="question",
                    idempotency_hash=uuid4().bytes + uuid4().bytes,
                    payload_ciphertext="synthetic-ciphertext", created_at=OLD, updated_at=OLD,
                    expires_at=NOW + timedelta(days=30),
                )
            )  # fmt: skip
    for day, name in enumerate(("note", "note_kept")):
        ids[name] = await _note(database, guest_id, day)
    async with database.sessions() as session, session.begin():
        for name, note in (("share", "note"), ("share_kept", "note_kept")):
            ids[name] = uuid4()
            session.add(
                ShareArtifactRow(
                    id=ids[name], guest_id=guest_id, daily_note_id=ids[note],
                    token_hash=uuid4().bytes + uuid4().bytes, safe_snapshot={},
                    format="story_9_16", created_at=OLD, expires_at=NOW + timedelta(days=7),
                )
            )  # fmt: skip
        for name, note in (("saved", "note"), ("saved_kept", "note_kept")):
            ids[name] = uuid4()
            session.add(
                SavedNoteRow(
                    id=ids[name], guest_id=guest_id, daily_note_id=ids[note], note_snapshot={},
                    saved_at=OLD,
                )
            )  # fmt: skip
    return ids


async def _erase(database: Database, ids: dict[str, UUID], at: datetime) -> None:
    sessions = database.sessions
    tarot = TarotSessionService(sessions, ENVELOPE, HASHER, erasure_journal=JOURNAL)
    await tarot.delete(ids["guest"], ids["tarot"])
    shares = PostgresShareArtifactRepository(sessions, ENVELOPE, JOURNAL)
    assert await shares.revoke_owned(ids["guest"], ids["share"], at)
    saved = PostgresSavedNoteRepository(sessions, ENVELOPE, JOURNAL)
    assert await saved.delete(ids["guest"], ids["note"])


async def _journal(database: Database) -> set[tuple[str, bytes]]:
    async with database.sessions() as session:
        rows = await session.scalars(select(ErasureJournalRow))
        return {(row.kind, row.subject_digest) for row in rows}


async def test_each_erasure_records_one_digest_of_the_row_id(storage: Database) -> None:
    ids = await _seed(storage)
    await _erase(storage, ids, NOW)
    expected = {
        (kind.value, JOURNAL.digest(kind, ids[name]))
        for kind, name in zip(KINDS, ("tarot", "share", "saved"), strict=True)
    }
    assert await _journal(storage) == expected
    exported = "\n".join(await export_entries(storage.sessions))
    for subject in ids.values():
        assert str(subject) not in exported and subject.hex not in exported


async def test_a_refused_erasure_records_nothing(storage: Database) -> None:
    ids = await _seed(storage)
    other = await _guest(storage)
    sessions = storage.sessions
    with pytest.raises(TarotSessionNotFound):
        await TarotSessionService(sessions, ENVELOPE, HASHER, erasure_journal=JOURNAL).delete(
            other, ids["tarot"]
        )
    assert not await PostgresShareArtifactRepository(sessions, ENVELOPE, JOURNAL).revoke_owned(
        other, ids["share"], NOW
    )
    assert not await PostgresSavedNoteRepository(sessions, ENVELOPE, JOURNAL).delete(
        other, ids["note"]
    )
    assert await _journal(storage) == set()


async def test_restore_then_replay_reapplies_and_keeps_everything_else(tmp_path: Path) -> None:
    live, dump = tmp_path / "live.db", tmp_path / "dump.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    ids = await _seed(database)
    await database.dispose()
    shutil.copyfile(live, dump)

    database = Database(f"sqlite+aiosqlite:///{live}")
    revoked_at = datetime.now(UTC)
    await _erase(database, ids, revoked_at)
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(dump, live)  # the restore brings all three back
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        async with database.sessions() as session:
            assert await session.get(TarotSessionRow, ids["tarot"]) is not None
            assert await session.get(SavedNoteRow, ids["saved"]) is not None
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert {kind.value: report.applied[kind.value] for kind in KINDS} == dict.fromkeys(
            (kind.value for kind in KINDS), 1
        )
        assert not report.unmatched and not report.reflected
        async with database.sessions() as session:
            assert await session.get(TarotSessionRow, ids["tarot"]) is None
            assert await session.get(TarotSessionRow, ids["tarot_kept"]) is not None
            share = await session.get(ShareArtifactRow, ids["share"])
            assert share is not None and share.revoked_at == revoked_at
            kept = await session.get(ShareArtifactRow, ids["share_kept"])
            assert kept is not None and kept.revoked_at is None
            assert await session.get(SavedNoteRow, ids["saved"]) is None
            assert await session.get(SavedNoteRow, ids["saved_kept"]) is not None
        again = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert sum(again.reflected.values()) == 3 and not again.applied
    finally:
        await database.dispose()


async def test_replay_keeps_an_earlier_revocation_and_misses_rows_created_later(
    tmp_path: Path,
) -> None:
    live, dump = tmp_path / "live.db", tmp_path / "dump.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    ids = await _seed(database)
    shares = PostgresShareArtifactRepository(database.sessions, ENVELOPE, JOURNAL)
    first = OLD + timedelta(hours=1)
    assert await shares.revoke_owned(ids["guest"], ids["share"], first)
    await database.dispose()
    shutil.copyfile(live, dump)  # the snapshot holds the first revocation and its entry

    database = Database(f"sqlite+aiosqlite:///{live}")
    shares = PostgresShareArtifactRepository(database.sessions, ENVELOPE, JOURNAL)
    assert await shares.revoke_owned(ids["guest"], ids["share"], NOW)
    saved = PostgresSavedNoteRepository(database.sessions, ENVELOPE, JOURNAL)
    assert await saved.delete(ids["guest"], ids["note"])
    async with database.sessions() as session, session.begin():
        # Saved again after the dump: a new row the restored copy never had.
        session.add(
            SavedNoteRow(
                guest_id=ids["guest"], daily_note_id=ids["note"], note_snapshot={}, saved_at=NOW
            )
        )
    assert await saved.delete(ids["guest"], ids["note"])
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(dump, live)
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert report.reflected[ErasureKind.SHARE_REVOKED.value] == 1
        assert report.applied[ErasureKind.SHARE_REVOKED.value] == 1
        assert report.applied[ErasureKind.SAVED_NOTE_REMOVED.value] == 1
        assert report.unmatched[ErasureKind.SAVED_NOTE_REMOVED.value] == 1
        async with database.sessions() as session:
            share = await session.get(ShareArtifactRow, ids["share"])
            assert share is not None and share.revoked_at == first
            assert await session.get(SavedNoteRow, ids["saved"]) is None
    finally:
        await database.dispose()
