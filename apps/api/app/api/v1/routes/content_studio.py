from __future__ import annotations

import hmac
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.domains.content.postgres import ContentPublishConflict, ContentRevisionConflict
from app.domains.content.service import ContentDraftRejected, ContentStudioService

router = APIRouter(prefix="/studio", include_in_schema=True)


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, Any]
    parent_revision_id: UUID | None = None
    reason: str = Field(min_length=3, max_length=240)


class PublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_generation: int = Field(ge=0)
    reason: str = Field(min_length=3, max_length=240)


def _headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store, max-age=0",
        "X-Robots-Tag": "noindex, nofollow, noarchive",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
    }


def _authorize(request: Request, authorization: str | None) -> None:
    settings = cast(Settings, request.app.state.settings)
    configured = settings.content_studio_api_token
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if configured is None or not hmac.compare_digest(configured.get_secret_value(), supplied):
        raise PermissionError


def _service(request: Request) -> ContentStudioService:
    return cast(ContentStudioService, request.app.state.content_studio_service)


def _problem(status_code: int, code: str, title: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"type": "about:blank", "title": title, "status": status_code, "code": code},
        media_type="application/problem+json",
        headers=_headers(),
    )


@router.get(
    "/workspace",
    operation_id="getContentStudioWorkspace",
    response_model=None,
)
async def workspace(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    try:
        _authorize(request, authorization)
    except PermissionError:
        return _problem(status.HTTP_401_UNAUTHORIZED, "STUDIO_UNAUTHORIZED", "Studio access denied")
    payload = await _service(request).workspace()
    return JSONResponse(
        content=_jsonable(payload),
        headers=_headers(),
    )


@router.post("/drafts", operation_id="createContentStudioDraft", response_model=None)
async def create_draft(
    body: DraftRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    try:
        _authorize(request, authorization)
    except PermissionError:
        return _problem(status.HTTP_401_UNAUTHORIZED, "STUDIO_UNAUTHORIZED", "Studio access denied")
    if not idempotency_key or len(idempotency_key) > 128:
        return _problem(
            status.HTTP_400_BAD_REQUEST, "IDEMPOTENCY_REQUIRED", "Idempotency-Key is required"
        )
    try:
        revision, receipt = await _service(request).create_draft(
            body.payload,
            parent_revision_id=body.parent_revision_id,
            request_key=idempotency_key,
            reason=body.reason,
        )
    except ContentDraftRejected as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_jsonable(
                {
                    "type": "about:blank",
                    "title": "Content gate rejected this draft",
                    "status": status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "code": "CONTENT_DRAFT_REJECTED",
                    "validation": error.receipt,
                }
            ),
            media_type="application/problem+json",
            headers=_headers(),
        )
    except (ContentRevisionConflict, IntegrityError):
        return _problem(
            status.HTTP_409_CONFLICT, "REVISION_CONFLICT", "Draft conflicts with stored content"
        )
    return JSONResponse(
        content=_jsonable({"revision": revision, "validation": receipt}),
        status_code=status.HTTP_201_CREATED,
        headers=_headers(),
    )


@router.post(
    "/revisions/{revision_id}/publish",
    operation_id="publishContentStudioRevision",
    response_model=None,
)
async def publish_revision(
    revision_id: UUID,
    body: PublishRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    try:
        _authorize(request, authorization)
    except PermissionError:
        return _problem(status.HTTP_401_UNAUTHORIZED, "STUDIO_UNAUTHORIZED", "Studio access denied")
    if not idempotency_key or len(idempotency_key) > 128:
        return _problem(
            status.HTTP_400_BAD_REQUEST, "IDEMPOTENCY_REQUIRED", "Idempotency-Key is required"
        )
    try:
        revision, channel = await _service(request).publish(
            revision_id,
            expected_generation=body.expected_generation,
            request_key=idempotency_key,
            reason=body.reason,
        )
    except (
        ContentPublishConflict,
        ContentRevisionConflict,
        IntegrityError,
        LookupError,
        ValueError,
    ):
        return _problem(
            status.HTTP_409_CONFLICT, "PUBLISH_CONFLICT", "Refresh and validate before publishing"
        )
    return JSONResponse(
        content=_jsonable({"revision": revision, "channel": channel}), headers=_headers()
    )


@router.post(
    "/revisions/{revision_id}/rollback",
    operation_id="rollbackContentStudioRevision",
    response_model=None,
)
async def rollback_revision(
    revision_id: UUID,
    body: PublishRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    try:
        _authorize(request, authorization)
    except PermissionError:
        return _problem(status.HTTP_401_UNAUTHORIZED, "STUDIO_UNAUTHORIZED", "Studio access denied")
    if not idempotency_key or len(idempotency_key) > 128:
        return _problem(
            status.HTTP_400_BAD_REQUEST, "IDEMPOTENCY_REQUIRED", "Idempotency-Key is required"
        )
    try:
        revision, channel = await _service(request).publish(
            revision_id,
            expected_generation=body.expected_generation,
            request_key=idempotency_key,
            reason=body.reason,
            rollback=True,
        )
    except (
        ContentPublishConflict,
        ContentRevisionConflict,
        IntegrityError,
        LookupError,
        ValueError,
    ):
        return _problem(
            status.HTTP_409_CONFLICT, "ROLLBACK_CONFLICT", "Refresh and validate before rollback"
        )
    return JSONResponse(
        content=_jsonable({"revision": revision, "channel": channel}), headers=_headers()
    )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
