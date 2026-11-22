"""Daily headlines that say the reader is tired, replaced once their rewrite is approved (#777).

A Daily headline is chosen before the person picks a mood, so a headline that states "you are
tired today" ("Bạn đang mệt, …") lands on "Rực" and "Chill" days too: 877 such days in the
returning-user persona run of 20.11.2026. Each of these code headlines has a rewrite that names
the habit, not today's state, written as a pair (direct and roast) in ``copy_registry.json`` under
``rewrite.headline.<issue>.<nn>.direct|roast``.

The rewrite pair is pending until a Codex copy batch approves it. Only when BOTH sentences are
approved does the code headline give way, in the served pool and in the Roast voice together, so
an approval can never leave a direct headline without its roast pair (the 16.11.2026 incident with
``daily.headline.*``). Anything else keeps the code headline (fail closed). A saved note that shows
the old headline keeps it, with its old roast wording.
"""

from __future__ import annotations

import re

from app.domains.content.copy_approval import approved_copy

REWRITE_PREFIX = "rewrite.headline."
REWRITE_VOICES = ("direct", "roast")

# States today's tiredness. "Bạn nói mệt" (what the reader said) counts too: on a "Chill" day it
# still reads as Lá telling them they are tired.
_TIRED = re.compile(r"(?<!\w)(?:mệt|đuối|kiệt sức|cạn sức|hết sức|pin đã đỏ)(?!\w)", re.IGNORECASE)

# Code headline -> (issue, number) of its rewrite pair in the copy registry.
HEADLINE_REWRITES: dict[str, tuple[str, str]] = {
    "Bạn đang mệt, vẫn nhận thêm việc giúp người khác.": ("automatic-caretaking", "01"),
    "Bạn giúp thêm một việc dù đã khá mệt.": ("automatic-caretaking", "02"),
    "Bạn đang mệt mà vẫn cố chọn cho đúng.": ("decision-fatigue", "01"),
    "Bạn đã mệt, danh sách lựa chọn còn dài.": ("decision-fatigue", "02"),
    "Bạn nói mệt, chưa nói muốn được giúp gì.": ("name-the-need", "01"),
}


def asserts_tiredness(text: str) -> bool:
    """True when ``text`` says or implies the reader is tired."""

    return _TIRED.search(text) is not None


def rewrite_ids(issue: str, number: str) -> tuple[str, str]:
    base = f"{REWRITE_PREFIX}{issue}.{number}"
    return f"{base}.direct", f"{base}.roast"


def approved_rewrite(headline: str) -> tuple[str, str] | None:
    """(direct, roast) that replaces ``headline``, or ``None`` while it is not fully approved."""

    found = HEADLINE_REWRITES.get(headline)
    if found is None:
        return None
    direct, roast = (approved_copy(entry_id) for entry_id in rewrite_ids(*found))
    if direct is None or roast is None or direct == roast:
        return None
    if asserts_tiredness(direct) or asserts_tiredness(roast):
        return None
    return direct, roast


def served_headline(headline: str) -> str:
    """The headline a reader sees for a code ``headline``: its approved rewrite, else itself."""

    rewrite = approved_rewrite(headline)
    return headline if rewrite is None else rewrite[0]


def rewrite_pairs() -> dict[str, tuple[str, str, str]]:
    """Approved rewrite direct -> (roast, issue, replaced code headline)."""

    pairs: dict[str, tuple[str, str, str]] = {}
    for headline, (issue, _) in HEADLINE_REWRITES.items():
        rewrite = approved_rewrite(headline)
        if rewrite is not None:
            pairs[rewrite[0]] = (rewrite[1], issue, headline)
    return pairs
