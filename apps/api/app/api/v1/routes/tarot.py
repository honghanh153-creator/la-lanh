from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.tarot.errors import TarotDomainError, TarotQuestionRejected
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotSessionView,
    TarotSpread,
    TarotVoice,
)
from app.domains.tarot.service import TarotSessionService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()


class TarotStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: TarotContext
    question: str = Field(min_length=8, max_length=280)
    spread: TarotSpread
    origin: TarotOrigin = TarotOrigin.DIRECT
    prompt_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")
    idempotency_key: str = Field(min_length=22, max_length=200)


class TarotSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fan_index: int = Field(ge=0, lt=78)
    expected_version: int = Field(ge=1)


def _tarot(request: Request) -> TarotSessionService:
    return cast(TarotSessionService, request.app.state.tarot_session_service)


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


async def _external_generation_authorized(request: Request, guest_id: UUID) -> bool:
    settings = request.app.state.settings
    authorization = getattr(request.app.state, "content_rewrite_authorization", None)
    return bool(
        settings.generation_enabled
        and authorization is not None
        and await authorization.authorized_guest(guest_id)
    )


def _problem(error: TarotDomainError | GuestDomainError) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": "Tarot request was rejected",
        "status": error.status_code,
        "code": error.code,
    }
    if isinstance(error, TarotQuestionRejected):
        body["explanation"] = error.assessment.explanation
        body["suggested_reframe"] = error.assessment.suggested_reframe
    return JSONResponse(
        status_code=error.status_code,
        content=body,
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


async def _guest_for_read(request: Request):  # type: ignore[no-untyped-def]
    settings = request.app.state.settings
    return await _guests(request).resume(request.cookies.get(settings.guest_cookie_name))


async def _guest_for_mutation(request: Request, csrf_token: str | None):  # type: ignore[no-untyped-def]
    settings = request.app.state.settings
    require_trusted_origin(request, trusted_origins(request))
    return await _guests(request).verify_csrf(
        request.cookies.get(settings.guest_cookie_name), csrf_token
    )


@router.post("/tarot/sessions", response_model=TarotSessionView, status_code=201)
async def start_tarot_session(
    body: TarotStartRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> TarotSessionView | Response:
    try:
        guest = await _guest_for_mutation(request, csrf_token)
        return await _tarot(request).start(
            guest_id=guest.id,
            context=body.context,
            question=body.question,
            spread=body.spread,
            voice=TarotVoice.PLAYFUL_GROUNDED,
            origin=body.origin,
            idempotency_key=body.idempotency_key,
            prompt_id=body.prompt_id,
        )
    except (TarotDomainError, GuestDomainError) as error:
        return _problem(error)


@router.get("/tarot/sessions/{session_id}", response_model=TarotSessionView)
async def get_tarot_session(session_id: UUID, request: Request) -> TarotSessionView | Response:
    try:
        guest = await _guest_for_read(request)
        return await _tarot(request).get(guest.id, session_id)
    except (TarotDomainError, GuestDomainError) as error:
        return _problem(error)


@router.put("/tarot/sessions/{session_id}/selections", response_model=TarotSessionView)
async def select_tarot_card(
    session_id: UUID,
    body: TarotSelectionRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> TarotSessionView | Response:
    try:
        guest = await _guest_for_mutation(request, csrf_token)
        return await _tarot(request).select_card(
            guest_id=guest.id,
            session_id=session_id,
            fan_index=body.fan_index,
            expected_version=body.expected_version,
            external_generation_authorized=await _external_generation_authorized(request, guest.id),
        )
    except (TarotDomainError, GuestDomainError) as error:
        return _problem(error)


@router.delete("/tarot/sessions/{session_id}", status_code=204)
async def delete_tarot_session(
    session_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        guest = await _guest_for_mutation(request, csrf_token)
        await _tarot(request).delete(guest.id, session_id)
    except (TarotDomainError, GuestDomainError) as error:
        return _problem(error)
    return Response(status_code=204)
