"""US-24 reads (server-clock release, owner only) and every erasure path of the new data."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from sqlalchemy import delete

from app.db.session import Database
from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.replay import replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.postgres import PostgresHistoryRepository
from app.domains.human_tarot import policy
from app.domains.human_tarot.errors import HumanTarotNotFound
from app.domains.human_tarot.models import VisibleStatus
from app.domains.human_tarot.tables import HumanTarotRequestRow, HumanTarotSlotRow
from tests.human_tarot import support
from tests.human_tarot.support import DAY, JOURNAL, QUESTION, Clock, vn


async def test_ac08_the_reading_opens_at_22_by_the_server_clock(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    await support.freeze(database, tarot, view.id, vn(DAY, 19))
    clock.moment = vn(DAY, 21, 59, 59)
    before = await tarot.get(guest, view.id)
    assert before.status is VisibleStatus.WAITING and before.result is None
    assert before.question == QUESTION
    clock.moment = vn(DAY, 22)
    after = await tarot.get(guest, view.id)
    assert after.status is VisibleStatus.READY and after.result is not None
    assert after.result.reader == "human"
    assert [item.card.id for item in after.result.cards] == ["major-star", "cups-5", "wands-ace"]
    assert after.result.cards[0].position_label == "Điều đã rõ"
    assert (await tarot.current(guest)).id == view.id


async def test_ac09_another_guest_sees_nothing(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 8)))
    owner, other = await support.guest(database), await support.guest(database)
    view = await support.create(tarot, owner)
    with pytest.raises(HumanTarotNotFound):
        await tarot.get(other, view.id)
    with pytest.raises(HumanTarotNotFound):
        await tarot.cancel(other, view.id)
    with pytest.raises(HumanTarotNotFound):
        await tarot.current(other)
    assert (await tarot.get(owner, view.id)).status is VisibleStatus.WAITING


async def test_ac10_late_then_unfulfilled_without_any_machine_reading(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    clock.moment = vn(DAY, 22, 30)
    late = await tarot.get(guest, view.id)
    assert late.status is VisibleStatus.LATE and late.result is None
    clock.moment = vn(DAY + timedelta(days=1), 0, 0, 1)
    shown = await tarot.get(guest, view.id)
    assert shown.status is VisibleStatus.UNFULFILLED and shown.question is None
    counts = await tarot.finalize_and_purge()
    assert counts["unfulfilled"] == 1 and counts["clear_due"] == 1
    row = await support.request_row(database, view.id)
    assert row is not None and row.payload_ciphertext is None and row.status == "unfulfilled"
    slot = await support.slot_for(database, view.id)
    assert slot is not None and slot.sheet_state == "clear_due"


async def test_ac11_provenance_is_stored_with_the_frozen_reading(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    await support.freeze(database, tarot, view.id, vn(DAY, 19))
    row = await support.request_row(database, view.id)
    assert row is not None
    payload = tarot.decrypt(row)
    assert payload["result"]["reader"] == policy.READER
    assert payload["result"]["schema"] == policy.RESULT_SCHEMA
    assert payload["result"]["imported_at"]


async def test_payload_is_encrypted_and_bound_to_the_request(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 8)))
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    row = await support.request_row(database, view.id)
    assert row is not None and row.payload_ciphertext is not None
    assert QUESTION not in row.payload_ciphertext
    assert "nhận thêm việc" not in json.dumps(
        {key: str(value) for key, value in vars(row).items() if not key.startswith("_")}
    ).replace(row.payload_ciphertext, "")


async def test_ac19_cancel_blocks_reading_and_tracks_the_sheet_copy(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    await support.freeze(database, tarot, view.id, vn(DAY, 19))
    async with database.sessions() as session, session.begin():
        slot = await session.get(HumanTarotSlotRow, (await support.slot_for(database, view.id)).id)  # type: ignore[union-attr]
        assert slot is not None
        slot.sheet_state = "on_sheet"
    await tarot.cancel(guest, view.id)
    await tarot.cancel(guest, view.id)  # idempotent
    clock.moment = vn(DAY, 23)
    cancelled = await tarot.get(guest, view.id)
    assert cancelled.status is VisibleStatus.CANCELLED
    assert cancelled.result is None and cancelled.question is None
    assert cancelled.copy_cleared is False
    slot_after = await support.slot_for(database, view.id)
    assert slot_after is not None and slot_after.sheet_state == "clear_due"
    async with database.sessions() as session:
        entries = list(
            await session.scalars(
                ErasureJournalRow.__table__.select().where(
                    ErasureJournalRow.kind == ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED.value
                )
            )
        )
    assert len(entries) == 1
    # Once the bridge confirms the cleared row the receipt says so.
    async with database.sessions() as session, session.begin():
        slot = await session.get(HumanTarotSlotRow, slot_after.id)
        assert slot is not None
        slot.sheet_state = "cleared"
    assert (await tarot.get(guest, view.id)).copy_cleared is True


async def test_question_is_purged_a_day_after_release_and_the_reading_after_thirty(
    database: Database,
) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    await support.freeze(database, tarot, view.id, vn(DAY, 19))
    clock.moment = vn(DAY, 22) + policy.QUESTION_KEPT_AFTER_RELEASE
    assert (await tarot.get(guest, view.id)).question is None
    counts = await tarot.finalize_and_purge()
    assert counts["questions_purged"] == 1
    row = await support.request_row(database, view.id)
    assert row is not None
    payload = tarot.decrypt(row)
    assert "question" not in payload and "result" in payload
    assert (await tarot.get(guest, view.id)).result is not None
    clock.moment = vn(DAY, 22) + policy.RESULT_KEPT_AFTER_RELEASE
    counts = await tarot.finalize_and_purge()
    assert counts["expired"] == 1
    assert await support.request_row(database, view.id) is None
    # The request is gone; its slot keeps the day's count and lost its link.
    (slot,) = await support.slots(database)
    assert slot.request_id is None and slot.guest_id == guest


async def test_ac21_guest_deletion_removes_the_request_and_queues_the_sheet_clear(
    database: Database,
) -> None:
    tarot = support.service(database, Clock(vn(DAY, 8)))
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest))
    assert await support.request_row(database, view.id) is None
    (slot,) = await support.slots(database)
    assert slot.request_id is None and slot.guest_id is None
    counts = await tarot.finalize_and_purge()
    assert counts["clear_due"] == 1
    (slot,) = await support.slots(database)
    assert slot.sheet_state == "clear_due"


async def test_ac21_manual_history_clear_removes_finished_requests_only(
    database: Database,
) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    finished, waiting = await support.guest(database), await support.guest(database)
    done = await support.create(tarot, finished)
    pending = await support.create(tarot, waiting)
    await support.freeze(database, tarot, done.id, vn(DAY, 19))
    history = PostgresHistoryRepository(database.sessions, support.CIPHER, JOURNAL)
    await history.clear(finished, vn(DAY, 23))
    await history.clear(waiting, vn(DAY, 21, 30))
    assert await support.request_row(database, done.id) is None
    assert await support.request_row(database, pending.id) is not None


async def test_ac21_journal_replay_cancels_a_restored_request(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    occurred = vn(DAY, 8, 30)
    line = json.dumps(
        {
            "kind": ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED.value,
            "subject_digest": JOURNAL.digest(
                ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED, view.id
            ).hex(),
            "scope": "",
            "occurred_at": occurred.isoformat(),
        }
    )
    report = await replay(database.sessions, JOURNAL, support.CIPHER, [line])
    assert report.applied[ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED.value] == 1
    row = await support.request_row(database, view.id)
    assert row is not None and row.status == "cancelled" and row.payload_ciphertext is None
    slot = await support.slot_for(database, view.id)
    assert slot is not None and slot.sheet_state == "clear_due"
    again = await replay(database.sessions, JOURNAL, support.CIPHER, [line])
    assert again.reflected[ErasureKind.HUMAN_TAROT_REQUEST_CANCELLED.value] == 1


async def test_slots_and_day_tallies_are_purged_after_their_window(database: Database) -> None:
    clock = Clock(vn(DAY, 8))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    await tarot.cancel(guest, view.id)
    async with database.sessions() as session, session.begin():
        slot = await session.get(HumanTarotSlotRow, (await support.slots(database))[0].id)
        assert slot is not None
        slot.sheet_state = "cleared"
    clock.moment = vn(DAY + timedelta(days=3), 1)
    counts = await tarot.finalize_and_purge()
    assert counts["slots_purged"] == 1
    clock.moment = vn(DAY + timedelta(days=41), 1)
    counts = await tarot.finalize_and_purge()
    assert counts["days_purged"] == 1
    async with database.sessions() as session:
        assert await session.get(HumanTarotRequestRow, view.id) is None
