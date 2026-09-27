from datetime import date, datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.models import OwnerIdentity
from app.domains.identity.service import OwnerIdentityService, OwnerSessionUnavailable
from app.domains.radar.models import RadarInviteView, RadarMode, RadarStatus
from app.domains.radar.service import (
    CONSENT_VERSION,
    RadarChartRequired,
    RadarError,
    RadarInvalid,
    RadarService,
)
from app.domains.relationships.models import RelationshipVoice
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
public_router = APIRouter()
RADAR_COOKIE = "la_lanh_radar_invite"
RADAR_RECEIPT_COOKIE = "la_lanh_radar_receipt"


class RadarCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient_label: str = Field(min_length=1, max_length=40)
    context: Literal["crush", "friend", "partner", "someone"]
    voice: RelationshipVoice = RelationshipVoice.STRAIGHT_WARM


class RadarPrivateCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient_label: str = Field(min_length=1, max_length=40)
    context: Literal["crush", "friend", "partner", "someone"]
    voice: RelationshipVoice = RelationshipVoice.STRAIGHT_WARM
    birth_date: date
    birth_time_local: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    place_id: str = Field(min_length=2, max_length=80)
    consent_version: str = Field(min_length=1, max_length=64)
    authorization_attested: bool


class RadarInviteResponse(BaseModel):
    id: UUID
    recipient_label: str
    context: str
    voice: str
    mode: RadarMode
    status: RadarStatus
    created_at: datetime
    expires_at: datetime
    share_url: str | None = None


class PublicRadarInviteResponse(BaseModel):
    request_id: UUID
    recipient_label: str
    context: str
    voice: str
    expires_at: datetime
    consent_version: str = CONSENT_VERSION
    requires_exact_birth_profile: bool = True
    privacy_note: str = (
        "Người mời không nhìn thấy ngày, giờ hoặc nơi sinh của bạn. "
        "Kết quả chỉ mở sau khi bạn tự nhập và đồng ý."
    )


class RadarAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    consent_version: str = Field(min_length=1, max_length=64)


class RadarBoundActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID


class RadarResultResponse(BaseModel):
    request_id: UUID | None = None
    recipient_label: str | None = None
    mode: RadarMode | None = None
    version: str
    headline: str
    summary: str
    pair_signature: dict[str, Any] | None = None
    compatibility_map: list[dict[str, Any]] = Field(default_factory=list)
    sections: list[dict[str, Any]] = Field(default_factory=list)
    dimensions: list[dict[str, Any]] = Field(default_factory=list)
    strongest_contacts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None
    disclaimer: str


def _service(request: Request) -> RadarService:
    return cast(RadarService, request.app.state.radar_service)


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


async def _owner(request: Request) -> OwnerIdentity:
    identity = cast(OwnerIdentityService, request.app.state.owner_identity_service)
    settings = request.app.state.settings
    return await identity.resume(request.cookies.get(settings.owner_cookie_name))


async def _owner_mutation(request: Request, csrf_token: str | None) -> OwnerIdentity:
    owner = await _owner(request)
    settings = request.app.state.settings
    require_trusted_origin(request, trusted_origins(request))
    guest = await _guests(request).verify_csrf(
        request.cookies.get(settings.guest_cookie_name), csrf_token
    )
    if guest.id != owner.source_guest_id:
        raise RadarInvalid
    return owner


def _safe_public(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )


def _invite(view: RadarInviteView, share_url: str | None = None) -> RadarInviteResponse:
    return RadarInviteResponse(
        id=view.id,
        recipient_label=view.recipient_label,
        context=view.context,
        voice=view.voice,
        mode=view.mode,
        status=view.status,
        created_at=view.created_at,
        expires_at=view.expires_at,
        share_url=share_url,
    )


@router.post("/radar/private-checks", response_model=RadarResultResponse)
async def create_private_check(
    body: RadarPrivateCheckRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RadarResultResponse | Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        result = await _service(request).create_private_check(
            principal_id=owner.principal_id,
            owner_guest_id=owner.source_guest_id,
            recipient_label=body.recipient_label,
            context=body.context,
            voice=body.voice,
            birth_date=body.birth_date,
            birth_time_local=body.birth_time_local,
            place_id=body.place_id,
            consent_version=body.consent_version,
            authorization_attested=body.authorization_attested,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except GuestDomainError:
        return Response(status_code=403)
    except RadarChartRequired:
        return Response(status_code=409)
    except RadarError:
        return Response(status_code=422)
    return RadarResultResponse.model_validate(result)


@router.post("/radar/requests", response_model=RadarInviteResponse)
async def create_request(
    body: RadarCreateRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RadarInviteResponse | Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        view, token = await _service(request).create(
            principal_id=owner.principal_id,
            owner_guest_id=owner.source_guest_id,
            recipient_label=body.recipient_label,
            context=body.context,
            voice=body.voice,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except GuestDomainError:
        return Response(status_code=403)
    except RadarChartRequired:
        return Response(status_code=409)
    except RadarError:
        return Response(status_code=422)
    return _invite(view, f"/radar/i/{token}")


@router.get("/radar/requests", response_model=tuple[RadarInviteResponse, ...])
async def list_requests(request: Request) -> tuple[RadarInviteResponse, ...] | Response:
    try:
        owner = await _owner(request)
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    return tuple(_invite(view) for view in await _service(request).list_owned(owner.principal_id))


@router.post("/radar/requests/{request_id}/share", response_model=RadarInviteResponse)
async def share_request(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RadarInviteResponse | Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        token = await _service(request).share_token(owner.principal_id, request_id)
        view = next(
            item
            for item in await _service(request).list_owned(owner.principal_id)
            if item.id == request_id
        )
    except (OwnerSessionUnavailable, GuestDomainError, RadarError, StopIteration):
        return Response(status_code=404)
    return _invite(view, f"/radar/i/{token}")


@router.post("/radar/requests/{request_id}/revoke", status_code=204)
async def revoke_request(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _service(request).revoke(owner.principal_id, request_id)
    except (OwnerSessionUnavailable, GuestDomainError, RadarError):
        return Response(status_code=404)
    return Response(status_code=204)


@router.get("/radar/results/{request_id}", response_model=RadarResultResponse)
async def owner_result(request_id: UUID, request: Request) -> RadarResultResponse | Response:
    try:
        owner = await _owner(request)
        result = await _service(request).result(owner.principal_id, request_id)
    except (OwnerSessionUnavailable, RadarError):
        return Response(status_code=404)
    return RadarResultResponse.model_validate(result)


@router.delete("/radar/results/{request_id}", status_code=204)
async def delete_owner_result(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _service(request).delete(owner.principal_id, request_id)
    except (OwnerSessionUnavailable, GuestDomainError, RadarError):
        return Response(status_code=404)
    return Response(status_code=204)


@public_router.get("/public/radar/current", response_model=PublicRadarInviteResponse)
async def current_invite(
    request: Request,
    response: Response,
    token: Annotated[str | None, Cookie(alias=RADAR_COOKIE)] = None,
) -> PublicRadarInviteResponse | Response:
    _safe_public(response)
    try:
        invite = await _service(request).preview(token or "")
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    return PublicRadarInviteResponse(
        request_id=invite.request_id,
        recipient_label=invite.recipient_label,
        context=invite.context,
        voice=invite.voice,
        expires_at=invite.expires_at,
    )


@public_router.post("/public/radar/current/accept", response_model=RadarResultResponse)
async def accept_invite(
    body: RadarAcceptRequest,
    request: Request,
    response: Response,
    token: Annotated[str | None, Cookie(alias=RADAR_COOKIE)] = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RadarResultResponse | Response:
    _safe_public(response)
    settings = request.app.state.settings
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guests(request).verify_csrf(
            request.cookies.get(settings.guest_cookie_name), csrf_token
        )
        result = await _service(request).accept(
            token or "",
            recipient_guest_id=guest.id,
            consent_version=body.consent_version,
            expected_request_id=body.request_id,
        )
    except GuestDomainError:
        return Response(status_code=401, headers=dict(response.headers))
    except RadarChartRequired:
        return Response(status_code=409, headers=dict(response.headers))
    except RadarError:
        return Response(status_code=422, headers=dict(response.headers))
    response.set_cookie(
        RADAR_RECEIPT_COOKIE,
        result.receipt_token,
        httponly=True,
        secure=settings.guest_cookie_secure,
        samesite="strict",
        max_age=7 * 86400,
        path="/v1/public/radar/receipt",
    )
    response.delete_cookie(RADAR_COOKIE, path="/v1/public/radar")
    return RadarResultResponse.model_validate(
        {
            "request_id": result.request_id,
            "mode": RadarMode.CONSENTED_INVITE,
            **result.result,
        }
    )


@public_router.post("/public/radar/current/decline", status_code=204)
async def decline_invite(
    body: RadarBoundActionRequest,
    request: Request,
    response: Response,
    token: Annotated[str | None, Cookie(alias=RADAR_COOKIE)] = None,
) -> Response:
    _safe_public(response)
    require_trusted_origin(request, trusted_origins(request))
    try:
        invite = await _service(request).preview(token or "")
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    if invite.request_id != body.request_id:
        return Response(status_code=409, headers=dict(response.headers))
    response.delete_cookie(RADAR_COOKIE, path="/v1/public/radar")
    response.status_code = 204
    return response


@public_router.post("/public/radar/receipt/withdraw", status_code=204)
async def withdraw_result(
    body: RadarBoundActionRequest,
    request: Request,
    response: Response,
    receipt: Annotated[str | None, Cookie(alias=RADAR_RECEIPT_COOKIE)] = None,
) -> Response:
    _safe_public(response)
    try:
        require_trusted_origin(request, trusted_origins(request))
        await _service(request).withdraw(receipt or "", expected_request_id=body.request_id)
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    response.delete_cookie(RADAR_RECEIPT_COOKIE, path="/v1/public/radar/receipt")
    response.status_code = 204
    return response


@public_router.get("/public/radar/receipt", response_model=RadarResultResponse)
async def receipt_result(
    request: Request,
    response: Response,
    receipt: Annotated[str | None, Cookie(alias=RADAR_RECEIPT_COOKIE)] = None,
) -> RadarResultResponse | Response:
    _safe_public(response)
    try:
        result = await _service(request).receipt_result(receipt or "")
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    return RadarResultResponse.model_validate(result)


@public_router.get("/public/radar/{token}", response_model=PublicRadarInviteResponse)
async def public_preview(
    token: str, request: Request, response: Response
) -> PublicRadarInviteResponse | Response:
    _safe_public(response)
    try:
        invite = await _service(request).preview(token)
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    settings = request.app.state.settings
    response.set_cookie(
        RADAR_COOKIE,
        token,
        httponly=True,
        secure=settings.guest_cookie_secure,
        samesite="lax",
        max_age=7 * 86400,
        path="/v1/public/radar",
    )
    return PublicRadarInviteResponse(
        request_id=invite.request_id,
        recipient_label=invite.recipient_label,
        context=invite.context,
        voice=invite.voice,
        expires_at=invite.expires_at,
    )
