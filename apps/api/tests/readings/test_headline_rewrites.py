"""A Daily headline that says the reader is tired never lands on a "Rực" or "Chill" day (#777).

The headline is picked before the mood, so the only way to keep "Bạn đang mệt, …" off a good-mood
day is to stop serving it. Each such code headline has a rewrite pair (direct and roast) in the
copy registry; it replaces the code headline once BOTH sentences are approved.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import headline_rewrites
from app.domains.readings.daily_psychology import _DAILY_VARIATIONS, DAILY_ISSUES
from app.domains.readings.headline_rewrites import (
    HEADLINE_REWRITES,
    REWRITE_PREFIX,
    approved_rewrite,
    asserts_tiredness,
    rewrite_ids,
    served_headline,
)
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.voice import ROAST_ISSUES, DailySections, roast_daily_sections
from tests.content.test_daily_variants import _check_clarity, _check_headline
from tests.readings.test_date_only_issue_rotation import START, _source, _variety

REGISTRY = load_registry()
GOOD_MOODS = ("Rực", "Chill")
# Signs whose date-only pool meets automatic-caretaking or name-the-need.
SIGNS = ("cancer", "scorpio", "pisces")


def _code_headlines() -> set[str]:
    """Every headline written in code (before any rewrite), direct and as roast keys."""

    titles = {title for titles, _, _ in _DAILY_VARIATIONS.values() for title in titles}
    pairs = {direct for voice in ROAST_ISSUES.values() for direct, _ in voice.headlines}
    return {*(h for issue in DAILY_ISSUES for h in issue.headlines), *titles, *pairs}


def _approve(
    monkeypatch: pytest.MonkeyPatch, *, voices: tuple[str, ...] = ("direct", "roast")
) -> None:
    entries: list[dict[str, Any]] = []
    for entry_id, entry in REGISTRY.items():
        approved = entry_id.startswith(REWRITE_PREFIX) and entry_id.rsplit(".", 1)[1] in voices
        if approved:
            entries.append(
                {
                    "id": entry_id,
                    "category": entry.category,
                    "text": entry.text,
                    "status": "approved",
                    "approver": "codex",
                    "date": "2026-11-20",
                    "digest": copy_digest(entry.text),
                }
            )
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _good_mood_days(sign: str, days: int) -> list[tuple[str, str]]:
    """(direct, roast) headline on the days of a mood cycle where the person picks Rực/Chill."""

    planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
    out = []
    for offset in range(days):
        if ("Rực", "Chill", "Đuối", "Căng")[offset % 4] not in GOOD_MOODS:
            continue
        local_date = START + timedelta(days=offset)
        plan = planner.plan(
            _source(sign),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=local_date.isoformat(),
            daily_variety=_variety(local_date),
        )
        card = renderer.render(plan)
        roast = roast_daily_sections(
            DailySections(card.hook, card.thesis, card.manifestation, card.micro_action)
        )
        out.append((card.hook, roast.hook))
    return out


def test_every_code_headline_that_says_tired_has_a_rewrite_pair_in_the_registry() -> None:
    tired = {headline for headline in _code_headlines() if asserts_tiredness(headline)}
    assert tired == set(HEADLINE_REWRITES)
    for issue, number in HEADLINE_REWRITES.values():
        assert any(issue == item.key for item in DAILY_ISSUES)
        for entry_id in rewrite_ids(issue, number):
            assert entry_id in REGISTRY, entry_id
            assert REGISTRY[entry_id].category == "reading"


@pytest.mark.parametrize("headline", sorted(HEADLINE_REWRITES))
def test_the_rewrite_names_the_habit_and_passes_the_headline_gates(headline: str) -> None:
    direct_id, roast_id = rewrite_ids(*HEADLINE_REWRITES[headline])
    direct, roast = REGISTRY[direct_id].text, REGISTRY[roast_id].text
    assert not asserts_tiredness(direct) and not asserts_tiredness(roast)
    assert direct != roast and direct != headline
    _check_clarity(direct_id, direct)
    _check_headline(direct_id, direct)
    _check_clarity(roast_id, roast)
    assert direct not in _code_headlines() and roast not in _code_headlines()


def test_the_detector_reads_vietnamese_words_not_substrings() -> None:
    assert asserts_tiredness("Bạn đang mệt, vẫn nhận thêm việc.")
    assert asserts_tiredness("Pin đã đỏ mà vẫn nhận thêm việc.")
    assert not asserts_tiredness("Bạn nhận thêm việc khi lịch đã kín.")


@pytest.mark.parametrize("sign", SIGNS)
def test_no_tired_headline_on_a_good_mood_day_once_the_rewrites_are_approved(
    sign: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # While the rewrites are pending the code headline is still served: this is the bug.
    before = _good_mood_days(sign, 72)
    assert any(asserts_tiredness(direct) for direct, _ in before), sign

    _approve(monkeypatch)
    after = _good_mood_days(sign, 72)
    assert [pair for pair in after if any(asserts_tiredness(text) for text in pair)] == []
    # Roast follows the rewrite pair, never the old roast of the replaced headline.
    pairs = {approved_rewrite(old) for old in HEADLINE_REWRITES}
    for direct, roast in after:
        for pair in pairs:
            if pair is not None and direct == pair[0]:
                assert roast == pair[1]


def test_a_half_approved_pair_keeps_the_code_headline(monkeypatch: pytest.MonkeyPatch) -> None:
    _approve(monkeypatch, voices=("direct",))
    for headline in HEADLINE_REWRITES:
        assert approved_rewrite(headline) is None
        assert served_headline(headline) == headline


def test_a_rewrite_that_still_says_tired_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    headline = next(iter(HEADLINE_REWRITES))
    direct_id, roast_id = rewrite_ids(*HEADLINE_REWRITES[headline])
    entries = [
        {
            "id": entry_id,
            "category": "reading",
            "text": text,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-20",
            "digest": copy_digest(text),
        }
        for entry_id, text in ((direct_id, "Bạn đã mệt mà vẫn giúp."), (roast_id, "Một câu khác."))
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)
    assert headline_rewrites.served_headline(headline) == headline


def test_a_saved_note_with_the_old_headline_keeps_its_old_roast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _approve(monkeypatch)
    old = "Bạn đang mệt, vẫn nhận thêm việc giúp người khác."
    issue = next(item for item in DAILY_ISSUES if item.key == "automatic-caretaking")
    roast = roast_daily_sections(
        DailySections(old, f"x {issue.takeaway}", issue.scenes[0], issue.advice[0])
    )
    assert roast.hook == "Pin đã đỏ mà vẫn nhận thêm việc giúp người khác."
