from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

HTTP_REQUESTS = Counter(
    "la_lanh_http_requests_total",
    "HTTP requests handled by the API.",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "la_lanh_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "route"),
)


def _route_template(request: Request) -> str:
    resolved_route = request.scope.get("route")
    if resolved_route is not None:
        route_path = str(getattr(resolved_route, "path", "unmatched"))
        request_path = request.url.path
        if route_path != "/" and request_path.endswith(route_path):
            return request_path
        return route_path
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match is Match.FULL:
            return str(getattr(route, "path", "unmatched"))
    return "unmatched"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = _route_template(request)
            HTTP_REQUESTS.labels(request.method, route, str(status_code)).inc()
            HTTP_REQUEST_DURATION.labels(request.method, route).observe(perf_counter() - started_at)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
