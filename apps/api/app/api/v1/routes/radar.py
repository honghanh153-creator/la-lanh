from datetime import date, datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.models import OwnerIdentity
from app.domains.identity.service import OwnerIdentityService, OwnerSessionUnavailable
from app.domains.radar.models import RadarInviteView, RadarMode, RadarReceivedView, RadarStatus
from app.domains.radar.service import (
    CONSENT_VERSION,
    RECEIPT_TTL,
    RadarChartRequired,
    RadarConflict,
    RadarError,
    RadarInvalid,
    RadarLimitReached,
    RadarService,
)
from app.domains.relationships.models import RelationshipVoice
from app.infrastructure.csrf import require_trusted_origin, trusted_origins
from app.infrastructure.owner_session import resume_owner_for_guest

router = APIRouter()
public_router = APIRouter()
RADAR_COOKIE = "la_lanh_radar_invite"
RADAR_RECEIPT_COOKIE = "la_lanh_radar_receipt"


class RadarProblem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    code: Literal[
        "RADAR_LIMIT_REACHED",
        "RADAR_IDEMPOTENCY_CONFLICT",
        "RADAR_CHART_REQUIRED",
        "ADMISSION_LIMITED",
    ]


RADAR_CREATE_ERRORS: dict[int | str, dict[str, Any]] = {
    status: {
        "description": description,
        "content": {"application/problem+json": {"schema": RadarProblem.model_json_schema()}},
    }
    for status, description in (
        (429, "Radar capacity reached or admission rate limited"),
        (409, "Chart required or conflicting retry"),
    )
}


def _creation_problem(
    error: RadarLimitReached | RadarConflict | RadarChartRequired,
) -> JSONResponse:
    limited = isinstance(error, RadarLimitReached)
    status = 429 if limited else 409
    problem = RadarProblem(
        title="Radar storage limit reached" if limited else "Radar chart or retry unavailable",
        status=status,
        code=(
            "RADAR_LIMIT_REACHED"
            if limited
            else "RADAR_CHART_REQUIRED"
            if isinstance(error, RadarChartRequired)
            else "RADAR_IDEMPOTENCY_CONFLICT"
        ),
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(),
        headers={"Cache-Control": "no-store"},
        media_type="application/problem+json",
    )


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
    birth_time_mode: Literal["exact", "unknown"] = "exact"
    birth_time_local: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    place_id: str = Field(min_length=2, max_length=80)
    consent_version: str = Field(min_length=1, max_length=64)
    authorization_attested: bool

    @model_validator(mode="after")
    def validate_birth_time(self) -> "RadarPrivateCheckRequest":
        if self.birth_time_mode == "exact" and self.birth_time_local is None:
            raise ValueError("exact birth time requires birth_time_local")
        if self.birth_time_mode == "unknown" and self.birth_time_local is not None:
            raise ValueError("unknown birth time must not include birth_time_local")
        return self


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


class RadarInviteWithdrawRequest(BaseModel):
    """B proves possession of the invite link; the token is in the body, never the URL."""

    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=43, max_length=43)


class RadarReceivedItem(BaseModel):
    request_id: UUID
    context: str
    voice: str
    completed_at: datetime
    expires_at: datetime


class RadarReceivedListResponse(BaseModel):
    items: list[RadarReceivedItem]


class RadarResultResponse(BaseModel):
    request_id: UUID | None = None
    recipient_label: str | None = None
    mode: RadarMode | None = None
    # Owner views only: when this stored result is hidden and queued for deletion.
    expires_at: datetime | None = None
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
    return await resume_owner_for_guest(request, identity)


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


@router.post(
    "/radar/private-checks", response_model=RadarResultResponse, responses=RADAR_CREATE_ERRORS
)
async def create_private_check(
    body: RadarPrivateCheckRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
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
            birth_time_mode=body.birth_time_mode,
            birth_time_local=body.birth_time_local,
            place_id=body.place_id,
            consent_version=body.consent_version,
            authorization_attested=body.authorization_attested,
            idempotency_key=idempotency_key,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except GuestDomainError:
        return Response(status_code=403)
    except RadarChartRequired as error:
        return _creation_problem(error)
    except (RadarLimitReached, RadarConflict) as error:
        return _creation_problem(error)
    except RadarError:
        return Response(status_code=422)
    return RadarResultResponse.model_validate(result)


@router.post("/radar/requests", response_model=RadarInviteResponse, responses=RADAR_CREATE_ERRORS)
async def create_request(
    body: RadarCreateRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
) -> RadarInviteResponse | Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        view, token = await _service(request).create(
            principal_id=owner.principal_id,
            owner_guest_id=owner.source_guest_id,
            recipient_label=body.recipient_label,
            context=body.context,
            voice=body.voice,
            idempotency_key=idempotency_key,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except GuestDomainError:
        return Response(status_code=403)
    except RadarChartRequired as error:
        return _creation_problem(error)
    except (RadarLimitReached, RadarConflict) as error:
        return _creation_problem(error)
    except RadarError:
        return Response(status_code=422)
    return _invite(view, f"/radar/i/{token}")


@router.get("/radar/requests", response_model=tuple[RadarInviteResponse, ...])
async def list_requests(
    request: Request,
    before: UUID | None = None,
    mode: RadarMode | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> tuple[RadarInviteResponse, ...] | Response:
    try:
        owner = await _owner(request)
        views = await _service(request).list_owned(
            owner.principal_id,
            before=before,
            mode=mode,
            limit=limit,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except RadarError:
        return Response(status_code=404)
    return tuple(_invite(view) for view in views)


@router.post("/radar/requests/{request_id}/share", response_model=RadarInviteResponse)
async def share_request(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RadarInviteResponse | Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        view, token = await _service(request).share_invite(owner.principal_id, request_id)
    except (OwnerSessionUnavailable, GuestDomainError, RadarError):
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


async def _recipient_guest(request: Request) -> UUID:
    settings = request.app.state.settings
    guest = await _guests(request).resume(request.cookies.get(settings.guest_cookie_name))
    return guest.id


def _received_item(view: RadarReceivedView) -> RadarReceivedItem:
    return RadarReceivedItem(
        request_id=view.request_id,
        context=view.context,
        voice=view.voice,
        completed_at=view.completed_at,
        expires_at=view.expires_at,
    )


@router.get("/radar/received", response_model=RadarReceivedListResponse)
async def received_results(request: Request) -> RadarReceivedListResponse | Response:
    """Results B accepted, found by B's own guest session (P09 D2): no receipt needed."""
    try:
        views = await _service(request).received(await _recipient_guest(request))
    except GuestDomainError:
        return Response(status_code=401)
    return RadarReceivedListResponse(items=[_received_item(view) for view in views])


@router.get("/radar/received/{request_id}", response_model=RadarResultResponse)
async def received_result(request_id: UUID, request: Request) -> RadarResultResponse | Response:
    try:
        result = await _service(request).received_result(
            await _recipient_guest(request), request_id
        )
    except (GuestDomainError, RadarError):
        return Response(status_code=404)
    return RadarResultResponse.model_validate(result)


@router.post("/radar/received/{request_id}/withdraw", status_code=204)
async def withdraw_received(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guests(request).verify_csrf(
            request.cookies.get(settings.guest_cookie_name), csrf_token
        )
        await _service(request).withdraw_received(guest.id, request_id)
    except (GuestDomainError, RadarError):
        return Response(status_code=404)
    return Response(status_code=204)


@public_router.post("/public/radar/invite/withdraw", status_code=204)
async def withdraw_by_invite(
    body: RadarInviteWithdrawRequest, request: Request, response: Response
) -> Response:
    """B withdraws by proving possession of the invite link, without receipt or session.

    Withdraw only: A holds the same link, so it never opens B's view.
    """
    _safe_public(response)
    try:
        require_trusted_origin(request, trusted_origins(request))
        await _service(request).withdraw_by_invite(body.token)
    except RadarError:
        return Response(status_code=404, headers=dict(response.headers))
    response.status_code = 204
    return response


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
        max_age=int(RECEIPT_TTL.total_seconds()),
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
