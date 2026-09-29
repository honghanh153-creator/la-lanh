from datetime import datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.domains.guest.errors import CsrfRejected, GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.models import OwnerIdentity
from app.domains.identity.service import OwnerIdentityService, OwnerSessionUnavailable
from app.domains.la_chung.models import IdentityMode, RequestStatus
from app.domains.la_chung.service import LaChungError, LaChungService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
public_router = APIRouter()


class InviteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient_label: str = Field(min_length=1, max_length=40)
    context: Literal["bff", "crush", "couple", "friend", "workmate"]
    idempotency_key: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


class InviteResponse(BaseModel):
    id: UUID
    recipient_label: str
    context: str
    status: RequestStatus
    created_at: datetime
    expires_at: datetime
    share_url: str | None = None


class PublicStatementResponse(BaseModel):
    id: str
    text: str
    domain: str


class PublicInviteResponse(BaseModel):
    recipient_label: str
    context: str
    expires_at: datetime
    statements: tuple[PublicStatementResponse, ...]
    privacy_note: str = "Không cần tài khoản, ngày sinh hay danh bạ."


class SubmitResponseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement_ids: tuple[str, ...] = Field(min_length=3, max_length=5)
    identity_mode: IdentityMode = IdentityMode.ANONYMOUS
    display_alias: str | None = Field(default=None, max_length=24)
    idempotency_key: str = Field(min_length=16, max_length=128)


class SubmitResponseResult(BaseModel):
    request_id: UUID
    submitted_at: datetime
    resumed: bool


class OwnerResultResponse(BaseModel):
    request_id: UUID
    recipient_label: str
    identity_mode: IdentityMode
    display_alias: str | None
    statements: tuple[str, ...]
    submitted_at: datetime


class ReportRequest(BaseModel):
    reason: Literal["not_for_me", "unsafe", "spam", "other"]


def _service(request: Request) -> LaChungService:
    return cast(LaChungService, request.app.state.la_chung_service)


def _new_activity_retired(request: Request) -> bool:
    return not bool(request.app.state.settings.la_chung_accepting_new_activity)


async def _owner(request: Request) -> OwnerIdentity:
    settings = request.app.state.settings
    identity = cast(OwnerIdentityService, request.app.state.owner_identity_service)
    return await identity.resume(request.cookies.get(settings.owner_cookie_name))


async def _owner_mutation(request: Request, csrf_token: str | None) -> OwnerIdentity:
    owner = await _owner(request)
    settings = request.app.state.settings
    require_trusted_origin(request, trusted_origins(request))
    guests = cast(GuestSessionService, request.app.state.guest_session_service)
    guest = await guests.verify_csrf(
        request.cookies.get(settings.guest_cookie_name),
        csrf_token,
    )
    if guest.id != owner.source_guest_id:
        raise CsrfRejected
    return owner


def _safe_public(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )


def _invite_response(view, *, share_url: str | None = None) -> InviteResponse:  # type: ignore[no-untyped-def]
    return InviteResponse(
        id=view.id,
        recipient_label=view.recipient_label,
        context=view.context,
        status=view.status,
        created_at=view.created_at,
        expires_at=view.expires_at,
        share_url=share_url,
    )


@router.post(
    "/la-chung/requests",
    response_model=InviteResponse,
    responses={401: {}, 410: {}, 422: {}},
)
async def create_invite(
    body: InviteCreateRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> InviteResponse | Response:
    if _new_activity_retired(request):
        return Response(status_code=410)
    try:
        owner = await _owner_mutation(request, csrf_token)
        view, token = await _service(request).create(
            principal_id=owner.principal_id,
            recipient_label=body.recipient_label,
            context=body.context,
            idempotency_key=body.idempotency_key,
        )
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    except GuestDomainError:
        return Response(status_code=403)
    except LaChungError:
        return Response(status_code=422)
    return _invite_response(view, share_url=f"/la-chung/i/{token}")


@router.get("/la-chung/requests", response_model=tuple[InviteResponse, ...])
async def list_invites(request: Request) -> tuple[InviteResponse, ...] | Response:
    try:
        owner = await _owner(request)
    except OwnerSessionUnavailable:
        return Response(status_code=401)
    return tuple(
        _invite_response(view) for view in await _service(request).list_owned(owner.principal_id)
    )


@router.post(
    "/la-chung/requests/{request_id}/resend",
    response_model=InviteResponse,
    responses={410: {}},
)
async def resend_invite(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> InviteResponse | Response:
    if _new_activity_retired(request):
        return Response(status_code=410)
    try:
        owner = await _owner_mutation(request, csrf_token)
        token = await _service(request).resend(owner.principal_id, request_id)
        views = await _service(request).list_owned(owner.principal_id)
        view = next(item for item in views if item.id == request_id)
    except GuestDomainError:
        return Response(status_code=403)
    except (OwnerSessionUnavailable, LaChungError, StopIteration):
        return Response(status_code=404)
    return _invite_response(view, share_url=f"/la-chung/i/{token}")


@router.post("/la-chung/requests/{request_id}/revoke", status_code=204)
async def revoke_invite(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _service(request).revoke(owner.principal_id, request_id)
    except GuestDomainError:
        return Response(status_code=403)
    except (OwnerSessionUnavailable, LaChungError):
        return Response(status_code=404)
    return Response(status_code=204)


@router.post(
    "/la-chung/requests/{request_id}/replacement",
    response_model=InviteResponse,
    responses={410: {}},
)
async def replace_invite(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> InviteResponse | Response:
    if _new_activity_retired(request):
        return Response(status_code=410)
    try:
        owner = await _owner_mutation(request, csrf_token)
        view, token = await _service(request).replace(owner.principal_id, request_id)
    except GuestDomainError:
        return Response(status_code=403)
    except (OwnerSessionUnavailable, LaChungError):
        return Response(status_code=404)
    return _invite_response(view, share_url=f"/la-chung/i/{token}")


@router.get("/la-chung/results/{request_id}", response_model=OwnerResultResponse)
async def owner_result(request_id: UUID, request: Request) -> OwnerResultResponse | Response:
    try:
        owner = await _owner(request)
        result = await _service(request).result(owner.principal_id, request_id)
    except (OwnerSessionUnavailable, LaChungError):
        return Response(status_code=404)
    return OwnerResultResponse(
        request_id=result.request_id,
        recipient_label=result.recipient_label,
        identity_mode=result.identity_mode,
        display_alias=result.display_alias,
        statements=result.statements,
        submitted_at=result.submitted_at,
    )


@router.post("/la-chung/results/{request_id}/hide", status_code=204)
async def hide_owner_result(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _service(request).hide_result(owner.principal_id, request_id)
    except GuestDomainError:
        return Response(status_code=403)
    except (OwnerSessionUnavailable, LaChungError):
        return Response(status_code=404)
    return Response(status_code=204)


@router.delete("/la-chung/results/{request_id}", status_code=204)
async def delete_owner_result(
    request_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    try:
        owner = await _owner_mutation(request, csrf_token)
        await _service(request).delete_result(owner.principal_id, request_id)
    except GuestDomainError:
        return Response(status_code=403)
    except (OwnerSessionUnavailable, LaChungError):
        return Response(status_code=404)
    return Response(status_code=204)


@public_router.get(
    "/public/la-chung/{token}",
    response_model=PublicInviteResponse,
    responses={410: {}},
)
async def public_invite(
    token: str, request: Request, response: Response
) -> PublicInviteResponse | Response:
    _safe_public(response)
    if _new_activity_retired(request):
        return Response(status_code=410, headers=dict(response.headers))
    try:
        invite = await _service(request).preview(token)
    except LaChungError:
        return Response(status_code=404, headers=dict(response.headers))
    return PublicInviteResponse(
        recipient_label=invite.recipient_label,
        context=invite.context,
        expires_at=invite.expires_at,
        statements=tuple(
            PublicStatementResponse(id=item.id, text=item.text, domain=item.domain)
            for item in invite.statements
        ),
    )


@public_router.post(
    "/public/la-chung/{token}/responses",
    response_model=SubmitResponseResult,
    responses={410: {}},
)
async def submit_response(
    token: str,
    body: SubmitResponseRequest,
    request: Request,
    response: Response,
) -> SubmitResponseResult | Response:
    _safe_public(response)
    if _new_activity_retired(request):
        return Response(status_code=410, headers=dict(response.headers))
    try:
        result = await _service(request).submit(
            token=token,
            selections=body.statement_ids,
            identity_mode=body.identity_mode,
            display_alias=body.display_alias,
            idempotency_key=body.idempotency_key,
        )
    except LaChungError:
        return Response(status_code=404, headers=dict(response.headers))
    settings = request.app.state.settings
    response.set_cookie(
        "la_lanh_lc_receipt",
        result.receipt_token,
        httponly=True,
        secure=settings.guest_cookie_secure,
        samesite="strict",
        max_age=7 * 86400,
        path="/v1/public/la-chung/receipt",
    )
    return SubmitResponseResult(
        request_id=result.request_id,
        submitted_at=result.submitted_at,
        resumed=result.resumed,
    )


@public_router.post("/public/la-chung/receipt/withdraw", status_code=204)
async def withdraw_response(
    request: Request,
    response: Response,
    receipt: Annotated[str | None, Cookie(alias="la_lanh_lc_receipt")] = None,
) -> Response:
    _safe_public(response)
    try:
        await _service(request).withdraw(receipt or "")
    except LaChungError:
        return Response(status_code=404, headers=dict(response.headers))
    success = Response(status_code=204, headers=dict(response.headers))
    success.delete_cookie("la_lanh_lc_receipt", path="/v1/public/la-chung/receipt")
    return success


@public_router.post("/public/la-chung/{token}/report", status_code=202)
async def report_invite(
    token: str, body: ReportRequest, request: Request, response: Response
) -> Response:
    _safe_public(response)
    await _service(request).report(token, body.reason)
    return Response(status_code=202, headers=dict(response.headers))
