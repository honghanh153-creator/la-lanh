import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_chart_snapshot_payload_is_encrypted_at_rest(tmp_path: Path) -> None:
    database_path = tmp_path / "encrypted-chart.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
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
                "idempotency_key": "encrypted-chart-guest-123456",
            },
        )
        created = client.post(
            "/v1/birth-profile",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
            json={"birth_date": "1990-01-01"},
        )
        assert created.status_code == 200
        assert client.get("/v1/birth-profile").status_code == 200

    with sqlite3.connect(database_path) as connection:
        result_payload, result_ciphertext = connection.execute(
            "SELECT result_payload, result_ciphertext FROM chart_snapshots"
        ).fetchone()
    # SQL JSON adapters may encode an explicit JSON null as the literal "null".
    assert result_payload in {None, "null"}
    assert result_ciphertext.startswith("aesgcm:")
    assert "capricorn" not in result_ciphertext
