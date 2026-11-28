"""Hỏi Lá bằng lá số (AK2, 20.11.2026): month answers, the on-tap easier window, the month card.

- ``GET /month/status``: whether the feature can show (every sentence approved) and the preset
  questions. No personal data.
- ``POST /month/answers``: a topic, optionally one of its preset questions. There is no typed
  question (owner chose AS1 on 21.11.2026), so the request holds closed values only.
- ``GET /month/window?topic=``: the easier window. Only the "Xem lúc nào dễ hơn" tap calls it; the
  answer itself never carries a date.
- ``GET /month/overview``: the Khám phá card, no dates.
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.domains.birth.errors import BirthDomainError
from app.domains.content.copy_approval import approved_copy
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.month_answer.answer import feature_ready
from app.domains.month_answer.facts import Topic
from app.domains.month_answer.presets import PresetId, ask_id, preset_topic
from app.domains.month_answer.service import (
    MonthAnswerService,
    MonthAnswerUnavailable,
    today_in_vietnam,
)
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
logger = logging.getLogger(__name__)

NO_STORE = {"Cache-Control": "no-store, max-age=0"}


class MonthPresetView(BaseModel):
    id: PresetId
    topic: Topic
    text: str


class MonthStatusResponse(BaseModel):
    available: bool
    month: str
    presets: tuple[MonthPresetView, ...] = ()


class MonthAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    preset: PresetId | None = None


class MonthBasis(BaseModel):
    line: str
    detail: str


class MonthAnswerView(BaseModel):
    month: str
    topic: Topic
    topic_label: str
    preset: PresetId | None
    question: str | None
    tip: str | None
    theme: str
    act: str
    say: str
    basis: MonthBasis
    disclaimer: str
    answer_key: str


class MonthAnswerResponse(BaseModel):
    status: Literal["answered"]
    answer: MonthAnswerView


class MonthWindowResponse(BaseModel):
    found: bool
    start: str | None = None
    end: str | None = None
    basis: str | None = None
    line: str | None = None


class MonthOverviewItem(BaseModel):
    area: Literal["work", "love", "money", "self"]
    label: str
    line: str
    try_text: str


class MonthOverviewResponse(BaseModel):
    month: str
    items: tuple[MonthOverviewItem, ...]


def _guests(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _service(request: Request) -> MonthAnswerService:
    return MonthAnswerService(
        engine=getattr(request.app.state, "astro_engine", None),
        birth_service=getattr(request.app.state, "birth_chart_service", None),
        daily_service=request.app.state.daily_note_service,
    )


def _problem(status: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": "about:blank",
            "title": "Month answer request was rejected",
            "status": status,
            "code": code,
        },
        media_type="application/problem+json",
        headers=NO_STORE,
    )


def _domain_problem(error: BirthDomainError | GuestDomainError) -> JSONResponse:
    return _problem(error.status_code, error.code)


def _presets() -> tuple[MonthPresetView, ...]:
    views: list[MonthPresetView] = []
    for preset in PresetId:
        text = approved_copy(ask_id(preset))
        if text is None:
            return ()
        views.append(MonthPresetView(id=preset, topic=preset_topic(preset), text=text))
    return tuple(views)


@router.get("/month/status", response_model=MonthStatusResponse)
async def month_status(request: Request, response: Response) -> MonthStatusResponse:
    response.headers.update(NO_STORE)
    available = feature_ready() and getattr(request.app.state, "astro_engine", None) is not None
    return MonthStatusResponse(
        available=available,
        month=today_in_vietnam().strftime("%Y-%m"),
        presets=_presets() if available else (),
    )


@router.post(
    "/month/answers",
    response_model=MonthAnswerResponse,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 422: {}, 503: {}},
)
async def month_answer(
    body: MonthAnswerRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> MonthAnswerResponse | Response:
    response.headers.update(NO_STORE)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guests(request).verify_csrf(
            request.cookies.get(request.app.state.settings.guest_cookie_name), csrf_token
        )
    except GuestDomainError as error:
        return _domain_problem(error)

    if body.preset is not None and preset_topic(body.preset) is not body.topic:
        return _problem(422, "MONTH_PRESET_TOPIC_MISMATCH")
    try:
        answer = await _service(request).answer(guest.id, body.topic, body.preset)
    except (BirthDomainError, GuestDomainError) as error:
        return _domain_problem(error)
    except MonthAnswerUnavailable:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    except Exception as error:
        # The exception type only: never the message (it could carry chart details).
        logger.error("month_answer_failed", extra={"error_type": type(error).__name__})
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    return MonthAnswerResponse(
        status="answered",
        answer=MonthAnswerView(
            month=answer.month,
            topic=answer.topic,
            topic_label=answer.topic_label,
            preset=answer.preset,
            question=answer.question,
            tip=answer.tip,
            theme=answer.theme,
            act=answer.act,
            say=answer.say,
            basis=MonthBasis(line=answer.basis.line, detail=answer.basis.detail),
            disclaimer=answer.disclaimer,
            answer_key=answer.answer_key,
        ),
    )


@router.get(
    "/month/window",
    response_model=MonthWindowResponse,
    responses={401: {}, 404: {}, 409: {}, 503: {}},
)
async def month_window(
    request: Request,
    response: Response,
    topic: Annotated[Topic, Query()],
) -> MonthWindowResponse | Response:
    response.headers.update(NO_STORE)
    try:
        guest = await _guests(request).resume(
            request.cookies.get(request.app.state.settings.guest_cookie_name)
        )
        found = await _service(request).window(guest.id, topic)
    except (BirthDomainError, GuestDomainError) as error:
        return _domain_problem(error)
    except MonthAnswerUnavailable:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    if found is None:
        return MonthWindowResponse(found=False)
    return MonthWindowResponse(
        found=True, start=found.start, end=found.end, basis=found.basis, line=found.line
    )


@router.get(
    "/month/overview",
    response_model=MonthOverviewResponse,
    responses={401: {}, 404: {}, 409: {}, 503: {}},
)
async def month_overview(request: Request, response: Response) -> MonthOverviewResponse | Response:
    response.headers.update(NO_STORE)
    try:
        guest = await _guests(request).resume(
            request.cookies.get(request.app.state.settings.guest_cookie_name)
        )
        month, items = await _service(request).overview(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _domain_problem(error)
    except MonthAnswerUnavailable:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    return MonthOverviewResponse(
        month=month,
        items=tuple(
            MonthOverviewItem(
                area=cast(Literal["work", "love", "money", "self"], item.area),
                label=item.label,
                line=item.line,
                try_text=item.try_,
            )
            for item in items
        ),
    )
