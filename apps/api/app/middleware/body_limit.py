from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodyLimitMiddleware:
    """Bound actual bytes before JSON parsing, including chunked requests."""

    def __init__(self, app: ASGIApp, *, max_bytes: int = 1_048_576) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    size = int(value)
                except ValueError:
                    size = -1
                if size < 0 or size > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                await self._reject(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        consumed = False

        async def bounded_receive() -> Message:
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "type": "about:blank",
                "title": "Request is too large",
                "status": 413,
                "code": "BODY_TOO_LARGE",
            },
            headers={"Cache-Control": "no-store"},
            media_type="application/problem+json",
        )
        await response(scope, receive, send)
