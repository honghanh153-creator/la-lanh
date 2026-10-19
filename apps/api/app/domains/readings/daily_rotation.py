"""Per-person Daily rotation (B3-1a / A1).

Spec: docs/plans/2026-10-16-personalisation-variety-plan.md §2.2-2.3 and US-21 AC01-AC06.

* The seed is stable and never contains the date:
  ``seed = HMAC(K[v], owner_scope ‖ "daily" ‖ catalog_version)``.
* The calendar day only picks a position: every axis (headline, scene, action)
  runs its own cycle of length ``n``. The order inside a cycle is a fresh
  deterministic shuffle of ``seed ‖ axis ‖ cycle_no``; the first value of a new
  cycle never repeats the last value of the previous one. So two consecutive
  days always differ on every axis that has at least two values, and every value
  appears exactly once per cycle.
* The situation comes from the top-K of the day's eligible pool, at
  ``day_index mod K``.

Pure functions only: no I/O, no clock, no ``random`` (its algorithm is not a
stability contract across Python versions).
"""

from __future__ import annotations

import hmac
from datetime import date
from hashlib import sha256
from uuid import UUID

VARIETY_KEY_VERSION = 1
DAY_INDEX_EPOCH = date(2026, 1, 1)
DAILY_TOP_K = 3
_KEY_LABEL = b"la-lanh/variety-salt/v"


def derive_variety_key(server_secret: bytes, version: int = VARIETY_KEY_VERSION) -> bytes:
    """Selection-only key K[v], domain-separated from the secret it is derived from.

    It never encrypts or authenticates data; knowing it reveals no personal data.
    """

    if version < 1:
        raise ValueError("variety key versions start at 1")
    return hmac.new(server_secret, _KEY_LABEL + str(version).encode(), sha256).digest()


def daily_variety_seed(key: bytes, owner_scope: UUID, catalog_version: str) -> str:
    message = b"\x1f".join((owner_scope.bytes, b"daily", catalog_version.encode()))
    return hmac.new(key, message, sha256).hexdigest()[:32]


def day_index(local_date: date) -> int:
    return (local_date - DAY_INDEX_EPOCH).days


def _stream(seed: str, axis: str, cycle_no: int) -> list[int]:
    """Deterministic 64-bit words for one (seed, axis, cycle)."""

    words: list[int] = []
    block = 0
    while len(words) < 32:
        digest = sha256(f"{seed}\x1f{axis}\x1f{cycle_no}\x1f{block}".encode()).digest()
        words.extend(int.from_bytes(digest[i : i + 8], "big") for i in range(0, 32, 8))
        block += 1
    return words


def _shuffled(seed: str, axis: str, cycle_no: int, n: int) -> list[int]:
    order = list(range(n))
    words = _stream(seed, axis, cycle_no)
    # Fisher-Yates. Modulo bias over 64-bit words is far below anything observable here.
    for i in range(n - 1, 0, -1):
        j = words[(n - 1 - i) % len(words)] % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def cycle_order(seed: str, axis: str, cycle_no: int, n: int) -> tuple[int, ...]:
    """The order of one axis cycle, with the boundary rule already applied."""

    if n < 1:
        raise ValueError("an axis needs at least one value")
    if cycle_no < 0:
        raise ValueError("cycles start at day 0")
    if n == 2:
        # Strict alternation is the only order that never repeats a day, so every
        # cycle keeps the first cycle's order.
        return tuple(_shuffled(seed, axis, 0, n))
    order = _shuffled(seed, axis, cycle_no, n)
    if n >= 3 and cycle_no > 0:
        # The boundary swap touches positions 0 and 1 only, so for n >= 3 the
        # previous cycle's last value is its unswapped one: no recursion needed.
        if order[0] == _shuffled(seed, axis, cycle_no - 1, n)[-1]:
            order[0], order[1] = order[1], order[0]
    return tuple(order)


def axis_slot(seed: str, axis: str, n: int, index: int) -> int:
    """Value of ``axis`` on day ``index`` (days before the epoch are not served)."""

    if index < 0:
        raise ValueError("day_index must not be negative")
    return cycle_order(seed, axis, index // n, n)[index % n]


def top_k_slot(index: int, pool_size: int) -> int:
    return index % min(pool_size, DAILY_TOP_K) if pool_size else 0
