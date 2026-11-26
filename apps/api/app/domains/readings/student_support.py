"""Two small supports for readers who are students (#703).

1. An action that asks the reader to contact someone ("nhắn một người") always has another
   action that needs no contact, for a reader who does not want to, or has nobody to message.
   ``ALONE_CATALOG`` holds one such sentence per Daily issue (``lighter.alone.<issue>.<nn>``).
   ``alone_store_gaps`` lists every issue whose action pool contains a contact action and has no
   alone action; the store test is red while that list is not empty.

2. A short "nhiều bạn cũng vậy" line (``student.common.<nn>``), offered only with the Daily
   issues named in ``COMMON_LINE_ISSUES``. It is never part of crisis support: this module is the
   only place that hands the line out, and it answers ``None`` for anything else.

Both stores follow the freeze of ``lighter_action``: a sentence is served only once approved and
only with the text digest named here. The server reads nothing about the reader to pick either.

The Daily reading sends both (``alone_action`` and ``common_line`` of the reading content). The
alone action is sent only when one of the card's offered actions asks to contact someone, and it
can be kept like the lighter action. The web does not show either yet.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from hashlib import sha256
from itertools import pairwise
from typing import Literal
from uuid import UUID

from app.domains.content.copy_approval import approved_copy, copy_digest
from app.domains.readings.daily_psychology import DailyIssuePattern
from app.domains.readings.lighter_action import (
    ACTION_SHAPES,
    issue_key_of,
    lighter_action_for,
    lighter_experiment_for,
    mood_action_for,
    within_ten_minutes,
)
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS, AloneActionProjection

ContactKind = Literal["card", "light", "slow", "clear"]

ALONE_PREFIX = "lighter.alone."
COMMON_LINE_PREFIX = "student.common."

# Verbs that mean "reach another person". "tin nhắn" (the noun) is not one.
_CONTACT_WORDS = frozenset({"nhắn", "gọi", "hỏi", "nói", "nhờ", "xin", "gửi", "báo"})
_CONTACT_PAIRS = frozenset(
    {("trả", "lời"), ("trao", "đổi"), ("xác", "nhận"), ("đề", "nghị"), ("tin", "cho")}
)
_WORD = re.compile(r"\w+")


def needs_contact(text: str) -> bool:
    """True when the action asks the reader to contact someone. Errs towards True."""

    folded = unicodedata.normalize("NFC", text).casefold().replace("tin nhắn", "tin")
    words = _WORD.findall(folded)
    return any(word in _CONTACT_WORDS for word in words) or any(
        pair in _CONTACT_PAIRS for pair in pairwise(words)
    )


# Frozen per issue: (number, text digest, picture group). See the module docstring.
ALONE_CATALOG: dict[str, tuple[tuple[str, str, str], ...]] = {
    "missing-context": (
        ("01", "32f799fe3e8c52799ff1624b42baa1b4d1a07383230744f9096a2d3eb37e2710", "study_work"),
    ),
    "too-many-open-loops": (
        ("01", "393452dfc42b9c78484e62219ea1ff8d25e657d2211bd51226e782c5acb6c424", "study_work"),
    ),
    "changed-plan": (
        ("01", "879600c814c1b51a562f9f87beb6a4c8528979989a3ac0697d89f9ee084f9c81", "study_work"),
    ),
    "comparison-loop": (
        ("01", "06239c79c84bc6dc3072a4790c215a9c0726ca51e3390aaa285a91fb907f2dd1", "study_work"),
    ),
    "automatic-caretaking": (
        ("01", "284a5c83aee9a0908b5fac58459ba4324fc339f5fd9880ac2015d2c6c6c76359", "boundary"),
    ),
    "decision-fatigue": (
        ("01", "ca74b54d666e41af2023693f3bebb2d9abd9274ad6af15f8be30be11a1867a1d", "study_work"),
    ),
    "perfect-before-start": (
        ("01", "a3b2f30456880ddbe44789ce13aeb2bfeebac2fa0d7d4aedb7f032a242b4c870", "study_work"),
    ),
    "group-pressure": (
        ("01", "8f582e7c45a2211ad4a8b5c020eab19784625ea8a8bd3f99401e12943278b24a", "study_work"),
    ),
    "avoid-small-conflict": (
        ("01", "500583084c05c2855ec01718571ee5d5f2031ac0a7f3acf159810899075312bd", "boundary"),
    ),
    "defend-old-choice": (
        ("01", "1678a99680a88421cb18f2eb6ce5c54a67170e3dd36a14c039234e2f26acd17f", "study_work"),
    ),
    "capacity-before-agreement": (
        ("01", "6ed1d6bfac641c32aec0ae8d60a9b5a816689221cb99ba1b9b19960cc3f1a8f9", "boundary"),
    ),
    "quick-reply": (
        ("01", "c1c17e37eefcc52c217c03608e64f14bba09c14bb0759eb3a1b024333d371ba0", "boundary"),
    ),
    "repair-reply": (
        ("01", "e19001333d230b50a6a2ad89dc17a62adeab0e7c3b66877d540ecef1f34f339b", "connection"),
    ),
    "specific-feedback": (
        ("01", "b333f1c4057c7b6b9e20e59d82ef55b4d91fb9e2b249837d7af44afd8501f82b", "study_work"),
    ),
    "name-the-need": (
        ("01", "f9b9c8408e34e0e18552c2e1c572e1498cda865bbfa09690bcb4552eda458c36", "connection"),
    ),
}

# Frozen: (entry id, text digest).
COMMON_LINE_CATALOG: tuple[tuple[str, str], ...] = (
    ("student.common.01", "266935a74a5c441245480aece479dfca3418e85ab6b3cb94acb6adc81016cf63"),
    ("student.common.02", "dd8f012b0ae1c50a300f3ef925f8e983d5bc6d044f8d1f753c428b6c2b1e8f21"),
    ("student.common.03", "bf10c198412be379c932ae3726486de65f765c4269dc49b97691fa07ff181567"),
)

# Everyday study and group situations where "others meet this too" is true and kind to hear.
# Not the issues about one particular person's message or reply: there the line would speak
# for someone the reader knows.
COMMON_LINE_ISSUES = frozenset(
    {
        "too-many-open-loops",
        "comparison-loop",
        "decision-fatigue",
        "perfect-before-start",
        "group-pressure",
        "avoid-small-conflict",
    }
)


def alone_slots(issue_key: str) -> tuple[tuple[str, str, str], ...]:
    """(entry id, text digest, picture group) of every alone action written for an issue."""

    return tuple(
        (f"{ALONE_PREFIX}{issue_key}.{number}", digest, shape)
        for number, digest, shape in ALONE_CATALOG.get(issue_key, ())
    )


def contact_issues(issues: Iterable[DailyIssuePattern]) -> tuple[str, ...]:
    """Keys of the issues whose action pool holds at least one contact action."""

    return tuple(
        issue.key
        for issue in issues
        if any(needs_contact(text) for text in (*issue.advice, *issue.relationship_advice))
    )


def alone_store_gaps(issues: Iterable[DailyIssuePattern]) -> list[str]:
    """What the alone store lacks for ``issues`` (every Daily issue): empty when complete."""

    known = tuple(issues)
    keys = {issue.key for issue in known}
    found = [f"{key}: not a Daily issue" for key in ALONE_CATALOG if key not in keys]
    for issue_key in contact_issues(known):
        slots = alone_slots(issue_key)
        if not slots:
            found.append(f"{issue_key}: contact action without an alone action")
        found.extend(
            f"{entry_id}: picture group must be one of the six"
            for entry_id, _digest, shape in slots
            if shape not in ACTION_SHAPES
        )
    return found


def _served(entry_id: str, digest: str) -> str | None:
    text = approved_copy(entry_id)
    if text is None or copy_digest(text) != digest or len(text) > LIGHTER_ACTION_MAX_CHARS:
        return None
    return text


def alone_action_for(revision_id: UUID, mechanism_key: str | None) -> str | None:
    """The no-contact action of a card's Daily issue; ``None`` while unserved or unknown."""

    issue_key = issue_key_of(mechanism_key)
    slots = alone_slots(issue_key) if issue_key is not None else ()
    if not slots:
        return None
    seed = sha256(f"alone-v1\x1f{issue_key}\x1f{revision_id}".encode()).digest()
    entry_id, digest, _shape = slots[int.from_bytes(seed[:8], "big") % len(slots)]
    text = _served(entry_id, digest)
    if text is None or needs_contact(text) or not within_ten_minutes(text):
        return None
    return text


def alone_offer_for(
    revision_id: UUID, mechanism_key: str | None, card_action: str
) -> tuple[str, tuple[ContactKind, ...]] | None:
    """The alone action a card offers, and which of the card's actions ask to contact someone.

    ``None`` when the issue has no served alone action, or when none of the actions the card
    offers (its own, the lighter, the slow, the clear one) asks the reader to reach anyone.
    """

    text = alone_action_for(revision_id, mechanism_key)
    if text is None:
        return None
    offered: tuple[tuple[ContactKind, str | None], ...] = (
        ("card", card_action),
        ("light", lighter_action_for(revision_id, mechanism_key)),
        ("slow", mood_action_for("slow", revision_id, mechanism_key)),
        ("clear", mood_action_for("clear", revision_id, mechanism_key)),
    )
    replaces = tuple(
        kind for kind, action in offered if action is not None and needs_contact(action)
    )
    return (text, replaces) if replaces else None


def alone_action_projection(
    revision_id: UUID, *, keepable: bool, mechanism_key: str | None, card_action: str
) -> AloneActionProjection | None:
    offer = alone_offer_for(revision_id, mechanism_key, card_action)
    if offer is None:
        return None
    action, replaces = offer
    return AloneActionProjection(
        action=action,
        replaces=replaces,
        experiment=lighter_experiment_for(revision_id, action) if keepable else None,
    )


def common_line_for(revision_id: UUID, mechanism_key: str | None) -> str | None:
    """The "nhiều bạn cũng vậy" line of a card, only for an issue in ``COMMON_LINE_ISSUES``."""

    issue_key = issue_key_of(mechanism_key)
    if issue_key not in COMMON_LINE_ISSUES or not COMMON_LINE_CATALOG:
        return None
    seed = sha256(f"student-common-v1\x1f{issue_key}\x1f{revision_id}".encode()).digest()
    entry_id, digest = COMMON_LINE_CATALOG[
        int.from_bytes(seed[:8], "big") % len(COMMON_LINE_CATALOG)
    ]
    return _served(entry_id, digest)
