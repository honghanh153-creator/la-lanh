"""Leak checks for serialized API payloads.

A synthetic birth time such as "19:00" is also the clock time of every timestamp written during
that minute, so a plain substring check failed whenever CI ran at 19:00 UTC (#457, 15.11.2026).
Timestamps are masked before clock-time values are looked for; every other value is checked in
the payload as it is. A leaked birth datetime still fails on its date, and the key names
(birth_time, birth_date, ...) are checked separately by the callers.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
)
_CLOCK_TIME = re.compile(r"\d{1,2}:\d{2}")


def leaked(serialized: str, forbidden: Iterable[str]) -> list[str]:
    """Return the forbidden values found in `serialized`; clock times ignore timestamps."""

    masked = _TIMESTAMP.sub("<timestamp>", serialized)
    return [
        value
        for value in forbidden
        if value in (masked if _CLOCK_TIME.fullmatch(value) else serialized)
    ]
