from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings
from app.db.session import Database
from app.middleware.correlation import CorrelationIdMiddleware
from app.observability.metrics import MetricsMiddleware, metrics_response


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(str(resolved_settings.database_url))
        app.state.database = database
        app.state.readiness_probe = database.ping
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
