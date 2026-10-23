"""Deletion journal (audit P07, option A): record, export, restore, import, replay.

Synthetic SQLite stand-in for a restore: the database file is copied as the "backup", erasures
happen afterwards, the copy is put back, the exported journal is imported and replayed.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import Database
from app.domains.birth.models import BirthSupplement, BirthTimeMode
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.tables import BirthProfileRow
from app.domains.daily.models import DailyNoteRecord
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.tables import DailyNoteRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.erasure_journal.replay import (
    export_entries,
    import_entries,
    purge_entries,
    replay,
)
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.history.postgres import PostgresHistoryRepository, activate_policy
from app.domains.identity.tables import PrincipalRow
from app.domains.matching.postgres import PostgresMatchingRepository
from app.domains.matching.tables import MatchingConsentRow
from app.domains.radar.service import RadarService
from app.domains.radar.tables import RadarRequestRow
from app.domains.resonance.postgres import RESONANCE_PURPOSE, PostgresResonanceRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

NOW = datetime.now(UTC)
OLD = NOW - timedelta(days=3)
PURPOSE = "content_rewrite_personal"
HASHER = SecretHasher(b"j" * 32)
JOURNAL = ErasureJournal(HASHER)
RECEIPT = "synthetic-receipt-token"
ENVELOPE = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"h" * 32))


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def _guest(database: Database, token_hash: bytes | None = None) -> UUID:
    guest_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=token_hash or uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes,
                state="active",
                onboarding_status="birth_ready",
                created_at=OLD,
                last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )
        await session.flush()
        session.add(ConsentRow(guest_id=guest_id, version="v1", purpose=PURPOSE, accepted_at=OLD))
        session.add(
            ConsentRow(guest_id=guest_id, version="v1", purpose=RESONANCE_PURPOSE, accepted_at=OLD)
        )
        session.add(
            BirthProfileRow(
                guest_id=guest_id,
                profile_level=3,
                time_precision="exact",
                birth_time_ciphertext="synthetic-time",
                birth_place_ciphertext="synthetic-place",
                created_at=OLD,
                updated_at=OLD,
            )
        )
        await activate_policy(session, guest_id, OLD)
    return guest_id


async def _note(database: Database, guest_id: UUID) -> UUID:
    record = await PostgresDailyNoteRepository(database.sessions, ENVELOPE).get_or_create(
        DailyNoteRecord(
            id=uuid4(), guest_id=guest_id, note_date=OLD.date(), title="synthetic",
            body="private", context_label="test", content_version="test",
            chart_snapshot_id=None, created_at=OLD,
        )
    )  # fmt: skip
    return record.id


async def _principal(database: Database, guest_id: UUID) -> UUID:
    principal_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(PrincipalRow(id=principal_id, source_guest_id=guest_id, created_at=OLD))
        await session.flush()
        session.add(
            MatchingConsentRow(
                principal_id=principal_id, version="v1", purpose="matching", accepted_at=OLD
            )
        )
    return principal_id


async def _radar(
    database: Database, principal_id: UUID, guest_id: UUID, receipt: str | None = None
) -> UUID:
    request_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            RadarRequestRow(
                id=request_id, principal_id=principal_id, owner_guest_id=guest_id,
                recipient_label_ciphertext="synthetic", context="friend", mode="consented_invite",
                status="completed", result_ciphertext="synthetic-result",
                receipt_ciphertext="synthetic-receipt", created_at=OLD, completed_at=NOW,
                receipt_hash=HASHER.digest("radar-receipt", receipt) if receipt else None,
                expires_at=NOW + timedelta(days=30),
            )
        )  # fmt: skip
    return request_id


async def _erase_everything(
    database: Database, ids: dict[str, UUID], token: bytes, at: datetime = NOW
) -> None:
    """Eight explicit erasures through their real repositories, each with the journal."""

    sessions = database.sessions
    guests = PostgresGuestRepository(sessions, erasure_journal=JOURNAL)
    await PostgresHistoryRepository(sessions, ENVELOPE, JOURNAL).clear(ids["history"], at)
    await guests.revoke_consent(ids["consent"], PURPOSE, at)
    await PostgresResonanceRepository(sessions, ENVELOPE, JOURNAL).clear_with_consent(
        ids["consent"], revoke_consent=True, now=at
    )
    birth = PostgresBirthRepository(sessions, ENVELOPE, JOURNAL)
    await birth.clear_supplement(ids["birth"], remove_time=True, remove_place=False)
    await PostgresMatchingRepository(sessions, ENVELOPE, JOURNAL).withdraw_consent(
        ids["principal"], now=at
    )
    # Delete and withdraw never touch the birth service or the ephemeris engine.
    radar = RadarService(
        sessions, HASHER, ENVELOPE, cast(Any, None), cast(Any, None), erasure_journal=JOURNAL
    )
    await radar.delete(ids["principal"], ids["radar_deleted"])
    await radar.withdraw(RECEIPT, expected_request_id=ids["radar_withdrawn"])
    assert await guests.delete_by_token_hash(token, at)


async def _seed(database: Database) -> tuple[dict[str, UUID], bytes]:
    token = uuid4().bytes + uuid4().bytes
    ids = {
        "erased": await _guest(database, token),
        "history": await _guest(database),
        "consent": await _guest(database),
        "birth": await _guest(database),
        "owner": await _guest(database),
    }
    ids["note"] = await _note(database, ids["history"])
    ids["principal"] = await _principal(database, ids["owner"])
    ids["radar_deleted"] = await _radar(database, ids["principal"], ids["owner"])
    ids["radar_withdrawn"] = await _radar(database, ids["principal"], ids["owner"], RECEIPT)
    return ids, token


async def test_each_explicit_erasure_records_one_pseudonymous_entry(storage: Database) -> None:
    ids, token = await _seed(storage)
    await _erase_everything(storage, ids, token)
    async with storage.sessions() as session:
        rows = list(await session.scalars(select(ErasureJournalRow)))
    found = {(row.kind, row.subject_digest, row.scope) for row in rows}
    expected = {
        (ErasureKind.HISTORY_CLEARED, ids["history"], ""),
        (ErasureKind.CONSENT_REVOKED, ids["consent"], PURPOSE),
        (ErasureKind.RESONANCE_CLEARED, ids["consent"], "consent"),
        (ErasureKind.BIRTH_SUPPLEMENT_REMOVED, ids["birth"], "time"),
        (ErasureKind.MATCHING_CONSENT_WITHDRAWN, ids["principal"], ""),
        (ErasureKind.RADAR_DELETED, ids["radar_deleted"], ""),
        (ErasureKind.RADAR_WITHDRAWN, ids["radar_withdrawn"], ""),
        (ErasureKind.GUEST_ERASED, ids["erased"], ""),
    }
    assert found == {
        (kind.value, JOURNAL.digest(kind, subject), scope) for kind, subject, scope in expected
    }
    exported = "\n".join(await export_entries(storage.sessions))
    for subject in ids.values():
        assert str(subject) not in exported and subject.hex not in exported
    assert all(set(json.loads(line)) == {"kind", "subject_digest", "scope", "occurred_at"}
               for line in exported.splitlines())  # fmt: skip


async def test_digests_are_keyed_and_separated_by_kind() -> None:
    subject = uuid4()
    other_key = ErasureJournal(SecretHasher(b"k" * 32))
    assert JOURNAL.digest(ErasureKind.GUEST_ERASED, subject) != other_key.digest(
        ErasureKind.GUEST_ERASED, subject
    )
    assert JOURNAL.digest(ErasureKind.GUEST_ERASED, subject) != JOURNAL.digest(
        ErasureKind.HISTORY_CLEARED, subject
    )


async def test_restore_then_replay_reapplies_every_post_backup_erasure(tmp_path: Path) -> None:
    live, backup = tmp_path / "live.db", tmp_path / "backup.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    ids, token = await _seed(database)
    await database.dispose()
    shutil.copyfile(live, backup)  # the dump
    dumped_at = datetime.now(UTC)

    database = Database(f"sqlite+aiosqlite:///{live}")
    await _erase_everything(database, ids, token, datetime.now(UTC))
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(backup, live)  # the restore: every erasure above is undone
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        async with database.sessions() as session:
            assert await session.get(GuestSessionRow, ids["erased"]) is not None
            assert await session.get(RadarRequestRow, ids["radar_deleted"]) is not None
        assert await import_entries(database.sessions, exported) == len(exported)
        report = await replay(database.sessions, JOURNAL, ENVELOPE, since=dumped_at)
        assert sum(report.applied.values()) == 8 and not report.unmatched
        await PostgresGuestRepository(database.sessions).purge_expired(NOW, 500)  # option C step

        async with database.sessions() as session:
            assert await session.get(GuestSessionRow, ids["erased"]) is None
            assert await session.get(DailyNoteRow, ids["note"]) is None
            consents = {
                (row.guest_id, row.purpose): row.revoked_at
                for row in await session.scalars(select(ConsentRow))
            }
            assert consents[(ids["consent"], PURPOSE)] is not None
            assert consents[(ids["consent"], RESONANCE_PURPOSE)] is not None
            assert consents[(ids["history"], PURPOSE)] is None
            profile = await session.scalar(
                select(BirthProfileRow).where(BirthProfileRow.guest_id == ids["birth"])
            )
            assert profile is not None and profile.birth_time_ciphertext is None
            assert profile.birth_place_ciphertext == "synthetic-place"
            matching = await session.scalar(
                select(MatchingConsentRow).where(
                    MatchingConsentRow.principal_id == ids["principal"]
                )
            )
            assert matching is not None and matching.revoked_at is not None
            assert await session.get(RadarRequestRow, ids["radar_deleted"]) is None
            withdrawn = await session.get(RadarRequestRow, ids["radar_withdrawn"])
            assert withdrawn is not None and withdrawn.status == "withdrawn"
            assert withdrawn.result_ciphertext is None and withdrawn.receipt_ciphertext is None
            journal_rows = await session.scalar(select(func.count()).select_from(ErasureJournalRow))

        # Idempotent, and replay itself journals nothing new.
        again = await replay(database.sessions, JOURNAL, ENVELOPE, since=dumped_at)
        assert sum(again.applied.values()) + sum(again.unmatched.values()) == 8
        async with database.sessions() as session:
            assert await session.scalar(select(func.count()).select_from(ErasureJournalRow)) == (
                journal_rows
            )
        assert await import_entries(database.sessions, exported) == 0
    finally:
        await database.dispose()


async def test_entries_at_or_before_the_dump_are_not_replayed(storage: Database) -> None:
    guest_id = await _guest(storage)
    note_id = await _note(storage, guest_id)
    async with storage.sessions() as session, session.begin():
        JOURNAL.record(session, ErasureKind.HISTORY_CLEARED, guest_id, OLD - timedelta(days=1))
    report = await replay(storage.sessions, JOURNAL, ENVELOPE, since=OLD)
    assert not report.entries
    async with storage.sessions() as session:
        assert await session.get(DailyNoteRow, note_id) is not None


async def test_import_fails_closed_and_purge_keeps_recent_entries(storage: Database) -> None:
    good = {
        "kind": "guest_erased",
        "subject_digest": "ab" * 32,
        "scope": "",
        "occurred_at": NOW.isoformat(),
    }
    with pytest.raises(ValueError):
        await import_entries(storage.sessions, [json.dumps({**good, "kind": "unknown"})])
    with pytest.raises(ValueError):
        await import_entries(storage.sessions, [json.dumps({**good, "subject_digest": "ab"})])
    old = {**good, "occurred_at": (NOW - timedelta(days=20)).isoformat()}
    assert await import_entries(storage.sessions, [json.dumps(good), json.dumps(old)]) == 2
    assert await purge_entries(storage.sessions, before=NOW - timedelta(days=15)) == 1
    assert len(await export_entries(storage.sessions)) == 1


async def test_switching_to_an_unknown_time_is_journaled_and_replayed(storage: Database) -> None:
    guest_id = await _guest(storage)
    birth = PostgresBirthRepository(storage.sessions, ENVELOPE, JOURNAL)
    await birth.save_supplement(
        guest_id,
        None,
        BirthSupplement(
            birth_time_mode=BirthTimeMode.UNKNOWN, birth_time_ciphertext=None,
            approx_window=None, birth_place_ciphertext="synthetic-place", consent_version="v1",
        ),
        expected_snapshot_id=None,  # type: ignore[arg-type]
        expected_updated_at=OLD,
    )  # fmt: skip
    async with storage.sessions() as session:
        row = await session.scalar(select(ErasureJournalRow))
        assert row is not None and row.kind == ErasureKind.BIRTH_TIME_DOWNGRADED.value
        assert row.subject_digest == JOURNAL.digest(ErasureKind.BIRTH_TIME_DOWNGRADED, guest_id)
        profile = await session.scalar(
            select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
        )
        assert profile is not None
        # Stand-in for the restored copy: the precise time is back.
    async with storage.sessions() as session, session.begin():
        restored = await session.scalar(
            select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
        )
        assert restored is not None
        restored.birth_time_ciphertext, restored.time_precision = "synthetic-time", "exact"
    report = await replay(storage.sessions, JOURNAL, ENVELOPE, since=OLD)
    assert report.applied[ErasureKind.BIRTH_TIME_DOWNGRADED.value] == 1
    async with storage.sessions() as session:
        profile = await session.scalar(
            select(BirthProfileRow).where(BirthProfileRow.guest_id == guest_id)
        )
        assert profile is not None and profile.birth_time_ciphertext is None
        assert profile.time_precision == "unknown"
        assert profile.birth_place_ciphertext == "synthetic-place"
