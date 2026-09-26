from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.cloud_run import create_cloud_run_app
from app.config import Settings


@pytest.fixture
def cloud_client(tmp_path: Path) -> Iterator[TestClient]:
    web_dist = tmp_path / "dist"
    (web_dist / "assets").mkdir(parents=True)
    (web_dist / "index.html").write_text("<main>Lá Lành beta</main>", encoding="utf-8")
    (web_dist / "assets" / "app-test.js").write_text("console.log('la-lanh')", encoding="utf-8")
    application = create_cloud_run_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'cloud.db'}",
            cors_origins=["https://la-lanh-test.run.app"],
        ),
        web_dist_dir=web_dist,
    )
    with TestClient(application, base_url="https://la-lanh-test.run.app") as client:
        yield client


def test_spa_deep_link_is_served_with_browser_security_headers(
    cloud_client: TestClient,
) -> None:
    response = cloud_client.get("/radar/start", headers={"Accept": "text/html"})

    assert response.status_code == 200
    assert "Lá Lành beta" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_hashed_asset_can_be_cached_immutably(cloud_client: TestClient) -> None:
    response = cloud_client.get("/assets/app-test.js")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_unknown_api_route_never_falls_back_to_spa(cloud_client: TestClient) -> None:
    response = cloud_client.get("/v1/does-not-exist", headers={"Accept": "text/html"})

    assert response.status_code == 404
    assert "Lá Lành beta" not in response.text


def test_api_responses_are_not_cacheable(cloud_client: TestClient) -> None:
    response = cloud_client.get("/v1/health")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_staging_refuses_an_unresolved_swisseph_license_posture() -> None:
    with pytest.raises(ValidationError, match="Swiss Ephemeris"):
        Settings(
            environment="staging",
            database_url="postgresql+asyncpg://user:password@localhost/la_lanh",
            cors_origins=["https://la-lanh-test.run.app"],
            guest_cookie_secure=True,
            guest_hash_key="c3RhZ2luZy1oYXNoLWtleS0zMi1ieXRlcyEhISEhISE=",
            guest_encryption_key="c3RhZ2luZy1lbmMta2V5LTMyLWJ5dGVzISEhISEhISE=",
        )
