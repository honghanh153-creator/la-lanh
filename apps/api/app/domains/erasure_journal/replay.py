"""Export, replay and purge of the deletion journal (audit P07, option A).

Checkpoint: each journal row commits in the same transaction as its erasure, and database dumps
keep the journal's rows. A restored copy therefore holds exactly the journal entries whose
erasures its snapshot already reflects, whatever the wall-clock times. Replay applies only the
exported entries that the restored copy does not hold, then records them.

Restore order (runbook): export the live journal if the database is still readable; restore the
dump; `replay` every exported journal file; run the guest and expired cleanups (option C);
verify; only then serve.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.content_rewrite.tables import ContentRewriteJobRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.guest.models import GuestState
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.postgres import PostgresHistoryRepository
from app.domains.matching.postgres import PostgresMatchingRepository
from app.domains.matching.tables import MatchingConsentRow, MatchingProfileRow
from app.domains.radar.models import RadarStatus
from app.domains.radar.tables import RadarRequestRow
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.infrastructure.crypto import EnvelopeCipher

_GUEST_KINDS = frozenset(
    {
        ErasureKind.GUEST_ERASED,
        ErasureKind.HISTORY_CLEARED,
        ErasureKind.BIRTH_SUPPLEMENT_REMOVED,
        ErasureKind.BIRTH_TIME_DOWNGRADED,
        ErasureKind.CONSENT_REVOKED,
        ErasureKind.RESONANCE_CLEARED,
    }
)
_RADAR_KINDS = frozenset({ErasureKind.RADAR_DELETED, ErasureKind.RADAR_WITHDRAWN})


@dataclass
class ReplayReport:
    entries: Counter[str] = field(default_factory=Counter)
    applied: Counter[str] = field(default_factory=Counter)
    unmatched: Counter[str] = field(default_factory=Counter)
    reflected: Counter[str] = field(default_factory=Counter)

    def lines(self) -> Iterator[str]:
        for kind in sorted(self.entries):
            yield (
                f"{kind}: entries={self.entries[kind]} reflected={self.reflected[kind]} "
                f"applied={self.applied[kind]} unmatched={self.unmatched[kind]}"
            )


def _entry(row: ErasureJournalRow) -> dict[str, str]:
    return {
        "kind": row.kind,
        "subject_digest": row.subject_digest.hex(),
        "scope": row.scope,
        "occurred_at": row.occurred_at.isoformat(),
    }


async def export_entries(sessions: async_sessionmaker[AsyncSession]) -> list[str]:
    """JSON lines of digests, kinds, scopes and times: no id, content or key material."""

    async with sessions() as session:
        query = select(ErasureJournalRow).order_by(
            ErasureJournalRow.occurred_at, ErasureJournalRow.id
        )
        return [json.dumps(_entry(row), sort_keys=True) for row in await session.scalars(query)]


@dataclass(frozen=True)
class JournalEntry:
    kind: ErasureKind
    subject_digest: bytes
    scope: str
    occurred_at: datetime


def parse_entries(lines: Iterable[str]) -> list[JournalEntry]:
    """Exported lines, de-duplicated across files and in time order. Unknown kinds fail closed."""

    entries: set[JournalEntry] = set()
    for line in lines:
        if not line.strip():
            continue
        raw = json.loads(line)
        digest = bytes.fromhex(raw["subject_digest"])
        if len(digest) != 32:
            raise ValueError("journal digest must be 32 bytes")
        occurred_at = datetime.fromisoformat(raw["occurred_at"])
        if occurred_at.tzinfo is None:
            raise ValueError("journal time must carry a UTC offset")
        entries.add(
            JournalEntry(
                kind=ErasureKind(raw["kind"]),
                subject_digest=digest,
                scope=str(raw.get("scope", "")),
                occurred_at=occurred_at,
            )
        )
    return sorted(entries, key=lambda entry: (entry.occurred_at, entry.kind.value))


async def purge_entries(sessions: async_sessionmaker[AsyncSession], *, before: datetime) -> int:
    async with sessions() as session, session.begin():
        result = await session.execute(
            delete(ErasureJournalRow).where(ErasureJournalRow.occurred_at < before)
        )
        return int(cast(CursorResult[Any], result).rowcount or 0)


async def _subjects(
    sessions: async_sessionmaker[AsyncSession], journal: ErasureJournal, kind: ErasureKind
) -> dict[bytes, UUID]:
    async with sessions() as session:
        if kind in _GUEST_KINDS:
            ids = set(await session.scalars(select(GuestSessionRow.id)))
        elif kind in _RADAR_KINDS:
            ids = set(await session.scalars(select(RadarRequestRow.id)))
        else:
            ids = set(await session.scalars(select(MatchingConsentRow.principal_id)))
            ids |= set(await session.scalars(select(MatchingProfileRow.principal_id)))
    return {journal.digest(kind, subject): subject for subject in ids}


async def _held(sessions: async_sessionmaker[AsyncSession], entry: JournalEntry) -> bool:
    async with sessions() as session:
        found = await session.scalar(
            select(ErasureJournalRow.id).where(
                ErasureJournalRow.kind == entry.kind.value,
                ErasureJournalRow.subject_digest == entry.subject_digest,
                ErasureJournalRow.scope == entry.scope,
                ErasureJournalRow.occurred_at == entry.occurred_at,
            )
        )
    return found is not None


async def replay(
    sessions: async_sessionmaker[AsyncSession],
    journal: ErasureJournal,
    envelope: EnvelopeCipher,
    lines: Iterable[str],
) -> ReplayReport:
    """Re-apply every exported erasure that the restored snapshot does not already reflect.

    An entry the restored copy holds committed with its erasure before the snapshot, so it is
    skipped ("reflected"); data created afterwards stays. Any other entry is applied through the
    same repository code, built without a journal, and only then recorded, so an interrupted
    replay re-applies it next time. Every step is idempotent.
    """

    guests = PostgresGuestRepository(sessions)
    history = PostgresHistoryRepository(sessions, envelope)
    birth = PostgresBirthRepository(sessions, envelope)
    resonance = PostgresResonanceRepository(sessions, envelope)
    matching = PostgresMatchingRepository(sessions, envelope)
    subjects: dict[ErasureKind, dict[bytes, UUID]] = {}
    report = ReplayReport()
    for entry in parse_entries(lines):
        kind = entry.kind
        report.entries[kind.value] += 1
        if await _held(sessions, entry):
            report.reflected[kind.value] += 1
            continue
        if kind not in subjects:
            subjects[kind] = await _subjects(sessions, journal, kind)
        subject = subjects[kind].get(entry.subject_digest)
        if subject is None:
            # Not in the restored copy: created after the snapshot, or already gone.
            report.unmatched[kind.value] += 1
        else:
            await _apply(entry, subject, guests, history, birth, resonance, matching, sessions)
            report.applied[kind.value] += 1
        async with sessions() as session, session.begin():
            session.add(
                ErasureJournalRow(
                    kind=kind.value,
                    subject_digest=entry.subject_digest,
                    scope=entry.scope,
                    occurred_at=entry.occurred_at,
                )
            )
    return report


async def _apply(
    entry: JournalEntry,
    subject: UUID,
    guests: PostgresGuestRepository,
    history: PostgresHistoryRepository,
    birth: PostgresBirthRepository,
    resonance: PostgresResonanceRepository,
    matching: PostgresMatchingRepository,
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    kind, at = entry.kind, entry.occurred_at
    if kind is ErasureKind.GUEST_ERASED:
        # The guest cleanup job finishes it exactly like an interrupted deletion.
        async with sessions() as session, session.begin():
            await session.execute(
                update(GuestSessionRow)
                .where(GuestSessionRow.id == subject)
                .values(state=GuestState.DELETING.value)
            )
    elif kind is ErasureKind.HISTORY_CLEARED:
        await history.replay_clear(subject, at)
    elif kind is ErasureKind.BIRTH_SUPPLEMENT_REMOVED:
        fields = set(entry.scope.split(","))
        try:
            await birth.clear_supplement(
                subject, remove_time="time" in fields, remove_place="place" in fields
            )
        except RuntimeError:
            return  # no birth profile left in the restored copy: nothing to remove
    elif kind is ErasureKind.BIRTH_TIME_DOWNGRADED:
        await birth.replay_time_downgrade(subject)
    elif kind is ErasureKind.CONSENT_REVOKED:
        await guests.revoke_consent(subject, entry.scope, at)
    elif kind is ErasureKind.RESONANCE_CLEARED:
        await resonance.clear_with_consent(subject, revoke_consent=entry.scope == "consent", now=at)
    elif kind is ErasureKind.MATCHING_CONSENT_WITHDRAWN:
        await matching.withdraw_consent(subject, now=at)
    elif kind is ErasureKind.RADAR_DELETED:
        async with sessions() as session, session.begin():
            await session.execute(
                delete(ContentRewriteJobRow).where(ContentRewriteJobRow.radar_request_id == subject)
            )
            await session.execute(delete(RadarRequestRow).where(RadarRequestRow.id == subject))
    elif kind is ErasureKind.RADAR_WITHDRAWN:
        async with sessions() as session, session.begin():
            await session.execute(
                delete(ContentRewriteJobRow).where(ContentRewriteJobRow.radar_request_id == subject)
            )
            await session.execute(
                update(RadarRequestRow)
                .where(RadarRequestRow.id == subject)
                .values(
                    status=RadarStatus.WITHDRAWN.value,
                    withdrawn_at=at,
                    result_ciphertext=None,
                    receipt_ciphertext=None,
                )
            )
