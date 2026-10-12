"""Each Daily part says something new (Codex reviews of PR #8, 11-12.10.2026).

Sentence 1 describes the reader's tendency, sentence 2 adds information the
tendency does not contain (a consequence or a reframe), and only the action
says what to do. Two layers of evidence:

- mechanical: advice words outside the action and shared content phrases
  between parts are rejected over every authored combination;
- editorial: ``TAKEAWAY_ROLES`` records, per situation, what new information
  the takeaway adds. It is pinned to the exact text, so any copy change fails
  until someone re-reads the pair and updates the record. Phrase checks alone
  cannot prove two sentences carry different ideas (Codex, second review).
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

# situation -> (exact takeaway, role, what it adds beyond the tendency)
TAKEAWAY_ROLES: dict[str, tuple[str, str, str]] = {
    "missing-context": (
        "Tin nhắn ngắn không có nghĩa là người kia đang khó chịu với bạn.",
        "reframe",
        "another explanation for a short reply than annoyance",
    ),
    "too-many-open-loops": (
        "Mỗi lần chuyển việc, bạn mất thêm thời gian để nhớ lại mình đang làm tới đâu.",
        "consequence",
        "the switching cost of starting new tasks",
    ),
    "changed-plan": (
        "Một lịch hẹn bị đổi thường kéo theo cả ngày của bạn, không chỉ một buổi gặp.",
        "consequence",
        "a moved appointment ripples through the whole day",
    ),
    "comparison-loop": (
        "Thứ người khác đăng lên thường là khoảnh khắc đẹp nhất, không phải cả quá trình.",
        "reframe",
        "posts show highlights, not the process being compared",
    ),
    "automatic-caretaking": (
        "Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.",
        "consequence",
        "your own work piles up, not just 'capacity is limited'",
    ),
    "decision-fatigue": (
        "Khó chọn lúc mệt không có nghĩa là bạn thiếu quyết đoán.",
        "reframe",
        "difficulty comes from tiredness, not a personality flaw",
    ),
    "perfect-before-start": (
        "Người đọc cần một bản nháp, không cần một bản hoàn hảo.",
        "reframe",
        "what the reader actually needs to give feedback",
    ),
    "group-pressure": (
        "Chỗ chưa hiểu hôm nay thường quay lại thành việc phải làm lại sau.",
        "consequence",
        "unclear parts come back as rework",
    ),
    "avoid-small-conflict": (
        "Một câu đồng ý cho xong dễ làm người kia hiểu sai điều bạn muốn.",
        "consequence",
        "the other person misreads what you want",
    ),
    "defend-old-choice": (
        "Đã tốn nhiều công sức không phải lý do để giữ một cách chưa ổn.",
        "reframe",
        "effort already spent is not evidence the method works",
    ),
    "capacity-before-agreement": (
        "Nhận thêm khi lịch đã kín thường khiến việc nào cũng bị làm vội.",
        "consequence",
        "every task gets rushed, not just 'time is limited'",
    ),
    "quick-reply": (
        "Câu bật ra đầu tiên chưa chắc là điều bạn thật sự muốn nói.",
        "reframe",
        "the first reaction differs from what you mean",
    ),
    "repair-reply": (
        "Lỡ nói gắt một câu không có nghĩa là cả cuộc trò chuyện đã hỏng.",
        "reframe",
        "one harsh line does not ruin the conversation",
    ),
    "specific-feedback": (
        "Người đọc thường góp ý theo điều họ thấy, không theo điều bạn đang lo.",
        "reframe",
        "why a vague request gets feedback on the wrong part",
    ),
    "name-the-need": (
        "Lời than mệt thường chỉ nhận lại lời an ủi, chưa phải sự giúp đỡ.",
        "consequence",
        "saying you are tired brings comfort, not concrete help",
    ),
}
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


def test_every_takeaway_has_a_reviewed_information_role() -> None:
    assert set(TAKEAWAY_ROLES) == set(_ISSUES)
    for key, (text, role, adds) in TAKEAWAY_ROLES.items():
        # Changing a takeaway means re-reading it against its tendencies here.
        assert _ISSUES[key].takeaway == text, (key, "re-review TAKEAWAY_ROLES")
        assert role in {"consequence", "reframe"}, key
        assert adds, key
