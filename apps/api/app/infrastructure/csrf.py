from urllib.parse import urlsplit

from fastapi import Request

from app.domains.guest.errors import CsrfRejected

NATIVE_CLIENT_HEADER = "X-La-Lanh-Client"
NATIVE_CLIENT_VALUE = "capacitor-v1"
NATIVE_APP_ORIGINS = frozenset({"capacitor://localhost", "https://localhost"})


def require_trusted_origin(request: Request, trusted_origins: frozenset[str]) -> None:
    origin = request.headers.get("Origin")
    native_client = request.headers.get(NATIVE_CLIENT_HEADER) == NATIVE_CLIENT_VALUE
    if native_client and (origin is None or origin.rstrip("/") in NATIVE_APP_ORIGINS):
        # CapacitorHttp uses native networking, which may omit Origin. The custom
        # header forces browser callers through CORS preflight; the CSRF token is
        # still mandatory and remains the actual anti-forgery credential.
        return
    if origin is None:
        raise CsrfRejected
    normalized = normalize_origin(origin)
    if normalized is None or normalized not in trusted_origins:
        raise CsrfRejected


def trusted_origins(request: Request) -> frozenset[str]:
    return frozenset(
        origin
        for configured in request.app.state.settings.cors_origins
        if (origin := normalize_origin(str(configured))) is not None
    )


def normalize_origin(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.path not in {"", "/"}:
        return None
    if parsed.query or parsed.fragment:
        return None
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port
    authority = parsed.hostname.lower()
    if port is not None and port != default_port:
        authority = f"{authority}:{port}"
    return f"{parsed.scheme}://{authority}"
