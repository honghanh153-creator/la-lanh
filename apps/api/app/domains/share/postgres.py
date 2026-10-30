import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.postgres import account_transaction, lock_owner
from app.domains.daily.tables import DailyNoteRow
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.history.postgres import unavailable_daily
from app.domains.readings.tables import ReadingRevisionRow
from app.domains.share.errors import ShareArtifactUnavailable
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.tables import ShareArtifactRow
from app.infrastructure.crypto import EnvelopeCipher


class PostgresShareArtifactRepository:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._erasure_journal = erasure_journal

    async def create(self, record: ShareArtifactRecord) -> ShareArtifactRecord:
        """Insert a link only while its source is still live, under the owner's lock.

        Once migration 20261029_0039 drops the source foreign keys, nothing else rejects a link
        whose Daily note or revision was deleted after the service read it. Birth time/place
        removal and the birth-date correction take this same guest row lock, so the recheck here
        is serialized with them:
        a removal that commits first makes this create fail; one that commits later deletes or
        keeps the link exactly as for any other existing link.
        """

        async with account_transaction(self._sessions) as session:
            await lock_owner(session, record.guest_id)
            source = await session.scalar(
                select(DailyNoteRow.id).where(
                    DailyNoteRow.id == record.daily_note_id,
                    DailyNoteRow.guest_id == record.guest_id,
                    ~unavailable_daily(record.created_at),
                )
            )
            if source is None:
                raise ShareArtifactUnavailable
            if record.revision_id is not None:
                revision = await session.scalar(
                    select(ReadingRevisionRow.id).where(
                        ReadingRevisionRow.id == record.revision_id,
                        ReadingRevisionRow.guest_id == record.guest_id,
                        ReadingRevisionRow.profile_id == record.profile_id,
                    )
                )
                if revision is None:
                    raise ShareArtifactUnavailable
            row = ShareArtifactRow(
                id=record.id,
                guest_id=record.guest_id,
                daily_note_id=record.daily_note_id,
                profile_id=record.profile_id,
                revision_id=record.revision_id,
                token_hash=record.token_hash,
                safe_snapshot={},
                safe_snapshot_ciphertext=_encrypt_snapshot(record, self._envelope),
                format=record.format.value,
                created_at=record.created_at,
                expires_at=record.expires_at,
                revoked_at=record.revoked_at,
            )
            session.add(row)
            await session.flush()
            return _record(row, self._envelope)

    async def find_by_token_hash(self, token_hash: bytes) -> ShareArtifactRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(ShareArtifactRow).where(ShareArtifactRow.token_hash == token_hash)
            )
            return _record(row, self._envelope) if row is not None else None

    async def revoke_owned(self, guest_id: UUID, artifact_id: UUID, revoked_at: datetime) -> bool:
        async with self._sessions() as session, session.begin():
            result = await session.execute(
                update(ShareArtifactRow)
                .where(
                    ShareArtifactRow.id == artifact_id,
                    ShareArtifactRow.guest_id == guest_id,
                )
                .values(revoked_at=revoked_at)
            )
            revoked = bool(cast(CursorResult[Any], result).rowcount)
            if revoked and self._erasure_journal is not None:
                self._erasure_journal.record(
                    session, ErasureKind.SHARE_REVOKED, artifact_id, revoked_at
                )
            return revoked


def _snapshot_context(record_id: UUID) -> bytes:
    return f"share-artifact:{record_id}".encode()


def _encrypt_snapshot(record: ShareArtifactRecord, envelope: EnvelopeCipher) -> str:
    payload = json.dumps(
        asdict(record.safe_snapshot),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return envelope.encrypt(payload, context=_snapshot_context(record.id))


def _snapshot_payload(row: ShareArtifactRow, envelope: EnvelopeCipher) -> dict[str, object]:
    if row.safe_snapshot_ciphertext:
        decrypted = envelope.decrypt(
            row.safe_snapshot_ciphertext,
            context=_snapshot_context(row.id),
        )
        payload: object = json.loads(decrypted)
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted share snapshot")
        return cast(dict[str, object], payload)
    return row.safe_snapshot


def _record(row: ShareArtifactRow, envelope: EnvelopeCipher) -> ShareArtifactRecord:
    snapshot = _snapshot_payload(row, envelope)
    return ShareArtifactRecord(
        id=row.id,
        guest_id=row.guest_id,
        daily_note_id=row.daily_note_id,
        token_hash=row.token_hash,
        safe_snapshot=SafeShareSnapshot(
            title=str(snapshot["title"]),
            body=str(snapshot["body"]),
            context_label=str(snapshot["context_label"]),
            content_version=str(snapshot["content_version"]),
            persona_mode=str(snapshot.get("persona_mode", "vibe")),
            persona_label=str(snapshot.get("persona_label", "Mềm")),
            persona_version=str(snapshot.get("persona_version", "persona-v1")),
            watermark=str(snapshot["watermark"]),
        ),
        format=ShareFormat(row.format),
        created_at=row.created_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        profile_id=row.profile_id,
        revision_id=row.revision_id,
    )
