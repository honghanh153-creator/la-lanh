from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_resonance_api_is_owner_bound_atomic_bounded_and_no_store() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "resonance-api-1234567890",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile",
                json={"birth_date": "1990-01-01"},
                headers=headers,
            ).status_code
            == 200
        )
        note = client.get("/v1/daily-note")
        note_id = note.json()["id"]
        revision_id = note.json()["reading_projection"]["active"]["revision_id"]
        body = {
            "choice": "hit",
            "consent_version": "reading-resonance-v1",
            "revision_id": revision_id,
            "background_lens": "relationships",
        }

        no_origin = client.put(f"/v1/daily-note/{note_id}/resonance", json=body)
        assert no_origin.status_code == 403
        assert no_origin.headers["cache-control"] == "no-store, max-age=0"
        wrong_owner = client.put(
            "/v1/daily-note/00000000-0000-4000-8000-000000000099/resonance",
            json=body,
            headers=headers,
        )
        assert wrong_owner.status_code == 404
        status = client.get("/v1/daily-note/resonance")
        assert status.json() == {
            "consented": False,
            "feedback_count": 0,
            "last_choice": None,
        }

        for invalid in (
            {**body, "choice": "change_angle"},
            {**body, "free_text": "private prose"},
            {**body, "consent_version": "old-version"},
            {**body, "revision_id": "00000000-0000-4000-8000-000000000098"},
        ):
            rejected = client.put(
                f"/v1/daily-note/{note_id}/resonance",
                json=invalid,
                headers=headers,
            )
            assert rejected.status_code in {404, 422}
            assert rejected.headers["cache-control"] == "no-store, max-age=0"
        assert client.get("/v1/daily-note/resonance").json()["feedback_count"] == 0

        recorded = client.put(
            f"/v1/daily-note/{note_id}/resonance",
            json=body,
            headers=headers,
        )
        assert recorded.status_code == 200
        assert recorded.json()["choice"] == "hit"
        assert recorded.json()["background_lens"] == "relationships"
        assert recorded.headers["cache-control"] == "no-store, max-age=0"

        duplicate = client.put(
            f"/v1/daily-note/{note_id}/resonance",
            json={**body, "choice": "miss", "background_lens": "work"},
            headers=headers,
        )
        assert duplicate.status_code == 200
        assert client.get("/v1/daily-note/resonance").json() == {
            "consented": True,
            "feedback_count": 1,
            "last_choice": "miss",
        }

        reset = client.request(
            "DELETE",
            "/v1/daily-note/resonance",
            json={"revoke_consent": False},
            headers=headers,
        )
        assert reset.status_code == 204
        assert client.get("/v1/daily-note/resonance").json() == {
            "consented": True,
            "feedback_count": 0,
            "last_choice": None,
        }

        assert (
            client.put(
                f"/v1/daily-note/{note_id}/resonance",
                json=body,
                headers=headers,
            ).status_code
            == 200
        )
        revoke = client.request(
            "DELETE",
            "/v1/daily-note/resonance",
            json={"revoke_consent": True},
            headers=headers,
        )
        assert revoke.status_code == 204
        assert client.get("/v1/daily-note/resonance").json() == {
            "consented": False,
            "feedback_count": 0,
            "last_choice": None,
        }
