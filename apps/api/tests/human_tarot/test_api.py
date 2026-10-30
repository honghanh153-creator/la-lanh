"""US-24 HTTP contract: session, CSRF, owner-only reads, problem codes and no-store."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.human_tarot.support import DAY, QUESTION, Clock, vn

ORIGIN = "http://127.0.0.1:5173"


def _app(**settings: Any) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url="sqlite+aiosqlite:///:memory:",
                cors_origins=[ORIGIN],
                guest_cookie_secure=False,
                **settings,
            )
        ),
        base_url=ORIGIN,
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    with _app(human_tarot_enabled=True) as test_client:
        test_client.app.state.human_tarot_service._clock = Clock(vn(DAY, 8))  # type: ignore[attr-defined]
        yield test_client


def _guest(client: TestClient, key: str = "human-tarot-guest-1234567890") -> dict[str, str]:
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": key,
        },
    )
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}


def _body(**overrides: Any) -> dict[str, Any]:
    return {
        "context": "work",
        "question": QUESTION,
        "spread": "three_card",
        "consent_version": "human-tarot-v1",
        "idempotency_key": "human-tarot-create-1234567890",
        **overrides,
    }


def test_create_read_and_cancel_through_the_api(client: TestClient) -> None:
    headers = _guest(client)
    availability = client.get("/v1/human-tarot/availability")
    assert availability.status_code == 200
    assert availability.headers["cache-control"].startswith("no-store")
    assert availability.json()["accepting"] is True
    assert availability.json()["remaining"] == 10

    created = client.post("/v1/human-tarot/requests", headers=headers, json=_body())
    assert created.status_code == 201
    view = created.json()
    assert view["status"] == "waiting" and view["delivery"] == "pending"
    assert view["question"] == QUESTION and view["result"] is None
    assert view["release_at"].startswith("2026-10-30T15:00:00")  # 22:00 in Vietnam
    assert set(view) == {
        "id",
        "status",
        "delivery",
        "copy_cleared",
        "local_date",
        "release_at",
        "context",
        "spread",
        "question",
        "result",
        "expires_at",
    }
    assert client.get(f"/v1/human-tarot/requests/{view['id']}").json() == view
    assert client.get("/v1/human-tarot/requests/current").json()["id"] == view["id"]
    again = client.post("/v1/human-tarot/requests", headers=headers, json=_body())
    assert again.status_code == 201 and again.json()["id"] == view["id"]
    second = client.post(
        "/v1/human-tarot/requests",
        headers=headers,
        json=_body(idempotency_key="human-tarot-create-other-123"),
    )
    assert second.status_code == 409 and second.json()["code"] == "HUMAN_TAROT_ALREADY_REQUESTED"
    assert second.headers["cache-control"].startswith("no-store")
    assert QUESTION not in second.text

    deleted = client.delete(f"/v1/human-tarot/requests/{view['id']}", headers=headers)
    assert deleted.status_code == 204
    cancelled = client.get(f"/v1/human-tarot/requests/{view['id']}").json()
    assert cancelled["status"] == "cancelled" and cancelled["question"] is None


def test_mutations_need_origin_and_csrf(client: TestClient) -> None:
    headers = _guest(client)
    no_csrf = client.post("/v1/human-tarot/requests", headers={"Origin": ORIGIN}, json=_body())
    assert no_csrf.status_code == 403
    foreign = client.post(
        "/v1/human-tarot/requests",
        headers={**headers, "Origin": "https://evil.example"},
        json=_body(),
    )
    assert foreign.status_code == 403
    extra = client.post("/v1/human-tarot/requests", headers=headers, json=_body(birth_date="x"))
    assert extra.status_code == 422


def test_reads_need_a_session_and_stay_with_their_owner(client: TestClient) -> None:
    headers = _guest(client)
    view = client.post("/v1/human-tarot/requests", headers=headers, json=_body()).json()
    client.cookies.clear()
    public = client.get("/v1/human-tarot/availability")
    assert public.status_code == 200 and public.json()["current_request_id"] is None
    assert public.json()["remaining"] == 9
    assert client.get(f"/v1/human-tarot/requests/{view['id']}").status_code == 401
    other = _guest(client, key="human-tarot-guest-other-12345")
    missing = client.get(f"/v1/human-tarot/requests/{view['id']}")
    assert missing.status_code == 404 and missing.json()["code"] == "HUMAN_TAROT_NOT_FOUND"
    assert client.delete(f"/v1/human-tarot/requests/{view['id']}", headers=other).status_code == 404


def test_rejected_question_and_missing_consent(client: TestClient) -> None:
    headers = _guest(client)
    rejected = client.post(
        "/v1/human-tarot/requests",
        headers=headers,
        json=_body(question="Người ấy có đang nghĩ về mình không?"),
    )
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "TAROT_QUESTION_REFRAME_REQUIRED"
    assert rejected.json()["suggested_reframe"]
    consent = client.post(
        "/v1/human-tarot/requests", headers=headers, json=_body(consent_version="no")
    )
    assert consent.status_code == 422 and consent.json()["code"] == "HUMAN_TAROT_CONSENT_REQUIRED"
    assert client.get("/v1/human-tarot/availability").json()["remaining"] == 10


def test_off_by_default() -> None:
    with _app() as client:
        headers = _guest(client)
        availability = client.get("/v1/human-tarot/availability").json()
        assert availability["enabled"] is False and availability["reason"] == "disabled"
        created = client.post("/v1/human-tarot/requests", headers=headers, json=_body())
        assert created.status_code == 404 and created.json()["code"] == "HUMAN_TAROT_DISABLED"


def test_launch_needs_owner_approval_outside_local() -> None:
    with pytest.raises(ValueError, match="launch approval"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://synthetic:synthetic@127.0.0.1/synthetic",
            guest_cookie_secure=True,
            cors_origins=["https://app.example"],
            guest_hash_key="c3ludGhldGljLWhhc2gta2V5LTMyLWJ5dGVzLXRlc3Q=",
            guest_encryption_key="c3ludGhldGljLWVuY3J5cHRpb24ta2V5LTMyLWJ5dGU=",
            swisseph_license_mode="agpl",
            human_tarot_enabled=True,
        )
    with pytest.raises(ValueError, match="22:00"):
        Settings(environment="test", human_tarot_intake_closes_at="22:30")
    assert Settings(environment="test").human_tarot_intake_closes_at.hour == 18


@pytest.mark.parametrize("state", ["deleting", "expired"])
def test_admission_rechecks_the_owner_inside_the_lock(client: TestClient, state: str) -> None:
    """Codex r56: the session can turn DELETING or expire between authentication and admission;
    nothing is stored or counted for it."""

    from datetime import timedelta

    from app.domains.guest.tables import GuestSessionRow

    headers = _guest(client)
    service: Any = client.app.state.human_tarot_service  # type: ignore[attr-defined]
    original = service.create

    async def owner_changed_after_auth(**kwargs: Any) -> Any:
        async with service._sessions() as database, database.begin():
            owner = await database.get(GuestSessionRow, kwargs["guest_id"])
            if state == "deleting":
                owner.state = "deleting"
            else:
                owner.created_at = service.now() - timedelta(days=2)
                owner.expires_at = service.now() - timedelta(seconds=1)
        return await original(**kwargs)

    service.create = owner_changed_after_auth
    response = client.post("/v1/human-tarot/requests", headers=headers, json=_body())
    assert response.status_code == 401 and response.json()["code"] == "GUEST_EXPIRED"
    service.create = original
    service_view = client.portal.call(service.availability, None)  # type: ignore[union-attr]
    assert service_view.remaining == 10
