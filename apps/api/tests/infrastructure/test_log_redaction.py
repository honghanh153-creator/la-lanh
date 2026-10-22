"""P08 (audit 2026-10-22): exception logs never carry the user data an error message can echo."""

from __future__ import annotations

import io
import logging
from collections.abc import Iterator

import pytest

from app.infrastructure.log_redaction import (
    ExceptionMessageRedaction,
    install_log_redaction,
    redacted_exception,
)

QUESTION = "zqcanary-question Mình có nên xin lỗi không?"
BIRTH = "zqcanary-1987-06-05T04:33"
TOKEN = "zqcanaryTOKEN_abcdefghijklmnopqrstuvwxyz01234567"  # noqa: S105 - synthetic canary


@pytest.fixture
def stream() -> Iterator[io.StringIO]:
    """A root handler like production's, isolated from pytest's own capture handlers."""

    root = logging.getLogger()
    saved = root.handlers[:]
    output = io.StringIO()
    root.handlers = [logging.StreamHandler(output)]
    try:
        install_log_redaction()
        yield output
    finally:
        root.handlers = saved


def _fail() -> None:
    try:
        raise KeyError(TOKEN)
    except KeyError as cause:
        raise ValueError(f"cannot parse {QUESTION} / {BIRTH}") from cause


@pytest.mark.parametrize(
    "name",
    [
        "app.api.v1.routes.daily_notes",
        "app.domains.readings.application",
        "app.domains.daily.service",
        "app.api.v1.routes.insights",
        "uvicorn.error",
    ],
)
def test_logged_exceptions_keep_frames_and_types_but_no_message(
    stream: io.StringIO, name: str
) -> None:
    logger = logging.getLogger(name)
    try:
        _fail()
    except ValueError:
        logger.exception("Private Daily reading projection failed; returning legacy note")
    written = stream.getvalue()
    assert "Private Daily reading projection failed" in written
    assert "builtins.ValueError: <message redacted>" in written
    assert "builtins.KeyError: <message redacted>" in written
    assert "_fail" in written  # frames stay useful for debugging
    for canary in ("zqcanary", QUESTION, BIRTH, TOKEN):
        assert canary not in written


def test_install_is_idempotent_and_covers_uvicorn_handlers(stream: io.StringIO) -> None:
    uvicorn = logging.getLogger("uvicorn.error")
    extra = logging.StreamHandler(io.StringIO())
    uvicorn.addHandler(extra)
    try:
        install_log_redaction()
        install_log_redaction()
        for handler in [*logging.getLogger().handlers, extra]:
            assert sum(isinstance(f, ExceptionMessageRedaction) for f in handler.filters) == 1
    finally:
        uvicorn.removeHandler(extra)


def test_without_any_root_handler_a_redacting_one_replaces_last_resort() -> None:
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers = []
    try:
        install_log_redaction()
        assert root.handlers and all(
            any(isinstance(f, ExceptionMessageRedaction) for f in h.filters) for h in root.handlers
        )
    finally:
        root.handlers = saved


def test_redacted_exception_handles_suppressed_and_cyclic_context() -> None:
    try:
        try:
            raise RuntimeError(TOKEN)
        except RuntimeError:
            raise OSError(QUESTION) from None
    except OSError as error:
        text = redacted_exception((OSError, error, error.__traceback__))
    assert "builtins.OSError: <message redacted>" in text and "RuntimeError" not in text
    assert "zqcanary" not in text


def test_app_and_workers_install_the_redaction(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    import app.domains.content_rewrite.worker as rewrite_worker
    import app.domains.readings.worker as readings_worker
    import app.main as main

    for module in (main, rewrite_worker, readings_worker):
        monkeypatch.setattr(
            module, "install_log_redaction", lambda m=module: calls.append(m.__name__)
        )
    monkeypatch.setattr("asyncio.run", lambda coroutine: coroutine.close())
    rewrite_worker.main()
    readings_worker.main()
    main.create_app()
    assert {"app.main", "app.domains.content_rewrite.worker", "app.domains.readings.worker"} <= set(
        calls
    )


def test_exc_info_field_and_an_earlier_filter_never_see_the_raw_exception() -> None:
    """Codex #51: a handler installed before create_app with %(exc_info)s, and a filter that was
    attached before the redaction, must only ever see the redacted exception."""

    root = logging.getLogger()
    saved = root.handlers[:]
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(logging.Formatter("%(message)s %(exc_info)s"))
    seen: list[object] = []

    class EarlierFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            seen.append(record.exc_info)
            seen.append(record.exc_text)
            return True

    handler.addFilter(EarlierFilter())
    root.handlers = [handler]
    try:
        install_log_redaction()
        try:
            _fail()
        except ValueError:
            logging.getLogger("app.api.v1.routes.daily_notes").exception("safe message")
    finally:
        root.handlers = saved
    written = output.getvalue()
    assert "safe message" in written and "<message redacted>" in written
    assert "zqcanary" not in written
    assert all("zqcanary" not in repr(item) for item in seen)


def test_a_filter_added_after_install_also_sees_only_the_redacted_record(
    stream: io.StringIO,
) -> None:
    seen: list[str] = []

    class LateFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            seen.append(repr(record.exc_info) + str(record.exc_text))
            return True

    logging.getLogger().handlers[0].addFilter(LateFilter())
    try:
        _fail()
    except ValueError:
        logging.getLogger("app.domains.readings.application").exception("safe message")
    assert seen and all("zqcanary" not in item for item in seen)
