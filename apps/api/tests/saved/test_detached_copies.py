"""US-23 prerequisite: saved notes and share links outlive their Daily note and revision.

Since migration 20261029_0039 the copies no longer cascade from their source. They stay listable,
unsavable, revocable, publicly readable while live, purgeable, and replayable from the journal;
guest deletion still removes them, and removing birth time or place still deletes every copy, as
its confirmation promises. Synthetic data, SQLite with foreign keys on.
"""

from __future__ import annotations

import asyncio
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import Database
from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.replay import export_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.history.postgres import PostgresHistoryRepository
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from tests.saved.copy_flow import (
    count,
    delete_sources,
    hex_id,
    make_app,
    save_and_share,
    start_guest,
)


def _envelope(app: Any) -> Any:
    return app.state.birth_chart_service._envelope


def test_copies_outlive_their_source_and_stay_manageable(tmp_path: Path) -> None:
    database_path = tmp_path / "detached.db"
    app = make_app(database_path)
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        delete_sources(database_path)

        assert count(database_path, "daily_notes") == 0
        assert count(database_path, "saved_notes") == 1
        assert count(database_path, "share_artifacts") == 1
        listed = client.get("/v1/saved-notes")
        assert listed.status_code == 200
        assert [item["daily_note_id"] for item in listed.json()] == [copies.note_id]
        assert listed.json()[0]["reading_snapshot"]["revision_id"] == copies.revision_id
        public = client.get(copies.public_path)
        assert public.status_code == 200 and public.json()["safe_snapshot"]["watermark"]

        # A detached note cannot be saved again: saving still needs a live source.
        resave = client.put(f"/v1/daily-note/{copies.note_id}/saved", headers=headers)
        assert resave.status_code != 200
        assert count(database_path, "saved_notes") == 1

        revoked = client.delete(f"/v1/share-artifacts/{copies.share_id}", headers=headers)
        assert revoked.status_code == 204
        assert client.get(copies.public_path).status_code == 404
        unsaved = client.delete(f"/v1/daily-note/{copies.note_id}/saved", headers=headers)
        assert unsaved.status_code == 204
        assert client.get("/v1/saved-notes").json() == []
        assert count(database_path, "saved_notes") == 0
        kinds = count(
            database_path,
            "erasure_journal",
            "kind IN (?, ?)",
            ErasureKind.SHARE_REVOKED.value,
            ErasureKind.SAVED_NOTE_REMOVED.value,
        )
        assert kinds == 2


def test_removing_time_or_place_still_deletes_attached_and_detached_copies(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "precision.db"
    app = make_app(database_path)
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        headers = start_guest(client)
        save_and_share(client, headers)
        delete_sources(database_path)  # a copy detached the way a date correction detaches it
        attached = save_and_share(client, headers)  # today's rebuilt note, saved and shared
        assert count(database_path, "saved_notes") == 2
        assert count(database_path, "share_artifacts") == 2
        supplement = client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "exact",
                "birth_time_local": "08:15",
                "place_id": "vn-hanoi",
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        )
        assert supplement.status_code == 200

        removed = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            json={"remove_time": False, "remove_place": True},
            headers=headers,
        )
        assert removed.status_code == 200
        # "Xóa nơi sinh và mọi note, bản lưu, link chia sẻ hiện có?" — every copy goes.
        assert count(database_path, "saved_notes") == 0
        assert count(database_path, "share_artifacts") == 0
        assert client.get(attached.public_path).status_code == 404


def test_guest_deletion_still_removes_detached_copies(tmp_path: Path) -> None:
    database_path = tmp_path / "guest-delete.db"
    app = make_app(database_path)
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        headers = start_guest(client)
        save_and_share(client, headers)
        delete_sources(database_path)
        assert client.delete("/v1/guest-session", headers=headers).status_code == 204
    assert count(database_path, "guest_sessions") == 0
    assert count(database_path, "saved_notes") == 0
    assert count(database_path, "share_artifacts") == 0


def test_cleanup_purges_a_revoked_detached_link_and_keeps_the_saved_copy(tmp_path: Path) -> None:
    database_path = tmp_path / "purge.db"
    app = make_app(database_path)
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        delete_sources(database_path)
        assert client.delete(f"/v1/share-artifacts/{copies.share_id}", headers=headers).status_code
        history = PostgresHistoryRepository(app.state.database.sessions, _envelope(app))
        purged = client.portal.call(history.purge_expired, datetime.now(UTC))  # type: ignore[union-attr]
        assert purged >= 1
    assert count(database_path, "share_artifacts") == 0
    assert count(database_path, "saved_notes", "id = ?", hex_id(copies.saved_id)) == 1


def test_journal_replay_reapplies_unsave_and_revoke_on_detached_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "live.db"
    dump = tmp_path / "dump.db"
    app = make_app(database_path)
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        delete_sources(database_path)
        shutil.copyfile(database_path, dump)  # the "backup": detached copies, nothing erased yet
        assert client.delete(f"/v1/share-artifacts/{copies.share_id}", headers=headers).status_code
        assert client.delete(f"/v1/daily-note/{copies.note_id}/saved", headers=headers).status_code
        journal, envelope = app.state.erasure_journal, _envelope(app)
        lines = client.portal.call(export_entries, app.state.database.sessions)  # type: ignore[union-attr]

    restored = Database(f"sqlite+aiosqlite:///{dump}")

    async def _replay() -> tuple[Any, Any, Any, int]:
        try:
            report = await replay(restored.sessions, journal, envelope, lines)
            async with restored.sessions() as session:
                share = await session.scalar(select(ShareArtifactRow))
                saved = await session.scalar(select(SavedNoteRow))
                held = len(tuple(await session.scalars(select(ErasureJournalRow))))
            return report, share, saved, held
        finally:
            await restored.dispose()

    report, share, saved, held = asyncio.run(_replay())
    assert report.applied[ErasureKind.SHARE_REVOKED.value] == 1
    assert report.applied[ErasureKind.SAVED_NOTE_REMOVED.value] == 1
    assert share is not None and share.revoked_at is not None
    assert saved is None
    assert held == 2
