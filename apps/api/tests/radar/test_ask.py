""" "Hỏi về hai bạn" (Hợp gu direction B, AL1 20.11.2026).

Answers come only from the stored reading's theme levels, never from free text or an external
AI; a question shows only when every line it can show is approved; the mind-reading question
always gets the refusal.
"""

from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.content.copy_approval import load_registry, text_lint_problems
from app.domains.radar import ask
from app.main import create_app
from tests.radar.test_reading import FORBIDDEN, JARGON

ORIGIN = "http://127.0.0.1:5173"


def _reading(context: str, **levels: str) -> dict[str, Any]:
    return {
        "context": context,
        "sections": [
            {
                "key": "why",
                "factors": [
                    {
                        "key": key,
                        "label": key,
                        "level": level,
                        "technical_note": "Ghi chú kỹ thuật.",
                        "evidence_ids": [f"syn:{key}"],
                    }
                    for key, level in levels.items()
                ],
            }
        ],
    }


@pytest.fixture
def approved(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = load_registry()
    monkeypatch.setattr(
        ask,
        "approved_copy",
        lambda entry_id: registry[entry_id].text if entry_id in registry else None,
    )


def test_every_line_is_registered_pending_and_follows_the_rules() -> None:
    registry = load_registry()
    for entry_id in ask.registry_ids():
        entry = registry[entry_id]
        assert entry.category == "reading"
        low = entry.text.lower()
        assert not [term for term in JARGON if term in low], entry.text
        assert not [term for term in FORBIDDEN if term in low], entry.text
    # The panel (20.11) flagged a line judging the other person; "Vì sao" describes the pair.
    for topic in ask.TOPICS:
        for level in ask.ANSWER_LEVELS.values():
            assert "người ấy" not in registry[f"radar.ask.{topic}.{level}.why"].text
    # The copy lint (#411) allows no template slot: every line is a whole sentence as stored.
    assert not [
        entry_id for entry_id in ask.registry_ids() if text_lint_problems(registry[entry_id].text)
    ]


def test_nothing_shows_while_the_lines_are_pending() -> None:
    assert ask.questions_for(_reading("crush", communication="good")) == []
    with pytest.raises(KeyError):
        ask.answer(_reading("crush", communication="good"), "message")


@pytest.mark.usefixtures("approved")
@pytest.mark.parametrize(
    ("context", "first"),
    [
        ("crush", "Nhắn tin cho người ấy kiểu nào thì dễ nghe?"),
        ("someone", "Nhắn tin với bạn ấy kiểu nào thì dễ hiểu nhau?"),
        ("coworker", "Nhắn việc cho người ấy thế nào cho rõ?"),
        ("family", "Nói chuyện với người ấy thế nào cho đỡ căng?"),
    ],
)
def test_questions_follow_the_relationship(context: str, first: str) -> None:
    questions = ask.questions_for(_reading(context))
    assert [item["id"] for item in questions] == ["message", "timing", "together", "direct", "mind"]
    assert questions[0]["text"] == first


@pytest.mark.usefixtures("approved")
def test_answer_reads_the_pair_facts_watch_first_and_is_deterministic() -> None:
    reading = _reading("crush", communication="good", clarity="watch")
    first = ask.answer(reading, "message").as_dict()
    assert first == ask.answer(reading, "message").as_dict()
    assert first["say"] == "Nói ý chính ngay câu đầu để không ai phải đoán."
    # "Vì sao" is the stored sentence as is; the theme it came from is in "Dựa vào".
    assert first["why"] == "Hai bạn dễ hiểu lệch nhau, nên câu càng rõ càng đỡ nhầm."
    assert first["based_on"]["theme"] == "clarity"
    assert first["based_on"]["evidence_ids"] == ["syn:clarity"]
    assert first["can_send"] == "Tối thứ Sáu bạn rảnh không? Mình muốn rủ đi ăn."
    good = ask.answer(_reading("crush", communication="good"), "message").as_dict()
    assert good["say"] == "Cứ nhắn tự nhiên, hai bạn vốn dễ hiểu ý nhau."


@pytest.mark.usefixtures("approved")
def test_a_topic_without_facts_says_so() -> None:
    found = ask.answer(_reading("coworker"), "timing").as_dict()
    assert found["why"] == "Lá chưa thấy điểm nào rõ ở chỗ này, nên đây là gợi ý chung."
    assert found["based_on"] is None


@pytest.mark.usefixtures("approved")
@pytest.mark.parametrize("context", ["crush", "friend", "coworker", "family"])
def test_the_mind_question_is_always_refused(context: str) -> None:
    found = ask.answer(_reading(context, attraction="good"), "mind").as_dict()
    assert found["refusal"] is True
    assert found["say"] == "Lá không đoán được người ấy nghĩ gì. Bạn có thể hỏi thẳng:"
    assert found["based_on"] is None and found["try_today"] is None
    assert found["can_send"].endswith("?")


def _owner(client: TestClient) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "radar-ask-owner-1234567890",
        },
    )
    headers = {"Origin": ORIGIN, "X-CSRF-Token": str(guest.json()["csrf_token"])}
    client.post("/v1/birth-profile", headers=headers, json={"birth_date": "1994-03-12"})
    client.post(
        "/v1/birth-profile/supplement",
        headers=headers,
        json={
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        },
    )
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    return headers


def test_ask_is_owner_bound_and_answers_from_the_stored_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'ask.db'}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url=ORIGIN) as client:
        headers = _owner(client)
        created = client.post(
            "/v1/radar/private-checks",
            headers=headers,
            json={
                "recipient_label": "Mèo",
                "context": "coworker",
                "birth_date": "1996-07-21",
                "birth_time_mode": "unknown",
                "place_id": "vn-hanoi",
                "consent_version": "radar-authorized-input-v1",
                "authorization_attested": True,
            },
        )
        assert created.status_code == 200
        request_id = created.json()["request_id"]

        pending = client.get(f"/v1/radar/results/{request_id}/ask")
        assert pending.status_code == 200
        assert pending.json() == {"version": "radar-ask-v1", "questions": []}
        assert pending.headers["cache-control"].startswith("no-store")

        registry = load_registry()
        monkeypatch.setattr(
            ask,
            "approved_copy",
            lambda entry_id: registry[entry_id].text if entry_id in registry else None,
        )
        listed = client.get(f"/v1/radar/results/{request_id}/ask").json()["questions"]
        assert listed[0]["text"] == "Nhắn việc cho người ấy thế nào cho rõ?"
        answer = client.get(f"/v1/radar/results/{request_id}/ask/together")
        assert answer.status_code == 200
        body = answer.json()
        assert body["refusal"] is False and body["say"] and body["can_send"]
        for raw in ("1996", "Mèo", "vn-hanoi"):
            assert raw not in answer.text

        assert client.get(f"/v1/radar/results/{request_id}/ask/guess").status_code == 404
        assert client.get(f"/v1/radar/results/{request_id}/ask/Bad-Id").status_code == 422
        stranger = TestClient(app, base_url=ORIGIN)
        assert stranger.get(f"/v1/radar/results/{request_id}/ask").status_code == 404
        assert stranger.get(f"/v1/radar/results/{request_id}/ask/together").status_code == 404
