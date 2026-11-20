"""Hỏi Lá bằng lá số (AK2, 20.11.2026): month answers, the on-tap easier window, the month card.

- ``GET /month/status``: whether the feature can show (every sentence approved) and whether the
  typed-question path is on. No personal data.
- ``POST /month/answers``: a topic, or (when switched on) a typed question. The typed text goes
  through the crisis guard before anything else, is read into closed labels (topic, kind) in memory
  and dropped: never stored, logged, echoed or sent anywhere (retention: the request itself).
- ``GET /month/window?topic=``: the easier window. Only the "Xem lúc nào dễ hơn" tap calls it; the
  answer itself never carries a date.
- ``GET /month/overview``: the Khám phá card, no dates.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.crisis_guard import crisis_guard
from app.domains.birth.errors import BirthDomainError
from app.domains.content.copy_approval import approved_copy
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import (
    MONTH_QUESTION_CONSENT_VERSION as TYPED_CONSENT_VERSION,
)
from app.domains.guest.service import GuestSessionService
from app.domains.month_answer.answer import feature_ready
from app.domains.month_answer.facts import Topic
from app.domains.month_answer.question import (
    QUESTION_MAX_CHARS,
    QUESTION_MIN_CHARS,
    QuestionKind,
    read_question,
)
from app.domains.month_answer.saved import (
    PostgresSavedMonthAnswers,
    SavedMonthAnswer,
    SavedMonthAnswerLimit,
)
from app.domains.month_answer.service import (
    MonthAnswerService,
    MonthAnswerUnavailable,
    today_in_vietnam,
)
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
logger = logging.getLogger(__name__)

MONTH_CRISIS_COPY_ID = "crisis.self_harm.notice.month"
TYPED_CONSENT_COPY_ID = "consent.month.typed_question"
NEED_TOPIC_COPY_ID = "month.line.need_topic"
NO_STORE = {"Cache-Control": "no-store, max-age=0"}


class MonthConsent(BaseModel):
    version: str
    copy_id: str
    text: str


class MonthStatusResponse(BaseModel):
    available: bool
    typed_questions: bool
    month: str
    consent: MonthConsent | None = None


class MonthAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic | None = None
    question: str | None = Field(
        default=None, min_length=QUESTION_MIN_CHARS, max_length=QUESTION_MAX_CHARS
    )
    consent_version: str | None = Field(default=None, max_length=64)


class MonthBasis(BaseModel):
    line: str
    detail: str


class MonthAnswerView(BaseModel):
    month: str
    topic: Topic
    topic_label: str
    reframe: str | None
    theme: str
    act: str
    say: str
    basis: MonthBasis
    disclaimer: str
    answer_key: str


class MonthAnswerResponse(BaseModel):
    status: Literal["answered", "need_topic"]
    answer: MonthAnswerView | None = None
    need_topic: str | None = None


class MonthWindowResponse(BaseModel):
    found: bool
    start: str | None = None
    end: str | None = None
    basis: str | None = None
    line: str | None = None


class MonthSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    answer_key: str = Field(min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$")


class SavedMonthAnswerView(BaseModel):
    id: UUID
    month: str
    saved_at: datetime
    answer: MonthAnswerView


class SavedMonthAnswerList(BaseModel):
    items: tuple[SavedMonthAnswerView, ...]


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


def _saved(request: Request) -> PostgresSavedMonthAnswers | None:
    return cast(
        PostgresSavedMonthAnswers | None,
        getattr(request.app.state, "saved_month_answers", None),
    )


def _saved_view(item: SavedMonthAnswer) -> SavedMonthAnswerView:
    content = item.content
    basis = content.get("basis")
    basis_map = cast(dict[str, str], basis) if isinstance(basis, dict) else {}
    return SavedMonthAnswerView(
        id=item.id,
        month=item.month,
        saved_at=item.saved_at,
        answer=MonthAnswerView(
            month=item.month,
            topic=Topic(item.topic),
            topic_label=str(content.get("topic_label", "")),
            reframe=cast(str | None, content.get("reframe")),
            theme=str(content.get("theme", "")),
            act=str(content.get("act", "")),
            say=str(content.get("say", "")),
            basis=MonthBasis(
                line=str(basis_map.get("line", "")), detail=str(basis_map.get("detail", ""))
            ),
            disclaimer=str(content.get("disclaimer", "")),
            answer_key="",
        ),
    )


async def _mutation_guest(request: Request, csrf_token: str | None):  # type: ignore[no-untyped-def]
    require_trusted_origin(request, trusted_origins(request))
    return await _guests(request).verify_csrf(
        request.cookies.get(request.app.state.settings.guest_cookie_name), csrf_token
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


def typed_questions_on(request: Request) -> bool:
    """The typed path needs the switch and the owner-approved consent and crisis sentences."""

    settings = request.app.state.settings
    return bool(
        getattr(settings, "month_typed_questions_enabled", False)
        and approved_copy(TYPED_CONSENT_COPY_ID) is not None
        and approved_copy(MONTH_CRISIS_COPY_ID) is not None
    )


@router.get("/month/status", response_model=MonthStatusResponse)
async def month_status(request: Request, response: Response) -> MonthStatusResponse:
    response.headers.update(NO_STORE)
    typed = typed_questions_on(request)
    consent_text = approved_copy(TYPED_CONSENT_COPY_ID) if typed else None
    return MonthStatusResponse(
        available=feature_ready() and getattr(request.app.state, "astro_engine", None) is not None,
        typed_questions=typed,
        month=today_in_vietnam().strftime("%Y-%m"),
        consent=(
            MonthConsent(
                version=TYPED_CONSENT_VERSION, copy_id=TYPED_CONSENT_COPY_ID, text=consent_text
            )
            if consent_text is not None
            else None
        ),
    )


@router.post(
    "/month/answers",
    response_model=MonthAnswerResponse,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 422: {}, 428: {}, 503: {}},
    dependencies=[Depends(crisis_guard("question", notice_id=MONTH_CRISIS_COPY_ID))],
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

    topic = body.topic
    kind = QuestionKind.HOW
    if body.question is not None:
        if not typed_questions_on(request):
            return _problem(403, "MONTH_TYPED_QUESTIONS_OFF")
        if body.consent_version != TYPED_CONSENT_VERSION:
            return _problem(428, "MONTH_TYPED_CONSENT_REQUIRED")
        try:
            # Decree 356 Art. 6(1)-(2): keep a verifiable record before the text is read.
            await _guests(request).accept_month_question_consent(
                guest.id, version=TYPED_CONSENT_VERSION
            )
        except GuestDomainError as error:
            return _domain_problem(error)
        labels = read_question(body.question)
        kind = labels.kind
        topic = topic or labels.topic
        if topic is None:
            need = approved_copy(NEED_TOPIC_COPY_ID)
            if need is None:
                return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
            return MonthAnswerResponse(status="need_topic", need_topic=need)
    if topic is None:
        return _problem(422, "MONTH_TOPIC_REQUIRED")
    try:
        answer = await _service(request).answer(guest.id, topic, kind)
    except (BirthDomainError, GuestDomainError) as error:
        return _domain_problem(error)
    except MonthAnswerUnavailable:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    except Exception as error:
        # The exception type only: never the message or the body (it may hold the typed question).
        logger.error("month_answer_failed", extra={"error_type": type(error).__name__})
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    return MonthAnswerResponse(
        status="answered",
        answer=MonthAnswerView(
            month=answer.month,
            topic=answer.topic,
            topic_label=answer.topic_label,
            reframe=answer.reframe,
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


@router.post(
    "/month/saved",
    response_model=SavedMonthAnswerView,
    status_code=201,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 429: {}, 503: {}},
)
async def save_month_answer(
    body: MonthSaveRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> SavedMonthAnswerView | Response:
    """Explicit "Lưu" only. The answer is recomputed server-side; the client sends no text."""

    response.headers.update(NO_STORE)
    repository = _saved(request)
    if repository is None:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    try:
        guest = await _mutation_guest(request, csrf_token)
        answer = await _service(request).answer_for_key(guest.id, body.topic, body.answer_key)
        if answer is None:
            return _problem(409, "MONTH_ANSWER_CHANGED")
        saved = await repository.save(guest.id, answer)
    except (BirthDomainError, GuestDomainError) as error:
        return _domain_problem(error)
    except MonthAnswerUnavailable:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    except SavedMonthAnswerLimit:
        return _problem(429, "MONTH_SAVED_LIMIT")
    return _saved_view(saved)


@router.get(
    "/month/saved",
    response_model=SavedMonthAnswerList,
    responses={401: {}, 503: {}},
)
async def list_saved_month_answers(
    request: Request, response: Response
) -> SavedMonthAnswerList | Response:
    response.headers.update(NO_STORE)
    repository = _saved(request)
    if repository is None:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    try:
        guest = await _guests(request).resume(
            request.cookies.get(request.app.state.settings.guest_cookie_name)
        )
    except GuestDomainError as error:
        return _domain_problem(error)
    items = await repository.list_for_guest(guest.id)
    return SavedMonthAnswerList(items=tuple(_saved_view(item) for item in items))


@router.delete(
    "/month/saved/{saved_id}",
    status_code=204,
    responses={401: {}, 403: {}, 404: {}, 503: {}},
)
async def delete_saved_month_answer(
    saved_id: UUID,
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    repository = _saved(request)
    if repository is None:
        return _problem(503, "MONTH_ANSWER_UNAVAILABLE")
    try:
        guest = await _mutation_guest(request, csrf_token)
    except GuestDomainError as error:
        return _domain_problem(error)
    if not await repository.delete(guest.id, saved_id):
        return _problem(404, "MONTH_SAVED_NOT_FOUND")
    return Response(status_code=204, headers=NO_STORE)


@router.delete(
    "/month/consent",
    status_code=204,
    responses={401: {}, 403: {}},
)
async def withdraw_month_question_consent(
    request: Request,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    """Withdraw consent to typed questions; nothing typed was ever stored, so nothing else goes."""

    try:
        guest = await _mutation_guest(request, csrf_token)
        await _guests(request).revoke_month_question_consent(guest.id)
    except GuestDomainError as error:
        return _domain_problem(error)
    return Response(status_code=204, headers=NO_STORE)
