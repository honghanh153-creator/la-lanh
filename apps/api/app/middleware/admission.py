import asyncio
import re
import time
from dataclasses import dataclass
from hashlib import sha256

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

_INVITE_RESEND_PATH = re.compile(r"^/v1/la-chung/requests/[^/]+/resend$")


@dataclass(frozen=True, slots=True)
class AdmissionPolicy:
    name: str
    per_peer: int
    global_limit: int


class AdmissionControlMiddleware(BaseHTTPMiddleware):
    """Small application backstop; production still needs distributed edge limits."""

    def __init__(self, app, *, window_seconds: int = 60) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._window_seconds = window_seconds
        self._lock = asyncio.Lock()
        self._windows: dict[tuple[str, str], tuple[int, int]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        policy = _policy(request)
        if policy is None:
            return await call_next(request)
        peer = request.client.host if request.client is not None else "unknown"
        peer_key = sha256(peer.encode()).hexdigest()[:24]
        allowed, retry_after = await self._admit(policy, peer_key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "type": "about:blank",
                    "title": "Request rate is temporarily limited",
                    "status": 429,
                    "code": "ADMISSION_LIMITED",
                },
                headers={"Retry-After": str(retry_after), "Cache-Control": "no-store"},
                media_type="application/problem+json",
            )
        return await call_next(request)

    async def _admit(self, policy: AdmissionPolicy, peer_key: str) -> tuple[bool, int]:
        now = int(time.monotonic())
        window = now // self._window_seconds
        retry_after = self._window_seconds - (now % self._window_seconds)
        async with self._lock:
            if len(self._windows) > 4096:
                self._windows = {
                    key: value for key, value in self._windows.items() if value[0] == window
                }
            peer_count = self._windows.get((policy.name, peer_key), (window, 0))
            global_count = self._windows.get((policy.name, "*"), (window, 0))
            peer_used = peer_count[1] if peer_count[0] == window else 0
            global_used = global_count[1] if global_count[0] == window else 0
            if peer_used >= policy.per_peer or global_used >= policy.global_limit:
                return False, retry_after
            self._windows[(policy.name, peer_key)] = (window, peer_used + 1)
            self._windows[(policy.name, "*")] = (window, global_used + 1)
            return True, retry_after


def _policy(request: Request) -> AdmissionPolicy | None:
    path = request.url.path
    if request.method == "POST" and path == "/v1/guest-sessions":
        return AdmissionPolicy("guest-create", per_peer=10, global_limit=120)
    if request.method == "POST" and path == "/v1/la-chung/requests":
        return AdmissionPolicy("la-chung-invite-create", per_peer=10, global_limit=120)
    if request.method == "POST" and _INVITE_RESEND_PATH.fullmatch(path):
        return AdmissionPolicy("la-chung-invite-resend", per_peer=20, global_limit=240)
    if request.method == "POST" and path in {
        "/v1/birth-profile",
        "/v1/birth-profile/supplement",
    }:
        return AdmissionPolicy("birth-compute", per_peer=20, global_limit=120)
    if path.startswith("/v1/public/") or path.startswith("/v1/share-artifacts/"):
        return AdmissionPolicy("public-capability", per_peer=120, global_limit=1200)
    return None
