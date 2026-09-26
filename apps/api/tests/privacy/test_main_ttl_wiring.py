from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_configured_identity_ttls_are_wired_into_services(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'ttl-wiring.db'}",
            guest_ttl_days=7,
            guest_replay_minutes=4,
            owner_ttl_days=6,
        )
    )

    with TestClient(app):
        assert app.state.guest_session_service._ttl == timedelta(days=7)
        assert app.state.guest_session_service._replay_window == timedelta(minutes=4)
        assert app.state.owner_identity_service._ttl == timedelta(days=6)
