"""Luna sprint S1: a surface that is off never compiles a rewrite job.

ContentRewriteService.enqueue already refuses an off surface, so nothing was stored; but Tarot and
Radar still built the payload for every reading and logged an "enqueue failed" warning, because
they only looked at the global generation flag (on for the Daily pilot).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(rollout: dict[str, str]) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
            generation_enabled=True,
            generation_provider="openai",
            generation_governance_approved=True,
            generation_surface_rollout=rollout,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


@pytest.fixture
def daily_only() -> Iterator[TestClient]:
    yield from _client({"daily_home": "full"})


def test_daily_only_rollout_keeps_tarot_and_radar_from_building_jobs(
    daily_only: TestClient,
) -> None:
    state = daily_only.app.state  # type: ignore[attr-defined]
    assert state.tarot_session_service._generation_enabled is False
    if state.radar_service is not None:
        assert state.radar_service._generation_enabled is False
    if state.reading_application_service is not None:
        assert state.reading_application_service._generation_enabled is True
