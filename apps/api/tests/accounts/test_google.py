import base64
import hashlib
import json
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlsplit
from uuid import NAMESPACE_URL, uuid5

import httpx
import pytest
from fastapi.testclient import TestClient
from httpx2 import Response as ClientResponse
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from tests.accounts.support import EMAIL, ORIGIN, PROJECT, PUBLISHABLE, guest, headers

CALLBACK = ORIGIN + "/auth/callback"


def google_settings(path: Path, *, auth_google_callback_url: str = CALLBACK) -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite+aiosqlite:///{path}",
        cors_origins=[ORIGIN],
        auth_enabled=True,
        auth_google_enabled=True,
        auth_google_callback_url=auth_google_callback_url,
        auth_supabase_url=PROJECT,
        auth_supabase_publishable_key=PUBLISHABLE,
    )


class GoogleTransport:
    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.bad_identity = False
        self.unconfirmed = False
        self.status = 200
        self.code = "synthetic-provider-auth-code"

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        assert str(request.url) == PROJECT + "/auth/v1/token?grant_type=pkce"
        assert request.headers["apikey"] == PUBLISHABLE
        body = json.loads(request.content)
        assert body["auth_code"] == self.code
        assert 43 <= len(body["code_verifier"]) <= 128
        return httpx.Response(
            self.status,
            json={
                "access_token": "private-google-access",
                "refresh_token": "private-google-refresh",
                "provider_token": "private-google-provider-token",
                "user": {
                    "id": str(uuid5(NAMESPACE_URL, EMAIL)),
                    "email": EMAIL,
                    "email_confirmed_at": None if self.unconfirmed else "2026-10-10T00:00:00Z",
                    "is_anonymous": False,
                    "identities": [{"provider": "email" if self.bad_identity else "google"}],
                    "user_metadata": {"guest_id": "forged", "role": "admin"},
                },
            },
        )


def start(client: TestClient, csrf: object) -> dict[str, object]:
    response = client.post(
        "/v1/account/login/google",
        headers=headers(csrf),
        json={"account_storage_consent": "account-storage-v1"},
    )
    assert response.status_code == 200
    return cast(dict[str, object], response.json())


def finish(client: TestClient, nonce: str, code: str) -> ClientResponse:
    return client.post(
        "/v1/account/login/google/verify", headers=headers(nonce), json={"code": code}
    )


def test_google_pkce_links_same_guest_without_email_delivery_or_browser_bearers(
    tmp_path: Path,
) -> None:
    transport = GoogleTransport()
    app = create_app(
        google_settings(tmp_path / "google.db"),
        auth_transport=httpx.MockTransport(transport.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        created = guest(client)
        assert (
            client.post(
                "/v1/birth-profile",
                headers=headers(created["csrf_token"]),
                json={"birth_date": "1990-03-15"},
            ).status_code
            == 200
        )
        old_birth = client.get("/v1/birth-profile").json()
        begun = start(client, created["csrf_token"])
        authorize = urlsplit(str(begun["authorize_url"]))
        assert parse_qs(authorize.query)["scopes"] == ["openid email profile"]
        assert authorize.netloc == "abcdefghijklmnopqrst.supabase.co"
        query = parse_qs(authorize.query)
        assert query["provider"] == ["google"] and query["code_challenge_method"] == ["s256"]
        callback = urlsplit(query["redirect_to"][0])
        assert callback.path == "/auth/callback"
        nonce = parse_qs(callback.query)["state"][0]
        assert not transport.calls
        cookie = client.cookies.get("la_lanh_guest")
        invalid = finish(client, "forged-state", transport.code)
        assert invalid.status_code == 403 and not transport.calls
        result = finish(client, nonce, transport.code)
        assert result.status_code == 200 and result.json()["status"] == "signed_in"
        assert client.cookies.get("la_lanh_guest") != cookie
        assert client.get("/v1/birth-profile").json() == old_birth
        body = json.loads(transport.calls[0].content)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(body["code_verifier"].encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        assert query["code_challenge"] == [challenge]
        assert "private-google" not in result.text
        assert result.headers["cache-control"] == "no-store, max-age=0"
        assert finish(client, nonce, transport.code).status_code == 403
        assert len(transport.calls) == 1


def test_google_cancel_or_cookie_change_cannot_exchange_or_replace_owner(tmp_path: Path) -> None:
    transport = GoogleTransport()
    app = create_app(
        google_settings(tmp_path / "cancel.db"),
        auth_transport=httpx.MockTransport(transport.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        created = guest(client)
        begun = start(client, created["csrf_token"])
        nonce = parse_qs(
            urlsplit(parse_qs(urlsplit(str(begun["authorize_url"])).query)["redirect_to"][0]).query
        )["state"][0]
        assert client.post("/v1/account/login/cancel", headers=headers(nonce)).status_code == 204
        assert finish(client, nonce, transport.code).status_code == 403
        begun = start(client, created["csrf_token"])
        nonce = parse_qs(
            urlsplit(parse_qs(urlsplit(str(begun["authorize_url"])).query)["redirect_to"][0]).query
        )["state"][0]
        client.cookies.set("la_lanh_guest", "foreign-credential")
        assert finish(client, nonce, transport.code).status_code == 403
        assert not transport.calls


@pytest.mark.parametrize(
    "callback",
    [
        "https://evil.example/auth/callback",
        ORIGIN + "/auth/callback?next=evil",
        ORIGIN + "/home",
        "http://localhost:5173/auth/callback#fragment",
    ],
)
def test_google_callback_must_be_exact_trusted_origin_and_path(
    tmp_path: Path, callback: str
) -> None:
    with pytest.raises(ValidationError):
        google_settings(tmp_path / "config.db", auth_google_callback_url=callback)


@pytest.mark.parametrize("template", [".env.example", "infra/hetzner/app.env.example"])
def test_flags_off_environment_templates_do_not_set_invalid_empty_auth_fields(
    tmp_path: Path, template: str
) -> None:
    example = Path(__file__).resolve().parents[4] / template
    config = Settings(
        _env_file=example,
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'template.db'}",
    )
    assert not config.auth_enabled and not config.auth_google_enabled
    assert config.auth_supabase_url is None
    assert config.auth_supabase_publishable_key is None


@pytest.mark.parametrize("invalid", ["bad_identity", "unconfirmed"])
def test_google_no_unconfirmed_or_non_google_identity_is_linked(
    tmp_path: Path, invalid: str
) -> None:
    transport = GoogleTransport()
    setattr(transport, invalid, True)
    app = create_app(
        google_settings(tmp_path / "invalid.db"),
        auth_transport=httpx.MockTransport(transport.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        created = guest(client)
        begun = start(client, created["csrf_token"])
        nonce = parse_qs(
            urlsplit(parse_qs(urlsplit(str(begun["authorize_url"])).query)["redirect_to"][0]).query
        )["state"][0]
        old = client.cookies.get("la_lanh_guest")
        response = finish(client, nonce, transport.code)
        assert response.status_code == 400
        assert "private-google" not in response.text
        assert client.cookies.get("la_lanh_guest") == old
        assert client.get("/v1/account").json()["signed_in"] is False


def login_nonce(begun: dict[str, object]) -> str:
    callback = parse_qs(urlsplit(str(begun["authorize_url"])).query)["redirect_to"][0]
    return parse_qs(urlsplit(callback).query)["state"][0]


def test_google_existing_account_restores_only_after_confirmation_without_guest_merge(
    tmp_path: Path,
) -> None:
    transport = GoogleTransport()
    app = create_app(
        google_settings(tmp_path / "restore.db"),
        auth_transport=httpx.MockTransport(transport.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        first = guest(client, "synthetic-google-first-1234567890")
        assert (
            client.post(
                "/v1/birth-profile",
                headers=headers(first["csrf_token"]),
                json={"birth_date": "1990-03-15"},
            ).status_code
            == 200
        )
        expected = client.get("/v1/birth-profile").json()
        signed = finish(client, login_nonce(start(client, first["csrf_token"])), transport.code)
        assert signed.json()["status"] == "signed_in"
        assert (
            client.post(
                "/v1/account/logout", headers=headers(signed.json()["session"]["csrf_token"])
            ).status_code
            == 204
        )
        second = guest(client, "synthetic-google-second-1234567890")
        assert (
            client.post(
                "/v1/birth-profile",
                headers=headers(second["csrf_token"]),
                json={"birth_date": "1991-08-25"},
            ).status_code
            == 200
        )
        second_birth = client.get("/v1/birth-profile").json()
        nonce = login_nonce(start(client, second["csrf_token"]))
        pending = finish(client, nonce, transport.code)
        assert pending.json()["status"] == "restore_required"
        assert client.get("/v1/birth-profile").json() == second_birth
        restored = client.post(
            "/v1/account/login/restore", headers=headers(nonce), json={"confirm": True}
        )
        assert restored.status_code == 200
        assert client.get("/v1/birth-profile").json() == expected
        assert client.get("/v1/session/content-rewrite-consent").json()["consented"] is False
        assert (
            client.post(
                "/v1/account/login/restore", headers=headers(nonce), json={"confirm": True}
            ).status_code
            == 403
        )


def test_google_failed_provider_exchange_cannot_be_replayed(tmp_path: Path) -> None:
    transport = GoogleTransport()
    transport.status = 503
    app = create_app(
        google_settings(tmp_path / "failure.db"),
        auth_transport=httpx.MockTransport(transport.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        created = guest(client)
        old = client.cookies.get("la_lanh_guest")
        nonce = login_nonce(start(client, created["csrf_token"]))
        failure = finish(client, nonce, transport.code)
        assert failure.status_code == 400
        assert failure.json()["code"] == "LOGIN_VERIFICATION_FAILED"
        assert client.cookies.get("la_lanh_guest") == old
        replay = finish(client, nonce, transport.code)
        assert replay.status_code == 400
        assert replay.json()["code"] == "LOGIN_CHALLENGE_USED"
        assert len(transport.calls) == 1
