"""A lighter thing to do next to the Daily action (#627).

The sentences live in ``copy_registry.json`` as ``lighter.action.<nn>`` and are served only once
approved. Nothing here reads the person's mood: the server offers both actions and the device
chooses.

Which sentence a card offers is frozen. ``LIGHTER_CATALOG`` is a fixed list of (entry id, text
digest) slots, and a revision id always maps to the same slot. A card therefore offers that one
sentence or, while it is not approved, nothing; approving, adding or removing any other sentence
never changes it, and editing a sentence stops it being offered until the catalog names the new
text. To add sentences later, add a new catalog for revisions that carry a new version stamp;
never append to or reorder this one, because that would move cards people already opened.
"""

from __future__ import annotations

import re
import unicodedata
from hashlib import sha256
from uuid import UUID

from app.domains.content.copy_approval import approved_copy, copy_digest
from app.domains.readings.models import (
    LIGHTER_ACTION_MAX_CHARS,
    ExperimentProjection,
    LighterActionProjection,
    experiment_projection_for,
)

LIGHTER_ACTION_PREFIX = "lighter.action."

# Frozen: see the module docstring before touching this list.
LIGHTER_CATALOG: tuple[tuple[str, str], ...] = (
    ("lighter.action.01", "5d54c9aae4a17d49fd558b1c5d4897e0292a586c420f94f11578fbb75e6cb9e8"),
    ("lighter.action.02", "4f76f23e00efb850aa8074cebb12de1752072268089dd2bbc9335526b66f509d"),
    ("lighter.action.03", "2b283f8bbf71fccb0f804b2b5a502d20bfe646086cc301ef57848b77feab1d11"),
    ("lighter.action.04", "b262c55bf4c48264ececdfe97207afac248e3eb2e75fb44b0dabbe86dbac9375"),
    ("lighter.action.05", "7f78cce6165e2db74f53375c325f3db0505679b8cf585972fbf82c829523b500"),
    ("lighter.action.06", "85283f7ebe9452b83d989743794f57a8019283e7c282564484ff2f40df786615"),
    ("lighter.action.07", "e15ee36172c735031821fb60fa9c52e04fe1ccd2333d8165ca7e9b540ff07b59"),
    ("lighter.action.08", "f991cf6a4b9b56982b3e2361a9ab811d9b511a3dc903af5041fa76ce62de9b08"),
    ("lighter.action.09", "697f916fa052559980e86a3d1af7c4b5e41d32be93ce5490b2265f311708b6b4"),
    ("lighter.action.10", "4503332447e8e93215e5aeef7505e0c6f69dd3e25ecc03d0770a137a13acb64a"),
    ("lighter.action.11", "2ead2960b11ea4a20007488e83dbeb17c28e80fb3fec4850d43eef69884e3fee"),
    ("lighter.action.12", "3d2ad21b07a7c65695e05d372cd32a3610bfa28ca6e3c9821c15d4b3bb80f622"),
)

# "Light" means doable alone within five minutes (qa/personas/judge-rubric.md).
_UP_TO_FIVE = frozenset({"một", "hai", "ba", "bốn", "năm"})
_TENS = frozenset({"mười", "mươi"})
_AMOUNTS = (
    _UP_TO_FIVE
    | _TENS
    | frozenset({"sáu", "bảy", "tám", "chín", "lăm", "rưỡi", "nửa", "vài", "mấy", "nhiều"})
)
_WORD = re.compile(r"\w+")


def within_five_minutes(text: str) -> bool:
    """False when the sentence names a duration longer than five minutes, or an unclear one."""

    words = _WORD.findall(unicodedata.normalize("NFC", text).casefold())
    for index, word in enumerate(words):
        amount = words[index - 1] if index else ""
        if word == "phút":
            if amount not in _UP_TO_FIVE or (index >= 2 and words[index - 2] in _TENS):
                return False
        elif word in {"giờ", "tiếng"} and (amount in _AMOUNTS or amount.isdigit()):
            return False
    return True


def lighter_action_for(revision_id: UUID) -> str | None:
    """The lighter action offered with ``revision_id``; ``None`` while its sentence is unserved."""

    if not LIGHTER_CATALOG:
        return None
    seed = sha256(f"lighter-action-v1\x1f{revision_id}".encode()).digest()
    entry_id, digest = LIGHTER_CATALOG[int.from_bytes(seed[:8], "big") % len(LIGHTER_CATALOG)]
    text = approved_copy(entry_id)
    if (
        text is None
        or copy_digest(text) != digest
        or len(text) > LIGHTER_ACTION_MAX_CHARS
        or not within_five_minutes(text)
    ):
        return None
    return text


def lighter_experiment_for(revision_id: UUID, action: str) -> ExperimentProjection:
    """The keepable form of a lighter action: its own key, the generic observation wording."""

    return experiment_projection_for(revision_id, action)


def lighter_action_projection(
    revision_id: UUID, *, keepable: bool
) -> LighterActionProjection | None:
    action = lighter_action_for(revision_id)
    if action is None:
        return None
    return LighterActionProjection(
        action=action,
        experiment=lighter_experiment_for(revision_id, action) if keepable else None,
    )
