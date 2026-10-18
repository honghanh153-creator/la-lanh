"""Per-session Tarot variants (US-20 AC15, B2-4).

Spec: docs/plans/2026-10-18-b2-4-tarot-variety-roast-task.md §1.

* ``seed = HMAC(K[v], owner_scope ‖ "tarot" ‖ catalog_version)`` with the selection-only key of
  B3-1a (``derive_variety_key``). The owner scope of a Tarot session is its guest.
* The position is the guest's session ordinal at creation. Every axis takes its value with
  ``axis_slot``, so two consecutive sessions of one guest differ on every axis with two or more
  values, and each value appears once per cycle.
* Only the chosen indices are stored, in the session's AES-GCM payload, when the session starts
  (with the deck shuffle). Rendering reads them and never recomputes them, so a key rotation, a
  catalog change, a cache miss or a restart cannot change what was drawn.

Pure functions only: no I/O, no clock.
"""

from __future__ import annotations

import hmac
from hashlib import sha256
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.readings.daily_rotation import VARIETY_KEY_VERSION, axis_slot
from app.domains.tarot import roles

TAROT_VARIANTS_VERSION: Literal["tarot-variants-v1"] = "tarot-variants-v1"
# Bump when a variant table changes length or meaning: a new catalog version reseeds new
# sessions only, stored sessions keep their indices.
TAROT_VARIANT_CATALOG_VERSION = "tarot-variant-catalog-v1"
HEADLINE_VARIANTS = 3
# Example scenes per card x topic. One today; the axis exists so new scenes are data only.
SCENE_VARIANTS = 1

_FrameIndex = Annotated[int, Field(ge=0, lt=roles.FRAME_VARIANTS)]
_SceneIndex = Annotated[int, Field(ge=0, lt=SCENE_VARIANTS)]


class TarotVariants(BaseModel):
    """Indices chosen once per session; never text, never the seed."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    version: Literal["tarot-variants-v1"] = TAROT_VARIANTS_VERSION
    key_version: int = Field(default=VARIETY_KEY_VERSION, ge=0)
    lead: int = Field(default=0, ge=0, lt=roles.LEAD_VARIANTS)
    headline: int = Field(default=0, ge=0, lt=HEADLINE_VARIANTS)
    frames: dict[str, _FrameIndex] = Field(default_factory=dict, max_length=5)
    scenes: dict[str, _SceneIndex] = Field(default_factory=dict, max_length=5)

    def frame(self, position_key: str) -> int:
        return self.frames.get(position_key, 0)

    def scene(self, position_key: str) -> int:
        return self.scenes.get(position_key, 0)


class _PersistedVariants(BaseModel):
    """The stored record exactly as ``start`` writes it: all six fields, the supported
    version, strict integers (no bools, no numeric strings), known keys only."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    version: Literal["tarot-variants-v1"]
    key_version: int = Field(ge=0)
    lead: int = Field(ge=0, lt=roles.LEAD_VARIANTS)
    headline: int = Field(ge=0, lt=HEADLINE_VARIANTS)
    frames: dict[str, _FrameIndex] = Field(max_length=5)
    scenes: dict[str, _SceneIndex] = Field(max_length=5)


# Sessions without a key (tests, unconfigured environments) or started before B2-4.
DEFAULT_VARIANTS = TarotVariants(key_version=0)


def tarot_variety_seed(key: bytes, owner_scope: UUID, catalog_version: str) -> str:
    message = b"\x1f".join((owner_scope.bytes, b"tarot", catalog_version.encode()))
    return hmac.new(key, message, sha256).hexdigest()[:32]


def choose_variants(
    key: bytes | None,
    owner_scope: UUID,
    position: int,
    position_keys: tuple[str, ...],
    *,
    catalog_version: str = TAROT_VARIANT_CATALOG_VERSION,
    key_version: int = VARIETY_KEY_VERSION,
) -> TarotVariants:
    if key is None:
        return DEFAULT_VARIANTS
    seed = tarot_variety_seed(key, owner_scope, catalog_version)
    slot = max(position, 0)
    return TarotVariants(
        key_version=key_version,
        lead=axis_slot(seed, "lead", roles.LEAD_VARIANTS, slot),
        headline=axis_slot(seed, "headline", HEADLINE_VARIANTS, slot),
        frames={
            position_key: axis_slot(seed, f"frame:{position_key}", roles.FRAME_VARIANTS, slot)
            for position_key in position_keys
        },
        scenes={
            position_key: axis_slot(seed, f"scene:{position_key}", SCENE_VARIANTS, slot)
            for position_key in position_keys
        },
    )


def stored_variants(payload: dict[str, Any]) -> TarotVariants:
    """The indices recorded when the session started.

    Only an absent ``variants`` key (a framed session started before B2-4) falls back to index
    0 everywhere. A present record, ``null`` included, must decode strictly; anything else fails
    loudly instead of inventing indices. The record is server-written and authenticated, so a
    failure means a bug or corruption, never client input."""

    if "variants" not in payload:
        return DEFAULT_VARIANTS
    persisted = _PersistedVariants.model_validate(payload["variants"], strict=True)
    return TarotVariants.model_validate(persisted.model_dump(), strict=True)
