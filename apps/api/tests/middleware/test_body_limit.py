import pytest
from starlette.types import Message

from app.middleware.body_limit import BodyLimitMiddleware


@pytest.mark.parametrize(
    "chunks,headers,rejected",
    [
        ([b"12345"], [], False),
        ([b"12", b"3456"], [], True),
        ([b"123456"], [(b"content-length", b"2")], True),
        ([b""], [(b"content-length", b"999")], True),
        ([b""], [(b"content-length", b"-1")], True),
        ([b""], [(b"content-length", b"bad")], True),
    ],
)
async def test_actual_body_bounded_before_parser(chunks, headers, rejected):  # type: ignore[no-untyped-def]
    parsed = []
    sent = []
    messages = [
        {"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1}
        for index, chunk in enumerate(chunks)
    ]

    async def receive() -> Message:
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        sent.append(message)

    async def app(scope, receive, send):  # type: ignore[no-untyped-def]
        del scope
        parsed.append((await receive())["body"])
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    await BodyLimitMiddleware(app, max_bytes=5)({"type": "http", "headers": headers}, receive, send)
    assert sent[0]["status"] == (413 if rejected else 200)
    assert parsed == ([] if rejected else [b"".join(chunks)])
