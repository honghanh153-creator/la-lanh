"""Codex r56 P1 on #122: dropping the source cascades must not strand an older app's deletions.

The deploy runs migrations before it replaces the app, so a release whose migration drops the
cascades would leave the previous app running for a while on a schema where its time/place
removal no longer reaches saved notes and share links. This release is the compatibility step:
it adds the explicit deletes and keeps the cascades. 20261029_0039 drops them in the next release,
and refuses to run in the same upgrade as this release's marker (tested there).

The older writer is simulated by turning the explicit copy delete off: the rest of the removal
is exactly the pre-US-23 method. Synthetic data, SQLite with foreign keys on.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

import app.domains.birth.postgres as birth_postgres
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from tests.erasure_journal.test_postgres_restore_probe import MIGRATIONS
from tests.saved.copy_flow import ORIGIN, count, make_app, save_and_share, start_guest

MARKER: Any = import_module("migrations.versions.20261029_0038a_explicit_copy_deletion_release")
SUPPLEMENT = {
    "birth_time_mode": "exact",
    "birth_time_local": "08:15",
    "place_id": "vn-hanoi",
    "consent_version": "birth-profile-deep-v1",
}


def _cascades(table: Any) -> set[tuple[str, str]]:
    return {
        (key.constraint.referred_table.name, key.constraint.ondelete or "")
        for key in table.foreign_keys
        if key.constraint.referred_table.name in {"daily_notes", "reading_revisions"}
    }


def test_this_release_keeps_the_source_cascades() -> None:
    assert ScriptDirectory(str(MIGRATIONS)).get_current_head() == MARKER.revision
    for row in (SavedNoteRow, ShareArtifactRow):
        assert _cascades(row.__table__) == {
            ("daily_notes", "CASCADE"),
            ("reading_revisions", "CASCADE"),
        }


async def _old_writer(*_: Any, **__: Any) -> None:
    """A pre-US-23 app: its removal never deleted copies itself."""


@pytest.mark.parametrize("writer", ["previous", "this"])
def test_time_or_place_removal_removes_every_copy_on_this_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writer: str
) -> None:
    if writer == "previous":
        monkeypatch.setattr(birth_postgres, "delete_copies", _old_writer)
    path = tmp_path / f"{writer}.db"
    app = make_app(path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        added = client.post("/v1/birth-profile/supplement", headers=headers, json=SUPPLEMENT)
        assert added.status_code == 200
        removed = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            headers=headers,
            json={"remove_time": False, "remove_place": True},
        )
        assert removed.status_code == 200
        facts = {
            "saved": count(path, "saved_notes"),
            "shares": count(path, "share_artifacts"),
            "public": client.get(copies.public_path).status_code,
        }
    assert facts == {"saved": 0, "shares": 0, "public": 404}


def test_the_marker_changes_no_schema_and_flags_its_own_run() -> None:
    bind = MagicMock()
    bind.info = {}
    context = MagicMock(as_sql=False)
    with (
        patch.object(MARKER.op, "get_bind", return_value=bind),
        patch.object(MARKER.op, "get_context", return_value=context),
    ):
        MARKER.upgrade()
        MARKER.downgrade()
    assert bind.info == {MARKER.APPLIED_THIS_RUN: True}
    assert bind.method_calls == []
    assert MARKER.down_revision == "20261023_0038"
