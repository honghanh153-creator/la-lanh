from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domains.birth.errors import BirthDomainError
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.models import OwnerIdentity
from app.domains.identity.service import OwnerIdentityService, OwnerSessionUnavailable
from app.domains.matching.errors import MatchingDomainError
from app.domains.matching.models import (
    GenderPreference,
    MatchingGender,
    MatchingIntent,
    MatchingProfile,
    MatchingReadiness,
    VerificationStatus,
    WeeklyIntent,
)
from app.domains.matching.service import MatchingService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter(prefix="/matching")


class MatchingProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=2, max_length=32, pattern=r"^[^<>\n\r]+$")
    gender_identity: MatchingGender
    intent: MatchingIntent
    gender_preference: GenderPreference
    min_age: int = Field(ge=18, le=120)
    max_age: int = Field(ge=18, le=120)
    region_code: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    weekly_intent: WeeklyIntent = WeeklyIntent.LET_LA_BALANCE


class MatchingConsentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, max_length=64)


class PoolMembershipInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool


class MatchingProfileResponse(BaseModel):
    display_name: str
    gender_identity: MatchingGender
    intent: MatchingIntent
    gender_preference: GenderPreference
    min_age: int
    max_age: int
    region_code: str
    weekly_intent: WeeklyIntent
    active: bool
    joined_at: datetime | None
    updated_at: datetime


class ReadinessCheck(BaseModel):
    key: str
    complete: bool
    blocking: bool


class MatchingReadinessResponse(BaseModel):
    ready: bool
    profile: MatchingProfileResponse | None
    consent_version: str | None
    verification_status: VerificationStatus
    verification_reason_code: str | None
    birth_profile_level: int
    checks: list[ReadinessCheck]


def _identity(request: Request) -> OwnerIdentityService:
    return cast(OwnerIdentityService, request.app.state.owner_identity_service)


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _matching(request: Request) -> MatchingService:
    return cast(MatchingService, request.app.state.matching_service)


async def _owner(request: Request) -> OwnerIdentity:
    settings = request.app.state.settings
    return await _identity(request).resume(request.cookies.get(settings.owner_cookie_name))


async def _owner_mutation(request: Request, csrf_token: str | None) -> OwnerIdentity:
    settings = request.app.state.settings
    require_trusted_origin(request, trusted_origins(request))
    guest = await _guests(request).verify_csrf(
        request.cookies.get(settings.guest_cookie_name), csrf_token
    )
    owner = await _owner(request)
    if owner.source_guest_id != guest.id:
        raise OwnerSessionUnavailable
    return owner


def _problem(status: int, code: str, title: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": "about:blank", "title": title, "status": status, "code": code},
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


def _profile_response(profile: MatchingProfile) -> MatchingProfileResponse:
    return MatchingProfileResponse(
        display_name=profile.display_name,
        gender_identity=profile.gender_identity,
        intent=profile.intent,
        gender_preference=profile.gender_preference,
        min_age=profile.min_age,
        max_age=profile.max_age,
        region_code=profile.region_code,
        weekly_intent=profile.weekly_intent,
        active=profile.active,
        joined_at=profile.joined_at,
        updated_at=profile.updated_at,
    )


def _readiness_response(value: MatchingReadiness) -> MatchingReadinessResponse:
    consented = value.consent is not None and value.consent.revoked_at is None
    return MatchingReadinessResponse(
        ready=value.ready,
        profile=_profile_response(value.profile) if value.profile else None,
        consent_version=value.consent.version if consented and value.consent else None,
        verification_status=value.verification.status,
        verification_reason_code=value.verification.reason_code,
        birth_profile_level=value.birth_profile_level,
        checks=[
            ReadinessCheck(key="age_18_plus", complete=value.age_eligible, blocking=True),
            ReadinessCheck(
                key="birth_profile_level_3",
                complete=value.birth_profile_level >= 3,
                blocking=True,
            ),
            ReadinessCheck(
                key="matching_profile", complete=value.profile is not None, blocking=True
            ),
            ReadinessCheck(key="matching_consent", complete=consented, blocking=True),
            ReadinessCheck(
                key="photo_verification",
                complete=value.verification.status is VerificationStatus.APPROVED,
                blocking=True,
            ),
        ],
    )


@router.get("/readiness", response_model=MatchingReadinessResponse, responses={401: {}, 409: {}})
async def get_readiness(
    request: Request, response: Response
) -> MatchingReadinessResponse | Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        owner = await _owner(request)
        value = await _matching(request).readiness(owner.principal_id, owner.source_guest_id)
    except OwnerSessionUnavailable:
        return _problem(401, "OWNER_REQUIRED", "Xác nhận tài khoản để vào Vòng Lá")
    except BirthDomainError as error:
        return _problem(error.status_code, error.code, "Cần hoàn thiện Lá khai sinh trước")
    return _readiness_response(value)


@router.put("/profile", response_model=MatchingProfileResponse, responses={401: {}, 403: {}})
async def put_profile(
    payload: MatchingProfileInput,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> MatchingProfileResponse | Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    if payload.min_age > payload.max_age:
        return _problem(422, "MATCHING_AGE_RANGE_INVALID", "Khoảng tuổi chưa hợp lệ")
    try:
        owner = await _owner_mutation(request, csrf_token)
        profile = await _matching(request).save_profile(
            owner.principal_id,
            display_name=payload.display_name,
            gender_identity=payload.gender_identity,
            intent=payload.intent,
            gender_preference=payload.gender_preference,
            min_age=payload.min_age,
            max_age=payload.max_age,
            region_code=payload.region_code,
            weekly_intent=payload.weekly_intent,
        )
    except (OwnerSessionUnavailable, GuestDomainError):
        return _problem(401, "OWNER_REQUIRED", "Phiên Vòng Lá đã hết hạn")
    except MatchingDomainError as error:
        return _problem(error.status_code, error.code, "Hồ sơ Vòng Lá chưa hợp lệ")
    return _profile_response(profile)


@router.post("/consent", status_code=204, responses={401: {}, 403: {}, 422: {}})
async def grant_consent(
    payload: MatchingConsentInput,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _matching(request).grant_consent(owner.principal_id, version=payload.version)
    except (OwnerSessionUnavailable, GuestDomainError):
        return _problem(401, "OWNER_REQUIRED", "Phiên Vòng Lá đã hết hạn")
    except MatchingDomainError as error:
        return _problem(error.status_code, error.code, "Consent matching không hợp lệ")
    return Response(status_code=204, headers={"Cache-Control": "no-store, max-age=0"})


@router.delete("/consent", status_code=204, responses={401: {}, 403: {}})
async def withdraw_consent(
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _matching(request).withdraw_consent(owner.principal_id)
    except (OwnerSessionUnavailable, GuestDomainError):
        return _problem(401, "OWNER_REQUIRED", "Phiên Vòng Lá đã hết hạn")
    return Response(status_code=204, headers={"Cache-Control": "no-store, max-age=0"})


@router.put(
    "/pool-membership", response_model=MatchingProfileResponse, responses={401: {}, 409: {}}
)
async def set_pool_membership(
    payload: PoolMembershipInput,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> MatchingProfileResponse | Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        owner = await _owner_mutation(request, csrf_token)
        profile = await _matching(request).set_pool_membership(
            owner.principal_id,
            owner.source_guest_id,
            active=payload.active,
        )
    except (OwnerSessionUnavailable, GuestDomainError):
        return _problem(401, "OWNER_REQUIRED", "Phiên Vòng Lá đã hết hạn")
    except (BirthDomainError, MatchingDomainError) as error:
        return _problem(error.status_code, error.code, "Hồ sơ chưa sẵn sàng vào vòng")
    return _profile_response(profile)
