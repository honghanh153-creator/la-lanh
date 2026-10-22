"""Keep user data out of exception logs (audit 2026-10-22 P08).

``logger.exception`` prints the exception message, and a library error can echo its input (a
Tarot question, a birth date, a capability token, a provider response). Every handler installed
here formats exceptions as frames plus the exception type only.

Boundary, as enforced and tested:
- The redaction filter runs first on each handler; after it, ``record.exc_info`` is ``None`` and
  ``record.exc_text`` holds the redacted traceback, so formatters (including ``%(exc_info)s``) and
  any later filter only see the redacted form.
- Not covered: the log message and its args themselves (our call sites log types only), filters
  attached to individual loggers (they run before handlers; none exist), and handlers added after
  the last ``install_log_redaction()`` call (it runs at app creation, again at startup and in each
  worker's main).
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
            # Drop the live exception so no formatter field or later consumer can reach it.
            record.exc_info = None
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
                # First in line, so filters attached earlier also see only the redacted record.
                handler.filters.insert(0, ExceptionMessageRedaction())
                setattr(handler, _MARK, True)
