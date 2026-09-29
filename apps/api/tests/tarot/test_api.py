from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.domains.tarot.tables import TarotSessionRow
from app.main import create_app


@pytest.fixture
def tarot_client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


def _guest_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "tarot-api-guest-1234567890",
        },
    )
    assert response.status_code == 200
    return {
        "Origin": "http://127.0.0.1:5173",
        "X-CSRF-Token": response.json()["csrf_token"],
    }


def _start(client: TestClient, headers: dict[str, str], spread: str = "one_card") -> dict[str, Any]:
    response = client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": "relationships",
            "question": "Mình nên nhìn rõ điều gì trước khi nhắn lại?",
            "spread": spread,
            "origin": "direct",
            "idempotency_key": f"tarot-start-{spread}-1234567890",
        },
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def test_guest_can_draw_resume_and_delete_without_login(tarot_client: TestClient) -> None:
    headers = _guest_headers(tarot_client)
    started = _start(tarot_client, headers)

    assert started["state"] == "choosing"
    assert started["fan_size"] == 78
    assert "deck_order" not in started
    selected = tarot_client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 17, "expected_version": started["version"]},
    )
    assert selected.status_code == 200
    result = selected.json()
    assert result["state"] == "complete"
    assert len(result["selected_cards"]) == 1
    assert (
        result["reading"]["positions"][0]["card"]["id"] == result["selected_cards"][0]["card"]["id"]
    )

    resumed = tarot_client.get(f"/v1/tarot/sessions/{started['id']}")
    assert resumed.status_code == 200
    assert resumed.json() == result

    duplicate = tarot_client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 17, "expected_version": started["version"]},
    )
    assert duplicate.status_code == 200
    assert duplicate.json() == result

    deleted = tarot_client.delete(f"/v1/tarot/sessions/{started['id']}", headers=headers)
    assert deleted.status_code == 204
    assert tarot_client.get(f"/v1/tarot/sessions/{started['id']}").status_code == 404


def test_three_card_session_rejects_competing_stale_selection(tarot_client: TestClient) -> None:
    headers = _guest_headers(tarot_client)
    started = _start(tarot_client, headers, spread="three_card")
    first = tarot_client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 4, "expected_version": 1},
    )
    assert first.status_code == 200

    stale = tarot_client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 5, "expected_version": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "TAROT_SESSION_CONFLICT"


def test_five_card_session_freezes_map_and_completes_after_five_choices(
    tarot_client: TestClient,
) -> None:
    headers = _guest_headers(tarot_client)
    started = _start(tarot_client, headers, spread="five_card")

    assert started["spread_map"] == "five_conversation"
    assert started["required_cards"] == 5
    current = started
    for fan_index in range(5):
        response = tarot_client.put(
            f"/v1/tarot/sessions/{started['id']}/selections",
            headers=headers,
            json={"fan_index": fan_index, "expected_version": current["version"]},
        )
        assert response.status_code == 200
        current = response.json()

    assert current["state"] == "complete"
    assert len(current["reading"]["positions"]) == 5
    assert current["reading"]["spread_map"] == started["spread_map"]


def test_question_gate_creates_no_session_and_returns_safe_reframe(
    tarot_client: TestClient,
) -> None:
    headers = _guest_headers(tarot_client)
    rejected = tarot_client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": "relationships",
            "question": "Người ấy chắc chắn đang nghĩ gì về mình?",
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": "tarot-rejected-1234567890",
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "TAROT_QUESTION_REFRAME_REQUIRED"
    assert "suggested_reframe" in rejected.json()

    app = cast(Any, tarot_client.app)

    async def count_rows() -> int:
        async with app.state.database.sessions() as session:
            rows = tuple(await session.scalars(select(TarotSessionRow.id)))
            return len(rows)

    assert tarot_client.portal is not None
    assert tarot_client.portal.call(count_rows) == 0


def test_tarot_payload_is_encrypted_at_rest(tarot_client: TestClient) -> None:
    headers = _guest_headers(tarot_client)
    started = _start(tarot_client, headers)

    app = cast(Any, tarot_client.app)

    async def load_row() -> TarotSessionRow:
        async with app.state.database.sessions() as session:
            row = (await session.scalars(select(TarotSessionRow))).one()
            return cast(TarotSessionRow, row)

    assert tarot_client.portal is not None
    row = tarot_client.portal.call(load_row)
    assert row.payload_ciphertext.startswith("aesgcm:")
    assert "Mình nên nhìn rõ" not in row.payload_ciphertext
    assert not hasattr(row, "question")
    assert not hasattr(row, "deck_order")
    assert str(started["id"]) not in row.payload_ciphertext


def test_expired_tarot_sessions_are_physically_purged(tarot_client: TestClient) -> None:
    headers = _guest_headers(tarot_client)
    _start(tarot_client, headers)
    app = cast(Any, tarot_client.app)
    now = datetime.now(UTC)

    async def expire_and_purge() -> tuple[int, int]:
        async with app.state.database.sessions() as session, session.begin():
            row = (await session.scalars(select(TarotSessionRow))).one()
            row.expires_at = now - timedelta(seconds=1)
        purged = await app.state.tarot_session_service.cleanup(now=now)
        async with app.state.database.sessions() as session:
            remaining = len(tuple(await session.scalars(select(TarotSessionRow.id))))
        return purged, remaining

    assert tarot_client.portal is not None
    assert tarot_client.portal.call(expire_and_purge) == (1, 0)
