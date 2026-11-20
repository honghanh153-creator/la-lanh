"""Crisis guard for every endpoint that accepts free text a user typed (14.11.2026).

``crisis_guard("question")`` is a route dependency. FastAPI solves route dependencies before it
validates the body, so the guard sees the raw JSON even when the text would fail validation (a
five-letter "tự tử" is shorter than Tarot's 8-character minimum). On a match it raises
``CrisisContentUnsupported`` and the endpoint never runs: no reading, no row, no idempotency
record, no provider call. The app answers one problem+json carrying the owner-approved notice.

Nothing here logs, stores or echoes the text; the exception carries no message.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domains.safety.crisis import crisis_notice, detect_crisis

CRISIS_NOTICE_CODE = "CRISIS_NOTICE"
PROBLEM_MEDIA_TYPE = "application/problem+json"


class CrisisContentUnsupported(Exception):
    """The submitted text reads as self-harm or suicide intent. Deliberately carries no text.

    ``notice_id`` names the owner-approved notice for the surface (Tarot's when ``None``).
    """

    def __init__(self, notice_id: str | None = None) -> None:
        super().__init__()
        self.notice_id = notice_id


def crisis_problem_body(notice_id: str | None = None) -> dict[str, Any]:
    notice = crisis_notice(notice_id)
    return {
        "type": "about:blank",
        "title": "Content is not supported",
        "status": 422,
        "code": CRISIS_NOTICE_CODE,
        "notice": {"copy_id": notice.copy_id, "text": notice.text},
    }


def crisis_guard(
    *fields: str, notice_id: str | None = None
) -> Callable[[Request], Awaitable[None]]:
    """A dependency that checks these top-level JSON string fields before validation."""

    async def guard(request: Request) -> None:
        try:
            body = await request.json()
        except ValueError:
            return  # not JSON: the endpoint's own validation answers
        if not isinstance(body, dict):
            return
        for field in fields:
            value = body.get(field)
            if isinstance(value, str) and detect_crisis(value):
                raise CrisisContentUnsupported(notice_id)

    return guard


async def crisis_response(_request: Request, error: Exception) -> JSONResponse:
    notice_id = error.notice_id if isinstance(error, CrisisContentUnsupported) else None
    return JSONResponse(
        status_code=422,
        content=crisis_problem_body(notice_id),
        media_type=PROBLEM_MEDIA_TYPE,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


def install_crisis_guard(application: FastAPI) -> None:
    application.add_exception_handler(CrisisContentUnsupported, crisis_response)
