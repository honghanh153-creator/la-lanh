"""More than one line of Lá per Daily issue (#626): pool, pick by day, storage, both voices."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from typing import Any
from uuid import UUID

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import DateOnlySunResult, ZodiacSign
from app.domains.birth.models import BirthSnapshotRecord
from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import companion_pool as companion
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.companion import (
    COMPANION_ISSUE_LINES,
    CompanionLine,
    companion_issue_entry,
)
from app.domains.readings.companion_pool import (
    COMPANION_LINE_PREFIX,
    COMPANION_LINE_VOICES,
    companion_pool_slot,
    daily_companion_line,
    extra_line_problems,
    extra_lines_by_issue,
    roast_companion_line,
)
from app.domains.readings.daily_psychology import DAILY_PSYCHOLOGY_MATRIX_VERSION
from app.domains.readings.daily_rotation import (
    DAILY_TOP_K,
    VARIETY_KEY_VERSION,
    daily_variety_seed,
    day_index,
    derive_variety_key,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    COMPANION_CANDIDATE_SCHEMA_VERSION,
    DailyVariety,
    ReadingCandidate,
    ReadingPurpose,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.voice import ReadingVoice
from scripts.persona_metrics import repeats_ever
from tests.readings.test_application import MemoryReadingRepository
from tests.readings.test_application import _date_only_snapshot as _pisces_snapshot
from tests.readings.test_voice import BANNED_WORDS, _contains_word


def _date_only_snapshot(guest_id: UUID, profile_id: UUID) -> BirthSnapshotRecord:
    """A made-up person with a birth date only who meets ONE issue every day.

    Since the wider date-only rotation (#626) most signs take turns between two issues. Cancer's
    own issue and its element's issue are the same one, so this person still meets one issue a
    day, which is what the line-pool tests below measure.
    """

    snapshot = _pisces_snapshot(guest_id, profile_id)
    assert isinstance(snapshot.result, DateOnlySunResult)
    result = snapshot.result.model_copy(
        update={"sign": ZodiacSign.CANCER, "candidates": (ZodiacSign.CANCER,)}
    )
    return replace(snapshot, result=result)


KEY = derive_variety_key(b"test-only-server-secret")
GUEST = UUID("20000000-0000-4000-8000-0000000000c6")
OWNER = UUID("30000000-0000-4000-8000-0000000000c6")
START = date(2026, 11, 1)
DAYS = 29  # the persona run's window
MAX_REPEAT_SHARE = 0.20  # threshold "Lời của Lá lặp ≤ 20% số ngày"
SEED = daily_variety_seed(KEY, OWNER, DAILY_PSYCHOLOGY_MATRIX_VERSION)
REGISTRY_LINES = {
    key: entry for key, entry in load_registry().items() if key.startswith(COMPANION_LINE_PREFIX)
}


@pytest.fixture(autouse=True)
def _selection_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pick is deferred in the product (decision D); these tests cover it behind the switch."""

    monkeypatch.setattr(companion, "EXTRA_LINE_SELECTION_ENABLED", True)


def _variety(local_date: date) -> DailyVariety:
    return DailyVariety(
        key_version=VARIETY_KEY_VERSION,
        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
        seed=SEED,
        day_index=day_index(local_date),
    )


def _pair(
    issue: str, number: int, direct: str, roast: str, *, pending: str | None = None
) -> list[dict[str, Any]]:
    entries = []
    for voice, text in (("direct", direct), ("roast", roast)):
        entry: dict[str, Any] = {
            "id": f"{COMPANION_LINE_PREFIX}{issue}.{number:02d}.{voice}",
            "category": "reading",
            "text": text,
            "status": "pending",
        }
        if voice != pending:
            entry.update(
                status="approved", approver="codex", date="2026-11-17", digest=copy_digest(text)
            )
        entries.append(entry)
    return entries


def _use(monkeypatch: pytest.MonkeyPatch, entries: list[dict[str, Any]]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _synthetic_pool(size: int) -> dict[str, tuple[CompanionLine, ...]]:
    """``size`` made-up extra pairs for every issue (test data, never served)."""

    return {
        issue: tuple(
            CompanionLine(f"Câu thử {issue} số {n}.", f"Câu khịa thử {issue} số {n}.")
            for n in range(size)
        )
        for issue in COMPANION_ISSUE_LINES
    }


def _line_shown(candidate: ReadingCandidate) -> str:
    blueprint = candidate.semantic_blueprint
    assert blueprint is not None
    return candidate.companion or companion_issue_entry(blueprint.mechanism_key).line.direct


def _month_of_lines() -> list[str]:
    """Lá's line on 29 days in a row for one made-up person who gave a birth date only."""

    source = _date_only_snapshot(GUEST, OWNER).result
    planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
    lines = []
    for offset in range(DAYS):
        local_date = START + timedelta(days=offset)
        plan = planner.plan(
            source,
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=local_date.isoformat(),
            daily_variety=_variety(local_date),
        )
        lines.append(_line_shown(renderer.render(plan)))
    return lines


# ------------------------------------------------------------------ AC2: 29 days, one person


def test_selection_is_deferred_so_no_extra_line_is_served_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Decision D (17.11.2026, Codex r2 on #657): until the owner decides how Lá knows the line of
    # an issue's last appearance, approved pairs are not served and Lá keeps the authored line.
    monkeypatch.setattr(companion, "EXTRA_LINE_SELECTION_ENABLED", False)
    monkeypatch.setattr(companion, "extra_lines_by_issue", lambda: _synthetic_pool(3))
    for offset in range(2 * DAILY_TOP_K):
        variety = _variety(START + timedelta(days=offset))
        assert daily_companion_line("psychology:missing-context", variety) is None
    plan = ReadingPlanner().plan(
        _date_only_snapshot(GUEST, OWNER).result,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
        daily_variety=_variety(START),
    )
    card = DeterministicVietnameseRenderer().render(plan)
    assert card.companion is None and card.companion_roast is None
    assert "companion" not in card.model_dump()


def test_the_shipped_default_keeps_selection_off() -> None:
    from pathlib import Path

    source = Path(companion.__file__).read_text(encoding="utf-8")
    assert "\nEXTRA_LINE_SELECTION_ENABLED = False\n" in source


def test_la_repeats_on_at_most_a_fifth_of_29_days_once_the_pool_is_deep_enough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Same rule as the persona report: a day repeats when its line was shown before.
    before = _month_of_lines()
    assert repeats_ever(before) / DAYS > MAX_REPEAT_SHARE  # one line per issue: the #626 failure

    # A person with a birth date only meets one issue every day, so the pool has to hold the
    # month by itself. 23 extra lines + the authored one: 24 different lines in 29 days.
    monkeypatch.setattr(companion, "extra_lines_by_issue", lambda: _synthetic_pool(23))
    after = _month_of_lines()

    assert repeats_ever(after) / DAYS <= MAX_REPEAT_SHARE
    assert len(set(after)) >= 24


def test_two_lines_per_issue_already_alternate_day_by_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(companion, "extra_lines_by_issue", lambda: _synthetic_pool(1))
    lines = _month_of_lines()

    # This person meets one issue every day: two lines alternate day by day.
    assert all(a != b for a, b in pairwise(lines))


# ------------------------------------------------------------------ the pick


@pytest.mark.parametrize("size", [2, 3, 5, 8])
def test_two_days_fewer_than_n_apart_never_show_the_same_line(size: int) -> None:
    # Codex r1 on #657: the pick follows the calendar day, not a count of appearances, so the
    # guarantee holds for any pattern of appearances (transits, the anti-repeat guard), not only
    # for an issue served every ``period`` days.
    issue = "missing-context"
    pool = _synthetic_pool(size - 1)

    def shown(day: int) -> str | None:
        line = daily_companion_line(f"psychology:{issue}", _variety(START + timedelta(days=day)))
        return None if line is None else line.direct

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(companion, "extra_lines_by_issue", lambda: pool)
        served = [shown(day) for day in range(size * 4)]

    for a in range(len(served)):
        for b in range(a + 1, min(a + size, len(served))):
            assert served[a] != served[b], (size, a, b)
    # Irregular appearances (Codex's example: days 300 and 302 with day 301 on another issue)
    # get different lines once the pool has more than two lines.
    if size > 2:
        assert served[0] != served[2]
    # The authored line (stored as "no extra line") is one of the pool, not skipped.
    assert served.count(None) == 4


def test_the_order_differs_between_people_and_issues_and_is_stable() -> None:
    other = daily_variety_seed(KEY, GUEST, DAILY_PSYCHOLOGY_MATRIX_VERSION)
    orders = {
        (seed, issue): tuple(companion_pool_slot(seed, issue, 6, n) for n in range(6))
        for seed in (SEED, other)
        for issue in ("missing-context", "quick-reply")
    }

    assert all(sorted(order) == list(range(6)) for order in orders.values())
    assert len(set(orders.values())) > 1
    assert orders[(SEED, "quick-reply")] == tuple(
        companion_pool_slot(SEED, "quick-reply", 6, n + 6) for n in range(6)
    )
    with pytest.raises(ValueError):
        companion_pool_slot(SEED, "quick-reply", 6, -1)


def test_nothing_changes_without_rotation_or_without_an_approved_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    variety = _variety(START)
    _use(monkeypatch, [])
    assert daily_companion_line("psychology:missing-context", variety) is None

    monkeypatch.setattr(companion, "extra_lines_by_issue", lambda: _synthetic_pool(3))
    assert daily_companion_line("psychology:missing-context", None) is None
    assert daily_companion_line("natal:sun", variety) is None
    assert daily_companion_line(None, variety) is None
    assert daily_companion_line("psychology:unknown", variety) is None


# ------------------------------------------------------------------ which pairs are served

GOOD = ("Chưa rõ thì hỏi lại một câu cho chắc.", "Đoán mãi chi cho mệt, hỏi một câu là xong.")


def test_a_pair_is_served_only_when_both_sentences_are_approved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _use(monkeypatch, _pair("missing-context", 1, *GOOD))
    assert extra_lines_by_issue() == {"missing-context": (CompanionLine(*GOOD),)}
    assert roast_companion_line(GOOD[0]) == GOOD[1]

    for voice in COMPANION_LINE_VOICES:
        _use(monkeypatch, _pair("missing-context", 1, *GOOD, pending=voice))
        assert extra_lines_by_issue() == {}
        assert roast_companion_line(GOOD[0]) == GOOD[0]


@pytest.mark.parametrize(
    ("direct", "roast", "problem"),
    [
        ("Uống nước rồi nghỉ sớm nhé.", GOOD[1], "direct missing_nudge"),
        ("Hỏi lại chỉ mất thời gian, trả lời luôn nhé.", GOOD[1], "direct negated_nudge"),
        ("Hỏi một câu, xong cứ đoán phần còn lại.", GOOD[1], "direct contrary_nudge"),
        (GOOD[0], GOOD[0], "roast must differ from direct"),
        (GOOD[0] + " " + "Hỏi lại nhé. " * 6, GOOD[1], "direct has"),
        ("Hỏi lại đi, số phận sẽ trả lời.", GOOD[1], "direct uses a forbidden fragment"),
        ("Chưa rõ thì hỏi lại một câu cho chắc", GOOD[1], "direct must end with punctuation"),
        (
            COMPANION_ISSUE_LINES["missing-context"].line.direct,
            GOOD[1],
            "direct repeats an authored line",
        ),
    ],
)
def test_a_pair_that_breaks_las_rules_is_left_out(
    monkeypatch: pytest.MonkeyPatch, direct: str, roast: str, problem: str
) -> None:
    entry = COMPANION_ISSUE_LINES["missing-context"]
    assert any(
        problem in found for found in extra_line_problems(CompanionLine(direct, roast), entry)
    )
    _use(monkeypatch, _pair("missing-context", 1, direct, roast))
    assert extra_lines_by_issue() == {}


def test_unknown_issues_malformed_ids_and_repeated_text_are_left_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stray = _pair("missing-context", 1, *GOOD)
    stray[0]["id"] = f"{COMPANION_LINE_PREFIX}missing-context.direct"
    _use(
        monkeypatch,
        [
            *_pair("no-such-issue", 1, *GOOD),
            *stray,
            *_pair("missing-context", 2, *GOOD),
            *_pair("missing-context", 3, *GOOD),
        ],
    )

    assert extra_lines_by_issue() == {"missing-context": (CompanionLine(*GOOD),)}


# ------------------------------------------------------------------ the card, end to end


@pytest.mark.asyncio
async def test_an_extra_line_is_stored_with_the_card_and_voiced_as_a_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(
        repository, engine, daily_variety_key=KEY, daily_variety_from=START
    )
    snapshot = _date_only_snapshot(GUEST, OWNER)

    async def open_day(local_date: date, voice: ReadingVoice = ReadingVoice.DIRECT) -> Any:
        return await service.project(
            guest_id=GUEST,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
            requested_at=datetime.combine(local_date, time(2), UTC),
            voice=voice,
        )

    def stored(projection: Any) -> ReadingCandidate:
        record = repository.revisions[(GUEST, OWNER, projection.active.revision_id)]
        candidate = record.evaluation.publishable_candidate
        assert candidate is not None
        return candidate

    authored = {entry.line.direct for entry in COMPANION_ISSUE_LINES.values()}
    first = await open_day(START)
    assert first.active.sections.companion in authored
    assert stored(first).companion is None

    # Two approved pairs per issue (made up from the authored pair). This date-only profile
    # rotates two situations, so each comes back every second day; with one extra pair the
    # calendar-day slot would lock each situation onto one line (the reason selection is deferred,
    # decision D). Three lines per situation are walked on that rhythm.
    extras = {
        issue: CompanionLine(
            f"{entry.line.direct.rstrip('.!?…')}, bạn nhé.",
            f"{entry.line.roast.rstrip('.!?…')}, nha.",
        )
        for issue, entry in COMPANION_ISSUE_LINES.items()
    }
    seconds = {
        issue: CompanionLine(
            f"{entry.line.direct.rstrip('.!?…')}, bạn à.",
            f"{entry.line.roast.rstrip('.!?…')}, nghe.",
        )
        for issue, entry in COMPANION_ISSUE_LINES.items()
    }
    for pool in (extras, seconds):
        for issue, line in pool.items():
            assert extra_line_problems(line, COMPANION_ISSUE_LINES[issue]) == [], issue
    _use(
        monkeypatch,
        [
            entry
            for number, pool in ((1, extras), (2, seconds))
            for issue, line in pool.items()
            for entry in _pair(issue, number, line.direct, line.roast)
        ],
    )
    roasts = {line.direct: line.roast for pool in (extras, seconds) for line in pool.values()}

    extra_day = plain_day = None
    for offset in range(1, 1 + 2 * DAILY_TOP_K):
        day = START + timedelta(days=offset)
        line = (await open_day(day)).active.sections.companion
        if line in roasts and extra_day is None:
            extra_day = day
        if line in authored and plain_day is None:
            plain_day = day
    assert extra_day is not None and plain_day is not None

    opened = await open_day(extra_day)
    line = opened.active.sections.companion
    assert stored(opened).companion == line
    assert stored(opened).companion_roast == roasts[line]
    assert stored(opened).schema_version == COMPANION_CANDIDATE_SCHEMA_VERSION
    assert "companion_roast" not in opened.active.sections.model_dump()  # never sent over the API
    roast = await open_day(extra_day, ReadingVoice.ROAST)
    assert roast.active.sections.companion == roasts[line]

    # The authored first line still stays out of storage (reading-candidate/v1).
    plain = stored(await open_day(plain_day))
    assert plain.companion is None and "companion" not in plain.model_dump()

    # A card already opened keeps both voices when the pair is edited or withdrawn later
    # (Codex r1 on #657: the roast used to be looked up again on every read).
    issue = next(
        key for pool in (extras, seconds) for key, pair in pool.items() if pair.direct == line
    )
    _use(monkeypatch, _pair(issue, 1, line, "Một câu khịa đã sửa sau đó, nha."))
    assert (await open_day(extra_day, ReadingVoice.ROAST)).active.sections.companion == roasts[line]
    _use(monkeypatch, [])
    assert (await open_day(extra_day)).active.sections.companion == line
    assert (await open_day(extra_day, ReadingVoice.ROAST)).active.sections.companion == roasts[line]


def test_the_gates_read_the_extra_line_like_any_other_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _date_only_snapshot(GUEST, OWNER).result
    plan = ReadingPlanner().plan(
        source,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
        daily_variety=_variety(START),
    )
    baseline = DeterministicVietnameseRenderer().render(plan)
    assert evaluate_candidate(plan, baseline).accepted

    off_topic = baseline.model_copy(update={"companion": "Uống nước rồi nghỉ sớm nhé."})
    assert not evaluate_candidate(plan, off_topic).accepted


# ------------------------------------------------------------------ the checked-in sentences


def test_checked_in_pairs_are_complete_and_pass_las_rules_before_anyone_approves_them() -> None:
    """Pending sentences are checked here, so a batch approval can never serve a broken pair."""

    from app.domains.readings.gates import anti_influence_gate, editorial_gate, privacy_gate

    pairs: dict[tuple[str, str], dict[str, str]] = {}
    for key, entry in REGISTRY_LINES.items():
        parts = key[len(COMPANION_LINE_PREFIX) :].split(".")
        assert len(parts) == 3 and parts[0] in COMPANION_ISSUE_LINES, key
        assert parts[1].isdigit() and len(parts[1]) == 2, key
        assert parts[2] in COMPANION_LINE_VOICES, key
        assert entry.category == "reading", key
        pairs.setdefault((parts[0], parts[1]), {})[parts[2]] = entry.text
    texts = [text for pair in pairs.values() for text in pair.values()]
    assert len(texts) == len(set(texts))

    plan = ReadingPlanner().plan(
        _date_only_snapshot(GUEST, OWNER).result,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
    )
    baseline = DeterministicVietnameseRenderer().render(plan)
    for (issue, number), pair in sorted(pairs.items()):
        assert set(pair) == set(COMPANION_LINE_VOICES), (issue, number)
        line = CompanionLine(pair["direct"], pair["roast"])
        assert extra_line_problems(line, COMPANION_ISSUE_LINES[issue]) == [], (issue, number)
        for text in (line.direct, line.roast):
            assert not any(_contains_word(text, word) for word in BANNED_WORDS), text
            candidate = baseline.model_copy(update={"companion": text})
            for gate in (anti_influence_gate, editorial_gate, privacy_gate):
                assert gate(candidate).passed, (text, gate(candidate).failure_codes)
