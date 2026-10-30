"""Share creation is fenced after the source foreign keys were dropped (Codex r54 P2).

The service reads the owned source, then the repository inserts in its own transaction. Without
the old FK, a source deleted in between (a birth-date correction, time/place removal, cleanup)
must make the insert fail, never publish old-chart content. Both orders are covered:
remove-then-create is rejected here; create-then-remove is covered by
tests/saved/test_detached_copies.py (removal deletes the copy) and by the correction tests
(a correction keeps an existing link, D2). Real app on SQLite, synthetic data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.domains.daily.models import DailyNoteRecord
from tests.saved.copy_flow import ORIGIN, count, make_app, raw, start_guest


class _PauseAfterSourceRead:
    """The share service's source reader: reads the real note, then lets a deletion commit."""

    def __init__(self, reader: Any, database_path: Path, statements: tuple[str, ...]) -> None:
        self._reader = reader
        self._database_path = database_path
        self._statements = statements
        self.paused = False

    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord:
        note: DailyNoteRecord = await self._reader.find_owned(guest_id, note_id)
        with raw(self._database_path) as connection:
            for statement in self._statements:
                connection.execute(statement)
        self.paused = True
        return note


@pytest.mark.parametrize(
    "deleted",
    [
        ("DELETE FROM daily_notes", "DELETE FROM reading_plans"),  # what a correction deletes
        ("DELETE FROM reading_plans",),  # only the exact revision is gone
    ],
)
def test_a_source_deleted_between_read_and_insert_rejects_the_link(
    tmp_path: Path, deleted: tuple[str, ...]
) -> None:
    database_path = tmp_path / "fence.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        daily = client.get("/v1/daily-note")
        assert daily.status_code == 200
        service = app.state.share_artifact_service
        pause = _PauseAfterSourceRead(service._daily_notes, database_path, deleted)
        service._daily_notes = pause

        response = client.post(
            f"/v1/daily-note/{daily.json()['id']}/share-artifacts",
            json={"format": "story_9_16"},
            headers=headers,
        )
        assert pause.paused
        assert response.status_code == 404
        assert response.json()["code"] == "SHARE_ARTIFACT_UNAVAILABLE"
        assert "token" not in response.text
    assert count(database_path, "share_artifacts") == 0


def test_a_live_source_still_shares(tmp_path: Path) -> None:
    database_path = tmp_path / "live.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        note_id = client.get("/v1/daily-note").json()["id"]
        response = client.post(
            f"/v1/daily-note/{note_id}/share-artifacts",
            json={"format": "story_9_16"},
            headers=headers,
        )
        assert response.status_code == 200
    assert count(database_path, "share_artifacts") == 1
