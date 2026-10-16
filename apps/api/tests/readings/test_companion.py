"""Lời của Lá: catalog coverage, voices, projection and Luna's companion line."""

from __future__ import annotations

import re

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.readings.companion import (
    COMPANION_FALLBACK,
    COMPANION_GREETINGS,
    COMPANION_ISSUE_LINES,
    COMPANION_LOADING,
    COMPANION_MOOD_NUDGE,
    COMPANION_MOOD_REACTIONS,
    companion_issue_entry,
    nudge_failures,
    roast_companion_line,
    validate_companion_catalog,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.models import ReadingPurpose, ReadingRevisionSource
from app.domains.readings.voice import ReadingVoice
from scripts.export_companion_catalog import OUTPUT, render
from tests.readings.test_application import NOW, _exact_snapshot
from tests.readings.test_voice import BANNED_WORDS, _contains_word
from tests.readings.test_voice_generated import GUEST_ID, PROFILE_ID, _generated_active


def _every_line() -> list[str]:
    lines = [COMPANION_MOOD_NUDGE]
    for entry in (*COMPANION_ISSUE_LINES.values(), COMPANION_FALLBACK):
        lines += [entry.line.direct, entry.line.roast]
    for line in (
        *COMPANION_GREETINGS.values(),
        *COMPANION_LOADING,
        *COMPANION_MOOD_REACTIONS.values(),
    ):
        lines += [line.direct, line.roast]
    return lines


def test_catalog_covers_every_daily_issue_in_both_voices() -> None:
    assert validate_companion_catalog() == []
    assert set(COMPANION_ISSUE_LINES) == {issue.key for issue in DAILY_ISSUES}
    for key, entry in COMPANION_ISSUE_LINES.items():
        assert entry.line.direct != entry.line.roast, key
        assert roast_companion_line(entry.line.direct) == entry.line.roast
    # Unknown text (e.g. a Luna line) is never "roasted" piecemeal.
    assert roast_companion_line("Một câu Luna viết.") == "Một câu Luna viết."


def test_lines_follow_las_voice_rules() -> None:
    for line in _every_line():
        assert not any(_contains_word(line, word) for word in BANNED_WORDS), line
        assert not re.search(r"người kia (?:đang )?(?:nghĩ|giận|ghét|thích|muốn)", line), line
        assert "số phận" not in line.casefold() and "lá biết hết" not in line.casefold(), line
        assert line[-1] in ".?!…", line


def test_mechanism_key_selects_the_issue_line_or_the_fallback() -> None:
    assert (
        companion_issue_entry("psychology:missing-context")
        is COMPANION_ISSUE_LINES["missing-context"]
    )
    assert companion_issue_entry("psychology:unknown") is COMPANION_FALLBACK
    assert companion_issue_entry(None) is COMPANION_FALLBACK
    assert companion_issue_entry("natal:sun") is COMPANION_FALLBACK


def test_web_catalog_export_is_current() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render()


@pytest.mark.asyncio
async def test_daily_projection_carries_the_authored_line_in_each_voice() -> None:
    from app.domains.readings.application import ReadingApplicationService
    from tests.readings.test_application import MemoryReadingRepository

    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    snapshot = _exact_snapshot(GUEST_ID, PROFILE_ID, engine)
    direct = await service.project(
        guest_id=GUEST_ID, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE, requested_at=NOW
    )
    record = repository.revisions[(GUEST_ID, PROFILE_ID, direct.active.revision_id)]
    candidate = record.evaluation.publishable_candidate
    assert candidate is not None and candidate.semantic_blueprint is not None
    entry = companion_issue_entry(candidate.semantic_blueprint.mechanism_key)
    # Deterministic cards keep the line out of storage and take it from the catalog.
    assert candidate.companion is None
    assert direct.active.sections.companion == entry.line.direct

    roast = await service.project(
        guest_id=GUEST_ID,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        voice=ReadingVoice.ROAST,
    )
    assert roast.active.sections.companion == entry.line.roast


@pytest.mark.asyncio
async def test_luna_line_is_kept_in_direct_and_roast_uses_the_whole_baseline() -> None:
    _repository, service, deterministic, generated = await _generated_active()
    assert generated.active.source is ReadingRevisionSource.GENERATED
    # Direct: the generated card shows Luna's own line.
    assert generated.active.sections.companion is not None
    assert generated.active.sections.companion.startswith("Nè, ")
    assert generated.active.sections.companion != deterministic.active.sections.companion

    roast = await service.project(
        guest_id=GUEST_ID,
        snapshot=_exact_snapshot(GUEST_ID, PROFILE_ID, NatalChartEngine()),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        voice=ReadingVoice.ROAST,
    )
    # Roast: the voiced deterministic baseline, Lá's line included — never a mix.
    assert roast.active.sections.companion == roast_companion_line(
        deterministic.active.sections.companion or ""
    )
    assert roast.active.sections.companion != generated.active.sections.companion


def test_every_authored_line_passes_the_shared_safety_gates() -> None:
    from app.domains.readings.gates import anti_influence_gate, editorial_gate, privacy_gate
    from app.domains.readings.planner import ReadingPlanner
    from app.domains.readings.renderers import DeterministicVietnameseRenderer
    from tests.readings.test_daily_psychology import _date_only

    plan = ReadingPlanner().plan(
        _date_only(), purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-14"
    )
    baseline = DeterministicVietnameseRenderer().render(plan)
    for line in _every_line():
        candidate = baseline.model_copy(update={"companion": line})
        for gate in (anti_influence_gate, editorial_gate, privacy_gate):
            report = gate(candidate)
            assert report.passed, (line, report.failure_codes)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Không cần phải hỏi lại, đoán ý tin nhắn rồi trả lời nhé.", {"negated_nudge"}),
        ("Hỏi lại chỉ mất thời gian, trả lời luôn nhé.", {"negated_nudge"}),
        ("Hỏi lại thì phí công lắm.", {"negated_nudge"}),
        ("Đoán còn hơn hỏi.", {"negated_nudge"}),
        # Contrary on its own: the anchor is affirmed but the line also endorses guessing.
        ("Hỏi một câu, xong cứ đoán phần còn lại.", {"contrary_nudge"}),
        ("Đoán nhanh hơn hỏi nhiều.", {"contrary_nudge"}),
        # The negation / dismissal targets another action, so guessing stays endorsed.
        ("Hỏi lại nhé, không chờ trả lời cứ đoán luôn.", {"contrary_nudge"}),
        ("Hỏi lại nhé, cứ đoán cho nhanh khỏi mất thời gian.", {"contrary_nudge"}),
        ("Hỏi lại đi, chẳng ai trách nếu bạn cứ đoán.", {"contrary_nudge"}),
        ("Uống nước rồi nghỉ sớm nhé.", {"missing_nudge"}),
        # Faithful lines: negation, "thay vì" and dismissals aimed at the contrary action.
        ("Đừng đoán mà hỏi lại cho chắc.", set()),
        ("Không rõ thì hỏi lại một câu nhé.", set()),
        ("Hỏi lại thay vì tự đoán, nhẹ đầu hơn.", set()),
        ("Hỏi thẳng một chữ đi, đoán làm gì cho mệt.", set()),
        ("Hỏi lại một câu thôi, đỡ hơn đoán cả buổi.", set()),
        ("Hỏi lại không mất thời gian đâu, thử đi.", set()),
        ("Đừng cứ đoán, hỏi lại một câu nhé.", set()),
        ("Khỏi đoán, hỏi lại cho rõ nhé.", set()),
    ],
)
def test_nudge_checker_reads_each_clause(text: str, expected: set[str]) -> None:
    entry = companion_issue_entry("psychology:missing-context")
    assert expected <= set(nudge_failures(text, entry))
    if not expected:
        assert nudge_failures(text, entry) == []


def test_a_refusal_anchor_is_not_treated_as_negated() -> None:
    entry = companion_issue_entry("psychology:avoid-small-conflict")
    assert nudge_failures("Việc nào không nhận được thì nói thật nhé.", entry) == []
    assert "negated_nudge" in nudge_failures("Từ chối chỉ mất thời gian, cứ nhận đi.", entry)
