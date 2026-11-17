"""More than one line of Lá per Daily issue (#626).

``companion.py`` holds one authored pair (direct + roast) per issue. Extra pairs live in
``copy_registry.json`` as ``la.issue.<issue>.<nn>.direct`` and ``la.issue.<issue>.<nn>.roast``.
A pair is served only when both sentences are approved and pass the same rules as the authored
lines; anything else is left out and Lá keeps the authored line (fail closed).

Each person walks the lines of an issue in a fixed order of their own, one step each time the
issue comes up, so a line returns only after every other line of that issue was shown. Nothing
here reads history or stores anything: the step is the day counter divided by how many days
apart the rotation serves the issue.

The authored first line stays out of storage, as before. An extra line is stored with the card
(``ReadingCandidate.companion``), so a card that was opened keeps its line when pairs are
approved or withdrawn later.
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
    """Which line of a ``size``-line pool a person sees the ``occurrence``-th time.

    A fixed order per person and issue, walked round-robin: any ``size`` occurrences in a row
    are all different, so a line comes back only after every other line of the pool was shown.
    """

    if occurrence < 0:
        raise ValueError("occurrence must not be negative")
    return cycle_order(seed, f"companion:{issue_key}", 0, size)[occurrence % size]


def daily_companion_line(
    mechanism_key: str | None, variety: DailyVariety | None, *, period: int = 1
) -> str | None:
    """The extra line Lá says for this Daily card, or ``None`` for the authored first line.

    ``period`` is how many days apart the rotation serves one issue to this person (one to
    ``DAILY_TOP_K``), so ``day_index // period`` counts how often the issue has come up. Without
    the per-person rotation, or while an issue has no approved extra pair, nothing changes.
    """

    if variety is None or not mechanism_key or not mechanism_key.startswith("psychology:"):
        return None
    issue_key = mechanism_key.removeprefix("psychology:")
    extras = extra_lines_by_issue().get(issue_key, ())
    if not extras:
        return None
    occurrence = variety.day_index // max(1, period)
    slot = companion_pool_slot(variety.seed, issue_key, len(extras) + 1, occurrence)
    return None if slot == 0 else extras[slot - 1].direct


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
