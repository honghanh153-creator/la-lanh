"""Every reading update the Home page offers ("Đọc bản mới") must open.

Regression: an approximate-time profile, and a date-only profile after a content re-read, were
offered an update whose activation answered 409 on every try, reload included. The web page
showed "Món quà chưa mở được" each time. All birth data here is fictional.
"""

from collections.abc import Iterator
from typing import cast

import pytest
from fastapi.testclient import TestClient

import app.domains.readings.application as reading_application
from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
FICTIONAL_BIRTH_DATE = "1995-04-10"
SUPPLEMENTS: dict[str, dict[str, object] | None] = {
    "date_only": None,
    "approximate": {
        "birth_time_mode": "approx_window",
        "birth_time_local": None,
        "approx_window": "morning",
        "place_id": "vn-hanoi",
        "consent_version": "birth-profile-deep-v1",
    },
    "exact": {
        "birth_time_mode": "exact",
        "birth_time_local": "08:15",
        "approx_window": None,
        "place_id": "vn-hanoi",
        "consent_version": "birth-profile-deep-v1",
    },
}
EXPECTED_ACTIVE = {
    "date_only": ("vibe_fallback", "unknown"),
    # 17.11.2026 (#626): a Daily from time-stable placements, not an empty LIMITED plan.
    "approximate": ("full_synthesis", "approximate"),
    "exact": ("full_synthesis", "exact"),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url=ORIGIN) as test_client:
        yield test_client


def _date_only_guest(client: TestClient) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "reading-update-activation-1234567890",
        },
    )
    assert guest.status_code in {200, 201}, guest.text
    headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
    created = client.post(
        "/v1/birth-profile", json={"birth_date": FICTIONAL_BIRTH_DATE}, headers=headers
    )
    assert created.status_code == 200, created.text
    return headers


def _add_birth_time(client: TestClient, headers: dict[str, str], profile: str) -> None:
    supplement = SUPPLEMENTS[profile]
    if supplement is None:
        return
    response = client.post("/v1/birth-profile/supplement", json=supplement, headers=headers)
    assert response.status_code == 200, response.text


def _projection(client: TestClient) -> dict[str, object]:
    note = client.get("/v1/daily-note")
    assert note.status_code == 200, note.text
    return cast(dict[str, object], note.json()["reading_projection"])


def _open_offered_update(
    client: TestClient, headers: dict[str, str], projection: dict[str, object]
) -> dict[str, object]:
    update = cast(dict[str, object], projection["available_update"])
    activated = client.put(
        f"/v1/reading-projections/{projection['scope_key']}/activate",
        json={"expected_revision_id": update["revision_id"]},
        headers=headers,
    )
    assert activated.status_code == 200, activated.text
    opened = cast(dict[str, object], activated.json())
    assert opened["available_update"] is None
    assert cast(dict[str, object], opened["active"])["revision_id"] == update["revision_id"]
    return opened


def _assert_settled(client: TestClient, profile: str, opened: dict[str, object]) -> None:
    mode, precision = EXPECTED_ACTIVE[profile]
    active = cast(dict[str, object], opened["active"])
    assert (active["mode"], active["precision"]) == (mode, precision)
    # A reload keeps the opened reading and offers nothing that cannot open.
    reloaded = _projection(client)
    assert reloaded["available_update"] is None
    assert cast(dict[str, object], reloaded["active"])["revision_id"] == active["revision_id"]


@pytest.mark.parametrize("profile", ["approximate", "exact"])
def test_birth_time_added_after_todays_note_opens_as_an_update(
    client: TestClient, profile: str
) -> None:
    """The reported path: today's note is read date-only, then a birth time is added."""

    headers = _date_only_guest(client)
    before = _projection(client)
    assert cast(dict[str, object], before["active"])["mode"] == "vibe_fallback"
    assert before["available_update"] is None

    _add_birth_time(client, headers, profile)
    offered = _projection(client)
    assert cast(dict[str, object], offered["active"])["mode"] == "vibe_fallback"
    assert offered["available_update"] is not None

    _assert_settled(client, profile, _open_offered_update(client, headers, offered))


@pytest.mark.parametrize("profile", ["date_only", "approximate", "exact"])
def test_a_content_re_read_opens_for_every_profile_type(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, profile: str
) -> None:
    """A content release re-reads today's note; the "Đọc bản mới" offer must open."""

    headers = _date_only_guest(client)
    _add_birth_time(client, headers, profile)
    first = _projection(client)
    assert first["available_update"] is None
    first_active = cast(dict[str, object], first["active"])
    assert (first_active["mode"], first_active["precision"]) == EXPECTED_ACTIVE[profile]

    monkeypatch.setattr(
        reading_application, "DETERMINISTIC_CONTENT_VERSION", "deterministic-reading-test-reread"
    )
    offered = _projection(client)
    assert offered["available_update"] is not None

    _assert_settled(client, profile, _open_offered_update(client, headers, offered))
