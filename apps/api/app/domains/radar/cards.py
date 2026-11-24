"""Hợp gu share card (owner AL1, 20.11.2026; direction C, first half).

The card says how two people get on, never who they are: the tier name, the reading's one-line
headline and the relationship, plus at most the first letter of the nickname the owner chose
(off by default). Never a birth date, birth time, place, real name or chart term. The image is
drawn on the device; a link to it (``radar_share_card_links``, off by default) keeps this frozen
snapshot, encrypted, no longer than the result.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

CARD_VERSION = "radar-card-v1"
MAX_CARDS_PER_RESULT = 5


@dataclass(frozen=True, slots=True)
class RadarCardView:
    """What the owner sees about a link: never its token."""

    id: UUID
    status: str
    created_at: datetime
    expires_at: datetime


def card_view(card: Any, now: datetime) -> RadarCardView:
    status = "active"
    if card.revoked_at is not None:
        status = "revoked"
    elif card.expires_at <= now:
        status = "expired"
    return RadarCardView(
        id=card.id, status=status, created_at=card.created_at, expires_at=card.expires_at
    )


def initial_of(label: str) -> str | None:
    """ "M." for "Mèo": the first letter only, uppercased; None when there is no letter."""

    for char in unicodedata.normalize("NFC", label.strip()):
        if char.isalpha():
            return f"{char.upper()}."
    return None


def card_snapshot(reading: dict[str, Any], *, label: str, show_initial: bool) -> dict[str, Any]:
    signature = reading.get("pair_signature") or {}
    tier = (signature.get("tier") or {}).get("label") or signature.get("kicker")
    return {
        "version": CARD_VERSION,
        "context": str(reading.get("context") or "someone"),
        "tier": str(tier or reading.get("headline") or ""),
        "line": str(signature.get("headline") or reading.get("headline") or ""),
        "initial": initial_of(label) if show_initial else None,
    }
