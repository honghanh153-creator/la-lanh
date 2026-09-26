from datetime import datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from pydantic import BaseModel

from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.service import OwnerIdentityService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()


class OwnerClaimResponse(BaseModel):
    principal_id: UUID
    expires_at: datetime
    resumed: bool


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _identity(request: Request) -> OwnerIdentityService:
    return cast(OwnerIdentityService, request.app.state.owner_identity_service)


@router.post("/identity/claim", response_model=OwnerClaimResponse, responses={401: {}, 403: {}})
async def claim_identity(
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> OwnerClaimResponse | Response:
    settings = request.app.state.settings
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guests(request).verify_csrf(
            request.cookies.get(settings.guest_cookie_name), csrf_token
        )
    except GuestDomainError:
        return Response(status_code=401)
    claimed = await _identity(request).claim_guest(guest.id)
    response.set_cookie(
        settings.owner_cookie_name,
        claimed.token,
        httponly=True,
        secure=settings.guest_cookie_secure,
        samesite="strict",
        max_age=settings.owner_ttl_days * 86400,
        path="/v1",
        domain=settings.cookie_domain,
    )
    return OwnerClaimResponse(
        principal_id=claimed.principal_id,
        expires_at=claimed.expires_at,
        resumed=claimed.resumed,
    )
