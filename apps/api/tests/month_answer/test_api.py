"""Month answers over HTTP. Synthetic births and questions only (no real person's data)."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.crisis_guard import CRISIS_NOTICE_CODE
from app.config import Settings
from app.db.base import Base
from app.main import create_app
from app.middleware import admission

from ..safety.crisis_phrases import NEGATIVES, POSITIVES

ORIGIN = "http://127.0.0.1:5173"
CANARY = "zqcanary7month"
CONSENT = "month-typed-question-v1"
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


@pytest.fixture
def typed_client() -> Iterator[TestClient]:
    with _client(month_typed_questions_enabled=True) as test_client:
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
    assert body["typed_questions"] is False
    assert body["consent"] is None


def test_status_once_copy_is_approved(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    response = client.get("/v1/month/status")
    assert response.headers["cache-control"].startswith("no-store")
    assert response.json()["available"] is True
    assert response.json()["typed_questions"] is False  # switch is off by default


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
        assert answer["reframe"] is None
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


# --- typed questions ---------------------------------------------------------------------------


def test_typed_question_refused_while_switched_off(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month(owner=True)
    headers = _person(client, "off")
    response = client.post(
        "/v1/month/answers",
        json={"question": "Làm sao nói với sếp là mình quá tải?", "consent_version": CONSENT},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "MONTH_TYPED_QUESTIONS_OFF"


def test_typed_question_needs_owner_approved_consent_even_when_on(
    typed_client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()  # month copy approved, consent and crisis copy still pending
    headers = _person(typed_client, "consent-pending")
    assert typed_client.get("/v1/month/status").json()["typed_questions"] is False
    response = typed_client.post(
        "/v1/month/answers",
        json={"question": "Làm sao nói với sếp là mình quá tải?", "consent_version": CONSENT},
        headers=headers,
    )
    assert response.status_code == 403


def test_typed_question_needs_consent(
    typed_client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month(owner=True)
    status = typed_client.get("/v1/month/status").json()
    assert status["typed_questions"] is True
    assert status["consent"]["version"] == CONSENT
    headers = _person(typed_client, "consent")
    response = typed_client.post(
        "/v1/month/answers",
        json={"question": "Làm sao nói với sếp là mình quá tải?"},
        headers=headers,
    )
    assert response.status_code == 428


def test_typed_outcome_question_gets_no_yes_no_and_is_not_echoed_logged_or_stored(
    typed_client: TestClient,
    approve_month: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    approve_month(owner=True)
    headers = _person(typed_client, "outcome")
    before = _row_counts(typed_client)
    question = f"Buổi phỏng vấn tới {CANARY} mình có đậu không?"
    with caplog.at_level(logging.DEBUG):
        response = typed_client.post(
            "/v1/month/answers",
            json={"question": question, "consent_version": CONSENT},
            headers=headers,
        )
    assert response.status_code == 200, response.text
    answer = response.json()["answer"]
    assert answer["topic"] == "work"
    assert answer["reframe"] == (
        "Lá không đoán được chuyện này sẽ ra sao. Đây là việc giúp bạn có thêm cơ hội."
    )
    for part in ("theme", "act", "say"):
        assert not re.match(r"^(Có|Không|Được|Chưa)\b", answer[part])
    assert CANARY not in response.text
    assert CANARY not in caplog.text
    assert _row_counts(typed_client) == before


def test_typed_question_without_a_topic_asks_for_one(
    typed_client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month(owner=True)
    headers = _person(typed_client, "need-topic")
    response = typed_client.post(
        "/v1/month/answers",
        json={"question": "Tháng này thế nào nhỉ?", "consent_version": CONSENT},
        headers=headers,
    )
    assert response.json() == {
        "status": "need_topic",
        "answer": None,
        "need_topic": "Lá chưa rõ câu này thuộc chuyện gì. Bạn chọn một mảng bên dưới nhé.",
    }


def test_same_typed_question_same_answer(
    typed_client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month(owner=True)
    headers = _person(typed_client, "same-typed")
    body = {"question": "Cuối tháng này mình có đủ tiền ăn không?", "consent_version": CONSENT}
    first = typed_client.post("/v1/month/answers", json=body, headers=headers).json()
    second = typed_client.post("/v1/month/answers", json=body, headers=headers).json()
    assert first == second and first["answer"]["topic"] == "money"


# --- crisis guard on typed text -----------------------------------------------------------------


def _post_in_budget(
    client: TestClient, _index: int, body: dict[str, str], headers: dict[str, str]
) -> Any:
    response = client.post("/v1/month/answers", json=body, headers=headers)
    assert response.status_code != 429
    return response


@pytest.fixture
def no_admission_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hundreds of phrases from one peer: the per-minute backstop is not under test here."""

    monkeypatch.setattr(admission, "_policy", lambda _request: None)


def _assert_month_crisis(response: Any, notice_copy_id: str) -> None:
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == CRISIS_NOTICE_CODE
    assert body["notice"]["copy_id"] == notice_copy_id
    assert response.headers["cache-control"].startswith("no-store")


@pytest.mark.usefixtures("no_admission_limit")
def test_every_crisis_phrase_is_routed_on_the_typed_path(
    typed_client: TestClient,
    approve_month: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    approve_month(owner=True)
    headers = _person(typed_client, "crisis")
    before = _row_counts(typed_client)
    with caplog.at_level(logging.DEBUG):
        for index, phrase in enumerate(POSITIVES):
            response = _post_in_budget(
                typed_client,
                index,
                {"question": phrase, "consent_version": CONSENT},
                headers,
            )
            _assert_month_crisis(response, "crisis.self_harm.notice.month")
            assert phrase not in response.text
        canary = typed_client.post(
            "/v1/month/answers",
            json={"question": f"Mình muốn chết {CANARY}", "consent_version": CONSENT},
            headers=headers,
        )
        _assert_month_crisis(canary, "crisis.self_harm.notice.month")
    assert CANARY not in canary.text
    assert CANARY not in caplog.text
    assert _row_counts(typed_client) == before


def test_crisis_text_is_routed_before_the_switch_and_length_checks(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    """Switch off and month crisis copy pending: the approved Tarot notice still answers."""

    approve_month()
    headers = _person(client, "crisis-off")
    response = client.post("/v1/month/answers", json={"question": "tự tử"}, headers=headers)
    _assert_month_crisis(response, "crisis.self_harm.notice")


@pytest.mark.usefixtures("no_admission_limit")
def test_false_alarms_stay_at_or_below_two_percent(
    typed_client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month(owner=True)
    headers = _person(typed_client, "negatives")
    flagged = 0
    for index, phrase in enumerate(NEGATIVES):
        text = phrase if len(phrase) >= 8 else f"{phrase} tháng này"
        response = _post_in_budget(
            typed_client, index, {"question": text[:280], "consent_version": CONSENT}, headers
        )
        assert response.status_code in {200, 422}, response.text
        flagged += response.status_code == 422 and response.json().get("code") == CRISIS_NOTICE_CODE
    assert flagged / len(NEGATIVES) <= 0.02
