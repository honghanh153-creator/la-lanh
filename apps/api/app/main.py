from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings
from app.db.session import Database
from app.domains.astro import NatalChartEngine
from app.domains.astro.ffi.swisseph import SwissEphemerisError
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.repository import BirthRepository
from app.domains.birth.service import BirthChartService
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.repository import GuestRepository
from app.domains.guest.service import GuestSessionService
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)
from app.middleware.correlation import CorrelationIdMiddleware
from app.observability.metrics import MetricsMiddleware, metrics_response


def create_app(
    settings: Settings | None = None,
    *,
    guest_repository: GuestRepository | None = None,
    birth_repository: BirthRepository | None = None,
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
            if app.state.astro_engine_error is not None:
                return False
            return await database.ping()

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
        app.state.guest_session_service = GuestSessionService(
            repository,
            SecretHasher(decode_key(resolved_settings.guest_hash_key.get_secret_value())),
            envelope,
            consent_version=resolved_settings.consent_version,
            consent_purpose=resolved_settings.consent_purpose,
        )
        app.state.birth_chart_service = (
            BirthChartService(
                birth_repository or PostgresBirthRepository(database.sessions),
                engine,
                envelope,
            )
            if engine is not None
            else None
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
    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(MetricsMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in resolved_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
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
