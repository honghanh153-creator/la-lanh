"""Codex auto-1 on #117: a removal after the sections were collected rebuilds the whole file.

Synthetic data only. The export is paused after its first full assembly (before the final birth
revision check); a time/place removal then deletes the Daily note and its readings. The returned
file must not carry the already-collected, now-erased Daily content.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.accounts.support import headers
from tests.radar.test_flow import _client, _full_profile


def test_a_removal_after_assembly_rebuilds_derived_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _client(tmp_path / "late-removal.db") as owner:
        csrf = _full_profile(owner, "synthetic-export-late-removal-1", "1991-02-03", "08:15")
        assert owner.get("/v1/daily-note").status_code == 200
        app: Any = owner.app
        service = app.state.data_export_service
        original = service._assemble
        entered, resume = Event(), Event()
        first: list[Any] = []

        async def paused(*args: Any) -> Any:
            result = await original(*args)
            if not first:
                first.append(result)
                entered.set()
                assert await asyncio.to_thread(resume.wait, 5)
            return result

        monkeypatch.setattr(service, "_assemble", paused)
        other = TestClient(owner.app, base_url="http://127.0.0.1:5173")
        other.cookies.update(owner.cookies)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(owner.post, "/v1/session/data-export", headers=headers(csrf))
            try:
                assert entered.wait(5)
                removal = other.request(
                    "DELETE",
                    "/v1/birth-profile/supplement",
                    headers=headers(csrf),
                    json={"remove_time": True, "remove_place": True},
                )
                assert removal.status_code == 200
            finally:
                resume.set()
            response = future.result(10)
        assert first and first[0].daily_notes, "the paused assembly held the Daily note"
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["birth_profile"]["birth_time_local"] is None
        assert all(not note.get("readings") for note in body["daily_notes"])
