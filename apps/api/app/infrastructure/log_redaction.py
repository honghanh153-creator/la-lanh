"""Keep user data out of exception logs (audit 2026-10-22 P08).

``logger.exception`` prints the exception message, and a library error can echo its input (a
Tarot question, a birth date, a capability token, a provider response). Every handler installed
here formats exceptions as frames plus the exception type only: the message, and the messages of
chained causes, are never written. Our own log messages already name only error types.
"""

from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType

ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]
_LOGGERS = ("", "uvicorn", "uvicorn.error")
_MARK = "_la_lanh_redaction"


def redacted_exception(exc_info: ExcInfo) -> str:
    """Traceback frames and exception types for the whole chain, without any message."""

    chain: list[BaseException] = []
    current: BaseException | None = exc_info[1]
    while current is not None and all(current is not seen for seen in chain):
        chain.append(current)
        current = current.__cause__ or (
            None if current.__suppress_context__ else current.__context__
        )
    blocks = [
        "Traceback (most recent call last):\n"
        + "".join(traceback.format_tb(error.__traceback__))
        + f"{type(error).__module__}.{type(error).__qualname__}: <message redacted>"
        for error in reversed(chain)
    ]
    return "\n\nThe above exception led to:\n\n".join(blocks)


class ExceptionMessageRedaction(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info and record.exc_info[1] is not None:
            record.exc_text = redacted_exception(record.exc_info)
        if record.stack_info:
            record.stack_info = None
        return True


def install_log_redaction() -> None:
    """Attach the filter to every handler of the root and uvicorn loggers (idempotent).

    Without a root handler Python falls back to ``logging.lastResort``, which would print the
    message unfiltered, so a stderr handler is added for WARNING and above.
    """

    root = logging.getLogger()
    if not root.handlers:
        fallback = logging.StreamHandler(sys.stderr)
        fallback.setLevel(logging.WARNING)
        fallback.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
        root.addHandler(fallback)
    for name in _LOGGERS:
        for handler in logging.getLogger(name).handlers:
            if not getattr(handler, _MARK, False):
                handler.addFilter(ExceptionMessageRedaction())
                setattr(handler, _MARK, True)
