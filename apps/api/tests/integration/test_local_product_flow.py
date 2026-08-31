from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_real_local_persistence_runs_guest_to_birth_reveal() -> None:
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
                "idempotency_key": "real-local-flow-1234567890",
            },
        )
        assert guest.status_code == 200
        csrf_token = guest.json()["csrf_token"]

        birth = client.post(
            "/v1/birth-profile",
            json={"birth_date": "1990-01-01"},
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": csrf_token,
            },
        )
        assert birth.status_code == 200
        assert birth.json()["calculation"]["sign"] == "capricorn"
        assert birth.json()["calculation"]["provenance"]["engine"] == "swiss_ephemeris"

        resumed = client.get("/v1/birth-profile")
        assert resumed.status_code == 200
        assert resumed.json()["snapshot_id"] == birth.json()["snapshot_id"]
