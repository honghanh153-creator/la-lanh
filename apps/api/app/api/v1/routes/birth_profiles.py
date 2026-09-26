from datetime import date, datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domains.astro.models import DateOnlySunResult, NatalChart
from app.domains.birth.errors import BirthDomainError, ChartEngineUnavailable
from app.domains.birth.models import ApproxWindow, BirthReveal, BirthSupplementState, BirthTimeMode
from app.domains.birth.service import BirthChartService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.models import OnboardingStatus
from app.domains.guest.service import GuestSessionService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()


class BirthDateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth_date: date


class BirthRevealResponse(BaseModel):
    profile_id: UUID
    snapshot_id: UUID
    birth_date: date
    calculation_kind: Literal["date_only_sun", "natal_chart"]
    calculation: DateOnlySunResult | NatalChart
    created_at: datetime
    resumed: bool


class PlaceResultResponse(BaseModel):
    place_id: str
    display_name: str
    country_code: str
    timezone_id: str
    confidence: str


class PlaceSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=80)


class BirthSupplementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth_time_mode: BirthTimeMode
    birth_time_local: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    approx_window: ApproxWindow | None = None
    place_id: str | None = Field(default=None, min_length=2, max_length=80)
    consent_version: str


class BirthSupplementResponse(BaseModel):
    profile_id: UUID
    snapshot_id: UUID | None
    profile_level: int
    time_precision: str
    place_display_name: str | None
    timezone_id: str | None
    chart: NatalChart | None


class BirthSupplementStateResponse(BaseModel):
    profile_id: UUID
    profile_level: int
    time_precision: str
    birth_time_mode: BirthTimeMode
    approx_window: ApproxWindow | None
    place_display_name: str | None
    timezone_id: str | None


class BirthSupplementRemoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remove_time: bool = False
    remove_place: bool = False


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
        calculation_kind=(
            "date_only_sun" if isinstance(reveal.result, DateOnlySunResult) else "natal_chart"
        ),
        calculation=reveal.result,
        created_at=reveal.created_at,
        resumed=reveal.resumed,
    )


def _supplement_response(state: BirthSupplementState) -> BirthSupplementStateResponse:
    return BirthSupplementStateResponse(
        profile_id=state.profile_id,
        profile_level=state.profile_level,
        time_precision=state.time_precision,
        birth_time_mode=state.birth_time_mode,
        approx_window=state.approx_window,
        place_display_name=state.place_display_name,
        timezone_id=state.timezone_id,
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
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        reveal = await _birth_service(request).create_date_only(
            guest_id=guest.id,
            birth_date=body.birth_date,
        )
        await _guest_service(request).set_onboarding_status(
            guest.id, OnboardingStatus.BASIC_REVEALED
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


@router.post(
    "/birth-places/search",
    response_model=list[PlaceResultResponse],
    responses={422: {}, 503: {}},
)
async def search_birth_places(
    body: PlaceSearchRequest, request: Request
) -> list[PlaceResultResponse] | Response:
    try:
        places = _birth_service(request).search_places(body.query)
    except BirthDomainError as error:
        return _problem(error)
    return [
        PlaceResultResponse(
            place_id=place.place_id,
            display_name=place.display_name,
            country_code=place.country_code,
            timezone_id=place.timezone_id,
            confidence=place.confidence,
        )
        for place in places
    ]


@router.post(
    "/birth-profile/supplement",
    response_model=BirthSupplementResponse,
    responses={401: {}, 403: {}, 422: {}, 503: {}},
)
async def add_birth_supplement(
    body: BirthSupplementRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> BirthSupplementResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        await _guest_service(request).accept_deep_birth_consent(
            guest.id, version=body.consent_version
        )
        result = await _birth_service(request).add_supplement(
            guest_id=guest.id,
            birth_time_mode=body.birth_time_mode,
            birth_time_local=body.birth_time_local,
            approx_window=body.approx_window,
            place_id=body.place_id,
            consent_version=body.consent_version,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return BirthSupplementResponse(
        profile_id=result.profile_id,
        snapshot_id=result.snapshot_id,
        profile_level=result.profile_level,
        time_precision=result.time_precision,
        place_display_name=result.place_display_name,
        timezone_id=result.timezone_id,
        chart=result.chart,
    )


@router.get(
    "/birth-profile/supplement",
    response_model=BirthSupplementStateResponse,
    responses={401: {}, 404: {}, 503: {}},
)
async def get_birth_supplement(request: Request) -> BirthSupplementStateResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        state = await _birth_service(request).supplement_state(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return _supplement_response(state)


@router.delete(
    "/birth-profile/supplement",
    response_model=BirthSupplementStateResponse,
    responses={401: {}, 403: {}, 404: {}, 422: {}, 503: {}},
)
async def remove_birth_supplement(
    body: BirthSupplementRemoveRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> BirthSupplementStateResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        state = await _birth_service(request).remove_supplement(
            guest.id,
            remove_time=body.remove_time,
            remove_place=body.remove_place,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return _supplement_response(state)
