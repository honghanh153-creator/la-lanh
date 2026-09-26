from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.config import Settings
from app.main import create_app

_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "form-action 'self'; img-src 'self' data: blob:; font-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; "
        "manifest-src 'self'; worker-src 'self' blob:"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
    ),
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
}
_RESERVED_PREFIXES = ("/v1", "/metrics", "/docs", "/openapi.json")


def _default_web_dist() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    return repository_root / "apps" / "web" / "dist"


def _accepts_html(scope: Scope) -> bool:
    if scope.get("method") not in {"GET", "HEAD"}:
        return False
    return "text/html" in Headers(scope=scope).get("accept", "")


class SpaStaticFiles(StaticFiles):
    """Serve built assets while keeping API misses as real 404 responses."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        request_path = f"/{path.lstrip('/')}"
        if request_path.startswith(_RESERVED_PREFIXES):
            return PlainTextResponse("Not Found", status_code=404)
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as error:
            if error.status_code != 404 or not _accepts_html(scope):
                raise
            return await super().get_response("index.html", scope)
        if response.status_code == 404 and _accepts_html(scope):
            return await super().get_response("index.html", scope)
        return response


def create_cloud_run_app(
    settings: Settings | None = None,
    *,
    web_dist_dir: Path | None = None,
    require_web_dist: bool | None = None,
) -> FastAPI:
    application = create_app(settings)
    resolved_web_dist = (web_dist_dir or _default_web_dist()).resolve()
    must_have_web = (
        require_web_dist
        if require_web_dist is not None
        else os.getenv("LA_LANH_REQUIRE_WEB_DIST", "false").lower() == "true"
    )

    @application.middleware("http")
    async def cloud_security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if request.url.path.startswith("/assets/") and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif request.url.path == "/sw.js":
            response.headers["Cache-Control"] = "no-cache"
        elif request.url.path.startswith(_RESERVED_PREFIXES):
            response.headers["Cache-Control"] = "no-store"
        elif "text/html" in response.headers.get("content-type", ""):
            response.headers["Cache-Control"] = "no-store"
        return response

    if resolved_web_dist.is_dir() and (resolved_web_dist / "index.html").is_file():
        application.mount(
            "/",
            SpaStaticFiles(directory=resolved_web_dist, html=True, check_dir=True),
            name="web",
        )
    elif must_have_web:
        raise RuntimeError(f"built web app is missing: {resolved_web_dist}")

    return application


app = create_cloud_run_app()
