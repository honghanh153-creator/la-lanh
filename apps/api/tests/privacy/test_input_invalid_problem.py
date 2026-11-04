"""#170: no route answers the default 422 that repeats submitted values in ``detail[].input``.

One app-wide handler turns every request-validation failure that a router does not already
sanitise into a fixed problem+json (``INPUT_INVALID``, ``no-store``) with no submitted value,
field name or location. Routers with their own code (birth, account, human Tarot) keep it.
All values below are synthetic markers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.saved.copy_flow import ORIGIN, make_app

MARKER = "zz-test-marker"
SYNTHETIC_DATE = "2001-02-30"  # not a calendar date
NOTE_ID = "00000000-0000-4000-8000-000000000001"

CASES: list[tuple[str, str, dict[str, Any] | None, str]] = [
    (
        "POST",
        "/v1/tarot/sessions",
        {
            "context": MARKER,
            "question": f"{MARKER} question text",
            "spread": MARKER,
            "idempotency_key": MARKER,
        },
        "INPUT_INVALID",
    ),
    ("GET", f"/v1/tarot/sessions/{MARKER}", None, "INPUT_INVALID"),
    (
        "PUT",
        f"/v1/tarot/sessions/{NOTE_ID}/selections",
        {"fan_index": MARKER, "expected_version": MARKER},
        "INPUT_INVALID",
    ),
    ("POST", "/v1/radar/private-checks", {MARKER: MARKER}, "INPUT_INVALID"),
    ("POST", "/v1/radar/requests", {MARKER: MARKER}, "INPUT_INVALID"),
    ("POST", "/v1/la-chung/requests", {MARKER: MARKER}, "INPUT_INVALID"),
    ("POST", f"/v1/public/la-chung/{MARKER}/responses", {MARKER: MARKER}, "INPUT_INVALID"),
    ("PUT", "/v1/matching/profile", {MARKER: MARKER}, "INPUT_INVALID"),
    ("PUT", f"/v1/daily-note/{NOTE_ID}/mood", {"mood": MARKER}, "INPUT_INVALID"),
    ("POST", "/v1/daily-note/context", {MARKER: MARKER}, "INPUT_INVALID"),
    # Already sanitised by PrivateBirthRoute: the fixed birth code stays as it was.
    (
        "POST",
        "/v1/birth-profile",
        {"birth_date": SYNTHETIC_DATE, MARKER: MARKER},
        "BIRTH_INPUT_INVALID",
    ),
    ("POST", "/v1/birth-places/search", {"query": MARKER * 10}, "BIRTH_INPUT_INVALID"),
    ("POST", "/v1/birth-places/search", {"query": MARKER, MARKER: 1}, "BIRTH_INPUT_INVALID"),
]


def _guest_headers(client: TestClient) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": f"input-invalid-{uuid4().hex}",
        },
    )
    assert guest.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}


@pytest.mark.parametrize(("method", "path", "body", "code"), CASES)
def test_invalid_input_never_comes_back(
    tmp_path: Path, method: str, path: str, body: dict[str, Any] | None, code: str
) -> None:
    app = make_app(tmp_path / "input-invalid.db")
    with TestClient(app, base_url=ORIGIN) as client:
        headers = _guest_headers(client)
        response = client.request(method, path, headers=headers, json=body)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["cache-control"].startswith("no-store")
    problem = response.json()
    assert problem["code"] == code
    assert set(problem) == {"type", "title", "status", "code"}
    assert MARKER not in response.text
    assert SYNTHETIC_DATE not in response.text
    assert "detail" not in problem


def test_contract_documents_the_problem_instead_of_the_echo() -> None:
    schema = create_app().openapi()
    rendered = json.dumps(schema)
    assert "HTTPValidationError" not in rendered
    assert "ValidationError" not in schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            response = operation["responses"].get("422")
            if response is None:
                continue
            content = response.get("content", {})
            assert "application/problem+json" in content, f"{method.upper()} {path}"
