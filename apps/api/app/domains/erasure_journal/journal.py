"""Deletion journal for explicit user erasures (audit P07, option A, owner decision 22/10/2026).

Each explicit erasure or withdrawal appends, in the same transaction, a keyed HMAC of its root id
with the kind of action and its time. After a restore, `replay` re-applies every exported entry
that the restored snapshot does not hold; time-based retention is re-run separately (option C).
The journal holds no content; dumps keep its rows as the snapshot checkpoint, and an hourly host
copy carries the entries committed after a snapshot.
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
    # Owned artifacts (follow-up batch 1): the root is the row's own random id, so a later
    # re-save or a new reading is never touched by a replay.
    TAROT_SESSION_DELETED = "tarot_session_deleted"
    SHARE_REVOKED = "share_revoked"
    SAVED_NOTE_REMOVED = "saved_note_removed"
    # Batch 2, keyed the same way: La Chung invite and response rows, the experiment row and the
    # pending Radar invite. Revoke, withdraw and hide each touch only the row they name.
    LA_CHUNG_INVITE_REVOKED = "la_chung_invite_revoked"
    LA_CHUNG_RESPONSE_WITHDRAWN = "la_chung_response_withdrawn"
    LA_CHUNG_RESULT_HIDDEN = "la_chung_result_hidden"
    LA_CHUNG_RESULT_DELETED = "la_chung_result_deleted"
    EXPERIMENT_UNDONE = "experiment_undone"
    RADAR_INVITE_REVOKED = "radar_invite_revoked"
    # Human Tarot (US-24): cancel or delete of one request; replay also clears its Sheet row.
    HUMAN_TAROT_REQUEST_CANCELLED = "human_tarot_request_cancelled"


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
