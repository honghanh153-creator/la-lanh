import logging
from datetime import date, datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domains.astro.models import TransitPhase
from app.domains.birth.errors import BirthDomainError
from app.domains.daily.models import (
    FallbackReason,
    PersonaLabel,
    PersonaMode,
    SourceLevel,
)
from app.domains.daily.service import DailyNoteService
from app.domains.experiments.errors import ExperimentDomainError
from app.domains.experiments.models import DailyExperiment, ExperimentOutcome, ExperimentState
from app.domains.experiments.service import ExperimentService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.domains.mood.models import MoodValue
from app.domains.mood.service import MoodService
from app.domains.readings.application import (
    ReadingActivationConflict,
    ReadingApplicationError,
    ReadingApplicationService,
)
from app.domains.readings.models import BackgroundLens, ReadingProjection, ReadingPurpose
from app.domains.resonance.errors import ResonanceDomainError
from app.domains.resonance.models import ResonanceChoice
from app.domains.resonance.service import ResonanceService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()
logger = logging.getLogger(__name__)


class AuraAwakeningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: str
    summary: str
    factors: list[str]
    precision_label: str
    scoring_version: str
    confidence: str


class SkyChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    summary: str
    phase: TransitPhase
    phase_label: str
    signal_label: str
    orb: float
    observed_at: datetime
    orb_policy_version: str
    ranking_version: str
    disclaimer: str


class DailyNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    note_date: date
    title: str
    body: str
    full_body: str
    context_label: str
    content_version: str
    persona_mode: PersonaMode
    persona_label: PersonaLabel
    persona_version: str
    source_level: SourceLevel
    astrology_source_version: str
    fallback_used: bool
    fallback_reason: FallbackReason | None
    created_at: datetime
    awakening: AuraAwakeningResponse | None = None
    sky_chapter: SkyChapterResponse | None = None
    reading_projection: ReadingProjection | None = None


class ActivateReadingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision_id: UUID


class AcknowledgeAuraTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class ContextProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    background_lens: BackgroundLens


class MoodRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mood: MoodValue


class MoodResponse(BaseModel):
    id: UUID
    daily_note_id: UUID
    mood: MoodValue
    checked_in_at: datetime


class ResonanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choice: ResonanceChoice
    consent_version: str = Field(min_length=1, max_length=64)
    revision_id: UUID | None = None
    background_lens: BackgroundLens | None = None


class ResonanceResponse(BaseModel):
    choice: ResonanceChoice
    background_lens: BackgroundLens | None
    created_at: datetime


class ResonanceStatusResponse(BaseModel):
    consented: bool
    feedback_count: int
    last_choice: ResonanceChoice | None


class ResonanceClearRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoke_consent: bool = False


class ExperimentChooseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: UUID
    background_lens: BackgroundLens
    action_key: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    consent_version: str = Field(min_length=1, max_length=64)
    expected_experiment_id: UUID | None = None
    expected_version: int | None = Field(default=None, ge=1)


class ExperimentMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: UUID
    expected_version: int = Field(ge=1)


class ExperimentOutcomeRequest(ExperimentMutationRequest):
    outcome: ExperimentOutcome


class ExperimentResponse(BaseModel):
    id: UUID
    version: int
    daily_note_id: UUID
    revision_id: UUID
    state: ExperimentState
    background_lens: BackgroundLens
    action_key: str
    action: str
    observation: str
    permission: str
    outcome: ExperimentOutcome | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    reflected_at: datetime | None


def _problem(
    error: BirthDomainError | ExperimentDomainError | GuestDomainError | ResonanceDomainError,
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Daily note request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


def _guest_service(request: Request) -> GuestSessionService:
    return cast(GuestSessionService, request.app.state.guest_session_service)


def _daily_service(request: Request) -> DailyNoteService:
    return cast(DailyNoteService, request.app.state.daily_note_service)


def _mood_service(request: Request) -> MoodService:
    return cast(MoodService, request.app.state.mood_service)


def _reading_service(request: Request) -> ReadingApplicationService | None:
    return cast(
        ReadingApplicationService | None,
        getattr(request.app.state, "reading_application_service", None),
    )


def _resonance_service(request: Request) -> ResonanceService:
    return cast(ResonanceService, request.app.state.resonance_service)


def _experiment_service(request: Request) -> ExperimentService:
    return cast(ExperimentService, request.app.state.experiment_service)


def _experiment_response(record: DailyExperiment) -> ExperimentResponse:
    return ExperimentResponse(
        id=record.id,
        version=record.version,
        daily_note_id=record.daily_note_id,
        revision_id=record.revision_id,
        state=record.state,
        background_lens=record.background_lens,
        action_key=record.action_key,
        action=record.projection.action,
        observation=record.projection.observation,
        permission=record.projection.permission,
        outcome=record.outcome,
        created_at=record.created_at,
        updated_at=record.updated_at,
        expires_at=record.expires_at,
        reflected_at=record.reflected_at,
    )


def _reading_problem(status: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": "about:blank",
            "title": "Reading update could not be completed",
            "status": status,
            "code": code,
        },
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"


@router.get("/daily-note", response_model=DailyNoteResponse, responses={401: {}, 404: {}})
async def get_daily_note(
    request: Request,
    response: Response,
    guest_token: Annotated[str | None, Cookie(alias="la_lanh_guest")] = None,
) -> DailyNoteResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name, guest_token)
    try:
        guest = await _guest_service(request).resume(token)
        note = await _daily_service(request).today(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    payload = DailyNoteResponse.model_validate(note)
    reading_service = _reading_service(request)
    if reading_service is None:
        return payload
    try:
        snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
        projection = await reading_service.project(
            guest_id=guest.id,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
        )
    except Exception:
        logger.exception(
            "Private Daily reading projection failed; returning legacy note",
            extra={"surface": "daily_note"},
        )
        return payload
    return payload.model_copy(update={"reading_projection": projection})


@router.post(
    "/daily-note/context",
    response_model=ReadingProjection,
    responses={401: {}, 403: {}, 404: {}, 422: {}, 503: {}},
)
async def project_daily_note_context(
    body: ContextProjectionRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ReadingProjection | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    reading_service = _reading_service(request)
    if reading_service is None:
        return _reading_problem(503, "READING_UNAVAILABLE")
    try:
        return await reading_service.project(
            guest_id=guest.id,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
            background_lens=body.background_lens,
        )
    except ReadingApplicationError:
        logger.exception(
            "Private contextual Daily reading projection failed",
            extra={"surface": "daily_note_context"},
        )
        return _reading_problem(503, "READING_UNAVAILABLE")


@router.put(
    "/reading-projections/{scope_key}/activate",
    response_model=ReadingProjection,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 503: {}},
)
async def activate_reading_projection(
    scope_key: Annotated[str, Field(min_length=64, max_length=64)],
    body: ActivateReadingRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ReadingProjection | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    reading_service = _reading_service(request)
    if reading_service is None:
        return _reading_problem(503, "READING_UNAVAILABLE")
    try:
        return await reading_service.activate(
            guest_id=guest.id,
            profile_id=snapshot.profile_id,
            scope_key=scope_key,
            expected_revision_id=body.expected_revision_id,
            expected_chart_snapshot_id=snapshot.id,
        )
    except ReadingActivationConflict:
        return _reading_problem(409, "READING_UPDATE_CONFLICT")
    except ReadingApplicationError:
        logger.exception(
            "Private reading activation failed",
            extra={"surface": "reading_activation"},
        )
        return _reading_problem(503, "READING_UNAVAILABLE")


@router.put(
    "/reading-projections/{scope_key}/aura-transition/acknowledge",
    response_model=ReadingProjection,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 422: {}, 503: {}},
)
async def acknowledge_aura_transition(
    scope_key: Annotated[str, Field(min_length=64, max_length=64)],
    body: AcknowledgeAuraTransitionRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ReadingProjection | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        snapshot = await _daily_service(request).current_birth_snapshot(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    reading_service = _reading_service(request)
    if reading_service is None:
        return _reading_problem(503, "READING_UNAVAILABLE")
    try:
        return await reading_service.acknowledge_aura_transition(
            guest_id=guest.id,
            profile_id=snapshot.profile_id,
            scope_key=scope_key,
            transition_id=body.transition_id,
        )
    except ReadingActivationConflict:
        return _reading_problem(409, "AURA_TRANSITION_CONFLICT")
    except ReadingApplicationError:
        logger.exception(
            "Private Aura transition acknowledgement failed",
            extra={"surface": "aura_transition_acknowledgement"},
        )
        return _reading_problem(503, "READING_UNAVAILABLE")


@router.put(
    "/daily-note/{daily_note_id}/mood",
    response_model=MoodResponse,
    responses={401: {}, 403: {}, 404: {}, 422: {}},
)
async def check_in_mood(
    daily_note_id: UUID,
    body: MoodRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> MoodResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        mood = await _mood_service(request).check_in(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            mood=body.mood,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return MoodResponse(
        id=mood.id,
        daily_note_id=mood.daily_note_id,
        mood=mood.mood,
        checked_in_at=mood.checked_in_at,
    )


@router.get(
    "/daily-note/{daily_note_id}/mood",
    response_model=MoodResponse | None,
    responses={401: {}, 404: {}},
)
async def get_current_mood(
    daily_note_id: UUID,
    request: Request,
    response: Response,
) -> MoodResponse | Response | None:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        mood = await _mood_service(request).current(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    if mood is None:
        return None
    return MoodResponse(
        id=mood.id,
        daily_note_id=mood.daily_note_id,
        mood=mood.mood,
        checked_in_at=mood.checked_in_at,
    )


@router.get(
    "/daily-note/experiment",
    response_model=ExperimentResponse | None,
    responses={401: {}},
)
async def get_current_experiment(
    request: Request,
    response: Response,
) -> ExperimentResponse | Response | None:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        record = await _experiment_service(request).current(guest.id)
    except (BirthDomainError, GuestDomainError, ExperimentDomainError) as error:
        return _problem(error)
    return _experiment_response(record) if record is not None else None


@router.put(
    "/daily-note/{daily_note_id}/experiment",
    response_model=ExperimentResponse,
    responses={401: {}, 403: {}, 404: {}, 409: {}, 422: {}},
)
async def choose_experiment(
    daily_note_id: UUID,
    body: ExperimentChooseRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ExperimentResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        record = await _experiment_service(request).choose(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            revision_id=body.revision_id,
            background_lens=body.background_lens,
            action_key=body.action_key,
            consent_version=body.consent_version,
            expected_experiment_id=body.expected_experiment_id,
            expected_version=body.expected_version,
        )
    except (BirthDomainError, GuestDomainError, ExperimentDomainError) as error:
        return _problem(error)
    return _experiment_response(record)


@router.delete(
    "/daily-note/experiment",
    status_code=204,
    responses={401: {}, 403: {}, 409: {}, 422: {}},
)
async def undo_experiment(
    body: ExperimentMutationRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        await _experiment_service(request).undo(
            guest.id,
            experiment_id=body.experiment_id,
            expected_version=body.expected_version,
        )
    except (BirthDomainError, GuestDomainError, ExperimentDomainError) as error:
        return _problem(error)
    return Response(status_code=204)


@router.post(
    "/daily-note/experiment/outcome",
    response_model=ExperimentResponse,
    responses={401: {}, 403: {}, 409: {}, 422: {}},
)
async def reflect_on_experiment(
    body: ExperimentOutcomeRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ExperimentResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        record = await _experiment_service(request).reflect(
            guest.id,
            experiment_id=body.experiment_id,
            expected_version=body.expected_version,
            outcome=body.outcome,
        )
    except (BirthDomainError, GuestDomainError, ExperimentDomainError) as error:
        return _problem(error)
    return _experiment_response(record)


@router.get(
    "/daily-note/resonance",
    response_model=ResonanceStatusResponse,
    responses={401: {}},
)
async def get_resonance_status(
    request: Request, response: Response
) -> ResonanceStatusResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        guest = await _guest_service(request).resume(token)
        status = await _resonance_service(request).status(guest.id)
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return ResonanceStatusResponse(
        consented=status.consented,
        feedback_count=status.feedback_count,
        last_choice=status.last_choice,
    )


@router.put(
    "/daily-note/{daily_note_id}/resonance",
    response_model=ResonanceResponse,
    responses={401: {}, 403: {}, 404: {}, 422: {}},
)
async def record_resonance(
    daily_note_id: UUID,
    body: ResonanceRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ResonanceResponse | Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        feedback = await _resonance_service(request).record(
            guest_id=guest.id,
            daily_note_id=daily_note_id,
            revision_id=body.revision_id,
            choice=body.choice,
            background_lens=body.background_lens,
            consent_version=body.consent_version,
        )
    except (BirthDomainError, GuestDomainError, ResonanceDomainError) as error:
        return _problem(error)
    return ResonanceResponse(
        choice=feedback.choice,
        background_lens=feedback.background_lens,
        created_at=feedback.created_at,
    )


@router.delete(
    "/daily-note/resonance",
    status_code=204,
    responses={401: {}, 403: {}},
)
async def clear_resonance(
    body: ResonanceClearRequest,
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    _no_store(response)
    settings = request.app.state.settings
    token = request.cookies.get(settings.guest_cookie_name)
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await _guest_service(request).verify_csrf(token, csrf_token)
        await _resonance_service(request).clear(
            guest.id,
            revoke_consent=body.revoke_consent,
        )
    except (BirthDomainError, GuestDomainError) as error:
        return _problem(error)
    return Response(status_code=204)
