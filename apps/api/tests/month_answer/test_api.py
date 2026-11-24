"""Month answers over HTTP. Synthetic births only (no real person's data)."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.db.base import Base
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


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
    with _client() as test_client:
        yield test_client


def _person(client: TestClient, key: str, *, exact: bool = True) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "history_consent_version": "history-retention-v1",
            "idempotency_key": f"month-answer-{key}-1234567890",
        },
    )
    assert guest.status_code == 200, guest.text
    headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
    birth = client.post("/v1/birth-profile", json={"birth_date": "1993-07-21"}, headers=headers)
    assert birth.status_code in {200, 201}, birth.text
    if exact:
        places = client.post("/v1/birth-places/search", json={"query": "Hà Nội"}, headers=headers)
        found = places.json()
        items = found if isinstance(found, list) else found.get("places") or found.get("results")
        supplement = client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "exact",
                "birth_time_local": "08:30",
                "place_id": items[0]["place_id"],
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        )
        assert supplement.status_code in {200, 201}, supplement.text
    return headers


def _row_counts(client: TestClient) -> dict[str, int]:
    app: Any = client.app

    async def count() -> dict[str, int]:
        async with app.state.database.sessions() as session:
            return {
                table.name: int(await session.scalar(select(func.count()).select_from(table)) or 0)
                for table in Base.metadata.sorted_tables
            }

    assert client.portal is not None
    return client.portal.call(count)


def test_status_hides_the_feature_while_copy_is_pending(client: TestClient) -> None:
    body = client.get("/v1/month/status").json()
    assert body["available"] is False
    assert body["presets"] == []
    assert "typed_questions" not in body and "consent" not in body


def test_status_once_copy_is_approved(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    response = client.get("/v1/month/status")
    assert response.headers["cache-control"].startswith("no-store")
    body = response.json()
    assert body["available"] is True
    assert len(body["presets"]) == 18
    assert {item["topic"] for item in body["presets"]} == {
        "work",
        "money",
        "love",
        "family",
        "study",
        "mind",
    }
    assert {
        "id": "work.hard_talk",
        "topic": "work",
        "text": "Làm sao nói chuyện khó với sếp?",
    } in body["presets"]


def test_topic_answer_has_three_parts_basis_and_no_date(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "topic")
    for topic in ("work", "money", "love", "family", "study", "mind"):
        response = client.post("/v1/month/answers", json={"topic": topic}, headers=headers)
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"].startswith("no-store")
        body = response.json()
        assert body["status"] == "answered"
        answer = body["answer"]
        assert answer["topic"] == topic
        assert answer["theme"] and answer["act"] and answer["say"]
        assert answer["basis"]["line"].startswith("Dựa vào: ")
        assert answer["disclaimer"] == (
            "Đây là một góc nhìn để bạn tự quyết, không phải điều chắc chắn sẽ xảy ra."
        )
        assert answer["preset"] is None and answer["question"] is None and answer["tip"] is None
        assert answer["month"] == "2026-11"
        # No dates anywhere in the answer: those only come from the on-tap window.
        assert not ISO_DATE.search(response.text)
        assert "start" not in answer and "end" not in answer


def test_answers_are_deterministic_over_http(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "same")
    first = client.post("/v1/month/answers", json={"topic": "work"}, headers=headers).json()
    second = client.post("/v1/month/answers", json={"topic": "work"}, headers=headers).json()
    assert first == second


def test_answers_differ_between_charts(approve_month: Callable[..., None]) -> None:
    approve_month()
    with _client() as client:
        exact = _person(client, "exact")
        exact_answer = client.post("/v1/month/answers", json={"topic": "work"}, headers=exact)
    with _client() as client:
        date_only = _person(client, "date-only", exact=False)
        date_answer = client.post("/v1/month/answers", json={"topic": "work"}, headers=date_only)
    assert exact_answer.status_code == date_answer.status_code == 200
    assert "Nhà tính theo cung Mặt Trời" in date_answer.json()["answer"]["basis"]["detail"]
    assert "Nhà tính theo cung Mặt Trời" not in exact_answer.json()["answer"]["basis"]["detail"]


def test_pending_copy_answers_unavailable_not_half(client: TestClient) -> None:
    headers = _person(client, "pending")
    response = client.post("/v1/month/answers", json={"topic": "work"}, headers=headers)
    assert response.status_code == 503
    assert response.json()["code"] == "MONTH_ANSWER_UNAVAILABLE"


def test_answering_stores_nothing(client: TestClient, approve_month: Callable[..., None]) -> None:
    """ "Lưu" is explicit: asking, opening the window or the card writes no row anywhere."""

    approve_month()
    headers = _person(client, "nostore")
    before = _row_counts(client)
    client.post("/v1/month/answers", json={"topic": "love"}, headers=headers)
    client.get("/v1/month/window", params={"topic": "love"}, headers=headers)
    client.get("/v1/month/overview", headers=headers)
    assert _row_counts(client) == before


def test_window_only_on_its_own_request(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "window")
    response = client.get("/v1/month/window", params={"topic": "money"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["line"] == "Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút."
    assert "2026-11-20" <= body["start"] <= body["end"]
    assert body["basis"].startswith("Dựa vào: Mặt Trăng")


def test_overview_card_has_four_areas_and_no_dates(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "overview")
    response = client.get("/v1/month/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert [item["area"] for item in body["items"]] == ["work", "love", "money", "self"]
    assert all(item["line"] and item["try_text"] for item in body["items"])
    assert not ISO_DATE.search(response.text)


def test_needs_a_guest(client: TestClient, approve_month: Callable[..., None]) -> None:
    approve_month()
    assert client.get("/v1/month/overview").status_code in {401, 403}
    assert client.post("/v1/month/answers", json={"topic": "work"}).status_code in {401, 403}


# --- preset questions (owner chose AS1 on 21.11.2026: no typed box) ----------------------------


def test_preset_question_answer(client: TestClient, approve_month: Callable[..., None]) -> None:
    approve_month()
    headers = _person(client, "preset")
    plain = client.post("/v1/month/answers", json={"topic": "work"}, headers=headers).json()
    response = client.post(
        "/v1/month/answers", json={"topic": "work", "preset": "work.hard_talk"}, headers=headers
    )
    assert response.status_code == 200, response.text
    answer = response.json()["answer"]
    assert answer["preset"] == "work.hard_talk"
    assert answer["question"] == "Làm sao nói chuyện khó với sếp?"
    assert answer["tip"]
    # The month parts and the basis still come from the chart, same as the topic answer.
    for part in ("theme", "act", "say", "basis"):
        assert answer[part] == plain["answer"][part]
    assert answer["answer_key"] != plain["answer"]["answer_key"]
    assert not ISO_DATE.search(response.text)


def test_every_preset_answers_without_yes_no(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "every-preset")
    presets = client.get("/v1/month/status").json()["presets"]
    for item in presets:
        body = {"topic": item["topic"], "preset": item["id"]}
        response = client.post("/v1/month/answers", json=body, headers=headers)
        assert response.status_code == 200, (item, response.text)
        answer = response.json()["answer"]
        assert answer["question"] == item["text"]
        for part in ("tip", "theme", "act", "say"):
            assert not re.match(r"^(Có|Không|Được|Chưa)\b", answer[part]), (item, part)


def test_preset_must_match_its_topic(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "mismatch")
    response = client.post(
        "/v1/month/answers", json={"topic": "love", "preset": "work.hard_talk"}, headers=headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "MONTH_PRESET_TOPIC_MISMATCH"


def test_free_text_is_not_accepted(client: TestClient, approve_month: Callable[..., None]) -> None:
    """No typed box: a request carrying free text is refused by validation, never read."""

    approve_month()
    headers = _person(client, "free-text")
    for body in (
        {"topic": "work", "question": "Làm sao nói với sếp là mình quá tải?"},
        {"topic": "work", "preset": "Làm sao nói với sếp là mình quá tải?"},
        {"question": "Làm sao nói với sếp là mình quá tải?"},
    ):
        response = client.post("/v1/month/answers", json=body, headers=headers)
        assert response.status_code == 422, body
        assert "quá tải" not in response.text
