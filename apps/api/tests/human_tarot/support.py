"""Synthetic helpers for the human Tarot tests (US-24). No real question, guest or Google data."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.session import Database
from app.domains.erasure_journal.journal import ErasureJournal
from app.domains.guest.tables import GuestSessionRow
from app.domains.human_tarot import policy
from app.domains.human_tarot.service import HumanTarotService
from app.domains.human_tarot.tables import HumanTarotRequestRow, HumanTarotSlotRow
from app.domains.tarot.models import TarotContext, TarotSpread
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

CIPHER = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"h" * 32))
HASHER = SecretHasher(b"synthetic-human-tarot-key" * 2)
JOURNAL = ErasureJournal(HASHER)
QUESTION = "Mình cần nhìn rõ điều gì trước khi nhận thêm việc?"
DAY = date(2026, 10, 30)


def vn(day: date, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(
        day.year, day.month, day.day, hour, minute, second, tzinfo=policy.PRODUCT_TIMEZONE
    )


class Clock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment.astimezone(UTC)

    def advance(self, **delta: float) -> None:
        self.moment += timedelta(**delta)


def service(
    database: Database,
    clock: Clock,
    *,
    enabled: bool = True,
    bridge: Any = None,
    closes: Any = None,
) -> HumanTarotService:
    extra = {"intake_closes_at": closes} if closes is not None else {}
    return HumanTarotService(
        database.sessions,
        CIPHER,
        HASHER,
        enabled=enabled,
        erasure_journal=JOURNAL,
        bridge=bridge,
        clock=clock,
        **extra,
    )


async def guest(database: Database) -> UUID:
    guest_id, now = uuid4(), datetime.now(UTC)
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=guest_id.bytes * 2,
                csrf_hash=b"c" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=30),
            )
        )
    return guest_id


async def create(
    tarot: HumanTarotService,
    guest_id: UUID,
    *,
    key: str | None = None,
    question: str = QUESTION,
    spread: TarotSpread = TarotSpread.THREE_CARD,
    consent: str = policy.CONSENT_VERSION,
) -> Any:
    return await tarot.create(
        guest_id=guest_id,
        context=TarotContext.WORK,
        question=question,
        spread=spread,
        consent_version=consent,
        idempotency_key=key or f"human-key-{guest_id.hex}",
    )


async def request_row(database: Database, request_id: UUID) -> HumanTarotRequestRow | None:
    async with database.sessions() as session:
        return await session.get(HumanTarotRequestRow, request_id)


async def slot_for(database: Database, request_id: UUID) -> HumanTarotSlotRow | None:
    async with database.sessions() as session:
        slot: HumanTarotSlotRow | None = await session.scalar(
            select(HumanTarotSlotRow).where(HumanTarotSlotRow.request_id == request_id)
        )
        return slot


async def slots(database: Database) -> list[HumanTarotSlotRow]:
    async with database.sessions() as session:
        return list(
            await session.scalars(select(HumanTarotSlotRow).order_by(HumanTarotSlotRow.slot_no))
        )


async def freeze(
    database: Database, tarot: HumanTarotService, request_id: UUID, at: datetime
) -> None:
    """Stand-in for the Sheet import (U5): a valid frozen reading for a three-card request."""

    async with database.sessions() as session, session.begin():
        row = await session.get(HumanTarotRequestRow, request_id)
        assert row is not None
        payload = tarot.decrypt(row)
        payload["result"] = {
            "schema": policy.RESULT_SCHEMA,
            "reader": policy.READER,
            "cards": [
                {"position_key": "clear", "card_id": "major-star"},
                {"position_key": "missed", "card_id": "cups-5"},
                {"position_key": "next", "card_id": "wands-ace"},
            ],
            "reading": "Một bài đọc tổng hợp cho kiểm thử, đủ dài để qua giới hạn tối thiểu.",
            "step": "Viết ra một việc nhỏ.",
            "imported_at": at.astimezone(UTC).isoformat(),
        }
        row.payload_ciphertext = tarot.encrypt(row.id, payload)
        row.status = "ready"
        row.imported_at = at.astimezone(UTC)
