import asyncio
import logging
from datetime import UTC, datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.domains.astro.models import (
    Ayanamsa,
    BodyName,
    CalculationConfig,
    HouseSystem,
    NodeMode,
    Tradition,
    ZodiacSign,
)
from app.domains.birth.errors import BirthDomainError, ChartEngineUnavailable
from app.domains.birth.service import BirthChartService
from app.domains.daily.service import DailyNoteService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.models import InsightReading, ReadingProjection, ReadingPurpose
from app.domains.readings.service import InsightReadingService

router = APIRouter()
logger = logging.getLogger(__name__)


class InsightBodyProjection(BaseModel):
    body: BodyName
    sign: ZodiacSign
    degree_in_sign: float
    retrograde: bool


class InsightOverviewResponse(BaseModel):
    status: Literal["ready", "locked"]
    required_fields: tuple[str, ...] = ()
    reading: InsightReading | None = None
    bodies: tuple[InsightBodyProjection, ...] = ()
    houses_available: bool = False
    time_precision: str = "unknown"
    reading_projection: ReadingProjection | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class SupportedConfigResponse(BaseModel):
    recommended: tuple[CalculationConfig, ...]
    ayanamsas: tuple[Ayanamsa, ...]
    node_modes: tuple[NodeMode, ...]
    house_systems: tuple[HouseSystem, ...]


class CurrentSkyResponse(BaseModel):
    observed_at: datetime
    tradition: Tradition
    config_hash: str
    bodies: tuple[InsightBodyProjection, ...]
    note: str


def _guest_service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _birth_service(request: Request) -> BirthChartService:
    service = request.app.state.birth_chart_service
    if service is None:
        raise ChartEngineUnavailable
    return cast(BirthChartService, service)


def _daily_service(request: Request) -> DailyNoteService:
    return cast(DailyNoteService, request.app.state.daily_note_service)


def _reading_service(request: Request) -> ReadingApplicationService | None:
    return cast(
        ReadingApplicationService | None,
        getattr(request.app.state, "reading_application_service", None),
    )


def _problem(error: BirthDomainError | GuestDomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Insight request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
    )


def _reading_problem(status: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": "about:blank",
            "title": "Insight reading is temporarily unavailable",
            "status": status,
            "code": code,
        },
        media_type="application/problem+json",
    )


def _calculation_config(
    tradition: Tradition,
    ayanamsa: Ayanamsa | None,
    node_mode: NodeMode,
    house_system: HouseSystem | None,
) -> CalculationConfig:
    if tradition is Tradition.JYOTISH:
        return CalculationConfig(
            tradition=tradition,
            ayanamsa=ayanamsa or Ayanamsa.LAHIRI,
            node_mode=node_mode,
            house_system=house_system or HouseSystem.WHOLE_SIGN,
        )
    return CalculationConfig(
        node_mode=node_mode,
        house_system=house_system or HouseSystem.PLACIDUS,
    )


@router.get("/insights/configs", response_model=SupportedConfigResponse)
async def supported_configs() -> SupportedConfigResponse:
    return SupportedConfigResponse(
        recommended=(
            CalculationConfig.western_recommended(),
            CalculationConfig.jyotish_recommended(),
        ),
        ayanamsas=tuple(Ayanamsa),
        node_modes=tuple(NodeMode),
        house_systems=tuple(HouseSystem),
    )


@router.get(
    "/insights/overview",
    response_model=InsightOverviewResponse,
    responses={401: {}, 404: {}, 503: {}},
)
async def insight_overview(
    request: Request,
    tradition: Annotated[Tradition, Query()] = Tradition.WESTERN,
    ayanamsa: Annotated[Ayanamsa | None, Query()] = None,
    node_mode: Annotated[NodeMode, Query()] = NodeMode.TRUE,
    house_system: Annotated[HouseSystem | None, Query()] = None,
) -> InsightOverviewResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        config = _calculation_config(tradition, ayanamsa, node_mode, house_system)
        chart = await _birth_service(request).chart_for_config(guest.id, config)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    if chart is None:
        return InsightOverviewResponse(
            status="locked",
            required_fields=("birth_time", "birth_place"),
        )
    reading = InsightReadingService().overview(chart, observed_at=datetime.now(UTC))
    projection = None
    reading_service = _reading_service(request)
    if reading_service is not None:
        try:
            snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
            projection = await reading_service.project(
                guest_id=guest.id,
                snapshot=snapshot,
                chart=chart,
                purpose=ReadingPurpose.READING_DETAIL,
            )
        except Exception:
            logger.exception(
                "Private insight projection failed",
                extra={"surface": "insight_overview"},
            )
            return _reading_problem(503, "READING_UNAVAILABLE")
    return InsightOverviewResponse(
        status="ready",
        reading=reading,
        bodies=tuple(
            InsightBodyProjection(
                body=position.body,
                sign=position.sign,
                degree_in_sign=position.degree_in_sign,
                retrograde=position.retrograde,
            )
            for position in chart.bodies
        ),
        houses_available=chart.houses is not None,
        time_precision=chart.time_precision.value,
        reading_projection=projection,
    )


@router.get(
    "/insights/readings/{purpose}",
    response_model=ReadingProjection,
    responses={401: {}, 404: {}, 409: {}, 503: {}},
)
async def private_reading(
    purpose: Literal["aura", "reading_detail", "personalized_sky"],
    request: Request,
    tradition: Annotated[Tradition, Query()] = Tradition.WESTERN,
    ayanamsa: Annotated[Ayanamsa | None, Query()] = None,
    node_mode: Annotated[NodeMode, Query()] = NodeMode.TRUE,
    house_system: Annotated[HouseSystem | None, Query()] = None,
) -> ReadingProjection | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        config = _calculation_config(tradition, ayanamsa, node_mode, house_system)
        chart = await _birth_service(request).chart_for_config(guest.id, config)
        snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    if chart is None:
        return _reading_problem(409, "READING_INPUT_INCOMPLETE")
    reading_service = _reading_service(request)
    if reading_service is None:
        return _reading_problem(503, "READING_UNAVAILABLE")
    try:
        return await reading_service.project(
            guest_id=guest.id,
            snapshot=snapshot,
            chart=chart,
            purpose=ReadingPurpose(purpose),
        )
    except Exception:
        logger.exception(
            "Private insight reading failed",
            extra={"surface": purpose, "tradition": tradition.value},
        )
        return _reading_problem(503, "READING_UNAVAILABLE")


@router.get("/insights/current-sky", response_model=CurrentSkyResponse)
async def current_sky(
    request: Request,
    tradition: Annotated[Tradition, Query()] = Tradition.WESTERN,
) -> CurrentSkyResponse | Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        await _guest_service(request).resume(token)
    except GuestDomainError as error:
        return _problem(error)
    config = (
        CalculationConfig.jyotish_recommended()
        if tradition is Tradition.JYOTISH
        else CalculationConfig.western_recommended()
    )
    observed_at = datetime.now(UTC)
    snapshot = await asyncio.to_thread(
        request.app.state.astro_engine.calculate_daily_transit,
        observed_at.date(),
        config,
    )
    return CurrentSkyResponse(
        observed_at=observed_at,
        tradition=tradition,
        config_hash=snapshot.config_hash,
        bodies=tuple(
            InsightBodyProjection(
                body=item.body,
                sign=item.sign,
                degree_in_sign=item.degree_in_sign,
                retrograde=item.retrograde,
            )
            for item in snapshot.bodies[:7]
        ),
        note="Bầu trời được chụp tại 12:00 UTC cho nhịp đọc trong ngày.",
    )
