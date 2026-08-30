from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_health_reports_versioned_service_without_claiming_database_readiness(
    client: TestClient,
) -> None:
    response = client.get("/v1/health", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "la-lanh-api",
        "api_version": "v1",
        "schema_version": "1.0.0",
    }
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_readiness_fails_closed_when_postgres_is_unavailable(
    client: TestClient,
    test_app: FastAPI,
) -> None:
    async def unavailable() -> bool:
        return False

    test_app.state.readiness_probe = unavailable
    response = client.get("/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_succeeds_only_after_the_database_probe_passes(
    client: TestClient,
    test_app: FastAPI,
) -> None:
    async def available() -> bool:
        return True

    probe: Callable[[], Awaitable[bool]] = available
    test_app.state.readiness_probe = probe
    response = client.get("/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_expose_api_request_instrumentation(client: TestClient) -> None:
    client.get("/v1/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "la_lanh_http_requests_total" in response.text
    assert 'route="/v1/health"' in response.text
