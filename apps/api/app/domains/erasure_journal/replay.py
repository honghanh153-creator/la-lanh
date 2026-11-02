"""Export, replay and purge of the deletion journal (audit P07, option A).

Checkpoint: each journal row commits in the same transaction as its erasure, and database dumps
keep the journal's rows. A restored copy therefore holds exactly the journal entries whose
erasures its snapshot already reflects, whatever the wall-clock times. Rows that retention purged
are covered by the purge horizon, recorded in the purge's own transaction and so also in the
snapshot. Replay applies only the exported entries that the restored copy neither holds nor
covers by its horizon, then records them.

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
from app.domains.erasure_journal.tables import ErasureJournalHorizonRow, ErasureJournalRow
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.models import GuestState
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.postgres import PostgresHistoryRepository
from app.domains.la_chung.models import RequestStatus
from app.domains.la_chung.tables import LaChungReportRow, LaChungRequestRow, LaChungResponseRow
from app.domains.matching.postgres import PostgresMatchingRepository
from app.domains.matching.tables import MatchingConsentRow, MatchingProfileRow
from app.domains.radar.models import RadarStatus
from app.domains.radar.tables import RadarRequestRow
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import EnvelopeCipher

_GUEST_KINDS = frozenset(
    {
        ErasureKind.GUEST_ERASED,
        ErasureKind.HISTORY_CLEARED,
        ErasureKind.BIRTH_SUPPLEMENT_REMOVED,
        ErasureKind.BIRTH_TIME_DOWNGRADED,
        ErasureKind.BIRTH_DATE_REPLACED,
        ErasureKind.CONSENT_REVOKED,
        ErasureKind.RESONANCE_CLEARED,
    }
)
_RADAR_KINDS = frozenset(
    {ErasureKind.RADAR_DELETED, ErasureKind.RADAR_WITHDRAWN, ErasureKind.RADAR_INVITE_REVOKED}
)
# Owned artifacts: the journal subject is the row's own id.
_ARTIFACT_IDS = {
    ErasureKind.TAROT_SESSION_DELETED: TarotSessionRow.id,
    ErasureKind.SHARE_REVOKED: ShareArtifactRow.id,
    ErasureKind.SAVED_NOTE_REMOVED: SavedNoteRow.id,
    ErasureKind.LA_CHUNG_INVITE_REVOKED: LaChungRequestRow.id,
    ErasureKind.LA_CHUNG_RESULT_DELETED: LaChungRequestRow.id,
    ErasureKind.LA_CHUNG_RESPONSE_WITHDRAWN: LaChungResponseRow.id,
    ErasureKind.LA_CHUNG_RESULT_HIDDEN: LaChungResponseRow.id,
    ErasureKind.EXPERIMENT_UNDONE: DailyExperimentRow.id,
}


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
    """Drop entries older than ``before`` and record that horizon in the same transaction.

    A snapshot holding the horizon reflects every entry older than it, under one stated
    assumption: an erasure commits well within the retention period after its ``occurred_at``
    (taken when the request starts) and the server clock is sane, so it committed before a purge
    that runs at least that long after it. Request deadlines make this expected, but nothing here
    proves it for PostgreSQL; the operator restore probe covers it. Replay therefore treats a
    missing row older than the horizon as reflected, never as an erasure to apply again. The
    boundary is strict: an entry exactly at the horizon still goes by row presence.
    """

    async with sessions() as session, session.begin():
        result = await session.execute(
            delete(ErasureJournalRow).where(ErasureJournalRow.occurred_at < before)
        )
        horizon = await session.get(ErasureJournalHorizonRow, 1, with_for_update=True)
        if horizon is None:
            session.add(ErasureJournalHorizonRow(id=1, purged_before=before))
        elif horizon.purged_before < before:
            horizon.purged_before = before
        return int(cast(CursorResult[Any], result).rowcount or 0)


async def _purge_horizon(sessions: async_sessionmaker[AsyncSession]) -> datetime | None:
    async with sessions() as session:
        horizon = await session.get(ErasureJournalHorizonRow, 1)
        return horizon.purged_before if horizon is not None else None


async def _subjects(
    sessions: async_sessionmaker[AsyncSession], journal: ErasureJournal, kind: ErasureKind
) -> dict[bytes, UUID]:
    async with sessions() as session:
        if kind in _GUEST_KINDS:
            ids = set(await session.scalars(select(GuestSessionRow.id)))
        elif kind in _RADAR_KINDS:
            ids = set(await session.scalars(select(RadarRequestRow.id)))
        elif kind in _ARTIFACT_IDS:
            ids = set(await session.scalars(select(_ARTIFACT_IDS[kind])))
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
    skipped ("reflected"); data created afterwards stays. So is an entry older than the restored
    copy's purge horizon: its row was purged, not missing (see ``purge_entries``). Any other
    entry is applied through the same repository code, built without a journal, and only then
    recorded, so an interrupted replay re-applies it next time. Every step is idempotent.
    """

    guests = PostgresGuestRepository(sessions)
    history = PostgresHistoryRepository(sessions, envelope)
    birth = PostgresBirthRepository(sessions, envelope)
    resonance = PostgresResonanceRepository(sessions, envelope)
    matching = PostgresMatchingRepository(sessions, envelope)
    subjects: dict[ErasureKind, dict[bytes, UUID]] = {}
    report = ReplayReport()
    horizon = await _purge_horizon(sessions)
    for entry in parse_entries(lines):
        kind = entry.kind
        report.entries[kind.value] += 1
        if (horizon is not None and entry.occurred_at < horizon) or await _held(sessions, entry):
            # Held, or purged from this snapshot's own journal: either way already reflected.
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
    elif kind is ErasureKind.BIRTH_DATE_REPLACED:
        # Reached only for a copy that does not hold the entry, i.e. one taken before the
        # correction: it holds the old subject and no replacement value. Fail closed.
        await birth.replay_date_replacement(subject)
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
    elif kind is ErasureKind.TAROT_SESSION_DELETED:
        async with sessions() as session, session.begin():
            await session.execute(
                delete(ContentRewriteJobRow).where(ContentRewriteJobRow.tarot_session_id == subject)
            )
            await session.execute(delete(TarotSessionRow).where(TarotSessionRow.id == subject))
    elif kind is ErasureKind.SHARE_REVOKED:
        async with sessions() as session, session.begin():
            # Keeps an earlier revocation; a restored link never becomes readable again.
            await session.execute(
                update(ShareArtifactRow)
                .where(ShareArtifactRow.id == subject, ShareArtifactRow.revoked_at.is_(None))
                .values(revoked_at=at)
            )
    elif kind is ErasureKind.SAVED_NOTE_REMOVED:
        async with sessions() as session, session.begin():
            await session.execute(delete(SavedNoteRow).where(SavedNoteRow.id == subject))
    elif kind is ErasureKind.RADAR_INVITE_REVOKED:
        async with sessions() as session, session.begin():
            # Only a still-pending invite: an accepted or withdrawn row keeps its own state.
            await session.execute(
                update(RadarRequestRow)
                .where(
                    RadarRequestRow.id == subject,
                    RadarRequestRow.status == RadarStatus.PENDING.value,
                )
                .values(status=RadarStatus.REVOKED.value, revoked_at=at, token_ciphertext=None)
            )
    elif kind is ErasureKind.LA_CHUNG_INVITE_REVOKED:
        async with sessions() as session, session.begin():
            await session.execute(
                update(LaChungRequestRow)
                .where(
                    LaChungRequestRow.id == subject,
                    LaChungRequestRow.status == RequestStatus.PENDING.value,
                )
                .values(status=RequestStatus.REVOKED.value, revoked_at=at, token_ciphertext=None)
            )
    elif kind is ErasureKind.LA_CHUNG_RESPONSE_WITHDRAWN:
        async with sessions() as session, session.begin():
            request_id = await session.scalar(
                select(LaChungResponseRow.request_id).where(LaChungResponseRow.id == subject)
            )
            await session.execute(
                update(LaChungResponseRow)
                .where(LaChungResponseRow.id == subject, LaChungResponseRow.withdrawn_at.is_(None))
                .values(withdrawn_at=at, receipt_ciphertext=None)
            )
            await session.execute(
                update(LaChungRequestRow)
                .where(
                    LaChungRequestRow.id == request_id,
                    LaChungRequestRow.status == RequestStatus.COMPLETED.value,
                )
                .values(status=RequestStatus.WITHDRAWN.value)
            )
    elif kind is ErasureKind.LA_CHUNG_RESULT_HIDDEN:
        async with sessions() as session, session.begin():
            # Keeps an earlier hide time.
            await session.execute(
                update(LaChungResponseRow)
                .where(LaChungResponseRow.id == subject, LaChungResponseRow.hidden_at.is_(None))
                .values(hidden_at=at)
            )
    elif kind is ErasureKind.LA_CHUNG_RESULT_DELETED:
        async with sessions() as session, session.begin():
            # Children first, so the result is gone even where the cascade is not enforced.
            for child in (LaChungResponseRow, LaChungReportRow):
                await session.execute(delete(child).where(child.request_id == subject))
            await session.execute(delete(LaChungRequestRow).where(LaChungRequestRow.id == subject))
    elif kind is ErasureKind.EXPERIMENT_UNDONE:
        async with sessions() as session, session.begin():
            await session.execute(
                delete(DailyExperimentRow).where(DailyExperimentRow.id == subject)
            )
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
