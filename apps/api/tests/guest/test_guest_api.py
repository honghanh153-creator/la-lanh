from collections.abc import Iterator
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.guest.test_guest_service import MemoryGuestRepository


@pytest.fixture
def guest_client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://la_lanh:test@127.0.0.1:5432/la_lanh_test",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        ),
        guest_repository=MemoryGuestRepository(),
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


def create_guest(guest_client: TestClient) -> dict[str, object]:
    response = guest_client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "guest-create-key-1234567890",
        },
    )
    assert response.status_code == 200
    return cast(dict[str, object], response.json())


def test_create_guest_sets_opaque_http_only_cookie_without_login(
    guest_client: TestClient,
) -> None:
    payload = create_guest(guest_client)
    cookie = guest_client.cookies.get("la_lanh_guest")

    assert cookie is not None
    assert (
        "HttpOnly"
        in guest_client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "guest-create-key-1234567890",
            },
        ).headers["set-cookie"]
    )
    assert payload["onboarding_status"] == "birth_pending"
    assert "token" not in payload
    assert "birth" not in cookie.lower()


def test_guest_resumes_from_cookie(guest_client: TestClient) -> None:
    created = create_guest(guest_client)
    response = guest_client.get("/v1/session")
    assert response.status_code == 200
    assert response.json()["state"] == "active"
    assert response.json()["session_epoch"] == created["session_epoch"]
    assert len(str(response.json()["session_epoch"])) == 64


def test_delete_requires_origin_and_csrf_then_clears_guest(guest_client: TestClient) -> None:
    payload = create_guest(guest_client)

    rejected = guest_client.delete("/v1/guest-session")
    assert rejected.status_code == 403

    deleted = guest_client.delete(
        "/v1/guest-session",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": str(payload["csrf_token"]),
        },
    )
    assert deleted.status_code == 204
    assert guest_client.get("/v1/session").status_code == 401


def test_native_mutation_accepts_explicit_app_marker_without_browser_origin(
    guest_client: TestClient,
) -> None:
    payload = create_guest(guest_client)

    deleted = guest_client.delete(
        "/v1/guest-session",
        headers={
            "X-La-Lanh-Client": "capacitor-v1",
            "X-CSRF-Token": str(payload["csrf_token"]),
        },
    )

    assert deleted.status_code == 204


def test_native_marker_does_not_bypass_an_untrusted_browser_origin(
    guest_client: TestClient,
) -> None:
    payload = create_guest(guest_client)

    rejected = guest_client.delete(
        "/v1/guest-session",
        headers={
            "Origin": "https://evil.example",
            "X-La-Lanh-Client": "capacitor-v1",
            "X-CSRF-Token": str(payload["csrf_token"]),
        },
    )

    assert rejected.status_code == 403


def test_unknown_consent_version_sets_no_cookie(guest_client: TestClient) -> None:
    response = guest_client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "unknown",
            "purpose": "birth_profile_basic",
            "idempotency_key": "guest-create-key-1234567890",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CONSENT_VERSION_INVALID"
    assert guest_client.cookies.get("la_lanh_guest") is None


def test_tarot_guest_uses_separate_reflection_consent_without_birth_data(
    guest_client: TestClient,
) -> None:
    response = guest_client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "tarot-guest-key-1234567890",
        },
    )

    assert response.status_code == 200
    assert guest_client.cookies.get("la_lanh_guest") is not None
    assert response.json()["state"] == "active"
