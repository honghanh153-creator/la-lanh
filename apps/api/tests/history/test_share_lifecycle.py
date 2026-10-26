"""P05 (audit 2026-10-22): a revoked or expired share on a saved note is physically removed by
cleanup; the saved note, its revision and live shares stay (real repositories, synthetic data)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.db.session import Database
from app.domains.daily.tables import DailyNoteRow
from app.domains.history.postgres import DAILY_PURGE_WINDOW, PostgresHistoryRepository
from app.domains.readings.tables import ReadingRevisionRow
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from tests.experiments.test_postgres import NOW, _create_target
from tests.history.test_daily_window_dependencies import _cipher


async def _saved_with_shares(tmp_path: Path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'share-lifecycle.db'}")
    await database.initialize()
    envelope = _cipher()
    target = await _create_target(database, envelope)
    await PostgresSavedNoteRepository(database.sessions, envelope).save(
        SavedNoteRecord(
            id=uuid4(),
            guest_id=target.guest_id,
            daily_note_id=target.daily_note_id,
            note_snapshot={"body": "synthetic"},
            saved_at=NOW,
        )
    )
    shares = PostgresShareArtifactRepository(database.sessions, envelope)
    made = {}
    for name, token in (("live", b"l"), ("revoked", b"r"), ("expired", b"x")):
        made[name] = await shares.create(
            ShareArtifactRecord(
                id=uuid4(),
                guest_id=target.guest_id,
                daily_note_id=target.daily_note_id,
                profile_id=target.profile_id,
                revision_id=target.revision_id,
                token_hash=token * 32,
                safe_snapshot=SafeShareSnapshot(*(["synthetic"] * 8)),
                format=ShareFormat.SQUARE_1_1,
                created_at=NOW,
                expires_at=NOW + (timedelta(hours=1) if name == "expired" else timedelta(days=14)),
            )
        )
    assert await shares.revoke_owned(target.guest_id, made["revoked"].id, NOW)
    return database, envelope, target, made


@pytest.mark.asyncio
@pytest.mark.parametrize("manual", [False, True])
async def test_inactive_shares_on_a_saved_note_are_purged_and_live_ones_kept(
    tmp_path: Path, manual: bool
) -> None:
    database, envelope, target, made = await _saved_with_shares(tmp_path)
    try:
        history = PostgresHistoryRepository(database.sessions, envelope)
        cleanup_at = NOW + DAILY_PURGE_WINDOW
        if manual:
            await history.clear(target.guest_id, cleanup_at)
        else:
            assert await history.remaining(cleanup_at) >= 2
            while await history.purge_expired(cleanup_at):
                pass
            assert await history.remaining(cleanup_at) == 0
        async with database.sessions() as session:
            present = {
                name: await session.get(ShareArtifactRow, record.id) is not None
                for name, record in made.items()
            }
            assert not present["revoked"] and not present["expired"]
            # Manual clear already removes the unsaved plan and cascades its live link
            # (test_manual_clear_is_unchanged_by_the_live_share_exemption); cleanup keeps it.
            assert present["live"] is not manual
            assert await session.get(DailyNoteRow, target.daily_note_id) is not None
            # Cleanup: the live share keeps its revision (PR #38 child exemption).
            revision = await session.get(ReadingRevisionRow, target.revision_id)
            assert (revision is not None) is not manual
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_purged_links_answer_exactly_like_before(tmp_path: Path) -> None:
    """Revocation behaviour is preserved: before and after purge, revoked and expired tokens
    preview as unavailable, and the live link still works."""

    database, envelope, _target, made = await _saved_with_shares(tmp_path)
    try:
        repository = PostgresShareArtifactRepository(database.sessions, envelope)
        later = NOW + DAILY_PURGE_WINDOW
        for _ in range(2):
            for name, record in made.items():
                found = await repository.find_by_token_hash(record.token_hash)
                visible = (
                    found is not None and found.revoked_at is None and found.expires_at > later
                )
                assert visible is (name == "live")
            await PostgresHistoryRepository(database.sessions, envelope).purge_expired(later)
    finally:
        await database.dispose()
