from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_guest_only_claims_owner_at_important_action(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'identity.db'}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "identity-guest-123456789",
            },
        )
        assert guest.status_code == 200
        assert "la_lanh_owner" not in client.cookies

        claim = client.post(
            "/v1/identity/claim",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
        )

        assert claim.status_code == 200
        assert claim.json()["resumed"] is False
        assert client.cookies.get("la_lanh_owner")
