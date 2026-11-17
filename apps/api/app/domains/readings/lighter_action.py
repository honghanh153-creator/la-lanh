"""A lighter thing to do next to the Daily action (#627).

The sentences live in ``copy_registry.json`` as ``lighter.action.<nn>`` and are served only once
approved. One is picked per accepted revision, so a card always offers the same lighter action.
Nothing here reads the person's mood: the server offers both actions and the device chooses.
"""

from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from app.domains.content.copy_approval import approved_texts
from app.domains.readings.models import (
    LIGHTER_ACTION_MAX_CHARS,
    ExperimentProjection,
    LighterActionProjection,
    experiment_projection_for,
)

LIGHTER_ACTION_PREFIX = "lighter.action."


def lighter_action_for(revision_id: UUID) -> str | None:
    """The approved lighter action offered with ``revision_id``; ``None`` if none is approved."""

    pool = tuple(
        text
        for text in approved_texts(LIGHTER_ACTION_PREFIX)
        if len(text) <= LIGHTER_ACTION_MAX_CHARS
    )
    if not pool:
        return None
    digest = sha256(f"lighter-action-v1\x1f{revision_id}".encode()).digest()
    return pool[int.from_bytes(digest[:8], "big") % len(pool)]


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
