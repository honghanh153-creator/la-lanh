"""Deletion journal for explicit user erasures (audit P07, option A, owner decision 22/10/2026).

Each explicit erasure or withdrawal appends, in the same transaction, a keyed HMAC of its root id
with the kind of action and its time. After a restore, `replay` re-applies every entry newer than
the backup; time-based retention is re-run separately (option C). The journal holds no content,
is excluded from database dumps and is exported to the host so post-backup entries survive.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.erasure_journal.tables import ErasureJournalRow
from app.infrastructure.crypto import SecretHasher


class ErasureKind(StrEnum):
    GUEST_ERASED = "guest_erased"
    HISTORY_CLEARED = "history_cleared"
    BIRTH_SUPPLEMENT_REMOVED = "birth_supplement_removed"
    BIRTH_TIME_DOWNGRADED = "birth_time_downgraded"
    RADAR_DELETED = "radar_deleted"
    RADAR_WITHDRAWN = "radar_withdrawn"
    CONSENT_REVOKED = "consent_revoked"
    RESONANCE_CLEARED = "resonance_cleared"
    MATCHING_CONSENT_WITHDRAWN = "matching_consent_withdrawn"


class ErasureJournal:
    def __init__(self, hasher: SecretHasher) -> None:
        self._hasher = hasher

    def digest(self, kind: ErasureKind, subject: UUID) -> bytes:
        # A separate HMAC domain per kind: digests never match other credential digests.
        return self._hasher.digest(f"erasure-journal:{kind.value}", str(subject))

    def record(
        self,
        session: AsyncSession,
        kind: ErasureKind,
        subject: UUID,
        occurred_at: datetime,
        *,
        scope: str = "",
    ) -> None:
        """Append inside the caller's transaction, so the fact commits with the erasure."""

        session.add(
            ErasureJournalRow(
                kind=kind.value,
                subject_digest=self.digest(kind, subject),
                scope=scope,
                occurred_at=occurred_at,
            )
        )
