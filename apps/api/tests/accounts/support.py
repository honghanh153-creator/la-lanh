import json
from pathlib import Path
from typing import cast
from uuid import NAMESPACE_URL, uuid5

import httpx
from fastapi.testclient import TestClient
from httpx2 import Response as ClientResponse

from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
EMAIL = "synthetic@example.org"
PROJECT = "https://abcdefghijklmnopqrst.supabase.co"
PUBLISHABLE = "sb_publishable_synthetic_offline_key_1234567890"
ADMIN = "sb_secret_synthetic_offline_key_1234567890"


class FakeTransport:
    """The only fake is at the external HTTP boundary, solely in tests."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.send_status = 200
        self.verify_status = 200
        self.invalid_identity = False
        self.erase_status = 200

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        assert str(request.url).startswith(PROJECT + "/auth/v1/")
        if request.method == "DELETE":
            assert request.headers["apikey"] == ADMIN
            assert request.url.path == f"/auth/v1/admin/users/{uuid5(NAMESPACE_URL, EMAIL)}"
            assert json.loads(request.content) == {"should_soft_delete": False}
            return httpx.Response(self.erase_status, json={})
        assert request.headers["apikey"] == PUBLISHABLE
        body = json.loads(request.content)
        assert "redirect_to" not in body
        if request.url.path.endswith("/otp"):
            assert body["create_user"] is True
            return httpx.Response(self.send_status, json={"error": "provider private email detail"})
        assert request.url.path.endswith("/verify")
        if body["token"] != "123456" or self.verify_status != 200:  # noqa: S105 - synthetic OTP
            return httpx.Response(400, json={"error": "provider private code detail"})
        return httpx.Response(
            200,
            json={
                "access_token": "provider-access-must-never-escape",
                "refresh_token": "provider-refresh-must-never-escape",
                "user": {
                    "id": str(uuid5(NAMESPACE_URL, body["email"])),
                    "email": "other@example.org" if self.invalid_identity else body["email"],
                    "email_confirmed_at": "2026-10-10T00:00:00Z",
                    "user_metadata": {"role": "admin", "guest_id": "untrusted"},
                },
            },
        )


def settings(path: Path, *, enabled: bool = True) -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite+aiosqlite:///{path}",
        cors_origins=[ORIGIN],
        auth_enabled=enabled,
        auth_delivery_approved=enabled,
        auth_supabase_url=PROJECT,
        auth_supabase_publishable_key=PUBLISHABLE,
        auth_supabase_admin_key=ADMIN,
    )


def client(path: Path, transport: FakeTransport, *, enabled: bool = True) -> TestClient:
    return TestClient(
        create_app(
            settings(path, enabled=enabled), auth_transport=httpx.MockTransport(transport.handle)
        ),
        base_url=ORIGIN,
    )


def guest(client: TestClient, key: str = "synthetic-guest-idempotency-123456") -> dict[str, object]:
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": key,
        },
    )
    assert response.status_code == 200
    return cast(dict[str, object], response.json())


def headers(csrf: object) -> dict[str, str]:
    return {"Origin": ORIGIN, "X-CSRF-Token": str(csrf)}


def request_code(
    client: TestClient,
    csrf: object = "",
    *,
    email: str = EMAIL,
    consent: bool = True,
) -> ClientResponse:
    body: dict[str, object] = {"email": email}
    if consent:
        body["account_storage_consent"] = "account-storage-v1"
    return client.post("/v1/account/login/code", headers=headers(csrf), json=body)


def verify(
    client: TestClient, challenge: dict[str, object], code: str = "123456"
) -> ClientResponse:
    return client.post(
        "/v1/account/login/verify",
        headers=headers(challenge["login_csrf_token"]),
        json={"code": code},
    )


def sign_in(client: TestClient, csrf: object) -> ClientResponse:
    challenge = request_code(client, csrf)
    assert challenge.status_code == 200
    response = verify(client, challenge.json())
    assert response.status_code == 200
    assert response.json()["status"] == "signed_in"
    return response
