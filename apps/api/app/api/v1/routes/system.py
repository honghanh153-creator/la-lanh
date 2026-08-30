from collections.abc import Awaitable, Callable
from typing import Literal, cast

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import Settings

router = APIRouter()

ReadinessProbe = Callable[[], Awaitable[bool]]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    api_version: str
    schema_version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]


@router.get("/health", operation_id="getHealth", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = cast(Settings, request.app.state.settings)
    return HealthResponse(
        service=settings.service_name,
        api_version=settings.api_version,
        schema_version=settings.schema_version,
    )


@router.get(
    "/ready",
    operation_id="getReadiness",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(request: Request) -> ReadinessResponse | JSONResponse:
    probe = cast(ReadinessProbe, request.app.state.readiness_probe)
    try:
        ready = await probe()
    except Exception:  # Readiness must fail closed without exposing connection details.
        ready = False

    payload = ReadinessResponse(status="ready" if ready else "not_ready")
    if not ready:
        return JSONResponse(
            content=payload.model_dump(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return payload
