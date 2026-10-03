from typing import Annotated, cast

from fastapi import APIRouter, Cookie, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.domains.content_rewrite.authorization import content_rewrite_receipt_id
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.models import GuestSessionRecord, OnboardingStatus
from app.domains.guest.service import GuestSessionService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()


class GuestCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_version: str = Field(min_length=1, max_length=64)
    purpose: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=22, max_length=200)


class GuestSessionResponse(BaseModel):
    state: str
    onboarding_status: str
    expires_at: str
    csrf_token: str | None = None
    resumed: bool = False
    session_epoch: str


class ProblemResponse(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    code: str


class OnboardingStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OnboardingStatus


class ContentRewriteConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_version: str = Field(min_length=1, max_length=64)


def _service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _problem(error: GuestDomainError) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Guest session request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
    )


def _payload(
    guest: GuestSessionRecord,
    *,
    session_epoch: str,
    csrf_token: str | None = None,
) -> dict[str, object]:
    return {
        "state": guest.state.value,
        "onboarding_status": guest.onboarding_status.value,
        "expires_at": guest.expires_at.isoformat(),
        "csrf_token": csrf_token,
        "session_epoch": session_epoch,
    }


@router.post(
    "/guest-sessions",
    response_model=GuestSessionResponse,
    responses={409: {"model": ProblemResponse}, 422: {"model": ProblemResponse}},
)
async def create_guest_session(
    body: GuestCreateRequest, request: Request, response: Response
) -> dict[str, object] | Response:
    settings = request.app.state.settings
    try:
        result = await _service(request).create(
            consent_version=body.consent_version,
            purpose=body.purpose,
            idempotency_key=body.idempotency_key,
        )
    except GuestDomainError as error:
        return _problem(error)
    response.set_cookie(
        key=settings.guest_cookie_name,
        value=result.token,
        max_age=settings.guest_ttl_days * 24 * 60 * 60,
        secure=settings.guest_cookie_secure,
        httponly=True,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        key=settings.guest_csrf_cookie_name,
        value=result.csrf_token,
        max_age=settings.guest_ttl_days * 24 * 60 * 60,
        secure=settings.guest_cookie_secure,
        httponly=False,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain,
    )
    return {
        **_payload(
            result.guest,
            session_epoch=_service(request).session_epoch(result.guest),
            csrf_token=result.csrf_token,
        ),
        "resumed": result.resumed,
    }


@router.get(
    "/session",
    response_model=GuestSessionResponse,
    responses={401: {"model": ProblemResponse}},
)
async def get_session(
    request: Request,
    response: Response,
    guest_token: Annotated[str | None, Cookie(alias="__Host-la_lanh_guest")] = None,
) -> dict[str, object] | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name, guest_token)
    try:
        guest = await _service(request).resume(token)
    except GuestDomainError as error:
        response = _problem(error)
        response.delete_cookie(settings.guest_cookie_name, path="/", domain=settings.cookie_domain)
        response.delete_cookie(
            settings.guest_csrf_cookie_name, path="/", domain=settings.cookie_domain
        )
        return response
    return _payload(guest, session_epoch=_service(request).session_epoch(guest))


@router.delete(
    "/guest-session",
    status_code=204,
    responses={401: {"model": ProblemResponse}, 403: {"model": ProblemResponse}},
)
async def delete_guest_session(
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        await _service(request).verify_csrf(token, csrf_token)
        await _service(request).delete(token)
    except GuestDomainError as error:
        return _problem(error)
    response.delete_cookie(settings.guest_cookie_name, path="/", domain=settings.cookie_domain)
    response.delete_cookie(settings.guest_csrf_cookie_name, path="/", domain=settings.cookie_domain)
    response.delete_cookie(settings.owner_cookie_name, path="/v1", domain=settings.cookie_domain)
    response.delete_cookie("la_lanh_radar_invite", path="/v1/public/radar")
    response.delete_cookie("la_lanh_radar_receipt", path="/v1/public/radar/receipt")
    response.status_code = 204
    return response


@router.put(
    "/session/onboarding-status",
    response_model=GuestSessionResponse,
    responses={401: {"model": ProblemResponse}, 403: {"model": ProblemResponse}},
)
async def update_onboarding_status(
    body: OnboardingStatusRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> dict[str, object] | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _service(request).verify_csrf(token, csrf_token)
        await _service(request).set_onboarding_status(guest.id, body.status)
        guest = await _service(request).resume(token)
    except GuestDomainError as error:
        return _problem(error)
    return _payload(guest, session_epoch=_service(request).session_epoch(guest))


@router.post(
    "/session/content-rewrite-consent",
    status_code=204,
    responses={401: {"model": ProblemResponse}, 403: {"model": ProblemResponse}},
)
async def grant_content_rewrite_consent(
    body: ContentRewriteConsentRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _service(request).verify_csrf(token, csrf_token)
        await _service(request).accept_content_rewrite_consent(
            guest.id,
            version=body.consent_version,
        )
    except GuestDomainError as error:
        return _problem(error)
    response.status_code = 204
    return response


@router.delete(
    "/session/content-rewrite-consent",
    status_code=204,
    responses={401: {"model": ProblemResponse}, 403: {"model": ProblemResponse}},
)
async def revoke_content_rewrite_consent(
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _service(request).verify_csrf(token, csrf_token)
        await _service(request).revoke_content_rewrite_consent(guest.id)
        await request.app.state.content_rewrite_repository.cancel_and_purge_authorization(
            content_rewrite_receipt_id(guest.id)
        )
    except GuestDomainError as error:
        return _problem(error)
    response.status_code = 204
    return response
