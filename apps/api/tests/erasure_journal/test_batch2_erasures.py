"""Deletion journal, batch 2 of the deferred kinds (audit P07, option A).

La Chung invite revoke, response withdraw, result hide and result delete; experiment undo; pending
Radar invite revoke. Each records a keyed digest of the row's own id in the erasure's transaction,
refused or no-op calls record nothing, a failed journal write rolls the erasure back, and replay
re-applies the erasure to a restored copy idempotently. Synthetic SQLite stand-in for a restore: the
database file is copied as the dump.
"""

from __future__ import annotations

import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Database
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.erasure_journal.replay import export_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.experiments.postgres import PostgresExperimentRepository
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.la_chung.models import IdentityMode, RequestStatus
from app.domains.la_chung.service import LaChungService, LaChungUnavailable
from app.domains.la_chung.tables import LaChungRequestRow, LaChungResponseRow
from app.domains.radar.service import RadarService, RadarUnavailable
from app.domains.radar.tables import RadarRequestRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider
from tests.experiments.test_postgres import NOW as EXPERIMENT_NOW
from tests.experiments.test_postgres import _choose, _create_target

NOW = datetime.now(UTC)
HASHER = SecretHasher(b"j" * 32)
JOURNAL = ErasureJournal(HASHER)
# The experiment fixtures encrypt with this key; one envelope serves every repository here.
ENVELOPE = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))
CIPHERTEXT = "synthetic-ciphertext"
SELECTIONS = ("warm-presence", "quiet-courage", "steady-care")
# Each erasure and the name of the row whose own id is its journal subject.
SUBJECTS = {
    ErasureKind.LA_CHUNG_INVITE_REVOKED: "lc_revoke",
    ErasureKind.LA_CHUNG_RESPONSE_WITHDRAWN: "lc_withdraw_response",
    ErasureKind.LA_CHUNG_RESULT_HIDDEN: "lc_hide_response",
    ErasureKind.LA_CHUNG_RESULT_DELETED: "lc_delete",
    ErasureKind.EXPERIMENT_UNDONE: "experiment",
    ErasureKind.RADAR_INVITE_REVOKED: "radar",
}
KINDS = tuple(SUBJECTS)


@pytest.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


def _la_chung(database: Database, journal: ErasureJournal | None = JOURNAL) -> LaChungService:
    return LaChungService(database.sessions, HASHER, ENVELOPE, journal)


def _radar(database: Database, journal: ErasureJournal | None = JOURNAL) -> RadarService:
    # Revoke never touches the birth service or the ephemeris engine.
    return RadarService(
        database.sessions, HASHER, ENVELOPE, cast(Any, None), cast(Any, None),
        erasure_journal=journal,
    )  # fmt: skip


def _experiments(
    database: Database, journal: ErasureJournal | None = JOURNAL
) -> PostgresExperimentRepository:
    return PostgresExperimentRepository(database.sessions, ENVELOPE, journal)


async def _principal(database: Database) -> tuple[UUID, UUID]:
    guest_id, principal_id = uuid4(), uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id, token_hash=uuid4().bytes + uuid4().bytes,
                csrf_hash=uuid4().bytes + uuid4().bytes, state="claimed",
                onboarding_status="birth_ready", created_at=NOW, last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )  # fmt: skip
        await session.flush()
        session.add(PrincipalRow(id=principal_id, source_guest_id=guest_id, created_at=NOW))
    return principal_id, guest_id


async def _invite(service: LaChungService, principal_id: UUID, *, answered: bool) -> dict[str, Any]:
    view, token = await service.create(
        principal_id=principal_id, recipient_label="Bạn tổng hợp", context="friend",
        idempotency_key=uuid4().hex,
    )  # fmt: skip
    if not answered:
        return {"request": view.id}
    result = await service.submit(
        token=token, selections=SELECTIONS, identity_mode=IdentityMode.ANONYMOUS,
        display_alias=None, idempotency_key=uuid4().hex,
    )  # fmt: skip
    return {"request": view.id, "receipt": result.receipt_token}


async def _response_id(database: Database, request_id: UUID) -> UUID:
    async with database.sessions() as session:
        found = await session.scalar(
            select(LaChungResponseRow.id).where(LaChungResponseRow.request_id == request_id)
        )
    assert found is not None
    return found


async def _pending_radar(database: Database, principal_id: UUID, guest_id: UUID) -> UUID:
    request_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            RadarRequestRow(
                id=request_id, principal_id=principal_id, owner_guest_id=guest_id,
                recipient_label_ciphertext="synthetic", context="friend", mode="consented_invite",
                status="pending", token_hash=uuid4().bytes + uuid4().bytes,
                token_ciphertext=CIPHERTEXT, created_at=NOW,
                expires_at=NOW + timedelta(days=7),
            )
        )  # fmt: skip
    return request_id


async def _seed(database: Database) -> dict[str, Any]:
    """One owner with an erasable and a sibling row of every kind; a second guest's experiment."""

    principal_id, guest_id = await _principal(database)
    service = _la_chung(database, None)
    ids: dict[str, Any] = {"principal": principal_id}
    ids["lc_revoke"] = (await _invite(service, principal_id, answered=False))["request"]
    ids["lc_pending_kept"] = (await _invite(service, principal_id, answered=False))["request"]
    for name in ("lc_withdraw", "lc_hide", "lc_delete", "lc_answered_kept"):
        invite = await _invite(service, principal_id, answered=True)
        ids[name] = invite["request"]
        ids[f"{name}_receipt"] = invite["receipt"]
        ids[f"{name}_response"] = await _response_id(database, invite["request"])
    ids["radar"] = await _pending_radar(database, principal_id, guest_id)
    ids["radar_kept"] = await _pending_radar(database, principal_id, guest_id)
    repository = _experiments(database, None)
    for name in ("experiment", "experiment_kept"):
        target = await _create_target(database, ENVELOPE)
        chosen = await _choose(repository, target)
        ids[name], ids[f"{name}_guest"] = chosen.id, target.guest_id
        ids[f"{name}_version"] = chosen.version
    return ids


async def _erase(database: Database, ids: dict[str, Any], journal: ErasureJournal) -> None:
    service = _la_chung(database, journal)
    await service.revoke(ids["principal"], ids["lc_revoke"])
    await service.withdraw(ids["lc_withdraw_receipt"])
    await service.hide_result(ids["principal"], ids["lc_hide"])
    await service.delete_result(ids["principal"], ids["lc_delete"])
    await _radar(database, journal).revoke(ids["principal"], ids["radar"])
    assert await _experiments(database, journal).undo(
        ids["experiment_guest"], experiment_id=ids["experiment"],
        expected_version=ids["experiment_version"], now=EXPERIMENT_NOW,
    )  # fmt: skip


async def _journal(database: Database) -> set[tuple[str, bytes]]:
    async with database.sessions() as session:
        rows = await session.scalars(select(ErasureJournalRow))
        return {(row.kind, row.subject_digest) for row in rows}


async def _state(database: Database, ids: dict[str, Any]) -> dict[str, Any]:
    """Everything an erasure here could change, erased rows and siblings alike."""

    async with database.sessions() as session:
        state: dict[str, Any] = {}
        for name in (
            "lc_revoke", "lc_pending_kept", "lc_withdraw", "lc_hide", "lc_delete",
            "lc_answered_kept",
        ):  # fmt: skip
            row = await session.get(LaChungRequestRow, ids[name])
            state[name] = None if row is None else (row.status, row.token_ciphertext is None)
        for name in ("lc_withdraw", "lc_hide", "lc_delete", "lc_answered_kept"):
            response = await session.get(LaChungResponseRow, ids[f"{name}_response"])
            state[f"{name}_response"] = (
                None
                if response is None
                else (
                    response.withdrawn_at,
                    response.receipt_ciphertext is None,
                    response.hidden_at,
                )
            )
        for name in ("radar", "radar_kept"):
            radar = await session.get(RadarRequestRow, ids[name])
            assert radar is not None
            state[name] = (radar.status, radar.revoked_at, radar.token_ciphertext)
        for name in ("experiment", "experiment_kept"):
            state[name] = await session.get(DailyExperimentRow, ids[name]) is not None
        return state


async def test_each_erasure_records_one_digest_of_its_own_row_id(storage: Database) -> None:
    ids = await _seed(storage)
    before = await _state(storage, ids)
    await _erase(storage, ids, JOURNAL)
    expected = {(kind.value, JOURNAL.digest(kind, ids[name])) for kind, name in SUBJECTS.items()}
    assert await _journal(storage) == expected
    after = await _state(storage, ids)
    for sibling in (
        "lc_pending_kept", "lc_answered_kept", "lc_answered_kept_response", "radar_kept",
        "experiment_kept",
    ):  # fmt: skip
        assert after[sibling] == before[sibling], sibling
    assert after["lc_revoke"] == (RequestStatus.REVOKED.value, True)
    assert after["lc_withdraw"] == (RequestStatus.WITHDRAWN.value, True)
    assert after["lc_delete"] is None and after["lc_delete_response"] is None
    assert after["lc_hide_response"][2] is not None
    assert after["radar"][0] == "revoked" and after["experiment"] is False
    exported = "\n".join(await export_entries(storage.sessions))
    for value in ids.values():
        if isinstance(value, UUID):
            assert str(value) not in exported and value.hex not in exported
        elif isinstance(value, str):
            assert value not in exported  # receipts never reach the journal


async def test_refused_or_no_op_erasures_record_nothing(storage: Database) -> None:
    ids = await _seed(storage)
    stranger, stranger_guest = await _principal(storage)
    service = _la_chung(storage)
    for call in (
        service.revoke(stranger, ids["lc_revoke"]),
        service.hide_result(stranger, ids["lc_hide"]),
        service.delete_result(stranger, ids["lc_delete"]),
        service.withdraw("not-a-receipt-" + uuid4().hex),
    ):
        with pytest.raises(LaChungUnavailable):
            await call
    with pytest.raises(RadarUnavailable):
        await _radar(storage).revoke(stranger, ids["radar"])
    experiments = _experiments(storage)
    assert not await experiments.undo(
        stranger_guest, experiment_id=ids["experiment"],
        expected_version=ids["experiment_version"], now=EXPERIMENT_NOW,
    )  # fmt: skip
    assert not await experiments.undo(
        ids["experiment_guest"], experiment_id=ids["experiment"],
        expected_version=ids["experiment_version"] + 1, now=EXPERIMENT_NOW,
    )  # fmt: skip
    # The owner revoking an answered invite is a no-op: nothing was erased, nothing is recorded.
    await service.revoke(ids["principal"], ids["lc_answered_kept"])
    async with storage.sessions() as session, session.begin():
        radar = await session.get(RadarRequestRow, ids["radar_kept"])
        assert radar is not None
        radar.status = "completed"
    await _radar(storage).revoke(ids["principal"], ids["radar_kept"])
    assert await _journal(storage) == set()


class _FailingJournal(ErasureJournal):
    """The journal write raises inside the erasure's transaction."""

    def record(self, session: AsyncSession, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("synthetic journal failure")


class _UnflushableJournal(ErasureJournal):
    """The journal row is added but cannot be written, so the commit's flush fails."""

    def record(self, session: AsyncSession, *args: Any, **kwargs: Any) -> None:
        session.add(
            ErasureJournalRow(
                kind="broken", subject_digest=cast(Any, None), scope="", occurred_at=NOW
            )
        )


@pytest.mark.parametrize(
    ("journal", "error"),
    [(_FailingJournal(HASHER), RuntimeError), (_UnflushableJournal(HASHER), IntegrityError)],
)
async def test_a_failed_journal_write_rolls_each_erasure_back(
    storage: Database, journal: ErasureJournal, error: type[Exception]
) -> None:
    ids = await _seed(storage)
    before = await _state(storage, ids)
    service = _la_chung(storage, journal)
    for call in (
        service.revoke(ids["principal"], ids["lc_revoke"]),
        service.withdraw(ids["lc_withdraw_receipt"]),
        service.hide_result(ids["principal"], ids["lc_hide"]),
        service.delete_result(ids["principal"], ids["lc_delete"]),
        _radar(storage, journal).revoke(ids["principal"], ids["radar"]),
        _experiments(storage, journal).undo(
            ids["experiment_guest"], experiment_id=ids["experiment"],
            expected_version=ids["experiment_version"], now=EXPERIMENT_NOW,
        ),
    ):  # fmt: skip
        with pytest.raises(error):
            await call
    assert await _state(storage, ids) == before
    assert await _journal(storage) == set()


async def test_restore_then_replay_reapplies_once_and_keeps_everything_else(
    tmp_path: Path,
) -> None:
    live, dump = tmp_path / "live.db", tmp_path / "dump.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    ids = await _seed(database)
    await database.dispose()
    shutil.copyfile(live, dump)

    database = Database(f"sqlite+aiosqlite:///{live}")
    await _erase(database, ids, JOURNAL)
    erased = await _state(database, ids)
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(dump, live)  # the restore brings every erased row back
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        restored = await _state(database, ids)
        assert restored != erased
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert {kind.value: report.applied[kind.value] for kind in KINDS} == dict.fromkeys(
            (kind.value for kind in KINDS), 1
        )
        assert not report.unmatched and not report.reflected
        assert await _state(database, ids) == erased

        again = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert sum(again.reflected.values()) == len(KINDS) and not again.applied

        # Interrupted between applying and recording: the entries are re-applied without effect.
        async with database.sessions() as session, session.begin():
            await session.execute(delete(ErasureJournalRow))
        rerun = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        assert sum(rerun.applied.values()) + sum(rerun.unmatched.values()) == len(KINDS)
        assert await _state(database, ids) == erased
    finally:
        await database.dispose()


async def test_replay_keeps_an_earlier_hide_and_never_crosses_kinds(tmp_path: Path) -> None:
    live, dump = tmp_path / "live.db", tmp_path / "dump.db"
    database = Database(f"sqlite+aiosqlite:///{live}")
    await database.initialize()
    ids = await _seed(database)
    service = _la_chung(database)
    await service.hide_result(ids["principal"], ids["lc_hide"])
    first = (await _state(database, ids))["lc_hide_response"][2]
    # A Radar row that happens to share the deleted La Chung request's id.
    principal_id, guest_id = await _principal(database)
    async with database.sessions() as session, session.begin():
        session.add(
            RadarRequestRow(
                id=ids["lc_delete"], principal_id=principal_id, owner_guest_id=guest_id,
                recipient_label_ciphertext="synthetic", context="friend", mode="consented_invite",
                status="pending", token_hash=uuid4().bytes + uuid4().bytes,
                token_ciphertext=CIPHERTEXT, created_at=NOW,
                expires_at=NOW + timedelta(days=7),
            )
        )  # fmt: skip
    await database.dispose()
    shutil.copyfile(live, dump)  # the snapshot holds the first hide and its entry

    database = Database(f"sqlite+aiosqlite:///{live}")
    service = _la_chung(database)
    await service.hide_result(ids["principal"], ids["lc_hide"])
    await service.delete_result(ids["principal"], ids["lc_delete"])
    exported = await export_entries(database.sessions)
    await database.dispose()

    shutil.copyfile(dump, live)
    database = Database(f"sqlite+aiosqlite:///{live}")
    try:
        report = await replay(database.sessions, JOURNAL, ENVELOPE, exported)
        hidden = ErasureKind.LA_CHUNG_RESULT_HIDDEN.value
        assert report.reflected[hidden] == 1 and report.applied[hidden] == 1
        assert report.applied[ErasureKind.LA_CHUNG_RESULT_DELETED.value] == 1
        state = await _state(database, ids)
        assert state["lc_hide_response"][2] == first
        assert state["lc_delete"] is None
        async with database.sessions() as session:
            twin = await session.get(RadarRequestRow, ids["lc_delete"])
            assert twin is not None and twin.status == "pending"
            assert twin.token_ciphertext == CIPHERTEXT
    finally:
        await database.dispose()
