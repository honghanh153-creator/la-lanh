"""More than one line of Lá per Daily issue (#626).

``companion.py`` holds one authored pair (direct + roast) per issue. Extra pairs live in
``copy_registry.json`` as ``la.issue.<issue>.<nn>.direct`` and ``la.issue.<issue>.<nn>.roast``.
A pair is served only when both sentences are approved and pass the same rules as the authored
lines; anything else is left out and Lá keeps the authored line (fail closed).

Each person has a fixed order of their own over an issue's lines, and the line follows the
calendar day: day ``d`` shows slot ``d mod n`` of that order (``n`` lines). Nothing here reads
history or stores anything, the same as the rest of Daily selection (owner decision 2026-10-21).

What that guarantees, and no more (Codex r1 on #657): two days fewer than ``n`` days apart never
show the same line of an issue, so an issue served on consecutive or near days changes line as
long as the pool is deep enough. It does not count how often the issue came up, so it does not
promise every other line before a repeat; the persona metric (repeat share over 29 days) is the
measure, and it needs a deep pool (24 lines for a person who meets one issue a day).

The authored first line stays out of storage, as before. An extra line is stored with the card
together with its roast wording (``ReadingCandidate.companion`` and ``companion_roast``), so a
card that was opened keeps both voices when pairs are approved, edited or withdrawn later.
"""

from __future__ import annotations

from app.domains.content.copy_approval import approved_copy, approved_ids
from app.domains.readings import companion
from app.domains.readings.companion import (
    COMPANION_FORBIDDEN_FRAGMENTS,
    COMPANION_ISSUE_LINES,
    DIRECT_MAX_WORDS,
    MIN_WORDS,
    ROAST_MAX_WORDS,
    CompanionIssueLine,
    CompanionLine,
    nudge_failures,
    word_count,
)
from app.domains.readings.daily_rotation import cycle_order
from app.domains.readings.models import DailyVariety
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS

COMPANION_LINE_PREFIX = "la.issue."
# Selection deferred (decision D, coordinator 17.11.2026, Codex r2 on #657): a calendar-day pick
# can lock onto an issue's rhythm (served every 2 days with 2 lines: always the same line), which
# breaks the content standard. A correct pick needs the line shown at the issue's last appearance,
# and that is an owner decision (it reverses "Daily selection reads no stored history", 21.10).
# Until then no extra line is served: Lá keeps the authored line, and the pool and the stored pair
# are ready for when selection is decided. Tests switch this on to cover them.
EXTRA_LINE_SELECTION_ENABLED = False
COMPANION_LINE_VOICES = ("direct", "roast")
_SENTENCE_ENDS = (".", "?", "!", "…")


def _authored_texts() -> frozenset[str]:
    return frozenset(text for _, text, _ in companion._all_lines())


def extra_line_problems(line: CompanionLine, entry: CompanionIssueLine) -> list[str]:
    """Why a registry pair may not be served as one more line of ``entry`` (empty when it may)."""

    forbidden = tuple(
        fragment.casefold() for fragment in (*COMPANION_FORBIDDEN_FRAGMENTS, *BANNED_CORE_FRAGMENTS)
    )
    authored = _authored_texts()
    problems: list[str] = []
    if line.direct == line.roast:
        problems.append("roast must differ from direct")
    for voice, text, limit in (
        ("direct", line.direct, DIRECT_MAX_WORDS),
        ("roast", line.roast, ROAST_MAX_WORDS),
    ):
        count = word_count(text)
        if not MIN_WORDS <= count <= limit:
            problems.append(f"{voice} has {count} words (limit {MIN_WORDS}-{limit})")
        if any(fragment in text.casefold() for fragment in forbidden):
            problems.append(f"{voice} uses a forbidden fragment")
        if not text.rstrip().endswith(_SENTENCE_ENDS):
            problems.append(f"{voice} must end with punctuation")
        if text in authored:
            problems.append(f"{voice} repeats an authored line")
    problems += [f"direct {problem}" for problem in nudge_failures(line.direct, entry)]
    return problems


def extra_lines_by_issue() -> dict[str, tuple[CompanionLine, ...]]:
    """Approved extra pairs per issue, in id order. Fails closed: a broken pair is left out."""

    numbers: dict[str, list[str]] = {}
    for entry_id in approved_ids(COMPANION_LINE_PREFIX):
        parts = entry_id[len(COMPANION_LINE_PREFIX) :].split(".")
        if len(parts) != 3 or parts[0] not in COMPANION_ISSUE_LINES:
            continue
        if parts[1] not in numbers.setdefault(parts[0], []):
            numbers[parts[0]].append(parts[1])
    seen: set[str] = set()
    found: dict[str, tuple[CompanionLine, ...]] = {}
    for issue_key, issue_numbers in numbers.items():
        entry = COMPANION_ISSUE_LINES[issue_key]
        lines: list[CompanionLine] = []
        for number in issue_numbers:
            prefix = f"{COMPANION_LINE_PREFIX}{issue_key}.{number}."
            direct, roast = (approved_copy(f"{prefix}{voice}") for voice in COMPANION_LINE_VOICES)
            if direct is None or roast is None:
                continue
            line = CompanionLine(direct, roast)
            if extra_line_problems(line, entry) or seen & {direct, roast}:
                continue
            seen |= {direct, roast}
            lines.append(line)
        if lines:
            found[issue_key] = tuple(lines)
    return found


def companion_pool_slot(seed: str, issue_key: str, size: int, occurrence: int) -> int:
    """Which line of a ``size``-line pool a person sees at step ``occurrence`` (the day index).

    A fixed order per person and issue, walked round-robin: any ``size`` steps in a row are all
    different.
    """

    if occurrence < 0:
        raise ValueError("occurrence must not be negative")
    return cycle_order(seed, f"companion:{issue_key}", 0, size)[occurrence % size]


def daily_companion_line(
    mechanism_key: str | None, variety: DailyVariety | None
) -> CompanionLine | None:
    """The extra pair Lá says for this Daily card, or ``None`` for the authored first line.

    The slot follows the calendar day (see the module docstring for what that guarantees).
    Without the per-person rotation, or while an issue has no approved extra pair, nothing
    changes.
    """

    if not EXTRA_LINE_SELECTION_ENABLED:
        return None
    if variety is None or not mechanism_key or not mechanism_key.startswith("psychology:"):
        return None
    issue_key = mechanism_key.removeprefix("psychology:")
    extras = extra_lines_by_issue().get(issue_key, ())
    if not extras:
        return None
    slot = companion_pool_slot(variety.seed, issue_key, len(extras) + 1, variety.day_index)
    return None if slot == 0 else extras[slot - 1]


def roast_companion_line(direct: str) -> str:
    """Roast wording for an authored or approved direct line; any other text passes through."""

    roast = companion.roast_companion_line(direct)
    if roast != direct:
        return roast
    for lines in extra_lines_by_issue().values():
        for line in lines:
            if line.direct == direct:
                return line.roast
    return direct
