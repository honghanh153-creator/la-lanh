"""Human Tarot reader (US-24). Owner-only reads; every response is no-store."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.human_tarot.errors import HumanTarotError
from app.domains.human_tarot.models import HumanTarotAvailability, HumanTarotRequestView
from app.domains.human_tarot.service import HumanTarotService
from app.domains.tarot.errors import TarotDomainError, TarotQuestionRejected
from app.domains.tarot.models import TarotContext, TarotSpread
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
_NO_STORE = {"Cache-Control": "no-store, max-age=0"}


class HumanTarotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: TarotContext
    question: str = Field(min_length=8, max_length=280)
    spread: TarotSpread
    consent_version: str = Field(min_length=1, max_length=32)
    idempotency_key: str = Field(min_length=22, max_length=200)


def _service(request: Request) -> HumanTarotService:
    return cast(HumanTarotService, request.app.state.human_tarot_service)


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _problem(error: HumanTarotError | TarotDomainError | GuestDomainError) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": "Human Tarot request was rejected",
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
        headers=_NO_STORE,
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


@router.get("/human-tarot/availability", response_model=HumanTarotAvailability)
async def human_tarot_availability(request: Request) -> HumanTarotAvailability | Response:
    try:
        guest = await _guest_for_read(request)
        return await _service(request).availability(guest.id)
    except GuestDomainError as error:
        return _problem(error)


@router.post("/human-tarot/requests", response_model=HumanTarotRequestView, status_code=201)
async def create_human_tarot_request(
    body: HumanTarotCreateRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> HumanTarotRequestView | Response:
    try:
        guest = await _guest_for_mutation(request, csrf_token)
        return await _service(request).create(
            guest_id=guest.id,
            context=body.context,
            question=body.question,
            spread=body.spread,
            consent_version=body.consent_version,
            idempotency_key=body.idempotency_key,
        )
    except (HumanTarotError, TarotDomainError, GuestDomainError) as error:
        return _problem(error)


@router.get("/human-tarot/requests/current", response_model=HumanTarotRequestView)
async def current_human_tarot_request(request: Request) -> HumanTarotRequestView | Response:
    try:
        guest = await _guest_for_read(request)
        return await _service(request).current(guest.id)
    except (HumanTarotError, GuestDomainError) as error:
        return _problem(error)


@router.get("/human-tarot/requests/{request_id}", response_model=HumanTarotRequestView)
async def get_human_tarot_request(
    request_id: UUID, request: Request
) -> HumanTarotRequestView | Response:
    try:
        guest = await _guest_for_read(request)
        return await _service(request).get(guest.id, request_id)
    except (HumanTarotError, GuestDomainError) as error:
        return _problem(error)


@router.delete("/human-tarot/requests/{request_id}", status_code=204)
async def cancel_human_tarot_request(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        guest = await _guest_for_mutation(request, csrf_token)
        await _service(request).cancel(guest.id, request_id)
    except (HumanTarotError, GuestDomainError) as error:
        return _problem(error)
    return Response(status_code=204, headers=_NO_STORE)
