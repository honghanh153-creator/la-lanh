import logging
from datetime import datetime, time
from typing import Annotated, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.domains.birth.errors import BirthDomainError
from app.domains.daily.service import DailyNoteService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.readings.application import ReadingApplicationError, ReadingApplicationService
from app.domains.readings.models import ReadingContentProjection, ReadingPurpose
from app.domains.share.errors import (
    ShareArtifactUnavailable,
    ShareDomainError,
    ShareReadingUnavailable,
)
from app.domains.share.models import ShareFormat
from app.domains.share.service import ShareArtifactService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
logger = logging.getLogger(__name__)


class ShareArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: ShareFormat = ShareFormat.STORY_9_16
    revision_id: UUID | None = None


class SafeShareSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    body: str
    context_label: str
    content_version: str
    persona_mode: str
    persona_label: str
    persona_version: str
    watermark: str


class ShareArtifactResponse(BaseModel):
    id: UUID
    daily_note_id: UUID
    format: ShareFormat
    safe_snapshot: SafeShareSnapshotResponse
    token: str | None = None
    public_path: str | None = None
    created_at: datetime
    expires_at: datetime
    revision_id: UUID | None = None


class PublicShareArtifactResponse(BaseModel):
    format: ShareFormat
    safe_snapshot: SafeShareSnapshotResponse
    expires_at: datetime


def _problem(error: BirthDomainError | GuestDomainError | ShareDomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Share artifact is unavailable"
            if isinstance(error, ShareArtifactUnavailable)
            else "Share artifact request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
    )


def _guest_service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _share_service(request: Request) -> ShareArtifactService:
    return cast(ShareArtifactService, request.app.state.share_artifact_service)


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
            raise ShareArtifactUnavailable
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
        logger.warning("Could not resolve a reading for share freeze")
        raise ShareReadingUnavailable from error
    if expected_revision_id is not None and projection.active.revision_id != expected_revision_id:
        raise ShareArtifactUnavailable
    return snapshot.profile_id, projection.active


@router.post(
    "/daily-note/{daily_note_id}/share-artifacts",
    response_model=ShareArtifactResponse,
    responses={401: {}, 403: {}, 404: {}, 422: {}},
)
async def create_share_artifact(
    daily_note_id: UUID,
    body: ShareArtifactRequest,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ShareArtifactResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        profile_id, reading = await _active_daily_reading(
            request,
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            expected_revision_id=body.revision_id,
        )
        artifact, share_token = await _share_service(request).create(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            format=body.format,
            profile_id=profile_id,
            reading=reading,
        )
    except (BirthDomainError, GuestDomainError, ShareDomainError) as error:
        return _problem(error)
    public_path = f"/share/{share_token}"
    return ShareArtifactResponse(
        id=artifact.id,
        daily_note_id=artifact.daily_note_id,
        format=artifact.format,
        safe_snapshot=SafeShareSnapshotResponse.model_validate(artifact.safe_snapshot),
        token=share_token,
        public_path=public_path,
        created_at=artifact.created_at,
        expires_at=artifact.expires_at,
        revision_id=artifact.revision_id,
    )


@router.get(
    "/share-artifacts/{share_token}",
    response_model=PublicShareArtifactResponse,
    responses={404: {}},
)
async def get_share_artifact(
    share_token: str, request: Request, response: Response
) -> PublicShareArtifactResponse | Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    artifact = await _share_service(request).preview(share_token)
    if artifact is None:
        unavailable = _problem(ShareArtifactUnavailable())
        unavailable.headers.update(response.headers)
        return unavailable
    return PublicShareArtifactResponse(
        format=artifact.format,
        safe_snapshot=SafeShareSnapshotResponse.model_validate(artifact.safe_snapshot),
        expires_at=artifact.expires_at,
    )


@router.delete(
    "/share-artifacts/{artifact_id}",
    status_code=204,
    responses={401: {}, 403: {}, 404: {}},
)
async def revoke_share_artifact(
    artifact_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        await _share_service(request).revoke(guest_id=guest.id, artifact_id=artifact_id)
    except (GuestDomainError, ShareDomainError) as error:
        return _problem(error)
    return Response(status_code=204)
