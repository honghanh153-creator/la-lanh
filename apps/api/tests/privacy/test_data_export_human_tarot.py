"""The data export carries the owner's own human Tarot requests (US-24) and nothing operational.

Synthetic data only: the questions, readings and guests below are made up for the test.
"""

from __future__ import annotations

import functools
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.data_export.models import DataExport, ExportHumanTarotRequest
from app.domains.human_tarot import policy
from app.domains.tarot.knowledge import card_by_id
from app.main import create_app
from tests.human_tarot import support
from tests.human_tarot.support import DAY, QUESTION, Clock, vn

ORIGIN = "http://127.0.0.1:5173"
EXPORT = "/v1/session/data-export"
OTHER_QUESTION = "Mình nên giữ nhịp nào cho tuần làm việc sắp tới?"
REQUEST_FIELDS = set(ExportHumanTarotRequest.model_fields)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(
        create_app(
            Settings(
                environment="test",
                database_url="sqlite+aiosqlite:///:memory:",
                cors_origins=[ORIGIN],
                guest_cookie_secure=False,
                human_tarot_enabled=True,
            )
        ),
        base_url=ORIGIN,
    ) as test_client:
        _state(test_client).human_tarot_service._clock = Clock(vn(DAY, 8))
        yield test_client


def _state(client: TestClient) -> Any:
    return cast(Any, client.app).state


def _guest(client: TestClient, key: str) -> dict[str, str]:
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


def _request(
    client: TestClient, headers: dict[str, str], question: str = QUESTION, key: str = "mine"
) -> str:
    created = client.post(
        "/v1/human-tarot/requests",
        headers=headers,
        json={
            "context": "work",
            "question": question,
            "spread": "three_card",
            "consent_version": "human-tarot-v1",
            "idempotency_key": f"export-human-{key}-1234567890",
        },
    )
    assert created.status_code == 201
    return str(created.json()["id"])


def _export(client: TestClient, headers: dict[str, str], at: datetime) -> dict[str, Any]:
    """POST the export through the real route (cookie, CSRF, origin) at a fixed server time."""

    service = _state(client).data_export_service
    original = type(service).export
    service.export = functools.partial(original, service, now=at.astimezone(UTC))
    try:
        response = client.post(EXPORT, headers=headers)
    finally:
        del service.export
    assert response.status_code == 200
    body = cast(dict[str, Any], response.json())
    DataExport.model_validate(body)  # strict schema: no unexpected field
    return body


def _freeze(client: TestClient, request_id: str, at: datetime) -> None:
    human_tarot = _state(client).human_tarot_service
    database = SimpleNamespace(sessions=human_tarot._sessions)
    client.portal.call(  # type: ignore[union-attr]
        support.freeze, cast(Any, database), human_tarot, UUID(request_id), at
    )


def _slot(client: TestClient, request_id: str) -> Any:
    database = SimpleNamespace(sessions=_state(client).human_tarot_service._sessions)
    return client.portal.call(  # type: ignore[union-attr]
        support.slot_for, cast(Any, database), UUID(request_id)
    )


def test_own_request_is_exported_with_question_then_reading(client: TestClient) -> None:
    headers = _guest(client, "export-human-owner-1234567890")
    request_id = _request(client, headers)
    slot = _slot(client, request_id)

    [waiting] = _export(client, headers, vn(DAY, 9))["human_tarot_requests"]
    assert set(waiting) == REQUEST_FIELDS
    assert waiting["status"] == "waiting"
    assert waiting["question"] == QUESTION
    assert waiting["context"] == "work" and waiting["spread"] == "three_card"
    assert waiting["local_date"] == DAY.isoformat()
    assert waiting["consent_version"] == "human-tarot-v1" and waiting["consented_at"]
    assert waiting["release_at"].startswith("2026-10-30T15:00:00")
    assert waiting["reading"] is None

    _freeze(client, request_id, vn(DAY, 20))
    # Imported but before 22:00: the app does not show the reading yet, nor does the file.
    [early] = _export(client, headers, vn(DAY, 21, 59, 59))["human_tarot_requests"]
    assert early["status"] == "waiting" and early["reading"] is None

    body = _export(client, headers, vn(DAY, 22, 30))
    [ready] = body["human_tarot_requests"]
    assert ready["status"] == "ready" and ready["question"] == QUESTION
    reading = ready["reading"]
    assert reading["reader"] == "human"
    assert reading["reading"].startswith("Một bài đọc tổng hợp")
    assert reading["step"] == "Viết ra một việc nhỏ."
    assert [card["card"] for card in reading["cards"]] == [
        card_by_id(card_id).title_vi for card_id in ("major-star", "cups-5", "wands-ace")
    ]
    assert all(set(card) == {"position", "card"} for card in reading["cards"])

    # Nothing operational: no request id, request code, Sheet row or day tally.
    text = str(body)
    assert request_id not in text and slot.request_code not in text
    for key in ("delivery", "copy_cleared", "request_code", "slot_no", "sheet_state", "spread_map"):
        assert f"'{key}'" not in text
    assert "accepted_count" not in text

    # A day after release the question is erased in the app; the file follows.
    [later] = _export(client, headers, vn(DAY, 22, 30) + timedelta(hours=24))[
        "human_tarot_requests"
    ]
    assert later["question"] is None and later["reading"] is not None


def test_another_guests_requests_are_not_in_my_file(client: TestClient) -> None:
    mine = _guest(client, "export-human-mine-1234567890")
    _request(client, mine)
    other = TestClient(client.app, base_url=ORIGIN)
    theirs = _guest(other, "export-human-theirs-1234567890")
    _request(other, theirs, OTHER_QUESTION, key="theirs")

    my_body = _export(client, mine, vn(DAY, 9))
    their_body = _export(other, theirs, vn(DAY, 9))
    assert [item["question"] for item in my_body["human_tarot_requests"]] == [QUESTION]
    assert [item["question"] for item in their_body["human_tarot_requests"]] == [OTHER_QUESTION]
    assert OTHER_QUESTION not in str(my_body) and QUESTION not in str(their_body)


def test_cancelled_request_is_not_exported(client: TestClient) -> None:
    headers = _guest(client, "export-human-cancel-1234567890")
    request_id = _request(client, headers)
    assert (
        client.delete(f"/v1/human-tarot/requests/{request_id}", headers=headers).status_code == 204
    )
    # The tombstone is still readable in the app as "cancelled", but it is not exported.
    assert client.get(f"/v1/human-tarot/requests/{request_id}").json()["status"] == "cancelled"
    body = _export(client, headers, vn(DAY, 9))
    assert body["human_tarot_requests"] == []
    assert QUESTION not in str(body)


def test_deleted_reading_is_not_exported(client: TestClient) -> None:
    headers = _guest(client, "export-human-delete-1234567890")
    request_id = _request(client, headers)
    _freeze(client, request_id, vn(DAY, 20))
    assert _export(client, headers, vn(DAY, 22, 30))["human_tarot_requests"][0]["reading"]
    _state(client).human_tarot_service._clock = Clock(vn(DAY, 22, 40))
    assert (
        client.delete(f"/v1/human-tarot/requests/{request_id}", headers=headers).status_code == 204
    )
    body = _export(client, headers, vn(DAY, 22, 45))
    assert body["human_tarot_requests"] == []
    assert "Một bài đọc tổng hợp" not in str(body)


def test_history_clear_removes_the_request_from_the_file(client: TestClient) -> None:
    headers = _guest(client, "export-human-history-1234567890")
    request_id = _request(client, headers)
    _freeze(client, request_id, vn(DAY, 20))
    assert len(_export(client, headers, vn(DAY, 22, 30))["human_tarot_requests"]) == 1
    # The real clock is past DAY's release, so the clear treats the request as finished.
    assert client.delete("/v1/session/history", headers=headers).status_code == 204
    assert _export(client, headers, vn(DAY, 22, 30))["human_tarot_requests"] == []


def test_unfulfilled_request_keeps_its_status_but_no_question(client: TestClient) -> None:
    headers = _guest(client, "export-human-unfulfilled-1234567890")
    _request(client, headers)
    after_day = policy.day_end(DAY)
    [item] = _export(client, headers, after_day)["human_tarot_requests"]
    assert item["status"] == "unfulfilled"
    assert item["question"] is None and item["reading"] is None


def test_expired_request_is_not_exported(client: TestClient) -> None:
    headers = _guest(client, "export-human-expired-1234567890")
    request_id = _request(client, headers)
    _freeze(client, request_id, vn(DAY, 20))
    expires_at = policy.release_at(DAY) + policy.RESULT_KEPT_AFTER_RELEASE
    assert _export(client, headers, expires_at - timedelta(minutes=1))["human_tarot_requests"]
    assert _export(client, headers, expires_at)["human_tarot_requests"] == []


def test_human_tarot_list_is_bounded(client: TestClient) -> None:
    headers = _guest(client, "export-human-bound-1234567890")
    _request(client, headers)
    _state(client).data_export_service._max_items = 0
    body = _export(client, headers, vn(DAY, 9))
    assert body["human_tarot_requests"] == []
    assert "human_tarot_requests" in body["truncated"]
