"""Hợp gu share-card links (AL1 direction C, first half).

Off by default. When on: no birth data, no name beyond an initial the owner asks for, the share
headers of every capability link, revocable, never longer than the result, gone with it.
"""

import sqlite3
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.radar.cards import initial_of
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"


def _client(path: Path, *, card_links: bool) -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{path}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
            radar_share_card_links=card_links,
        )
    )
    return TestClient(app, base_url=ORIGIN)


def _result(client: TestClient) -> tuple[dict[str, str], str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "radar-card-owner-1234567890",
        },
    )
    headers = {"Origin": ORIGIN, "X-CSRF-Token": str(guest.json()["csrf_token"])}
    client.post("/v1/birth-profile", headers=headers, json={"birth_date": "1994-03-12"})
    client.post(
        "/v1/birth-profile/supplement",
        headers=headers,
        json={
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        },
    )
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    created = client.post(
        "/v1/radar/private-checks",
        headers=headers,
        json={
            "recipient_label": "Mèo Hoang",
            "context": "crush",
            "birth_date": "1996-07-21",
            "birth_time_mode": "unknown",
            "place_id": "vn-hanoi",
            "consent_version": "radar-authorized-input-v1",
            "authorization_attested": True,
        },
    )
    assert created.status_code == 200
    return headers, str(created.json()["request_id"])


def test_initial_is_one_letter_or_nothing() -> None:
    assert initial_of("  mèo hoang") == "M."
    assert initial_of("Đồng nghiệp") == "Đ."
    assert initial_of("123 !!") is None


def test_card_links_are_off_by_default(tmp_path: Path) -> None:
    with _client(tmp_path / "off.db", card_links=False) as client:
        headers, request_id = _result(client)
        assert client.get("/v1/public/radar/consent-options").json()["card_links"] is False
        made = client.post(f"/v1/radar/results/{request_id}/cards", headers=headers, json={})
        assert made.status_code == 404
        assert client.get(f"/v1/public/radar/cards/{'a' * 43}").status_code == 404


def test_card_link_shows_no_birth_data_and_dies_with_the_result(tmp_path: Path) -> None:
    database = tmp_path / "on.db"
    with _client(database, card_links=True) as client:
        headers, request_id = _result(client)
        assert client.get("/v1/public/radar/consent-options").json()["card_links"] is True

        made = client.post(f"/v1/radar/results/{request_id}/cards", headers=headers, json={})
        assert made.status_code == 200
        assert made.headers["cache-control"].startswith("no-store")
        token = made.json()["share_url"].rsplit("/", 1)[-1]
        result_expiry = client.get(f"/v1/radar/results/{request_id}").json()["expires_at"]
        assert made.json()["expires_at"] == result_expiry

        viewer = TestClient(client.app, base_url=ORIGIN)  # anyone with the link, no session
        card = viewer.get(f"/v1/public/radar/cards/{token}")
        assert card.status_code == 200
        assert card.headers["cache-control"].startswith("no-store")
        assert card.headers["referrer-policy"] == "no-referrer"
        assert card.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        body = card.json()
        assert body["initial"] is None and body["context"] == "crush"
        assert body["tier"] and body["line"]
        for raw in ("1996", "1994", "Mèo", "Hoang", "vn-hanoi", "08:15"):
            assert raw not in card.text

        named = client.post(
            f"/v1/radar/results/{request_id}/cards", headers=headers, json={"show_initial": True}
        ).json()
        named_token = named["share_url"].rsplit("/", 1)[-1]
        assert viewer.get(f"/v1/public/radar/cards/{named_token}").json()["initial"] == "M."

        listed = client.get(f"/v1/radar/results/{request_id}/cards").json()
        assert [item["status"] for item in listed] == ["active", "active"]
        assert all(item["share_url"] is None for item in listed)
        assert token not in client.get(f"/v1/radar/results/{request_id}/cards").text

        # A stranger cannot revoke; the owner can, and the link stops at once.
        stranger = TestClient(client.app, base_url=ORIGIN)
        assert (
            stranger.post(f"/v1/radar/cards/{named['id']}/revoke", headers=headers).status_code
            != 204
        )
        assert (
            client.post(f"/v1/radar/cards/{named['id']}/revoke", headers=headers).status_code == 204
        )
        assert viewer.get(f"/v1/public/radar/cards/{named_token}").status_code == 404

        # Five live links per result at most.
        for _ in range(4):
            client.post(f"/v1/radar/results/{request_id}/cards", headers=headers, json={})
        limited = client.post(f"/v1/radar/results/{request_id}/cards", headers=headers, json={})
        assert limited.status_code == 429

        # Deleting the result removes every card link with it.
        assert client.delete(f"/v1/radar/results/{request_id}", headers=headers).status_code == 204
        assert viewer.get(f"/v1/public/radar/cards/{token}").status_code == 404
        with sqlite3.connect(database) as connection:
            assert connection.execute("SELECT COUNT(*) FROM radar_share_cards").fetchone()[0] == 0
