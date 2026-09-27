import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings
from app.db.session import Database
from app.domains.astro import NatalChartEngine
from app.domains.astro.ffi.swisseph import SwissEphemerisError
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.repository import BirthRepository
from app.domains.birth.service import BirthChartService
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.service import DailyNoteService
from app.domains.experiments.postgres import PostgresExperimentRepository
from app.domains.experiments.service import ExperimentService
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.repository import GuestRepository
from app.domains.guest.service import GuestSessionService
from app.domains.identity.service import OwnerIdentityService
from app.domains.la_chung.service import LaChungService
from app.domains.matching.postgres import PostgresMatchingRepository
from app.domains.matching.service import MatchingService
from app.domains.mood.postgres import PostgresMoodRepository
from app.domains.mood.service import MoodService
from app.domains.radar.service import RadarService
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.repository import ReadingRepository
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.domains.resonance.service import ResonanceService
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.domains.saved.service import SavedNoteService
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.service import ShareArtifactService
from app.domains.tarot.service import TarotSessionService
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)
from app.infrastructure.generation.openai import OPENAI_PROMPT_VERSION
from app.middleware.admission import AdmissionControlMiddleware
from app.middleware.correlation import CorrelationIdMiddleware
from app.observability.metrics import MetricsMiddleware, metrics_response


async def _runtime_ready(database: Database, engine: NatalChartEngine | None) -> bool:
    if engine is None or not await database.ping():
        return False
    try:
        await asyncio.to_thread(engine.calculate_date_only_sun, date(2000, 1, 1))
    except SwissEphemerisError:
        return False
    return True


def create_app(
    settings: Settings | None = None,
    *,
    guest_repository: GuestRepository | None = None,
    birth_repository: BirthRepository | None = None,
    reading_repository: ReadingRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(str(resolved_settings.database_url))
        await database.initialize()
        app.state.database = database
        engine: NatalChartEngine | None
        try:
            engine = NatalChartEngine()
            app.state.astro_engine = engine
            app.state.astro_engine_error = None
        except SwissEphemerisError as error:
            engine = None
            app.state.astro_engine = None
            app.state.astro_engine_error = str(error)

        async def readiness_probe() -> bool:
            return await _runtime_ready(database, engine)

        app.state.readiness_probe = readiness_probe
        repository = guest_repository or PostgresGuestRepository(database.sessions)
        envelope = AesGcmEnvelopeCipher(
            StaticDataKeyProvider(
                decode_key(
                    resolved_settings.guest_encryption_key.get_secret_value(),
                    expected_bytes=32,
                )
            )
        )
        credential_hasher = SecretHasher(
            decode_key(resolved_settings.guest_hash_key.get_secret_value())
        )
        app.state.guest_session_service = GuestSessionService(
            repository,
            credential_hasher,
            envelope,
            consent_version=resolved_settings.consent_version,
            consent_purpose=resolved_settings.consent_purpose,
            additional_consents=frozenset({("tarot-reflection-v1", "tarot_reflection")}),
            ttl=timedelta(days=resolved_settings.guest_ttl_days),
            replay_window=timedelta(minutes=resolved_settings.guest_replay_minutes),
        )
        app.state.owner_identity_service = OwnerIdentityService(
            database.sessions,
            credential_hasher,
            ttl=timedelta(days=resolved_settings.owner_ttl_days),
        )
        app.state.tarot_session_service = TarotSessionService(
            database.sessions, envelope, credential_hasher
        )
        app.state.la_chung_service = LaChungService(
            database.sessions,
            credential_hasher,
            envelope,
        )
        birth_repo = birth_repository or PostgresBirthRepository(database.sessions, envelope)
        app.state.birth_chart_service = (
            BirthChartService(
                birth_repo,
                engine,
                envelope,
                credential_hasher,
            )
            if engine is not None
            else None
        )
        app.state.matching_service = (
            MatchingService(
                PostgresMatchingRepository(database.sessions, envelope),
                app.state.birth_chart_service,
            )
            if app.state.birth_chart_service is not None
            else None
        )
        app.state.radar_service = (
            RadarService(
                database.sessions,
                credential_hasher,
                envelope,
                app.state.birth_chart_service,
                engine,
            )
            if app.state.birth_chart_service is not None and engine is not None
            else None
        )
        app.state.reading_application_service = None
        if engine is not None:
            daily_service = DailyNoteService(
                PostgresDailyNoteRepository(database.sessions, envelope), birth_repo, engine
            )
            app.state.daily_note_service = daily_service
            app.state.mood_service = MoodService(
                PostgresMoodRepository(database.sessions), daily_service
            )
            app.state.resonance_service = ResonanceService(
                PostgresResonanceRepository(database.sessions, envelope)
            )
            app.state.experiment_service = ExperimentService(
                PostgresExperimentRepository(database.sessions, envelope)
            )
            app.state.saved_note_service = SavedNoteService(
                PostgresSavedNoteRepository(database.sessions, envelope),
                daily_service,
            )
            app.state.share_artifact_service = ShareArtifactService(
                PostgresShareArtifactRepository(database.sessions, envelope),
                daily_service,
            )
            if birth_repository is None or reading_repository is not None:
                app.state.reading_application_service = ReadingApplicationService(
                    reading_repository or PostgresReadingRepository(database.sessions, envelope),
                    engine,
                    generation_enabled=resolved_settings.generation_enabled,
                    generation_provider=resolved_settings.generation_provider,
                    generation_model=resolved_settings.generation_openai_model,
                    generation_prompt_version=OPENAI_PROMPT_VERSION,
                    generation_max_attempts=resolved_settings.generation_max_attempts,
                )
        try:
            yield
        finally:
            await database.dispose()

    application = FastAPI(
        title="Lá Lành API",
        summary="Versioned product API for Lá Lành.",
        version=resolved_settings.schema_version,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings

    @application.middleware("http")
    async def private_response_cache_policy(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        version_prefix = f"/{resolved_settings.api_version}"
        if request.url.path.startswith(
            (
                f"{version_prefix}/daily-note",
                f"{version_prefix}/reading-projections",
                f"{version_prefix}/matching",
                f"{version_prefix}/radar",
                f"{version_prefix}/public/radar",
                f"{version_prefix}/tarot",
            )
        ):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(MetricsMiddleware)
    application.add_middleware(AdmissionControlMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in resolved_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=[
            "Content-Type",
            "X-CSRF-Token",
            "X-La-Lanh-Client",
            "X-Request-ID",
        ],
    )
    application.include_router(v1_router, prefix=f"/{resolved_settings.api_version}")
    application.add_api_route(
        "/metrics",
        metrics_response,
        methods=["GET"],
        include_in_schema=False,
    )
    return application


app = create_app()
