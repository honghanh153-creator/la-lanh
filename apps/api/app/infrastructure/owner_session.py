from typing import cast

from fastapi import Request

from app.config import Settings
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.identity.models import OwnerIdentity
from app.domains.identity.service import OwnerIdentityService, OwnerSessionUnavailable


async def resume_owner_for_guest(request: Request, identity: OwnerIdentityService) -> OwnerIdentity:
    """Owner GETs and mutations must agree with the current guest credential."""
    settings = cast(Settings, request.app.state.settings)
    guests = cast(GuestSessionService, request.app.state.guest_session_service)
    owner = await identity.resume(request.cookies.get(settings.owner_cookie_name))
    try:
        guest = await guests.resume(request.cookies.get(settings.guest_cookie_name))
    except GuestDomainError as error:
        raise OwnerSessionUnavailable from error
    if owner.source_guest_id != guest.id:
        raise OwnerSessionUnavailable
    return owner
