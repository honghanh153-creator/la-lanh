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


# Mood-shaped actions (#701). On a day saved as "Căng" the reader's device shows a "slow" action
# (pause before reacting, alone, at most ten minutes); on "Lạc trôi" a "clear" one (one concrete
# step that can start now, at most ten minutes). The server still never reads the mood: it offers
# these next to the card's action and the device chooses, as for "Đuối" (#627). Same freeze as
# ``ISSUE_LIGHT_CATALOG``: one fixed slot per issue, sentences served only once approved and only
# with the text digest named here; never re-tag or reorder a slot once released.
SLOW_PREFIX = "lighter.slow."
CLEAR_PREFIX = "lighter.clear."
MOOD_ACTION_PREFIXES: dict[str, str] = {"slow": SLOW_PREFIX, "clear": CLEAR_PREFIX}

# Frozen per kind and issue: (number, text digest, picture group). See the comment above.
MOOD_ACTION_CATALOG: dict[str, dict[str, tuple[tuple[str, str, str], ...]]] = {
    "slow": {
        "missing-context": (
            (
                "01",
                "f4c60b6ac8ef3a113133a6288416c45eccfd02a4774041797812b914aeb0ac89",
                "study_work",
            ),
        ),
        "too-many-open-loops": (
            ("01", "151a984066dd9ee4817e3fe9a0d698e5255ba523628119f6b7358f8e1e3264ee", "rest"),
        ),
        "changed-plan": (
            ("01", "10dacccc9cc3840d5548add6556c1d5f9a6f0247f7232a9a9d8e4e7607b5f617", "boundary"),
        ),
        "comparison-loop": (
            ("01", "ccb186ef70426b19f57de0ad85db469d7dc5a04446c0670eae15abd024b99b71", "body"),
        ),
        "automatic-caretaking": (
            ("01", "93e2b89b4fd18b23fc74da28d205b6b595cd4e8da9803e52468b80cbcf45af4b", "boundary"),
        ),
        "decision-fatigue": (
            ("01", "04190eb3e03808a175ed29b0556871dc33a1cca57696732937546c3c93aa2fe3", "rest"),
        ),
        "perfect-before-start": (
            (
                "01",
                "21916c3dfbb9dd9de92ca260a9566ea744ff21483f8be30f1a7b8d09fc113472",
                "study_work",
            ),
        ),
        "group-pressure": (
            ("01", "8f1dc68cabbf568d54def3cb8d791214938dd900524dfafd996d2e429f466fc9", "boundary"),
        ),
        "avoid-small-conflict": (
            ("01", "31afa05bb20d2dd9b32589bdc372bbef5e590f1ddcf76fe0f60f883f9340d73b", "body"),
        ),
        "defend-old-choice": (
            (
                "01",
                "ff842a95f930e40b538568f8d092da7afbedc62fd47bcdde67c3bd28bcde6ef3",
                "connection",
            ),
        ),
        "capacity-before-agreement": (
            ("01", "1c2cb68745d8410c3f616ad786ab46384ac3b730ad36f58fdbaf0fb7e54ce7c0", "boundary"),
        ),
        "quick-reply": (
            ("01", "4ee400394a61b1fb3e8c84fca26d56998912baed3621f4f24a1b5c08ce22214b", "boundary"),
        ),
        "repair-reply": (
            ("01", "854cc0155b1eb46e1ebc220ebeabd64527f2529e70eef7450465f90c8e4c45d6", "rest"),
        ),
        "specific-feedback": (
            (
                "01",
                "24c609d9a3773739701c19aa4a10346ab9afc60ec4961481a6e1187b53b3593c",
                "study_work",
            ),
        ),
        "name-the-need": (
            ("01", "276ee68fd1be664e254a9b10608c92b0bac64df74a62b9ff27ed31dfbd66ece2", "rest"),
        ),
    },
    "clear": {
        "missing-context": (
            (
                "01",
                "dded471ba9588d6faa6b518010ed7cd8e5f6e8f608af1e0de5c56b33daca37c1",
                "connection",
            ),
        ),
        "too-many-open-loops": (
            (
                "01",
                "423f7e8627222e3ea3f77e63d4ca10973891ee0b95d421d83bc1f696b6f64437",
                "study_work",
            ),
        ),
        "changed-plan": (
            (
                "01",
                "736d9daa5268c15f21b1a1a9521e0b16eae2374249f93c5fce87ea03cfe05364",
                "study_work",
            ),
        ),
        "comparison-loop": (
            (
                "01",
                "db41d6e6c521d333e95f060532f87a53ad700088925e2e7012f05a5fac286dd5",
                "study_work",
            ),
        ),
        "automatic-caretaking": (
            ("01", "e4f7869b76d5e77dd4ac4f6bff5618f9da6902b7a9e86ca817ba66d862685113", "boundary"),
        ),
        "decision-fatigue": (
            (
                "01",
                "1e400dd1e4020d32aaf26436f829e05a2bb97e4d50df65a87af1efac814534ee",
                "study_work",
            ),
        ),
        "perfect-before-start": (
            (
                "01",
                "794b7af16d416e8d781c063e04bb155baecef3d9876151c507cba7233f9ea897",
                "connection",
            ),
        ),
        "group-pressure": (
            ("01", "397a74a45a4e6e1228a272581f395aa52c5fe8e06d895f4d6a6e1ac172107eb9", "boundary"),
        ),
        "avoid-small-conflict": (
            (
                "01",
                "7bd258042836dbc6467131467491b41d1c0c44aaad58d587501e6f0fe6101d90",
                "connection",
            ),
        ),
        "defend-old-choice": (
            (
                "01",
                "093acd193cbece456c33feea954d266773beca87d1848854b2d357b29c4b189d",
                "study_work",
            ),
        ),
        "capacity-before-agreement": (
            ("01", "1b98e49d0835def93cf6b02ed7471b3ad784685e3d921009fe733c2137baea2f", "boundary"),
        ),
        "quick-reply": (
            (
                "01",
                "84adffea0efe76fab44574c97b3863f7323d240acff1d5ab9b89d40ba9879d9e",
                "study_work",
            ),
        ),
        "repair-reply": (
            (
                "01",
                "c5582450a82c39160f7a9ee09da5ff85751f8abad4f246869cfc3dc00bb1ee9a",
                "connection",
            ),
        ),
        "specific-feedback": (
            (
                "01",
                "78b30946a505eb284e7526cbe381639ef64a8c885745704d91deb39954759791",
                "connection",
            ),
        ),
        "name-the-need": (
            (
                "01",
                "84724945073e12bf02efd9cbb59e7d3b67543215cfd08b2c822687a1011db0cf",
                "connection",
            ),
        ),
    },
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


# A spoken minute count right before "phút": "năm", "mười", "mười lăm", "hai mươi", digits.
_UNITS = {
    "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4,
    "năm": 5, "lăm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9,
}  # fmt: skip
_NUMBER_WORDS = frozenset(_UNITS) | _TENS


def _spoken_number(tokens: list[str]) -> int | None:
    """The value of a run of Vietnamese number words, or None when it is not one number."""

    if not tokens:
        return None
    if tokens[0] == "mười":
        tens, rest = 10, tokens[1:]
    elif len(tokens) >= 2 and tokens[1] == "mươi" and tokens[0] in _UNITS:
        tens, rest = _UNITS[tokens[0]] * 10, tokens[2:]
    else:
        tens, rest = 0, tokens
    if len(rest) > 1 or (rest and rest[0] not in _UNITS) or (not tens and not rest):
        return None
    return tens + (_UNITS[rest[0]] if rest else 0)


def _minutes_at(words: list[str], index: int) -> float | None:
    """Minutes named by the "phút" at ``index``, with a trailing "rưỡi"; None when unclear."""

    start = index
    while start > 0 and words[start - 1] in _NUMBER_WORDS:
        start -= 1
    before = words[index - 1] if index else ""
    if start == index and before.isdigit():
        value: float | None = int(before)
    else:
        value = _spoken_number(words[start:index])
    if value is not None and index + 1 < len(words) and words[index + 1] == "rưỡi":
        value += 0.5
    return value


def _within_minutes(text: str, limit: int) -> bool:
    words = _WORD.findall(unicodedata.normalize("NFC", text).casefold())
    for index, word in enumerate(words):
        amount = words[index - 1] if index else ""
        if word == "phút":
            minutes = _minutes_at(words, index)
            if minutes is None or minutes > limit:
                return False
        elif word in {"giờ", "tiếng"} and (amount in _AMOUNTS or amount.isdigit()):
            return False
    return True


def within_five_minutes(text: str) -> bool:
    """False when the sentence names a duration longer than five minutes, or an unclear one."""

    return _within_minutes(text, 5)


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


def mood_slots(kind: str, issue_key: str) -> tuple[tuple[str, str, str], ...]:
    """(entry id, text digest, picture group) of every ``kind`` action written for an issue."""

    prefix = MOOD_ACTION_PREFIXES[kind]
    return tuple(
        (f"{prefix}{issue_key}.{number}", digest, shape)
        for number, digest, shape in MOOD_ACTION_CATALOG[kind].get(issue_key, ())
    )


def mood_store_gaps(issue_keys: Iterable[str]) -> list[str]:
    """What the slow and clear stores lack for ``issue_keys``: empty when both are complete."""

    wanted = tuple(issue_keys)
    found: list[str] = []
    for kind, catalog in MOOD_ACTION_CATALOG.items():
        found.extend(f"{kind} {key}: not a Daily issue" for key in catalog if key not in wanted)
        for issue_key in wanted:
            slots = mood_slots(kind, issue_key)
            if not slots:
                found.append(f"{kind} {issue_key}: no action")
            found.extend(
                f"{entry_id}: picture group must be one of the six"
                for entry_id, _digest, shape in slots
                if shape not in ACTION_SHAPES
            )
    return found


def within_ten_minutes(text: str) -> bool:
    """False when the sentence names a duration longer than ten minutes, or an unclear one."""

    return _within_minutes(text, 10)


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


def mood_action_for(kind: str, revision_id: UUID, mechanism_key: str | None) -> str | None:
    """The ``kind`` ("slow" or "clear") action offered with a card (#701); ``None`` while unserved.

    Only a card of a known Daily issue offers one: its issue's fixed slot, served once approved
    with the digest the catalog names, within the length bound and within ten minutes."""

    issue_key = issue_key_of(mechanism_key)
    if issue_key is None:
        return None
    slots = mood_slots(kind, issue_key)
    if not slots:
        return None
    seed = sha256(f"mood-{kind}-v1\x1f{issue_key}\x1f{revision_id}".encode()).digest()
    entry_id, digest, _shape = slots[int.from_bytes(seed[:8], "big") % len(slots)]
    text = approved_copy(entry_id)
    if (
        text is None
        or copy_digest(text) != digest
        or len(text) > LIGHTER_ACTION_MAX_CHARS
        or not within_ten_minutes(text)
    ):
        return None
    return text


def mood_action_projection(
    kind: str, revision_id: UUID, *, keepable: bool, mechanism_key: str | None = None
) -> LighterActionProjection | None:
    action = mood_action_for(kind, revision_id, mechanism_key)
    if action is None:
        return None
    return LighterActionProjection(
        action=action,
        weight="slow" if kind == "slow" else "clear",
        experiment=lighter_experiment_for(revision_id, action) if keepable else None,
    )


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
