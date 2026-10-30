"""Codex r55 on #117: the export's counterexamples, kept as regressions (synthetic data only).

1. A time/place removal that commits while an export is in flight must not leave the removed
   precision (or a chart computed from it) in the file.
2. The Daily reading the person sees (the active reading revision) is in the file, not only the
   legacy note text.
3. Nested lists (account devices, Matching consents) obey the export bound, newest first, and are
   named in ``truncated`` when cut.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.accounts.support import headers
from tests.radar.test_flow import _client, _full_profile


def _app(client: TestClient) -> Any:
    return client.app  # a FastAPI app; typed as plain ASGI by Starlette


def _export(client: TestClient, csrf: str) -> dict[str, Any]:
    response = client.post("/v1/session/data-export", headers=headers(csrf))
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def test_a_removal_during_the_export_leaves_no_removed_precision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _client(tmp_path / "removed.db") as owner:
        csrf = _full_profile(owner, "synthetic-export-removal-123456", "1991-02-03", "08:15")
        service = _app(owner).state.data_export_service
        original = service._birth_profile
        entered, resume = Event(), Event()
        calls: list[int] = []

        async def blocked(*args: Any) -> Any:
            result = await original(*args)
            calls.append(1)
            if len(calls) == 1:
                entered.set()
                assert await asyncio.to_thread(resume.wait, 5)
            return result

        monkeypatch.setattr(service, "_birth_profile", blocked)
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
        assert response.status_code == 200, response.text
        birth = response.json()["birth_profile"]
        assert birth["birth_time_local"] is None and birth["place_display_name"] is None
        assert birth["calculation_kind"] == "date_only_sun"


def test_the_visible_daily_reading_is_in_the_file(tmp_path: Path) -> None:
    with _client(tmp_path / "daily.db") as owner:
        csrf = _full_profile(owner, "synthetic-export-daily-12345678", "1991-02-03", "08:15")
        note = owner.get("/v1/daily-note")
        assert note.status_code == 200
        active = note.json()["reading_projection"]["active"]
        exported = _export(owner, csrf)["daily_notes"][0]
        texts = [text for text in active["sections"].values() if isinstance(text, str) and text]
        assert texts and all(text in str(exported["readings"]) for text in texts)
        reading = exported["readings"][0]
        assert reading["disclaimer"] == active["disclaimer"]
        assert set(reading) == {"sections", "evidence", "disclaimer"}  # no ids, drafts or keys


def test_nested_lists_are_bounded_newest_first_and_reported(tmp_path: Path) -> None:
    from app.domains.identity.tables import PrincipalRow
    from app.domains.matching.tables import MatchingConsentRow

    with _client(tmp_path / "bounded.db") as owner:
        csrf = _full_profile(owner, "synthetic-export-bounds-1234567", "1991-02-03", "08:15")
        assert owner.post("/v1/identity/claim", headers=headers(csrf)).status_code == 200
        now = datetime.now(UTC)

        async def seed(count: int, first_day: int) -> None:
            async with _app(owner).state.database.sessions() as session, session.begin():
                principal = await session.scalar(select(PrincipalRow))
                assert principal is not None
                for index in range(count):
                    session.add(
                        MatchingConsentRow(
                            principal_id=principal.id,
                            version="matching-v1",
                            purpose="matching",
                            accepted_at=now - timedelta(days=first_day + index),
                            revoked_at=now,
                        )
                    )

        assert owner.portal is not None
        owner.portal.call(seed, 2, 1)
        _app(owner).state.data_export_service._max_items = 2
        at_bound = _export(owner, csrf)
        assert len(at_bound["matching"]["consents"]) == 2
        assert "matching.consents" not in at_bound["truncated"]
        owner.portal.call(seed, 1, 3)
        above = _export(owner, csrf)
        consents = above["matching"]["consents"]
        assert len(consents) == 2 and "matching.consents" in above["truncated"]
        assert consents[0]["accepted_at"] > consents[1]["accepted_at"]  # newest first


def test_account_devices_are_bounded_newest_first_and_reported(tmp_path: Path) -> None:
    from tests.accounts.support import FakeTransport, guest, sign_in
    from tests.accounts.support import client as make_client

    with make_client(tmp_path / "devices.db", FakeTransport()) as owner:
        created = guest(owner)
        signed = sign_in(owner, created["csrf_token"]).json()
        csrf = signed["session"]["csrf_token"]
        service = _app(owner).state.data_export_service
        from app.domains.accounts.tables import AccountDeviceRow

        async def add_devices() -> None:
            async with _app(owner).state.database.sessions() as session, session.begin():
                existing = await session.scalar(select(AccountDeviceRow))
                assert existing is not None
                for index in range(2):
                    session.add(
                        AccountDeviceRow(
                            **{
                                column.name: getattr(existing, column.name)
                                for column in AccountDeviceRow.__table__.columns
                                if column.name not in {"id", "credential_digest", "created_at"}
                            },
                            credential_digest=bytes([index + 1]) * 32,
                            created_at=existing.created_at - timedelta(days=index + 1),
                        )
                    )

        assert owner.portal is not None
        owner.portal.call(add_devices)
        service._max_items = 2
        body = _export(owner, csrf)
        devices = body["account"]["devices"]
        assert len(devices) == 2 and "account.devices" in body["truncated"]
        assert devices[0]["created_at"] > devices[1]["created_at"]
