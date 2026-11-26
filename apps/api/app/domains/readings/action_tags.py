"""Size and picture group of every Daily action (#699, part 2).

A light action already carries its picture group in ``lighter_action.ISSUE_LIGHT_CATALOG``. The
normal actions are the sentences ``daily.action.<issue>.<nn>`` and
``daily.bundle.<issue>.<nn>.action`` in ``copy_registry.json``; their tags live beside this module
in ``normal_action_tags.json`` as ``entry id -> [text digest, picture group]``.

The tags describe a sentence. They take no part in choosing which sentence a card shows, so adding
or changing a tag never changes a card. The digest ties a tag to the wording it was given for: a
reworded sentence must be looked at again before its tag counts (``store_gaps`` names it).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from app.domains.readings.lighter_action import ACTION_SHAPES, light_slots, light_store_gaps

TAGS_PATH = Path(__file__).with_name("normal_action_tags.json")
_NORMAL_ID = re.compile(
    r"^daily\.(?:action\.(?P<loose>[a-z0-9-]+)\.\d+|bundle\.(?P<bundle>[a-z0-9-]+)\.\d+\.action)$"
)


@dataclass(frozen=True, slots=True)
class ActionTag:
    """What one action sentence is: how heavy, and which of the six pictures fits it."""

    weight: Literal["light", "normal"]
    shape: str


def normal_issue_of(entry_id: str) -> str | None:
    """The Daily issue a normal action sentence belongs to, or None for any other entry."""

    match = _NORMAL_ID.match(entry_id)
    return (match.group("loose") or match.group("bundle")) if match else None


@cache
def normal_tags() -> Mapping[str, tuple[str, str]]:
    """``entry id -> (text digest, picture group)`` for every tagged normal action."""

    raw = json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    return {entry_id: (str(digest), str(shape)) for entry_id, (digest, shape) in raw.items()}


def tag_of(entry_id: str, issue_keys: Iterable[str]) -> ActionTag | None:
    """Size and picture group of the action sentence ``entry_id``; None when it has no tag."""

    normal = normal_tags().get(entry_id)
    if normal is not None:
        return ActionTag("normal", normal[1])
    for issue_key in issue_keys:
        for light_id, _digest, shape in light_slots(issue_key):
            if light_id == entry_id:
                return ActionTag("light", shape)
    return None


def store_gaps(issue_keys: Iterable[str], registry_digests: Mapping[str, str]) -> list[str]:
    """What the action store lacks: empty when every Daily issue has a light and a normal action
    and every action has a size and one of the six picture groups.

    ``registry_digests`` is ``entry id -> text digest`` for the whole copy store.
    """

    wanted = tuple(issue_keys)
    tags = normal_tags()
    found = light_store_gaps(wanted)
    in_store = {
        entry_id: digest
        for entry_id, digest in registry_digests.items()
        if normal_issue_of(entry_id) is not None
    }
    for issue_key in wanted:
        if not any(normal_issue_of(entry_id) == issue_key for entry_id in in_store):
            found.append(f"{issue_key}: no normal action")
    for entry_id, digest in sorted(in_store.items()):
        if normal_issue_of(entry_id) not in wanted:
            found.append(f"{entry_id}: not a Daily issue")
        tag = tags.get(entry_id)
        if tag is None:
            found.append(f"{entry_id}: no picture group")
        elif tag[1] not in ACTION_SHAPES:
            found.append(f"{entry_id}: picture group must be one of the six")
        elif tag[0] != digest:
            found.append(f"{entry_id}: reworded, check its picture group again")
    found.extend(
        f"{entry_id}: tagged but not in the copy store"
        for entry_id in sorted(tags)
        if entry_id not in in_store
    )
    return found
