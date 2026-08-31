from urllib.parse import urlsplit

from fastapi import Request

from app.domains.guest.errors import CsrfRejected


def require_trusted_origin(request: Request, trusted_origins: frozenset[str]) -> None:
    origin = request.headers.get("Origin")
    if origin is None:
        raise CsrfRejected
    normalized = normalize_origin(origin)
    if normalized is None or normalized not in trusted_origins:
        raise CsrfRejected


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
