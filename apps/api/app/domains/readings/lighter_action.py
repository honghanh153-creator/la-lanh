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

Light actions per Daily issue (#699). ``ISSUE_LIGHT_CATALOG`` holds, for every Daily issue, the
light sentences written for that issue (``lighter.issue.<issue>.<nn>``), each with one of the six
picture groups (``ACTION_SHAPES``). A card whose issue is known offers one fixed slot of its own
issue, or nothing while that sentence is not approved; it never falls back to the general list,
so approving a sentence later cannot swap the sentence on a card. A card with no known issue
keeps the general list above. The same freeze applies: never append to, reorder or re-tag an
issue's slots once any of its sentences has been released; add a new catalog instead.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
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

ISSUE_LIGHT_PREFIX = "lighter.issue."
# The six picture groups of a small action (docs/reviews/2026-11-15-sang-tao-viral.md):
# nghỉ, cơ thể, học/việc, tiền, ranh giới, kết nối.
ACTION_SHAPES = ("rest", "body", "study_work", "money", "boundary", "connection")

# Frozen per issue: (number, text digest, picture group). See the module docstring.
ISSUE_LIGHT_CATALOG: dict[str, tuple[tuple[str, str, str], ...]] = {
    "missing-context": (
        ("01", "a86ecfd0a82db57683cce4d93d435d4d73c148fc445bfebbf5e5895312163da8", "body"),
        ("02", "1f069f9f8f8350a35c5d2b9f4e84ce6ca5a3e2055110ab487f7f3c5da7612a6a", "study_work"),
    ),
    "too-many-open-loops": (
        ("01", "b1f2d9675f5175fe43ea0d4da46a1e8550d5eaebae316b267800fe4c4e4d8e58", "rest"),
        ("02", "4fb95756d6627c1b95483afad2a378725246b3672b53315d7ad969e0bc646608", "study_work"),
    ),
    "changed-plan": (
        ("01", "9c2e5c6a1d7bd822c11b2ce1f614b49ac60810f58bee975e83272d2cef7f5fd2", "rest"),
        ("02", "8d74cd03620b603eb7e0f38064cc29e683e117927b0ea6f3eace08e0afb46b3f", "body"),
    ),
    "comparison-loop": (
        ("01", "7828dc7663c8c3d4765c90d5321a1c8f061475d1497f1b062ca7c33be50f33b0", "boundary"),
        ("02", "c4aedeca3101fcb10bdbd3b341a7edb54b717a65189780eaa29990790803db54", "study_work"),
    ),
    "automatic-caretaking": (
        ("01", "ac774a37b6434a7c90f9aa7d5b5bc5b9e81ef24f5cc4fbc46abeacbac6cb576a", "body"),
        ("02", "10e5d5d1bf212c8596fae22654e62e873be886c8cfe162237734d07fc05d4f4e", "rest"),
    ),
    "decision-fatigue": (
        ("01", "bdb1c14b41d1a63e1464e4a2c353fe9387a3ebb879bf112e7263cff0cf5014cf", "body"),
        ("02", "e8c55bedfd54d172a5945d24ed945fdab073bb942d792070ac75ceecf701978b", "rest"),
    ),
    "perfect-before-start": (
        ("01", "e828d6791fe2035c04559ce21b0fcd04223d291feb2f35f8a4e19867840a3c57", "body"),
        ("02", "a287b8451080ab5d8a78523e0968b2b912e7e946953c963821c3030bccbb9e3e", "rest"),
    ),
    "group-pressure": (
        ("01", "75f3bd38b1cb7cc695188dc55aae981a4104b7d3367004312aeaaac1843c8c37", "rest"),
        ("02", "ad4977d3639e6d13a78eb411755e48d02b1569d7f675f865cecdbf665bed8173", "boundary"),
    ),
    "avoid-small-conflict": (
        ("01", "48eeb1964bd41dd75f4ee11b22f53ce195d8e9a1d5819f703509a2c02549da1f", "body"),
        ("02", "be4e33ad4a41476f09737eedc7e019cfc40c5701816b590828d27cd3186280ef", "study_work"),
    ),
    "defend-old-choice": (
        ("01", "4e3d29ded132edab442c62addec24d9a886d6e033724de3d6035261f60b99203", "body"),
        ("02", "0af45b2ca45a2ebaa948f0ea6cbbe10526d0fc641f79fbd02dd378910c61f341", "rest"),
    ),
    "capacity-before-agreement": (
        ("01", "a414bee5824c18b8215106b00d334e3b3c4f7a9ac80273896646e354f8a9eaa7", "boundary"),
        ("02", "4cce812365a3fb6bad913bfbabb0d8422ac15c727486f2dbff0863b4bf61b9d8", "rest"),
    ),
    "quick-reply": (
        ("01", "4a397771d2ac08c18ee799bda24c735e84b1c970d03a282127fc7efaad81a639", "boundary"),
        ("02", "6c19fcdff596c54c396e643e4fa369c73bc180ec3a5434b36335996f5ea29e6a", "body"),
    ),
    "repair-reply": (
        ("01", "d392b943f4b76e248fcfc2e94fe75101cde7c249b36e696c1bc450ff890d0e6d", "rest"),
        ("02", "dd6754e167ca5e360abe886b307cb849d48574239aed56d9b6d05190f4a0f7de", "body"),
    ),
    "specific-feedback": (
        ("01", "b115b1b909f2123e6b787049bebfa47a20bdffec1c176a46b014d08ff2d32f6f", "body"),
        ("02", "57b6baeef6bdd6c6f0a1a6f95008032c2bdbab2c3b1946bf78212b908f58839a", "boundary"),
    ),
    "name-the-need": (
        ("01", "a3b05e29d94fbcab116d756962dfc9fb982d4a7a1930ec8aac49d8a30e36c5c0", "study_work"),
        ("02", "3409c8835ec2da4f09e9ec9c0b489ea2b7daaf60796696e5a5b5b6572f3b13fa", "body"),
    ),
}

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


def issue_key_of(mechanism_key: str | None) -> str | None:
    """The Daily issue of a blueprint mechanism (``psychology:<issue>``), when it has a store."""

    if mechanism_key and mechanism_key.startswith("psychology:"):
        issue_key = mechanism_key.removeprefix("psychology:")
        if issue_key in ISSUE_LIGHT_CATALOG:
            return issue_key
    return None


def light_slots(issue_key: str) -> tuple[tuple[str, str, str], ...]:
    """(entry id, text digest, picture group) of every light action written for ``issue_key``."""

    return tuple(
        (f"{ISSUE_LIGHT_PREFIX}{issue_key}.{number}", digest, shape)
        for number, digest, shape in ISSUE_LIGHT_CATALOG[issue_key]
    )


def light_store_gaps(issue_keys: Iterable[str]) -> list[str]:
    """What the store lacks for ``issue_keys`` (every Daily issue): empty when it is complete."""

    wanted = tuple(issue_keys)
    found = [f"{key}: not a Daily issue" for key in ISSUE_LIGHT_CATALOG if key not in wanted]
    for issue_key in wanted:
        slots = ISSUE_LIGHT_CATALOG.get(issue_key, ())
        if not slots:
            found.append(f"{issue_key}: no light action")
        found.extend(
            f"{ISSUE_LIGHT_PREFIX}{issue_key}.{number}: picture group must be one of the six"
            for number, _digest, shape in slots
            if shape not in ACTION_SHAPES
        )
    return found


def _slot(revision_id: UUID, issue_key: str | None) -> tuple[str, str] | None:
    if issue_key is not None:
        slots = light_slots(issue_key)
        seed = sha256(f"issue-light-v1\x1f{issue_key}\x1f{revision_id}".encode()).digest()
        entry_id, digest, _shape = slots[int.from_bytes(seed[:8], "big") % len(slots)]
        return entry_id, digest
    if not LIGHTER_CATALOG:
        return None
    seed = sha256(f"lighter-action-v1\x1f{revision_id}".encode()).digest()
    return LIGHTER_CATALOG[int.from_bytes(seed[:8], "big") % len(LIGHTER_CATALOG)]


def lighter_action_for(revision_id: UUID, mechanism_key: str | None = None) -> str | None:
    """The lighter action offered with ``revision_id``; ``None`` while its sentence is unserved.

    ``mechanism_key`` is the card's blueprint mechanism. A card of a known Daily issue offers a
    light action written for that issue; any other card offers one from the general list.
    """

    slot = _slot(revision_id, issue_key_of(mechanism_key))
    if slot is None:
        return None
    entry_id, digest = slot
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
    revision_id: UUID, *, keepable: bool, mechanism_key: str | None = None
) -> LighterActionProjection | None:
    action = lighter_action_for(revision_id, mechanism_key)
    if action is None:
        return None
    return LighterActionProjection(
        action=action,
        experiment=lighter_experiment_for(revision_id, action) if keepable else None,
    )
