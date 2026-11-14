"""Crisis guard over HTTP: no reading, nothing stored, nothing logged. Synthetic text only."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.crisis_guard import CRISIS_NOTICE_CODE
from app.config import Settings
from app.domains.human_tarot.tables import HumanTarotRequestRow
from app.domains.safety.crisis import CRISIS_NOTICE_TEXT
from app.domains.tarot.tables import TarotSessionRow
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
CRISIS_QUESTION = "Dạo này mình chỉ muốn chết thôi, có nên không"
CANARY = "zqcanary7crisis"


def _client(**settings: Any) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url="sqlite+aiosqlite:///:memory:",
                cors_origins=[ORIGIN],
                guest_cookie_name="la_lanh_guest",
                guest_cookie_secure=False,
                **settings,
            )
        ),
        base_url=ORIGIN,
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    with _client(human_tarot_enabled=True) as test_client:
        yield test_client


def _guest(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "crisis-guard-guest-1234567890",
        },
    )
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}


def _count(client: TestClient, row: Any) -> int:
    app: Any = client.app

    async def count() -> int:
        async with app.state.database.sessions() as session:
            return int(await session.scalar(select(func.count()).select_from(row)) or 0)

    assert client.portal is not None
    return client.portal.call(count)


def _tarot_body(question: str, key: str = "crisis-guard-tarot-1234567890") -> dict[str, Any]:
    return {
        "context": "general",
        "question": question,
        "spread": "one_card",
        "origin": "direct",
        "idempotency_key": key,
    }


def _assert_crisis(response: Any, *texts: str) -> None:
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["cache-control"].startswith("no-store")
    body = response.json()
    assert body["code"] == CRISIS_NOTICE_CODE
    assert body["notice"] == {"copy_id": "crisis.self_harm.notice", "text": CRISIS_NOTICE_TEXT}
    assert set(body) == {"type", "title", "status", "code", "notice"}
    assert "tel:" not in response.text
    for text in texts:
        assert text not in response.text


def test_tarot_crisis_question_gets_the_notice_and_no_session(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    headers = _guest(client)
    question = f"{CRISIS_QUESTION} {CANARY}"
    with caplog.at_level(logging.DEBUG):
        response = client.post("/v1/tarot/sessions", headers=headers, json=_tarot_body(question))
    _assert_crisis(response, CANARY, question)
    assert _count(client, TarotSessionRow) == 0
    assert CANARY not in caplog.text


def test_tarot_short_crisis_text_is_caught_before_length_validation(client: TestClient) -> None:
    headers = _guest(client)
    response = client.post("/v1/tarot/sessions", headers=headers, json=_tarot_body("tự tử"))
    _assert_crisis(response, "tự tử")
    assert _count(client, TarotSessionRow) == 0


def test_tarot_notice_needs_no_session_and_reveals_nothing_about_one(client: TestClient) -> None:
    response = client.post(
        "/v1/tarot/sessions", headers={"Origin": ORIGIN}, json=_tarot_body(CRISIS_QUESTION)
    )
    _assert_crisis(response, CRISIS_QUESTION)
    assert "set-cookie" not in response.headers


def test_tarot_figurative_question_still_gets_a_session(client: TestClient) -> None:
    headers = _guest(client)
    response = client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json=_tarot_body("Deadline dí chết, mình nên làm phần nào trước?"),
    )
    assert response.status_code == 201
    assert _count(client, TarotSessionRow) == 1


def test_tarot_crisis_retry_with_same_key_still_stores_nothing(client: TestClient) -> None:
    headers = _guest(client)
    for _ in range(2):
        response = client.post(
            "/v1/tarot/sessions", headers=headers, json=_tarot_body("minh muon chet")
        )
        _assert_crisis(response)
    assert _count(client, TarotSessionRow) == 0


def test_human_tarot_crisis_question_gets_the_notice_and_no_request(client: TestClient) -> None:
    headers = _guest(client)
    response = client.post(
        "/v1/human-tarot/requests",
        headers=headers,
        json={
            "context": "work",
            "question": f"Em không muốn sống nữa {CANARY}",
            "spread": "three_card",
            "consent_version": "human-tarot-v1",
            "idempotency_key": "crisis-guard-human-1234567890",
        },
    )
    _assert_crisis(response, CANARY)
    assert _count(client, HumanTarotRequestRow) == 0


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        (
            "POST",
            "/v1/la-chung/requests",
            {
                "recipient_label": "muốn chết",
                "context": "friend",
                "idempotency_key": "crisis-guard-la-chung-1",
            },
        ),
        (
            "POST",
            "/v1/public/la-chung/synthetic-token/responses",
            {
                "statement_ids": ["a", "b", "c"],
                "identity_mode": "alias",
                "display_alias": "muon tu tu",
                "idempotency_key": "crisis-guard-alias-1",
            },
        ),
        (
            "POST",
            "/v1/radar/requests",
            {"recipient_label": "chán sống", "context": "friend"},
        ),
        (
            "POST",
            "/v1/radar/private-checks",
            {
                "recipient_label": "kms",
                "context": "friend",
                "birth_date": "2000-01-01",
                "birth_time_mode": "unknown",
                "place_id": "synthetic-place",
                "consent_version": "synthetic",
                "authorization_attested": True,
            },
        ),
        (
            "PUT",
            "/v1/matching/profile",
            {
                "display_name": "Tự sát",
                "gender_identity": "x",
                "intent": "x",
                "gender_preference": "x",
                "min_age": 18,
                "max_age": 30,
                "region_code": "synthetic",
            },
        ),
    ],
)
def test_every_other_free_text_field_is_guarded(
    client: TestClient, method: str, path: str, body: dict[str, Any]
) -> None:
    headers = _guest(client)
    response = client.request(method, path, headers=headers, json=body)
    _assert_crisis(response)


def test_guarded_label_with_ordinary_text_reaches_its_endpoint(client: TestClient) -> None:
    headers = _guest(client)
    response = client.post(
        "/v1/radar/requests",
        headers=headers,
        json={"recipient_label": "Bạn cùng lớp", "context": "friend"},
    )
    assert response.status_code != 422 or response.json().get("code") != CRISIS_NOTICE_CODE
