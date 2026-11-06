"""Pending copy never reaches users (owner decision 06.11.2026). Synthetic sentences only."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.content import copy_approval
from app.domains.content.copy_approval import CopyEntry, copy_digest, parse_registry
from app.main import create_app

PENDING = "Câu thử nghiệm đang chờ duyệt, không được hiện ra."
APPROVED = "Câu thử nghiệm đã được duyệt."
FALLBACK_START = "Đừng cố nhớ hết cả bài."


def _entry(**overrides: Any) -> dict[str, Any]:
    entry = {
        "id": "tarot.closing_prompt",
        "category": "reading",
        "text": PENDING,
        "status": "pending",
    }
    entry.update(overrides)
    return entry


def _use(monkeypatch: pytest.MonkeyPatch, *entries: dict[str, Any]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _approved(text: str = APPROVED, **overrides: Any) -> dict[str, Any]:
    entry = _entry(
        text=text, status="approved", approver="codex", date="2026-11-06", digest=copy_digest(text)
    )
    entry.update(overrides)
    return entry


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as test_client:
        yield test_client


def _reading(client: TestClient) -> str:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "copy-flag-guest-1234567890",
        },
    )
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
    started = client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": "relationships",
            "question": "Mình nên nhìn rõ điều gì trước khi nhắn lại?",
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": "copy-flag-start-1234567890",
        },
    )
    selected = client.put(
        f"/v1/tarot/sessions/{started.json()['id']}/selections",
        headers=headers,
        json={"fan_index": 17, "expected_version": started.json()["version"]},
    )
    assert selected.status_code == 200
    return selected.text


def test_pending_copy_never_reaches_an_api_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, _entry())
    body = _reading(client)
    assert PENDING not in body
    assert FALLBACK_START in body


def test_approved_copy_is_served(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _approved())
    assert APPROVED in _reading(client)


@pytest.mark.parametrize(
    "bad",
    [
        {"digest": copy_digest("câu khác")},
        {"approver": None},
        {"category": "privacy"},
        {"category": "crisis"},
    ],
)
def test_unsafe_approval_falls_back(monkeypatch: pytest.MonkeyPatch, bad: dict[str, Any]) -> None:
    _use(monkeypatch, _approved(**bad))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == "cũ"


def test_owner_may_approve_owner_only_category(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _approved(category="consent", approver="owner"))
    assert copy_approval.copy_text("tarot.closing_prompt", "cũ") == APPROVED


def test_pin_ignores_pending_and_tracks_approved() -> None:
    empty = copy_approval.approved_pin({})
    pending = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": [_entry()]})
    approved = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": [_approved()]})
    assert copy_approval.approved_pin(pending) == empty
    assert copy_approval.approved_pin(approved) != empty


def test_registry_rejects_codex_approval_of_safety_copy() -> None:
    entry = CopyEntry(**_approved(category="safety"))
    assert any("owner" in problem for problem in entry.problems())


def test_checked_in_registry_is_valid() -> None:
    assert copy_approval.registry_problems(copy_approval.load_registry()) == []
