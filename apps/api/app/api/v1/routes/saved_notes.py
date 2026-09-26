import logging
from datetime import datetime, time
from typing import Annotated, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Cookie, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.domains.birth.errors import BirthDomainError
from app.domains.daily.service import DailyNoteService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.readings.application import ReadingApplicationError, ReadingApplicationService
from app.domains.readings.models import ReadingContentProjection, ReadingPurpose
from app.domains.saved.errors import (
    SavedDomainError,
    SavedReadingUnavailable,
    SavedRevisionUnavailable,
)
from app.domains.saved.service import SavedNoteService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
logger = logging.getLogger(__name__)


class SavedNoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: UUID | None = None


class SavedNoteResponse(BaseModel):
    id: UUID
    daily_note_id: UUID
    note_snapshot: dict[str, object]
    saved_at: datetime
    revision_id: UUID | None = None
    reading_snapshot: ReadingContentProjection | None = None


def _problem(error: BirthDomainError | GuestDomainError | SavedDomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Saved note request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
    )


def _guest_service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _saved_service(request: Request) -> SavedNoteService:
    return cast(SavedNoteService, request.app.state.saved_note_service)


async def _active_daily_reading(
    request: Request,
    *,
    guest_id: UUID,
    daily_note_id: UUID,
    expected_revision_id: UUID | None,
) -> tuple[UUID | None, ReadingContentProjection | None]:
    reading_service = cast(
        ReadingApplicationService | None,
        getattr(request.app.state, "reading_application_service", None),
    )
    daily_service = cast(
        DailyNoteService | None,
        getattr(request.app.state, "daily_note_service", None),
    )
    if reading_service is None or daily_service is None:
        if expected_revision_id is not None:
            raise SavedRevisionUnavailable
        return None, None
    try:
        note = await daily_service.find_owned(guest_id, daily_note_id)
        snapshot = await daily_service.current_birth_snapshot(guest_id)
        requested_at = datetime.combine(
            note.note_date,
            time(hour=12),
            tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"),
        )
        projection = await reading_service.project(
            guest_id=guest_id,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
            requested_at=requested_at,
        )
    except BirthDomainError:
        raise
    except ReadingApplicationError as error:
        logger.warning("Could not resolve a reading for saved-note freeze")
        raise SavedReadingUnavailable from error
    if expected_revision_id is not None and projection.active.revision_id != expected_revision_id:
        raise SavedRevisionUnavailable
    return snapshot.profile_id, projection.active


@router.get("/saved-notes", response_model=list[SavedNoteResponse], responses={401: {}})
async def list_saved_notes(
    request: Request,
    guest_token: Annotated[str | None, Cookie(alias="la_lanh_guest")] = None,
) -> list[SavedNoteResponse] | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name, guest_token)
    try:
        guest = await _guest_service(request).resume(token)
        saved = await _saved_service(request).list_for_guest(guest.id)
    except GuestDomainError as error:
        return _problem(error)
    return [
        SavedNoteResponse(
            id=item.id,
            daily_note_id=item.daily_note_id,
            note_snapshot=item.note_snapshot,
            saved_at=item.saved_at,
            revision_id=item.revision_id,
            reading_snapshot=item.reading_snapshot,
        )
        for item in saved
    ]


@router.put(
    "/daily-note/{daily_note_id}/saved",
    response_model=SavedNoteResponse,
    responses={401: {}, 403: {}, 404: {}},
)
async def save_note(
    daily_note_id: UUID,
    request: Request,
    body: SavedNoteRequest | None = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> SavedNoteResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        profile_id, reading = await _active_daily_reading(
            request,
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            expected_revision_id=body.revision_id if body is not None else None,
        )
        item = await _saved_service(request).save(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            profile_id=profile_id,
            reading=reading,
        )
    except (BirthDomainError, GuestDomainError, SavedDomainError) as error:
        return _problem(error)
    return SavedNoteResponse(
        id=item.id,
        daily_note_id=item.daily_note_id,
        note_snapshot=item.note_snapshot,
        saved_at=item.saved_at,
        revision_id=item.revision_id,
        reading_snapshot=item.reading_snapshot,
    )


@router.delete(
    "/daily-note/{daily_note_id}/saved",
    status_code=204,
    responses={401: {}, 403: {}, 404: {}},
)
async def unsave_note(
    daily_note_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        await _saved_service(request).unsave(guest_id=guest.id, daily_note_id=daily_note_id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return Response(status_code=204)
