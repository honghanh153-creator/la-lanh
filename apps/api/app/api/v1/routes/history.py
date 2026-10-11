from datetime import datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.domains.guest.errors import GuestDomainError
from app.domains.history.errors import HistoryBusy
from app.domains.history.service import HistoryService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()


class HistoryRetentionConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent_version: Literal["history-retention-v1"]


class HistoryRetentionStatus(BaseModel):
    enabled: bool
    history_days: Literal[30] = 30
    activated_at: datetime | None
    saved_notes_kept: Literal[True] = True


def _service(request: Request) -> HistoryService:
    return cast(HistoryService, request.app.state.history_service)


def _token(request: Request) -> str | None:
    return request.cookies.get(request.app.state.settings.guest_cookie_name)


def _problem(error: GuestDomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "History request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        headers={"Retry-After": "1"} if isinstance(error, HistoryBusy) else None,
        media_type="application/problem+json",
    )


@router.get("/session/history-retention", response_model=HistoryRetentionStatus)
async def get_history_retention(request: Request) -> HistoryRetentionStatus | Response:
    try:
        activated = await _service(request).request("status", _token(request))
        return HistoryRetentionStatus(enabled=activated is not None, activated_at=activated)
    except GuestDomainError as error:
        return _problem(error)


@router.post("/session/history-retention", response_model=HistoryRetentionStatus)
async def activate_history_retention(
    body: HistoryRetentionConsent,
    request: Request,
    csrf: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> HistoryRetentionStatus | Response:
    try:
        require_trusted_origin(request, trusted_origins(request))
        activated = await _service(request).request("activate", _token(request), csrf)
        return HistoryRetentionStatus(enabled=True, activated_at=activated)
    except GuestDomainError as error:
        return _problem(error)


@router.delete("/session/history", status_code=204)
async def clear_history(
    request: Request,
    csrf: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        require_trusted_origin(request, trusted_origins(request))
        await _service(request).request("clear", _token(request), csrf)
        return Response(status_code=204)
    except GuestDomainError as error:
        return _problem(error)
