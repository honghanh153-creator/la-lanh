"""Each Daily part says something new (Codex review of PR #8, 11.10.2026).

Sentence 1 describes the reader's tendency, sentence 2 adds an insight, and
only the action says what to do. "Different words" is not enough: shared
content phrases between parts are rejected, not just identical sentences.
"""

import re
from collections.abc import Iterator
from itertools import pairwise

import pytest

from app.domains.readings.daily_personalization import (
    CAPACITY_AT_WORK_MEANING,
    PAIR_RULES,
    PLACEMENT_MEANINGS,
    REPAIR_REPLY_MEANING,
)
from app.domains.readings.daily_psychology import (
    DAILY_ISSUES,
    NO_PERSONAL_MEANING,
    DailyIssuePattern,
)

_ISSUES = {issue.key: issue for issue in DAILY_ISSUES}
# Words that tell the reader what to do belong to the action only.
# "nên" also means "so" and "thử thêm việc" describes a habit, so those two
# count only when they open the sentence or follow "bạn".
_ADVICE = re.compile(
    r"\b(?:có thể|hãy|đừng|cứ việc)\b|(?:^|\bbạn\s+)(?:nên|thử)\b",
    re.IGNORECASE,
)
# Grammar and referents; sharing these is not repeating an idea.
_FUNCTION = frozenset(
    "bạn mình của và là không có nghĩa người kia khi thì đã đang một những các cho với "
    "để được rồi chưa vẫn dễ muốn cần nhưng dù mà nếu này đó thường chỉ cả hơn "
    "rất trong về theo".split()
)


def personal_meanings() -> Iterator[tuple[str, str]]:
    """Every authored (issue, tendency sentence) the renderer can pair."""
    yield from PLACEMENT_MEANINGS.items()
    for rule in PAIR_RULES:
        yield rule.tension_issue, rule.tension_meaning
        yield rule.cooperative_issue, rule.cooperative_meaning
        if rule.conjunction_meaning is not None:
            yield rule.conjunction_issue or rule.cooperative_issue, rule.conjunction_meaning
    yield "capacity-before-agreement", CAPACITY_AT_WORK_MEANING
    yield "repair-reply", REPAIR_REPLY_MEANING
    yield "capacity-before-agreement", NO_PERSONAL_MEANING


def _phrases(text: str, issue: DailyIssuePattern) -> set[str]:
    words = re.findall(r"[^\W\d_]+", text.casefold())
    pairs = {f"{a} {b}" for a, b in pairwise(words) if a not in _FUNCTION and b not in _FUNCTION}
    # The situation's own topic ("tin nhắn", "bản nháp") may be named everywhere.
    return pairs - {anchor.casefold() for anchor in issue.scene_anchors}


def _actions(issue: DailyIssuePattern) -> tuple[str, ...]:
    return (*issue.advice, *issue.relationship_advice)


@pytest.mark.parametrize(("issue_key", "meaning"), list(personal_meanings()))
def test_tendency_sentence_gives_no_advice(issue_key: str, meaning: str) -> None:
    assert issue_key in _ISSUES
    assert meaning.startswith(("Bạn ", "Lá ")), meaning
    assert not _ADVICE.search(meaning), meaning


@pytest.mark.parametrize("issue", DAILY_ISSUES, ids=lambda issue: issue.key)
def test_takeaway_is_an_insight_not_the_action(issue: DailyIssuePattern) -> None:
    assert not _ADVICE.search(issue.takeaway), issue.takeaway
    for action in _actions(issue):
        shared = _phrases(issue.takeaway, issue) & _phrases(action, issue)
        assert not shared, (issue.key, issue.takeaway, action, shared)


@pytest.mark.parametrize(("issue_key", "meaning"), list(personal_meanings()))
def test_two_thesis_sentences_do_not_restate_each_other(issue_key: str, meaning: str) -> None:
    issue = _ISSUES[issue_key]
    shared = _phrases(meaning, issue) & _phrases(issue.takeaway, issue)
    assert not shared, (issue_key, meaning, issue.takeaway, shared)


def test_moon_mars_separating_repair_reply_regression() -> None:
    """The exact case Codex reproduced: tendency, takeaway and action all said 'nói lại'."""
    issue = _ISSUES["repair-reply"]
    thesis = f"{REPAIR_REPLY_MEANING} {issue.takeaway}"
    assert "nói lại" not in thesis
    assert all("nói lại" not in sentence for sentence in (REPAIR_REPLY_MEANING, issue.takeaway))


def test_detectors_catch_the_reviewed_failure() -> None:
    """Guard the guard: the v7 draft Codex rejected must fail these checks."""
    issue = _ISSUES["repair-reply"]
    old_tendency = "Bạn dễ thấy mình vừa trả lời hơi nhanh, và vẫn kịp nói lại cho rõ."
    old_takeaway = "Bạn có thể nói lại cho rõ ý mà không cần đoán người kia đang nghĩ gì."
    assert _ADVICE.search(old_takeaway)
    assert "nói lại" in _phrases(old_tendency, issue) & _phrases(old_takeaway, issue)
    assert not _ADVICE.search("Bạn muốn làm tốt, nên dễ tự chê.")
