"""Stateless per-reader variant choice (Daily v2 C2d) and the weekly ⚠ cap (rule N-6).

Spec: ``docs/plans/2026-11-02-daily-v2-content-quality-plan.md`` (C2d, N-6) as changed by the
gap register ``docs/plans/2026-11-03-daily-v2-gap-register.md`` (PV-1, PL-17, PV-2): nothing is
stored. The old C2d design kept 30 days of fragment codes per person; that contradicts the 24-hour
lifetime of a Daily note and the codes would reveal the house cusps, hence the birth time.

* **Key.** The caller passes the selection-only key ``K[v]`` that
  ``daily_rotation.derive_variety_key`` derives from the server secret (the same key the Daily
  service already receives as ``daily_variety_key``). This module derives its own sub-key from
  it with a fixed label, so its outputs never coincide with the B3-1a Daily seed or the Tarot
  variants. It never encrypts or authenticates anything; a key is never written here and there is
  no default key.
* **Reader seed.** ``reader_seed = HMAC(sub-key, reader_scope)``: the profile scope only, no date
  and no birth data, so the seed reveals nothing about the chart.
* **Variants.** ``variant_slot`` is ``daily_rotation.axis_slot`` on the reader seed: the day picks
  a position in a per-(reader, slot) shuffled cycle of ``n`` days. So one (reader, slot, day, key)
  always gives the same variant, two consecutive days differ when ``n >= 2``, and each variant
  appears once per ``n``-day cycle. ``slot`` is a closed catalog code (for example a contact code
  plus a fragment role); the caller may pass any non-negative rotation index instead of the day.
* **⚠ cap (N-6), rolling window.** The plan says "at most once a week" without saying ISO week
  or any seven days. ISO weeks would allow Sunday then Monday, so this uses the stricter reading:
  any seven consecutive days hold at most one day on which a ⚠ meaning may appear in the trend
  tag. Days are cut into blocks of ``SENSITIVE_BLOCK_DAYS``, shifted by a fixed per-reader HMAC
  phase; the reader's open day inside a block sits at an HMAC offset
  ``0..SENSITIVE_JITTER_DAYS``. Two open days are therefore at least
  ``SENSITIVE_BLOCK_DAYS - SENSITIVE_JITTER_DAYS = 7`` days apart, readers fall on different days,
  and the day moves from block to block. On an open day at most one ⚠ meaning is kept across all
  of the day's trend tags, chosen by the same seed; on every other day all ⚠ meanings are dropped.
  ⚠ meanings never lead a tag and never stand alone (N-3), and meanings that must never reach a
  daily reading are always dropped.

Pure functions only: no I/O, no clock, no logging, no cache, no ``random``. Nothing is persisted;
every call recomputes from (key, reader, day).
"""

from __future__ import annotations

import hmac
from collections.abc import Sequence
from datetime import date
from hashlib import sha256
from uuid import UUID

from app.domains.readings.daily_rotation import DAY_INDEX_EPOCH, axis_slot, day_index
from app.domains.readings.house_meanings import SourcedMeaning

DAILY_V2_VARIANT_VERSION = "daily-v2-variants-v1"
_SUBKEY_LABEL = b"la-lanh/daily-v2/variant-rotation/v1"
# derive_variety_key returns a 32-byte SHA-256 HMAC; anything shorter is not that key.
MIN_KEY_BYTES = 32

SENSITIVE_WINDOW_DAYS = 7
SENSITIVE_BLOCK_DAYS = 9
SENSITIVE_JITTER_DAYS = 2
if SENSITIVE_BLOCK_DAYS - SENSITIVE_JITTER_DAYS < SENSITIVE_WINDOW_DAYS:  # pragma: no cover
    raise RuntimeError("open ⚠ days must stay at least a rolling window apart")

_SENSITIVE_PHASE_AXIS = "n6:phase"
_SENSITIVE_DAY_AXIS = "n6:open-day"
_SENSITIVE_PICK_AXIS = "n6:pick"


def _subkey(variety_key: bytes) -> bytes:
    if len(variety_key) < MIN_KEY_BYTES:
        raise ValueError("variant rotation needs the derived selection key")
    return hmac.new(variety_key, _SUBKEY_LABEL, sha256).digest()


def reader_seed(variety_key: bytes, reader_scope: UUID) -> str:
    """Per-reader seed under the selection key. Holds no date and no birth data."""

    message = b"\x1f".join((DAILY_V2_VARIANT_VERSION.encode(), reader_scope.bytes))
    return hmac.new(_subkey(variety_key), message, sha256).hexdigest()[:32]


def _day(local_date: date) -> int:
    index = day_index(local_date)
    if index < 0:
        raise ValueError(f"days before {DAY_INDEX_EPOCH.isoformat()} are not served")
    return index


def variant_slot(seed: str, slot: str, n: int, index: int) -> int:
    """Variant ``0..n-1`` of ``slot`` at rotation ``index`` (normally the day index)."""

    if not slot:
        raise ValueError("a variant slot needs a catalog code")
    if n < 1:
        raise ValueError("a slot needs at least one variant")
    return axis_slot(seed, f"c2d:{slot}", n, index)


def daily_variant(
    variety_key: bytes, reader_scope: UUID, slot: str, n: int, local_date: date
) -> int:
    """Variant of ``slot`` for one reader on one local day."""

    return variant_slot(reader_seed(variety_key, reader_scope), slot, n, _day(local_date))


def _word(seed: str, axis: str, index: int) -> int:
    digest = sha256(f"{seed}\x1f{axis}\x1f{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _sensitive_block(seed: str, index: int) -> tuple[int, int]:
    """(block, offset) of day ``index`` in this reader's ⚠ blocks.

    A fixed per-reader phase shifts the block edges, so open days fall on every calendar day
    across readers instead of only the first days of one shared block.
    """

    if index < 0:
        raise ValueError("day_index must not be negative")
    phase = _word(seed, _SENSITIVE_PHASE_AXIS, 0) % SENSITIVE_BLOCK_DAYS
    return divmod(index + phase, SENSITIVE_BLOCK_DAYS)


def sensitive_day_open(seed: str, index: int) -> bool:
    """Whether a ⚠ meaning may appear in this reader's trend tag on day ``index``."""

    block, offset = _sensitive_block(seed, index)
    return offset == _word(seed, _SENSITIVE_DAY_AXIS, block) % (SENSITIVE_JITTER_DAYS + 1)


def limit_sensitive(
    seed: str, index: int, tags: Sequence[Sequence[SourcedMeaning]]
) -> tuple[tuple[SourcedMeaning, ...], ...]:
    """The day's trend tags with N-6 applied, in their original order.

    Drops every meaning that must never reach a daily reading, then every ⚠ meaning except at
    most one on the reader's open day. The kept ⚠ meaning is never the first of its tag and never
    alone: only a tag that opens with a non-⚠ meaning (which always stays) offers a candidate.
    """

    allowed = [tuple(m for m in tag if m.daily_allowed) for tag in tags]
    candidates = [
        (tag_no, position)
        for tag_no, tag in enumerate(allowed)
        if tag and not tag[0].sensitive
        for position, meaning in enumerate(tag)
        if meaning.sensitive
    ]
    keep: tuple[int, int] | None = None
    if candidates and sensitive_day_open(seed, index):
        block, _ = _sensitive_block(seed, index)
        keep = candidates[_word(seed, _SENSITIVE_PICK_AXIS, block) % len(candidates)]
    return tuple(
        tuple(
            meaning
            for position, meaning in enumerate(tag)
            if not meaning.sensitive or (tag_no, position) == keep
        )
        for tag_no, tag in enumerate(allowed)
    )


def daily_trend_tags(
    variety_key: bytes,
    reader_scope: UUID,
    local_date: date,
    tags: Sequence[Sequence[SourcedMeaning]],
) -> tuple[tuple[SourcedMeaning, ...], ...]:
    """``limit_sensitive`` for one reader on one local day."""

    return limit_sensitive(reader_seed(variety_key, reader_scope), _day(local_date), tags)
