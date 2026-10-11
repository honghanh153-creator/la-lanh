import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import cast

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response as ClientResponse
from pydantic import SecretStr
from starlette.types import Message, Receive, Scope, Send

from app.config import Settings
from app.domains.accounts.models import Challenge
from app.domains.accounts.service import LOGIN_COOKIE, RESTORE_COOKIE, AccountService
from app.main import create_app
from tests.accounts.support import (
    EMAIL,
    FakeTransport,
    guest,
    headers,
    request_code,
    settings,
    sign_in,
    verify,
)
from tests.accounts.support import (
    client as make_client,
)

ORIGIN = "http://127.0.0.1:5173"


def test_account_validation_contract_matches_private_problem_runtime(tmp_path: Path) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "contract.db", fake) as client:
        result = client.post(
            "/v1/account/login/verify",
            headers={"Origin": ORIGIN},
            json={"code": "not-a-six-digit-code"},
        )
        assert result.status_code == 422
        assert result.headers["content-type"] == "application/problem+json"
        assert result.json()["code"] == "ACCOUNT_INPUT_INVALID"
        assert "no-store" in result.headers["cache-control"]
        spec = client.get("/openapi.json").json()
        content = spec["paths"]["/v1/account/login/verify"]["post"]["responses"]["422"]["content"]
        assert set(content) == {"application/problem+json"}
        assert set(content["application/problem+json"]["schema"]["required"]) == {
            "title",
            "status",
            "code",
        }
        assert fake.calls == []


def test_provider_erase_error_is_private_pending_503_not_false_204(tmp_path: Path) -> None:
    transport = FakeTransport()
    with make_client(tmp_path / "provider-erasure.db", transport) as client:
        created = guest(client)
        signed = sign_in(client, created["csrf_token"])
        assert signed.status_code == 200
        transport.erase_status = 500
        result = client.delete(
            "/v1/guest-session", headers=headers(signed.json()["session"]["csrf_token"])
        )
        assert result.status_code == 503
        assert result.json()["code"] == "ACCOUNT_ERASURE_PENDING"
        assert "private" not in result.text and EMAIL not in result.text
        assert "no-store" in result.headers["cache-control"]
        assert client.get("/v1/session").status_code == 401


def test_tarot_guest_cannot_store_dob_until_separate_birth_consent(tmp_path: Path) -> None:
    with make_client(tmp_path / "purpose-boundary.db", FakeTransport()) as client:
        session = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "tarot-reflection-v1",
                "purpose": "tarot_reflection",
                "idempotency_key": "synthetic-tarot-only-1234567890",
            },
        ).json()
        old_cookie = client.cookies.get("la_lanh_guest")
        csrf = session["csrf_token"]
        data = {"birth_date": "1990-03-15"}
        denied = client.post("/v1/birth-profile", headers=headers(csrf), json=data)
        assert denied.status_code == 403
        assert denied.json()["code"] == "BIRTH_CONSENT_REQUIRED"
        assert client.get("/v1/birth-profile").status_code == 404
        url = "/v1/session/birth-profile-consent"
        assert (
            client.post(
                url, headers=headers("wrong"), json={"consent_version": "birth-profile-v1"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                url,
                headers=headers(csrf),
                json={
                    "consent_version": "birth-profile-v1",
                    "guest_id": "another-owner",
                },
            ).status_code
            == 422
        )
        for _ in range(2):
            assert (
                client.post(
                    url, headers=headers(csrf), json={"consent_version": "birth-profile-v1"}
                ).status_code
                == 204
            )
        assert client.cookies.get("la_lanh_guest") == old_cookie
        assert client.post("/v1/birth-profile", headers=headers(csrf), json=data).status_code == 200
        assert client.get("/v1/session/content-rewrite-consent").json()["consented"] is False


def test_device_api_is_self_scoped_and_revocation_fences_private_routes(tmp_path: Path) -> None:
    fake = FakeTransport()
    config = settings(tmp_path / "devices.db").model_copy(
        update={
            "content_studio_enabled": True,
            "content_studio_api_token": SecretStr("synthetic-operator-test-token-1234567890"),
        }
    )
    app = create_app(config, auth_transport=httpx.MockTransport(fake.handle))
    with TestClient(app, base_url=ORIGIN) as client:
        created = guest(client)
        signed = sign_in(client, created["csrf_token"]).json()
        csrf = signed["session"]["csrf_token"]
        devices = client.get("/v1/account/devices")
        assert devices.status_code == 200
        row = devices.json()[0]
        assert set(row) == {"id", "current", "created_at", "last_active_at", "expires_at"}
        assert row["current"] is True
        assert devices.headers["Cache-Control"] == "no-store, max-age=0"
        # Provider metadata contains role=admin; it must confer no operator role.
        assert client.get("/v1/studio/workspace").status_code == 401
        url = f"/v1/account/devices/{row['id']}/revoke"
        assert client.post(url, headers=headers("wrong")).status_code == 403
        assert (
            client.post(
                url, headers={"Origin": "https://evil.example", "X-CSRF-Token": csrf}
            ).status_code
            == 403
        )
        token = client.cookies.get("la_lanh_guest")
        assert token is not None
        assert client.post(url, headers=headers(csrf)).status_code == 204
        assert client.cookies.get("la_lanh_guest") is None
        # Replaying stolen old cookies still fails after authoritative revocation.
        client.cookies.set("la_lanh_guest", token, domain="127.0.0.1", path="/")
        client.cookies.set("la_lanh_csrf", csrf, domain="127.0.0.1", path="/")
        for path in ("/v1/session", "/v1/birth-profile", "/v1/account/devices"):
            assert client.get(path).status_code == 401


def test_disabled_status_is_honest_and_code_never_creates_guest(tmp_path: Path) -> None:
    fake = FakeTransport()
    app = create_app(
        Settings(
            _env_file=None,
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'disabled.db'}",
            cors_origins=[ORIGIN],
        ),
        auth_transport=httpx.MockTransport(fake.handle),
    )
    with TestClient(app, base_url=ORIGIN) as client:
        status = client.get("/v1/account")
        assert status.status_code == 200
        assert status.json() == {
            "login_enabled": False,
            "google_login_enabled": False,
            "signed_in": False,
            "masked_email": None,
            "profile_expires_at": None,
            "guest_inactivity_days": 30,
            "history_days": 30,
            "account_inactivity_days": 365,
        }
        denied = client.post(
            "/v1/account/login/code",
            headers={"Origin": ORIGIN},
            json={"email": "synthetic@example.org"},
        )
        assert denied.status_code == 503
        assert "Set-Cookie" not in denied.headers
        assert client.get("/v1/session").status_code == 401
        assert fake.calls == []
        assert status.headers["Cache-Control"] == "no-store, max-age=0"


def rows(path: Path, table: str) -> list[tuple[object, ...]]:
    assert table in {
        "guest_sessions",
        "consents",
        "accounts",
        "account_devices",
        "birth_profiles",
        "account_login_challenges",
        "guest_session_creations",
        "daily_notes",
        "owner_sessions",
    }
    with sqlite3.connect(path) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()  # noqa: S608


@pytest.mark.parametrize("origin", [None, "https://evil.example", "null", "http://127.0.0.1:bad"])
def test_origin_cannot_be_bypassed_by_native_header(tmp_path: Path, origin: str | None) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "origin.db", fake) as client:
        supplied = {"X-La-Lanh-Client": "capacitor-v1"}
        if origin:
            supplied["Origin"] = origin
        response = client.post("/v1/account/login/code", headers=supplied, json={"email": EMAIL})
        assert response.status_code == 403
        assert fake.calls == []


@pytest.mark.parametrize(
    "code",
    ["12345", "1234567", " 123456", "\uff11\uff12\uff13\uff14\uff15\uff16", 123456, "12345a"],
)
def test_exact_otp_validation_is_generic_without_echo(tmp_path: Path, code: object) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "validation.db", fake) as client:
        response = client.post(
            "/v1/account/login/verify", headers=headers("x"), json={"code": code}
        )
        assert response.status_code == 422
        assert response.json()["code"] == "ACCOUNT_INPUT_INVALID"
        assert "input" not in response.text
        assert str(code) not in response.text
        assert fake.calls == []


@pytest.mark.parametrize("email", ["synthetic@", "private\n@example.org", "a..b@example.org"])
def test_email_validation_does_not_echo_personal_input(tmp_path: Path, email: str) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "email.db", fake) as client:
        response = request_code(client, email=email)
        assert response.status_code == 422
        assert email not in response.text
        assert "input" not in response.text
        assert fake.calls == []


def test_first_link_retains_chart_and_owner_but_invalidates_guest_and_replay(
    tmp_path: Path,
) -> None:
    path = tmp_path / "first.db"
    fake = FakeTransport()
    with make_client(path, fake) as client:
        created = guest(client)
        old_token, old_csrf = client.cookies.get("la_lanh_guest"), created["csrf_token"]
        assert (
            client.post(
                "/v1/birth-profile", headers=headers(old_csrf), json={"birth_date": "1994-03-12"}
            ).status_code
            == 200
        )
        birth_before = rows(path, "birth_profiles")
        assert client.get("/v1/daily-note").status_code == 200
        notes_before = rows(path, "daily_notes")
        assert client.post("/v1/identity/claim", headers=headers(old_csrf)).status_code == 200
        old_owner = client.cookies.get("la_lanh_owner")
        signed = sign_in(client, old_csrf)
        payload = signed.json()
        assert payload["session"]["session_epoch"] == created["session_epoch"]
        assert payload["session"]["onboarding_status"] != "birth_pending"
        assert payload["session"]["csrf_token"] != old_csrf
        assert client.cookies.get("la_lanh_guest") != old_token
        assert client.cookies.get("la_lanh_owner") is None
        assert rows(path, "birth_profiles") == birth_before
        assert rows(path, "daily_notes") == notes_before
        status = client.get("/v1/account")
        assert status.json()["signed_in"] is True
        assert status.json()["masked_email"] == "s***@example.org"
        assert EMAIL not in signed.text + status.text
        assert "provider-access" not in signed.text
        with sqlite3.connect(path) as connection:
            assert (
                connection.execute(
                    "SELECT credential_envelope FROM guest_session_creations"
                ).fetchone()[0]
                is None
            )
            assert (
                connection.execute(
                    "SELECT version FROM consents WHERE purpose='account_storage'"
                ).fetchone()[0]
                == "account-storage-v1"
            )
        replay = guest_replay(client)
        assert replay.status_code == 409
        assert "csrf_token" not in replay.text
        device = client.cookies.get("la_lanh_guest")
        client.cookies.set("la_lanh_guest", str(old_token), domain="127.0.0.1", path="/")
        assert client.get("/v1/session").status_code == 401
        client.cookies.set("la_lanh_guest", str(device), domain="127.0.0.1", path="/")
        # A late legacy owner cookie cannot authorize until the explicit client claim.
        client.cookies.set("la_lanh_owner", str(old_owner), domain="127.0.0.1", path="/v1")
        assert client.get("/v1/radar/requests").status_code == 401
        assert (
            client.post(
                "/v1/identity/claim", headers=headers(payload["session"]["csrf_token"])
            ).status_code
            == 200
        )


def guest_replay(client: TestClient) -> ClientResponse:
    return client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "synthetic-guest-idempotency-123456",
        },
    )


def test_cancel_restore_preserves_unrelated_guest_then_confirm_restores_only_account(
    tmp_path: Path,
) -> None:
    path = tmp_path / "restore.db"
    fake = FakeTransport()
    with make_client(path, fake) as first, make_client(path, fake) as second:
        first_guest = guest(first)
        assert (
            first.post(
                "/v1/birth-profile",
                headers=headers(first_guest["csrf_token"]),
                json={"birth_date": "1994-03-12"},
            ).status_code
            == 200
        )
        signed = sign_in(first, first_guest["csrf_token"]).json()
        assert first.get("/v1/account").headers.get_list("set-cookie") == []
        second_guest = guest(second, "synthetic-unrelated-guest-123456")
        assert (
            second.post(
                "/v1/birth-profile",
                headers=headers(second_guest["csrf_token"]),
                json={"birth_date": "2000-10-06"},
            ).status_code
            == 200
        )
        assert (
            second.post(
                "/v1/session/content-rewrite-consent",
                headers=headers(second_guest["csrf_token"]),
                json={"consent_version": "external-content-rewrite-v1"},
            ).status_code
            == 204
        )
        before_guest, before_birth = rows(path, "guest_sessions"), rows(path, "birth_profiles")
        before_consents = rows(path, "consents")
        # A fresh transport/session does not bypass the persisted email cooldown.
        limited = request_code(second, second_guest["csrf_token"])
        assert limited.status_code == 429
        service = cast(AccountService, cast(FastAPI, second.app).state.account_service)
        # Use a deterministic service clock to advance without sleeping / real delivery.
        from datetime import UTC, datetime, timedelta

        assert second.portal is not None

        async def issue() -> Challenge:
            return await service.request_code(
                EMAIL,
                token=second.cookies.get("la_lanh_guest"),
                csrf=str(second_guest["csrf_token"]),
                consent="account-storage-v1",
                peer="testclient",
                now=datetime.now(UTC) + timedelta(seconds=61),
            )

        challenge = second.portal.call(issue)
        second.cookies.set(LOGIN_COOKIE, challenge.cookie, domain="127.0.0.1", path="/v1/account")
        pending = verify(second, {"login_csrf_token": challenge.csrf_token})
        assert pending.json()["status"] == "restore_required"
        assert "session" not in pending.json()
        assert second.cookies.get("la_lanh_guest") != first.cookies.get("la_lanh_guest")
        assert len(rows(path, "account_devices")) == 1
        assert rows(path, "guest_sessions") == before_guest
        assert rows(path, "birth_profiles") == before_birth
        assert rows(path, "consents") == before_consents
        cancelled = second.post("/v1/account/login/cancel", headers=headers(challenge.csrf_token))
        assert cancelled.status_code == 204
        assert second.cookies.get(LOGIN_COOKIE) is None
        assert second.cookies.get(RESTORE_COOKIE) is None
        assert rows(path, "guest_sessions") == before_guest

        # Issue another challenge after the same durable cooldown.
        async def again() -> Challenge:
            return await service.request_code(
                EMAIL,
                token=second.cookies.get("la_lanh_guest"),
                csrf=str(second_guest["csrf_token"]),
                consent="account-storage-v1",
                peer="testclient",
                now=datetime.now(UTC) + timedelta(seconds=122),
            )

        next_challenge = second.portal.call(again)
        second.cookies.set(
            LOGIN_COOKIE, next_challenge.cookie, domain="127.0.0.1", path="/v1/account"
        )
        assert (
            verify(second, {"login_csrf_token": next_challenge.csrf_token}).json()["status"]
            == "restore_required"
        )
        denied = second.post(
            "/v1/account/login/restore",
            headers=headers(next_challenge.csrf_token),
            json={"confirm": False},
        )
        assert denied.status_code == 422
        # Delay delivery of a valid A private response until after confirmed B
        # restore. Both profiles remain authoritative; only B owns this jar.
        ready, release = Event(), Event()
        app = cast(FastAPI, second.app)

        async def delayed(scope: Scope, receive: Receive, send: Send) -> None:
            async def hold(message: Message) -> None:
                if message["type"] == "http.response.start":
                    ready.set()
                    assert await asyncio.to_thread(release.wait, 5)
                await send(message)

            await app(scope, receive, hold)

        late = TestClient(delayed, base_url=ORIGIN)
        late.cookies.update(second.cookies)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending_response = pool.submit(late.get, "/v1/session")
            try:
                assert ready.wait(5)
                restored = second.post(
                    "/v1/account/login/restore",
                    headers=headers(next_challenge.csrf_token),
                    json={"confirm": True},
                )
            finally:
                release.set()
            delayed_a = pending_response.result(timeout=5)
        assert delayed_a.json()["session_epoch"] == second_guest["session_epoch"]
        b_cookies = (second.cookies.get("la_lanh_guest"), second.cookies.get("la_lanh_csrf"))
        second.cookies.extract_cookies(delayed_a)
        assert (
            second.cookies.get("la_lanh_guest"),
            second.cookies.get("la_lanh_csrf"),
        ) == b_cookies
        assert delayed_a.headers.get_list("set-cookie") == []
        # The unrelated A was not revoked, merged or deleted to avoid the race.
        assert late.get("/v1/session").status_code == 200
        assert restored.status_code == 200
        assert restored.json()["session"]["session_epoch"] == signed["session"]["session_epoch"]
        assert second.get("/v1/birth-profile").json()["birth_date"] == "1994-03-12"
        assert second.get("/v1/session/content-rewrite-consent").json()["consented"] is False
        assert rows(path, "birth_profiles") == before_birth
        assert first.get("/v1/session").status_code == 200
        assert len(rows(path, "account_devices")) == 2


def test_disabled_status_and_logout_still_resolve_real_account(tmp_path: Path) -> None:
    path = tmp_path / "off-logout.db"
    fake = FakeTransport()
    with make_client(path, fake) as client:
        created = guest(client)
        old_guest = client.cookies.get("la_lanh_guest")
        signed = sign_in(client, created["csrf_token"]).json()
        app = cast(FastAPI, client.app)
        app.state.settings.auth_enabled = False
        status = client.get("/v1/account")
        assert status.json()["login_enabled"] is False
        assert status.json()["signed_in"] is True
        denied = client.post("/v1/account/logout", headers=headers("wrong"))
        assert denied.status_code == 403
        assert client.get("/v1/session").status_code == 200
        device = client.cookies.get("la_lanh_guest")
        csrf = signed["session"]["csrf_token"]
        assert client.post("/v1/account/logout", headers=headers(csrf)).status_code == 204
        assert len(rows(path, "accounts")) == 1
        assert len(rows(path, "guest_sessions")) == 1
        for stale in (device, old_guest):
            client.cookies.set("la_lanh_guest", str(stale), domain="127.0.0.1", path="/")
            assert client.get("/v1/session").status_code == 401


def test_code_failures_and_wrong_csrf_never_reset_guest(tmp_path: Path) -> None:
    path = tmp_path / "failure.db"
    fake = FakeTransport()
    with make_client(path, fake) as client:
        created = guest(client)
        before = rows(path, "guest_sessions")
        denied = request_code(client, "wrong")
        assert denied.status_code == 403
        assert fake.calls == []
        fake.send_status = 429
        unavailable = request_code(client, created["csrf_token"])
        assert unavailable.status_code == 503
        assert "provider private" not in unavailable.text
        assert "Set-Cookie" not in unavailable.headers
        assert rows(path, "guest_sessions") == before
        assert len(rows(path, "accounts")) == 0


@pytest.mark.parametrize("origin", [None, "capacitor://localhost", "https://localhost"])
def test_enabled_native_requires_guest_csrf_and_challenge_proof(
    tmp_path: Path,
    origin: str | None,
) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "native.db", fake) as client:
        created = guest(client)
        cast(FastAPI, client.app).state.settings.native_app_enabled = True
        native = {"X-La-Lanh-Client": "capacitor-v1"}
        if origin:
            native["Origin"] = origin
        denied = client.post("/v1/account/login/code", headers=native, json={"email": EMAIL})
        assert denied.status_code == 403
        assert fake.calls == []
        native["X-CSRF-Token"] = str(created["csrf_token"])
        challenge = client.post(
            "/v1/account/login/code",
            headers=native,
            json={"email": EMAIL, "account_storage_consent": "account-storage-v1"},
        )
        assert challenge.status_code == 200
        native.pop("X-CSRF-Token")
        denied = client.post("/v1/account/login/verify", headers=native, json={"code": "123456"})
        assert denied.status_code == 403
        native["X-CSRF-Token"] = challenge.json()["login_csrf_token"]
        signed = client.post("/v1/account/login/verify", headers=native, json={"code": "123456"})
        assert signed.json()["status"] == "signed_in"
        assert client.get("/v1/account").json()["signed_in"] is True


def test_enabled_native_never_allows_untrusted_web_origin(tmp_path: Path) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "evil-native.db", fake) as client:
        cast(FastAPI, client.app).state.settings.native_app_enabled = True
        denied = client.post(
            "/v1/account/login/code",
            headers={"Origin": "https://evil.example", "X-La-Lanh-Client": "capacitor-v1"},
            json={"email": EMAIL},
        )
        assert denied.status_code == 403
        assert fake.calls == []
