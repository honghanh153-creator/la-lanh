from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any, Literal, TypedDict, cast
from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routes.guest_sessions import ProblemResponse
from app.config import Settings
from app.domains.accounts.models import (
    ACCOUNT_DAYS,
    CHALLENGE_SECONDS,
    AccountError,
    LoginResult,
)
from app.domains.accounts.service import LOGIN_COOKIE, RESTORE_COOKIE, AccountService
from app.domains.guest.service import GuestSessionService
from app.infrastructure.csrf import (
    NATIVE_APP_ORIGINS,
    NATIVE_CLIENT_HEADER,
    NATIVE_CLIENT_VALUE,
    normalize_origin,
    trusted_origins,
)
from app.infrastructure.session_cookies import clear_profile_cookies, set_profile_cookies


class PrivateAccountRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def safe(request: Request) -> Response:
            try:
                if request.method == "POST":
                    origin = request.headers.get("Origin")
                    try:
                        normalized = normalize_origin(origin) if origin else None
                    except ValueError:
                        normalized = None
                    native = (
                        _settings(request).native_app_enabled
                        and request.headers.get(NATIVE_CLIENT_HEADER) == NATIVE_CLIENT_VALUE
                        and (origin is None or origin.rstrip("/") in NATIVE_APP_ORIGINS)
                    )
                    # Native transport is an explicit deployment gate, not an
                    # authentication bypass. Guest CSRF and challenge proofs
                    # remain mandatory, and an evil web Origin is never allowed.
                    if not native and (
                        normalized is None or normalized not in trusted_origins(request)
                    ):
                        raise AccountError("LOGIN_ORIGIN_REJECTED", 403)
                response = await original(request)
            except RequestValidationError:
                response = _problem(AccountError("ACCOUNT_INPUT_INVALID", 422))
            except AccountError as error:
                response = _problem(error)
            except SQLAlchemyError:
                response = _problem(AccountError("ACCOUNT_TEMPORARILY_UNAVAILABLE", 503))
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Referrer-Policy"] = "no-referrer"
            return response

        return safe


router = APIRouter(
    prefix="/account",
    route_class=PrivateAccountRoute,
    responses={
        status: {
            "description": "Private account operation failed",
            "content": {
                "application/problem+json": {"schema": ProblemResponse.model_json_schema()}
            },
        }
        for status in (401, 403, 409, 422, 429, 503)
    },
)


class AccountStatus(BaseModel):
    login_enabled: bool
    google_login_enabled: bool = False
    signed_in: bool
    masked_email: str | None
    profile_expires_at: str | None
    guest_inactivity_days: int
    history_days: int = 30
    account_inactivity_days: int = ACCOUNT_DAYS


class DeviceResponse(BaseModel):
    id: UUID
    current: bool
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime


@router.get("/devices", response_model=list[DeviceResponse])
async def devices(request: Request) -> list[DeviceResponse]:
    rows = await _service(request).devices(
        request.cookies.get(_settings(request).guest_cookie_name)
    )
    return [
        DeviceResponse(
            id=row.id,
            current=row.current,
            created_at=row.created_at,
            last_active_at=row.last_active_at,
            expires_at=row.expires_at,
        )
        for row in rows
    ]


@router.post("/devices/revoke-others", status_code=204)
async def revoke_others(request: Request, response: Response) -> Response:
    await _service(request).revoke_devices(
        request.cookies.get(_settings(request).guest_cookie_name),
        request.headers.get("X-CSRF-Token"),
        others=True,
    )
    response.status_code = 204
    return response


@router.post("/devices/{device_id}/revoke", status_code=204)
async def revoke_device(device_id: UUID, request: Request, response: Response) -> Response:
    settings = _settings(request)
    revoked_current = await _service(request).revoke_devices(
        request.cookies.get(settings.guest_cookie_name),
        request.headers.get("X-CSRF-Token"),
        device_id=device_id,
    )
    if revoked_current:
        clear_profile_cookies(response, settings)
        _clear_login(response, settings)
    response.status_code = 204
    return response


class CodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        strict=True,
        min_length=3,
        max_length=254,
        pattern=r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$",
    )
    account_storage_consent: Literal["account-storage-v1"] | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        local, domain = value.split("@")
        if (
            local.startswith(".")
            or local.endswith(".")
            or ".." in value
            or "." not in domain
            or any(not label or len(label) > 63 for label in domain.split("."))
            or any(label.startswith("-") or label.endswith("-") for label in domain.split("."))
        ):
            raise ValueError("email is invalid")
        return value.lower()


class CodeResponse(BaseModel):
    status: Literal["code_sent"] = "code_sent"
    login_csrf_token: str
    expires_at: str
    resend_after_seconds: int = 60


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(strict=True, pattern=r"^[0-9]{6}$", min_length=6, max_length=6)


class GoogleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_storage_consent: Literal["account-storage-v1"]


class GoogleResponse(BaseModel):
    authorize_url: str
    expires_at: str


class GoogleVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(strict=True, min_length=8, max_length=2048, pattern=r"^[A-Za-z0-9_.~-]+$")


class RestoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: Literal[True]


class AccountSession(BaseModel):
    state: str
    onboarding_status: str
    expires_at: str
    csrf_token: str
    session_epoch: str
    resumed: bool


class LoginResponse(BaseModel):
    status: Literal["signed_in", "restore_required", "onboarding_required", "consent_required"]
    session: AccountSession | None = None
    masked_email: str | None = None
    profile_expires_at: str | None = None


def _problem(error: AccountError) -> Response:
    return JSONResponse(
        status_code=error.status,
        content={
            "type": "about:blank",
            "title": "Account request could not be completed",
            "status": error.status,
            "code": error.code,
        },
        headers={"Retry-After": str(error.retry_after)} if error.retry_after is not None else {},
        media_type="application/problem+json",
    )


def _service(request: Request) -> AccountService:
    return cast(AccountService, request.app.state.account_service)


def _settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


class ChallengeBinding(TypedDict):
    cookie: str | None
    csrf: str | None
    token: str | None


def _binding(request: Request) -> ChallengeBinding:
    return {
        "cookie": request.cookies.get(LOGIN_COOKIE),
        "csrf": request.headers.get("X-CSRF-Token"),
        "token": request.cookies.get(_settings(request).guest_cookie_name),
    }


def _peer(request: Request) -> str:
    # Never trust arbitrary Forwarded / X-Forwarded-For. Proxy trust must be
    # configured at the ASGI server / edge before release.
    return request.client.host if request.client else "unknown"


def _login_cookie(response: Response, settings: Settings, name: str, value: str, age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=age,
        httponly=True,
        secure=settings.guest_cookie_secure,
        samesite="strict",
        path="/v1/account",
        domain=settings.cookie_domain,
    )


def _clear_login(response: Response, settings: Settings) -> None:
    for name in (LOGIN_COOKIE, RESTORE_COOKIE):
        response.delete_cookie(name, path="/v1/account", domain=settings.cookie_domain)


@router.get("", response_model=AccountStatus)
async def status(request: Request, response: Response) -> AccountStatus:
    settings = _settings(request)
    signed_in, email, expiry = await _service(request).status(
        request.cookies.get(settings.guest_cookie_name)
    )
    return AccountStatus(
        login_enabled=settings.auth_enabled
        and (settings.auth_delivery_approved or settings.auth_google_enabled),
        google_login_enabled=settings.auth_enabled and settings.auth_google_enabled,
        signed_in=signed_in,
        masked_email=email,
        profile_expires_at=expiry.isoformat() if expiry else None,
        guest_inactivity_days=settings.guest_ttl_days,
    )


@router.post("/login/code", response_model=CodeResponse)
async def code(body: CodeRequest, request: Request, response: Response) -> CodeResponse:
    settings = _settings(request)
    challenge = await _service(request).request_code(
        body.email,
        token=request.cookies.get(settings.guest_cookie_name),
        csrf=request.headers.get("X-CSRF-Token"),
        consent=body.account_storage_consent,
        peer=_peer(request),
    )
    _login_cookie(response, settings, LOGIN_COOKIE, challenge.cookie, CHALLENGE_SECONDS)
    response.delete_cookie(RESTORE_COOKIE, path="/v1/account", domain=settings.cookie_domain)
    return CodeResponse(
        login_csrf_token=challenge.csrf_token,
        expires_at=challenge.expires_at.isoformat(),
    )


def _transition(request: Request, response: Response, result: LoginResult) -> LoginResponse:
    settings = _settings(request)
    session = None
    if result.status == "signed_in":
        if result.guest is None or result.token is None or result.csrf_token is None:
            raise RuntimeError("account transition missing device credentials")
        clear_profile_cookies(response, settings)
        set_profile_cookies(response, settings, result.token, result.csrf_token)
        _clear_login(response, settings)
        guests = cast(GuestSessionService, request.app.state.guest_session_service)
        session = AccountSession(
            state=result.guest.state.value,
            onboarding_status=result.guest.onboarding_status.value,
            expires_at=result.guest.expires_at.isoformat(),
            csrf_token=result.csrf_token,
            session_epoch=guests.session_epoch(result.guest),
            resumed=True,
        )
    elif result.status == "restore_required" and result.restore_token:
        _login_cookie(response, settings, RESTORE_COOKIE, result.restore_token, 300)
    else:
        _clear_login(response, settings)
    return LoginResponse(
        status=result.status,
        session=session,
        masked_email=result.masked_email,
        profile_expires_at=result.profile_expires_at.isoformat()
        if result.profile_expires_at
        else None,
    )


@router.post("/login/verify", response_model=LoginResponse, response_model_exclude_none=True)
async def verify(body: VerifyRequest, request: Request, response: Response) -> LoginResponse:
    result = await _service(request).verify(body.code, peer=_peer(request), **_binding(request))
    return _transition(request, response, result)


@router.post("/login/google", response_model=GoogleResponse)
async def google_start(body: GoogleRequest, request: Request, response: Response) -> GoogleResponse:
    settings = _settings(request)
    challenge, url = await _service(request).start_google(
        token=request.cookies.get(settings.guest_cookie_name),
        csrf=request.headers.get("X-CSRF-Token"),
        consent=body.account_storage_consent,
        peer=_peer(request),
    )
    _login_cookie(response, settings, LOGIN_COOKIE, challenge.cookie, CHALLENGE_SECONDS)
    response.delete_cookie(RESTORE_COOKIE, path="/v1/account", domain=settings.cookie_domain)
    return GoogleResponse(authorize_url=url, expires_at=challenge.expires_at.isoformat())


@router.post("/login/google/verify", response_model=LoginResponse, response_model_exclude_none=True)
async def google_verify(
    body: GoogleVerifyRequest, request: Request, response: Response
) -> LoginResponse:
    result = await _service(request).verify_google(
        body.code, peer=_peer(request), **_binding(request)
    )
    return _transition(request, response, result)


@router.post("/login/restore", response_model=LoginResponse, response_model_exclude_none=True)
async def restore(body: RestoreRequest, request: Request, response: Response) -> LoginResponse:
    result = await _service(request).restore(
        proof=request.cookies.get(RESTORE_COOKIE), **_binding(request)
    )
    return _transition(request, response, result)


@router.post("/login/cancel", status_code=204)
async def cancel(request: Request, response: Response) -> Response:
    await _service(request).cancel(**_binding(request))
    _clear_login(response, _settings(request))
    response.status_code = 204
    return response


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response) -> Response:
    settings = _settings(request)
    await _service(request).logout(
        request.cookies.get(settings.guest_cookie_name), request.headers.get("X-CSRF-Token")
    )
    clear_profile_cookies(response, settings)
    _clear_login(response, settings)
    response.status_code = 204
    return response
