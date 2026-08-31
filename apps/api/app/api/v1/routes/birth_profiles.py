from datetime import date, datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.domains.astro.models import DateOnlySunResult
from app.domains.birth.errors import BirthDomainError, ChartEngineUnavailable
from app.domains.birth.models import BirthReveal
from app.domains.birth.service import BirthChartService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.infrastructure.csrf import normalize_origin, require_trusted_origin

router = APIRouter()


class BirthDateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth_date: date


class BirthRevealResponse(BaseModel):
    profile_id: UUID
    snapshot_id: UUID
    birth_date: date
    calculation: DateOnlySunResult
    created_at: datetime
    resumed: bool


def _problem(error: BirthDomainError | GuestDomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Birth chart request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
    )


def _guest_service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _birth_service(request: Request) -> BirthChartService:
    service = request.app.state.birth_chart_service
    if service is None:
        raise ChartEngineUnavailable
    return cast(BirthChartService, service)


def _response(reveal: BirthReveal) -> BirthRevealResponse:
    return BirthRevealResponse(
        profile_id=reveal.profile_id,
        snapshot_id=reveal.snapshot_id,
        birth_date=reveal.birth_date,
        calculation=reveal.result,
        created_at=reveal.created_at,
        resumed=reveal.resumed,
    )


@router.post(
    "/birth-profile",
    response_model=BirthRevealResponse,
    responses={401: {}, 403: {}, 422: {}, 503: {}},
)
async def create_birth_profile(
    body: BirthDateRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> BirthRevealResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    trusted_origins = frozenset(
        origin
        for configured in settings.cors_origins
        if (origin := normalize_origin(str(configured))) is not None
    )
    try:
        require_trusted_origin(request, trusted_origins)
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        reveal = await _birth_service(request).create_date_only(
            guest_id=guest.id,
            birth_date=body.birth_date,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return _response(reveal)


@router.get(
    "/birth-profile",
    response_model=BirthRevealResponse,
    responses={401: {}, 404: {}, 503: {}},
)
async def get_birth_profile(
    request: Request,
    guest_token: Annotated[str | None, Cookie(alias="la_lanh_guest")] = None,
) -> BirthRevealResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name, guest_token)
    try:
        guest = await _guest_service(request).resume(token)
        reveal = await _birth_service(request).current(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return _response(reveal)
