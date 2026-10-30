"""US-24 admission: 10 a Vietnam day, one per guest, never refunded, closed at the cut-off."""

from __future__ import annotations

import asyncio
from datetime import time

import pytest

from app.db.session import Database
from app.domains.human_tarot.errors import (
    HumanTarotAlreadyRequested,
    HumanTarotClosed,
    HumanTarotConflict,
    HumanTarotConsentRequired,
    HumanTarotDisabled,
    HumanTarotFull,
    HumanTarotKeyInvalid,
)
from app.domains.human_tarot.models import AvailabilityReason, VisibleStatus
from app.domains.human_tarot.tables import HumanTarotDayRow
from app.domains.tarot.errors import TarotQuestionRejected
from tests.human_tarot import support
from tests.human_tarot.support import DAY, Clock, vn


async def _count(database: Database, day=DAY) -> int:  # type: ignore[no-untyped-def]
    async with database.sessions() as session:
        row = await session.get(HumanTarotDayRow, day)
        return row.accepted_count if row is not None else 0


async def test_ac01_twenty_concurrent_guests_get_exactly_ten(database: Database) -> None:
    clock = Clock(vn(DAY, 7))
    tarot = support.service(database, clock)
    guests = [await support.guest(database) for _ in range(20)]
    outcomes = await asyncio.gather(
        *(support.create(tarot, guest) for guest in guests), return_exceptions=True
    )
    accepted = [item for item in outcomes if not isinstance(item, BaseException)]
    full = [item for item in outcomes if isinstance(item, HumanTarotFull)]
    assert len(accepted) == 10 and len(full) == 10
    assert await _count(database) == 10
    slots = await support.slots(database)
    assert [slot.slot_no for slot in slots] == list(range(1, 11))
    assert len({slot.request_code for slot in slots}) == 10
    assert all(view.status is VisibleStatus.WAITING for view in accepted)
    availability = await tarot.availability(guests[0])
    assert availability.remaining == 0


async def test_ac02_same_key_twice_concurrently_is_one_request_and_one_debit(
    database: Database,
) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)))
    guest = await support.guest(database)
    first, second = await asyncio.gather(
        support.create(tarot, guest, key="same-key-" * 3),
        support.create(tarot, guest, key="same-key-" * 3),
    )
    assert first.id == second.id
    assert await _count(database) == 1
    with pytest.raises(HumanTarotConflict):
        await support.create(
            tarot, guest, key="same-key-" * 3, question="Mình nên nói gì với nhóm vào sáng mai?"
        )
    assert await _count(database) == 1


async def test_ac03_one_request_per_guest_per_day_even_after_cancel(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)))
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    with pytest.raises(HumanTarotAlreadyRequested):
        await support.create(tarot, guest, key="second-key-" * 3)
    await tarot.cancel(guest, view.id)
    with pytest.raises(HumanTarotAlreadyRequested):
        await support.create(tarot, guest, key="third-key-" * 3)
    assert await _count(database) == 1
    availability = await tarot.availability(guest)
    assert availability.reason is AvailabilityReason.ALREADY_REQUESTED
    assert availability.current_request_id == view.id


async def test_ac04_cut_off_rejects_new_requests_but_replays_old_ones(database: Database) -> None:
    clock = Clock(vn(DAY, 17, 59, 59))
    tarot = support.service(database, clock)
    early, late = await support.guest(database), await support.guest(database)
    accepted = await support.create(tarot, early)
    clock.moment = vn(DAY, 18)
    with pytest.raises(HumanTarotClosed):
        await support.create(tarot, late)
    assert (await support.create(tarot, early)).id == accepted.id  # retry after the cut-off
    assert (await tarot.availability(late)).reason is AvailabilityReason.CLOSED
    assert await _count(database) == 1


async def test_ac04_a_request_that_waited_for_the_lock_past_the_cut_off_is_closed(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.domains.human_tarot import service as module

    clock = Clock(vn(DAY, 17, 59, 59))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    from app.domains.accounts.postgres import lock_owner as original

    async def slow_lock(session, guest_id):  # type: ignore[no-untyped-def]
        clock.moment = vn(DAY, 18, 0, 1)  # the clock moves while waiting for the guest lock
        return await original(session, guest_id)

    monkeypatch.setattr(module, "lock_owner", slow_lock)
    with pytest.raises(HumanTarotClosed):
        await support.create(tarot, guest)
    assert await _count(database) == 0


async def test_a_cut_off_other_than_the_default_still_ends_before_the_release(
    database: Database,
) -> None:
    clock = Clock(vn(DAY, 9))
    tarot = support.service(database, clock, closes=time(9, 0))
    guest = await support.guest(database)
    with pytest.raises(HumanTarotClosed):
        await support.create(tarot, guest)
    availability = await tarot.availability(guest)
    assert availability.closes_at == vn(DAY, 9)
    assert availability.release_at == vn(DAY, 22)
    with pytest.raises(ValueError, match="22:00"):
        support.service(database, clock, closes=time(22, 1))
    default = await support.service(database, clock).availability(await support.guest(database))
    assert default.closes_at == vn(DAY, 18)


async def test_ac05_cancel_guest_deletion_and_retry_never_refund(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)))
    guests = [await support.guest(database) for _ in range(10)]
    views = [await support.create(tarot, guest) for guest in guests]
    await tarot.cancel(guests[0], views[0].id)
    from sqlalchemy import delete

    from app.domains.guest.tables import GuestSessionRow

    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guests[1]))
    assert await _count(database) == 10
    newcomer = await support.guest(database)
    with pytest.raises(HumanTarotFull):
        await support.create(tarot, newcomer)
    assert (await tarot.availability(newcomer)).reason is AvailabilityReason.FULL


async def test_ac06_the_day_changes_at_vietnam_midnight_not_utc(database: Database) -> None:
    # 23:59:59 on 30/10 in Vietnam is 16:59:59 UTC; 00:00 on 31/10 is 17:00 UTC on 30/10.
    clock = Clock(vn(DAY, 23, 59, 59))
    tarot = support.service(database, clock)
    guest = await support.guest(database)
    with pytest.raises(HumanTarotClosed):
        await support.create(tarot, guest)  # past the cut-off of 30/10
    clock.moment = vn(DAY.replace(day=31), 0)
    view = await support.create(tarot, guest)
    assert view.local_date == DAY.replace(day=31)
    assert view.release_at == vn(DAY.replace(day=31), 22)
    assert await _count(database, DAY.replace(day=31)) == 1
    assert await _count(database, DAY) == 0


async def test_ac07_consent_key_and_question_rejections_take_no_slot(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)))
    guest = await support.guest(database)
    with pytest.raises(HumanTarotConsentRequired):
        await support.create(tarot, guest, consent="tarot-reflection-v1")
    with pytest.raises(HumanTarotKeyInvalid):
        await support.create(tarot, guest, key="short")
    with pytest.raises(TarotQuestionRejected):
        await support.create(tarot, guest, question="Người ấy có đang nghĩ về mình không?")
    assert await _count(database) == 0
    assert await support.slots(database) == []


async def test_disabled_flag_rejects_and_hides(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)), enabled=False)
    guest = await support.guest(database)
    with pytest.raises(HumanTarotDisabled):
        await support.create(tarot, guest)
    availability = await tarot.availability(guest)
    assert availability.enabled is False and availability.reason is AvailabilityReason.DISABLED


async def test_intake_closed_after_restore_stays_closed(database: Database) -> None:
    tarot = support.service(database, Clock(vn(DAY, 7)))
    guest = await support.guest(database)
    await tarot.close_intake(DAY)
    with pytest.raises(HumanTarotClosed):
        await support.create(tarot, guest)
    assert (await tarot.availability(guest)).reason is AvailabilityReason.CLOSED


async def test_the_bridge_is_asked_to_export_after_commit_and_its_failure_keeps_the_receipt(
    database: Database,
) -> None:
    calls: list[str] = []

    class FailingBridge:
        async def export_now(self, slot_id):  # type: ignore[no-untyped-def]
            calls.append("export")
            raise TimeoutError

        async def clear_now(self, slot_id):  # type: ignore[no-untyped-def]
            calls.append("clear")

    tarot = support.service(database, Clock(vn(DAY, 7)), bridge=FailingBridge())
    guest = await support.guest(database)
    view = await support.create(tarot, guest)
    assert calls == ["export"]
    assert view.status is VisibleStatus.WAITING and view.delivery == "pending"
    await tarot.cancel(guest, view.id)
    assert calls == ["export", "clear"]
