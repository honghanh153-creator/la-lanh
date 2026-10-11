from pathlib import Path
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domains.mood.models import MoodValue
from tests.radar.test_flow import ORIGIN, _client, _full_profile


def test_new_guest_drops_previous_owner_and_recipient_capabilities(tmp_path: Path) -> None:
    with _client(tmp_path / "isolation.db") as client:
        csrf = _full_profile(client, "synthetic-owner-a-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert client.post("/v1/identity/claim", headers=headers).status_code == 200
        owner_cookie = cast(FastAPI, client.app).state.settings.owner_cookie_name
        assert client.cookies.get(owner_cookie) is not None
        client.cookies.set(
            "la_lanh_radar_invite",
            "synthetic-old-invite",
            domain="127.0.0.1",
            path="/v1/public/radar",
        )
        client.cookies.set(
            "la_lanh_radar_receipt",
            "synthetic-old-receipt",
            domain="127.0.0.1",
            path="/v1/public/radar/receipt",
        )

        response = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "synthetic-owner-b-123456789",
            },
        )

        assert response.status_code == 200
        assert client.cookies.get(owner_cookie) is None
        assert client.cookies.get("la_lanh_radar_invite") is None
        assert client.cookies.get("la_lanh_radar_receipt") is None
        assert client.get("/v1/radar/requests").status_code == 401


def test_stale_owner_cookie_cannot_read_a_after_guest_switches_to_b(tmp_path: Path) -> None:
    with _client(tmp_path / "stale-owner.db") as client:
        csrf = _full_profile(client, "synthetic-source-a-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert client.post("/v1/identity/claim", headers=headers).status_code == 200
        created = client.post(
            "/v1/radar/requests",
            headers=headers,
            json={
                "recipient_label": "Synthetic A only",
                "context": "friend",
            },
        )
        assert created.status_code == 200
        assert "Synthetic A only" in client.get("/v1/radar/requests").text
        owner_cookie = cast(FastAPI, client.app).state.settings.owner_cookie_name
        previous_owner = client.cookies.get(owner_cookie)
        assert previous_owner is not None

        csrf_b = _full_profile(client, "synthetic-source-b-123456789", "2000-10-06", "14:30")
        # A late response/legacy client can reintroduce a cookie; the server
        # must still reject mismatched owner and guest credentials on GET.
        client.cookies.set(owner_cookie, previous_owner, domain="127.0.0.1", path="/v1")
        rejected = client.get("/v1/radar/requests")
        assert rejected.status_code == 401
        assert "Synthetic A only" not in rejected.text
        assert client.get("/v1/la-chung/requests").status_code == 401
        assert client.get("/v1/matching/readiness").status_code == 401

        assert (
            client.post(
                "/v1/identity/claim",
                headers={
                    "Origin": ORIGIN,
                    "X-CSRF-Token": csrf_b,
                },
            ).status_code
            == 200
        )
        own = client.get("/v1/radar/requests")
        assert own.status_code == 200
        assert own.json() == []


def test_same_guest_idempotent_create_preserves_owner_binding(tmp_path: Path) -> None:
    with _client(tmp_path / "same-guest.db") as client:
        key = "synthetic-idempotent-123456789"
        csrf = _full_profile(client, key, "1994-03-12", "08:15")
        assert (
            client.post(
                "/v1/identity/claim",
                headers={
                    "Origin": ORIGIN,
                    "X-CSRF-Token": csrf,
                },
            ).status_code
            == 200
        )
        epoch = client.get("/v1/session").json()["session_epoch"]
        retried = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": key,
            },
        )
        assert retried.status_code == 200
        assert retried.json()["session_epoch"] == epoch
        assert (
            client.cookies.get(cast(FastAPI, client.app).state.settings.owner_cookie_name)
            is not None
        )
        assert client.get("/v1/radar/requests").status_code == 200


def test_independent_cookie_jars_keep_notes_and_foreign_note_access_separate(
    tmp_path: Path,
) -> None:
    with _client(tmp_path / "two-guests.db") as guest_a:
        guest_b = TestClient(guest_a.app, base_url=ORIGIN)
        csrf_a = _full_profile(guest_a, "independent-guest-a-123456789", "1994-03-12", "08:15")
        csrf_b = _full_profile(guest_b, "independent-guest-b-123456789", "2000-10-06", "14:30")
        session_a = guest_a.get("/v1/session").json()
        session_b = guest_b.get("/v1/session").json()
        assert session_a["session_epoch"] != session_b["session_epoch"]
        note_a = guest_a.get("/v1/daily-note")
        note_b = guest_b.get("/v1/daily-note")
        assert note_a.status_code == note_b.status_code == 200
        assert note_a.json()["id"] != note_b.json()["id"]
        assert guest_a.get("/v1/daily-note").json()["id"] == note_a.json()["id"]
        for client, csrf, foreign_id in (
            (guest_a, csrf_a, note_b.json()["id"]),
            (guest_b, csrf_b, note_a.json()["id"]),
        ):
            path = f"/v1/daily-note/{foreign_id}/mood"
            assert client.get(path).status_code == 404
            assert (
                client.put(
                    path,
                    json={"mood": MoodValue.CHILL},
                    headers={
                        "Origin": ORIGIN,
                        "X-CSRF-Token": csrf,
                    },
                ).status_code
                == 404
            )
