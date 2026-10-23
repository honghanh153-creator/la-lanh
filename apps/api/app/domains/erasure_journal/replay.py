"""Export, import, replay and purge of the deletion journal (audit P07, option A).

Restore order (runbook): export the live journal if the database is still readable; restore the
dump; import every exported journal file; `replay(since=<dump time>)`; run the guest and expired
cleanups (option C); verify; only then serve. Entries at or before the dump time are skipped: the
dump already reflects them, and replaying a clear judged at an older time could remove data the
person kept or created afterwards.
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

    def lines(self) -> Iterator[str]:
        for kind in sorted(self.entries):
            yield (
                f"{kind}: entries={self.entries[kind]} applied={self.applied[kind]} "
                f"unmatched={self.unmatched[kind]}"
            )


def _entry(row: ErasureJournalRow) -> dict[str, str]:
    return {
        "kind": row.kind,
        "subject_digest": row.subject_digest.hex(),
        "scope": row.scope,
        "occurred_at": row.occurred_at.isoformat(),
    }


async def export_entries(
    sessions: async_sessionmaker[AsyncSession], *, since: datetime | None = None
) -> list[str]:
    """JSON lines of digests, kinds, scopes and times: no id, content or key material."""

    async with sessions() as session:
        query = select(ErasureJournalRow).order_by(
            ErasureJournalRow.occurred_at, ErasureJournalRow.id
        )
        if since is not None:
            query = query.where(ErasureJournalRow.occurred_at > since)
        return [json.dumps(_entry(row), sort_keys=True) for row in await session.scalars(query)]


async def import_entries(sessions: async_sessionmaker[AsyncSession], lines: Iterable[str]) -> int:
    """Insert exported entries that are not present yet. Unknown kinds fail closed."""

    added = 0
    async with sessions() as session, session.begin():
        for line in lines:
            if not line.strip():
                continue
            raw = json.loads(line)
            kind = ErasureKind(raw["kind"])
            digest = bytes.fromhex(raw["subject_digest"])
            if len(digest) != 32:
                raise ValueError("journal digest must be 32 bytes")
            occurred_at = datetime.fromisoformat(raw["occurred_at"])
            scope = str(raw.get("scope", ""))
            exists = await session.scalar(
                select(ErasureJournalRow.id).where(
                    ErasureJournalRow.kind == kind.value,
                    ErasureJournalRow.subject_digest == digest,
                    ErasureJournalRow.scope == scope,
                    ErasureJournalRow.occurred_at == occurred_at,
                )
            )
            if exists is None:
                session.add(
                    ErasureJournalRow(
                        kind=kind.value, subject_digest=digest, scope=scope, occurred_at=occurred_at
                    )
                )
                added += 1
    return added


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


async def replay(
    sessions: async_sessionmaker[AsyncSession],
    journal: ErasureJournal,
    envelope: EnvelopeCipher,
    *,
    since: datetime,
) -> ReplayReport:
    """Re-apply every journaled erasure newer than ``since`` (the restored dump's time).

    Repositories are built without a journal, so replay appends no new entries. Every step is
    idempotent: replaying twice leaves the same state.
    """

    async with sessions() as session:
        entries = list(
            await session.scalars(
                select(ErasureJournalRow)
                .where(ErasureJournalRow.occurred_at > since)
                .order_by(ErasureJournalRow.occurred_at, ErasureJournalRow.id)
            )
        )
    guests = PostgresGuestRepository(sessions)
    history = PostgresHistoryRepository(sessions, envelope)
    birth = PostgresBirthRepository(sessions, envelope)
    resonance = PostgresResonanceRepository(sessions, envelope)
    matching = PostgresMatchingRepository(sessions, envelope)
    subjects: dict[ErasureKind, dict[bytes, UUID]] = {}
    report = ReplayReport()
    for entry in entries:
        kind = ErasureKind(entry.kind)
        report.entries[kind.value] += 1
        if kind not in subjects:
            subjects[kind] = await _subjects(sessions, journal, kind)
        subject = subjects[kind].get(entry.subject_digest)
        if subject is None:
            # Not in the restored copy: created after the dump, or already gone.
            report.unmatched[kind.value] += 1
            continue
        at = entry.occurred_at
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
                report.unmatched[kind.value] += 1
                continue
        elif kind is ErasureKind.BIRTH_TIME_DOWNGRADED:
            await birth.replay_time_downgrade(subject)
        elif kind is ErasureKind.CONSENT_REVOKED:
            await guests.revoke_consent(subject, entry.scope, at)
        elif kind is ErasureKind.RESONANCE_CLEARED:
            await resonance.clear_with_consent(
                subject, revoke_consent=entry.scope == "consent", now=at
            )
        elif kind is ErasureKind.MATCHING_CONSENT_WITHDRAWN:
            await matching.withdraw_consent(subject, now=at)
        elif kind is ErasureKind.RADAR_DELETED:
            async with sessions() as session, session.begin():
                await session.execute(
                    delete(ContentRewriteJobRow).where(
                        ContentRewriteJobRow.radar_request_id == subject
                    )
                )
                await session.execute(delete(RadarRequestRow).where(RadarRequestRow.id == subject))
        elif kind is ErasureKind.RADAR_WITHDRAWN:
            async with sessions() as session, session.begin():
                await session.execute(
                    delete(ContentRewriteJobRow).where(
                        ContentRewriteJobRow.radar_request_id == subject
                    )
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
        report.applied[kind.value] += 1
    return report
