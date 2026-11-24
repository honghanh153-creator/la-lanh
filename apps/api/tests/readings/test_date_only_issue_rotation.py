"""A birth date alone rotates two or three Daily situations, never one (#626, US-21 AC07).

The Sun sign's own situation, its element's and its modality's (cardinal, fixed, mutable), all
resting on the date-only Sun factor alone.
"""

from __future__ import annotations

from datetime import date, timedelta
from itertools import pairwise
from uuid import UUID

import pytest

from app.domains.astro.models import DateOnlySunResult, ZodiacSign
from app.domains.readings import daily_psychology
from app.domains.readings.daily_personalization import (
    PLACEMENT_ISSUES,
    SIGN_ELEMENTS,
    SIGN_MODALITIES,
    SUN_ISSUES,
    SUN_MODALITY_ISSUES,
    eligible_daily_situations,
)
from app.domains.readings.daily_psychology import (
    DAILY_PSYCHOLOGY_MATRIX_VERSION,
    FALLBACK_ISSUE_KEY,
)
from app.domains.readings.daily_rotation import (
    VARIETY_KEY_VERSION,
    daily_variety_seed,
    day_index,
    derive_variety_key,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import BackgroundLens, DailyVariety, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_application import _date_only_snapshot

KEY = derive_variety_key(b"test-only-server-secret")
GUEST = UUID("20000000-0000-4000-8000-0000000000d7")
OWNER = UUID("30000000-0000-4000-8000-0000000000d7")
START = date(2026, 11, 1)
DAYS = 29  # the persona run's window
SEED = daily_variety_seed(KEY, OWNER, DAILY_PSYCHOLOGY_MATRIX_VERSION)
SIGNS = tuple(SUN_ISSUES)
# Signs whose own situation and their element's situation are the same one: before the modality
# situation (US-21 AC07) these stayed on a single situation for the whole year.
ELEMENT_COLLISION_SIGNS = {"aries", "taurus", "cancer", "aquarius"}
# Signs where one of the three tables repeats another, so two situations rotate instead of three.
TWO_SITUATION_SIGNS = {"aries", "taurus", "gemini", "cancer", "scorpio", "aquarius"}


def _source(sign: str, status: str = "certain") -> DateOnlySunResult:
    """A made-up person who gave a birth date only, with the Sun in ``sign``."""

    result = _date_only_snapshot(GUEST, OWNER).result
    assert isinstance(result, DateOnlySunResult)
    zodiac = ZodiacSign(sign)
    return result.model_copy(update={"status": status, "sign": zodiac, "candidates": (zodiac,)})


def _variety(local_date: date, *, schedule: bool = False) -> DailyVariety:
    # ``schedule``: the topic anti-repeat (plan 2026-11-21) is on; a date-only plan then carries
    # an empty history and walks its whole pool in a fixed per-reader order.
    return DailyVariety(
        key_version=VARIETY_KEY_VERSION,
        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
        seed=SEED,
        day_index=day_index(local_date),
        topic_history=() if schedule else None,
    )


def _month_of_issues(sign: str, *, rotated: bool = True, status: str = "certain") -> list[str]:
    planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
    issues = []
    for offset in range(DAYS):
        local_date = START + timedelta(days=offset)
        plan = planner.plan(
            _source(sign, status),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=local_date.isoformat(),
            daily_variety=_variety(local_date) if rotated else None,
        )
        card = renderer.render(plan)
        assert evaluate_candidate(plan, card).accepted, (sign, local_date)
        blueprint = card.semantic_blueprint
        assert blueprint is not None
        issues.append(blueprint.mechanism_key.removeprefix("psychology:"))
    return issues


def _expected(sign: str) -> set[str]:
    return {
        SUN_ISSUES[sign],
        PLACEMENT_ISSUES["sun"][SIGN_ELEMENTS[sign]],
        SUN_MODALITY_ISSUES[SIGN_MODALITIES[sign]],
    }


def test_every_sign_has_a_modality_and_the_tables_leave_no_sign_on_one_situation() -> None:
    assert set(SIGN_MODALITIES) == set(SIGN_ELEMENTS) == set(SUN_ISSUES)
    # Three signs per modality, the same as per element.
    assert sorted(list(SIGN_MODALITIES.values()).count(m) for m in range(3)) == [4, 4, 4]
    assert {
        sign for sign in SIGNS if SUN_ISSUES[sign] == PLACEMENT_ISSUES["sun"][SIGN_ELEMENTS[sign]]
    } == ELEMENT_COLLISION_SIGNS
    assert {sign for sign in SIGNS if len(_expected(sign)) == 2} == TWO_SITUATION_SIGNS
    assert all(len(_expected(sign)) >= 2 for sign in SIGNS)


@pytest.mark.parametrize("sign", SIGNS)
def test_a_birth_date_alone_meets_every_situation_of_its_sign_in_a_month(sign: str) -> None:
    issues = _month_of_issues(sign)

    # Before #626 this was one situation on all 29 days; before the modality situation the four
    # element-collision signs still were.
    assert set(issues) == _expected(sign)
    assert len(set(issues)) == (2 if sign in TWO_SITUATION_SIGNS else 3)
    # US-21 AC05: never the same situation two days running when the pool has two or more.
    assert all(a != b for a, b in pairwise(issues))


@pytest.mark.parametrize("sign", SIGNS)
def test_plans_without_the_daily_rotation_keep_the_signs_own_situation(sign: str) -> None:
    assert set(_month_of_issues(sign, rotated=False)) == {SUN_ISSUES[sign]}


@pytest.mark.parametrize("sign", SIGNS)
def test_plans_without_the_daily_rotation_get_no_element_or_modality_situation(sign: str) -> None:
    plan = ReadingPlanner().plan(
        _source(sign),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
    )

    assert [s.rule_key for s in eligible_daily_situations(plan)] == [f"placement-sun-{sign}"]


def _unrotated_issue(sign: str, lens: BackgroundLens) -> str:
    plan = ReadingPlanner().plan(
        _source(sign),
        purpose=ReadingPurpose.DAILY_NOTE,
        background_lens=lens,
        editorial_seed=START.isoformat(),
    )
    card = DeterministicVietnameseRenderer().render(plan)
    blueprint = card.semantic_blueprint
    assert blueprint is not None
    return blueprint.mechanism_key.removeprefix("psychology:")


@pytest.mark.parametrize(
    ("sign", "lens"),
    [
        ("gemini", BackgroundLens.RELATIONSHIPS),
        ("gemini", BackgroundLens.COMMUNICATION),
        ("virgo", BackgroundLens.RELATIONSHIPS),
        ("pisces", BackgroundLens.ENERGY),
        ("pisces", BackgroundLens.SELF_CARE),
    ],
)
def test_a_lens_that_excludes_the_signs_situation_keeps_the_fallback_without_rotation(
    sign: str, lens: BackgroundLens
) -> None:
    # The lens filter runs before ranking: the element situation must not step in
    # for the fallback on plans that do not rotate.
    assert _unrotated_issue(sign, lens) == FALLBACK_ISSUE_KEY


@pytest.mark.parametrize("sign", SIGNS)
@pytest.mark.parametrize("lens", [lens for lens in BackgroundLens if lens.value != "auto"])
def test_no_lens_brings_the_element_situation_in_without_rotation(
    sign: str, lens: BackgroundLens
) -> None:
    assert _unrotated_issue(sign, lens) in {SUN_ISSUES[sign], FALLBACK_ISSUE_KEY}


def test_a_sun_on_a_sign_border_still_gets_no_sign_element_or_modality_situation() -> None:
    assert set(_month_of_issues("pisces", status="candidates")) == {FALLBACK_ISSUE_KEY}


@pytest.mark.parametrize("sign", SIGNS)
def test_the_extra_situations_rest_on_the_sun_factor_alone(sign: str) -> None:
    plan = ReadingPlanner().plan(
        _source(sign),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
        daily_variety=_variety(START),
    )
    situations = eligible_daily_situations(plan)

    assert {situation.issue_key for situation in situations} == _expected(sign)
    own = next(s for s in situations if s.rule_key == f"placement-sun-{sign}")
    for situation in situations:
        # No Moon, angle or house: the only evidence is the date-only Sun factor.
        assert situation.factor_refs == own.factor_refs
        assert len(situation.factor_refs) == 1
        assert situation.house is None
        assert situation is own or situation.rank < own.rank


def _days_of_cards(
    sign: str, days: int, *, schedule: bool = False
) -> list[tuple[int, str, str, str]]:
    """(day_index, situation, headline, scene) for ``days`` days from START."""

    return [card[:4] for card in _full_cards(sign, days, schedule=schedule)]


def _full_cards(
    sign: str, days: int, *, schedule: bool = False
) -> list[tuple[int, str, str, str, str]]:
    """(day_index, situation, headline, scene, action) for ``days`` days from START."""

    planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
    out = []
    for offset in range(days):
        local_date = START + timedelta(days=offset)
        plan = planner.plan(
            _source(sign),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=local_date.isoformat(),
            daily_variety=_variety(local_date, schedule=schedule),
        )
        card = renderer.render(plan)
        blueprint = card.semantic_blueprint
        assert blueprint is not None
        issue = blueprint.mechanism_key.removeprefix("psychology:")
        out.append((day_index(local_date), issue, card.hook, card.manifestation, card.micro_action))
    return out


@pytest.mark.parametrize("schedule", [False, True])
@pytest.mark.parametrize("sign", SIGNS)
def test_a_situation_shows_all_its_headlines_before_one_comes_back(
    sign: str, schedule: bool
) -> None:
    # A situation served every k-th day walks one fixed headline order by appearance (d // k), so
    # any 6 appearances in a row show 6 different headlines. Scenes only change between consecutive
    # appearances (they take an extra staircase step at each headline period, Codex on #778).
    # By calendar day the situation met only every k-th position of each reshuffled cycle and
    # repeated a headline after about n / 2 appearances.
    k = len(_expected(sign))
    cards = _days_of_cards(sign, 6 * 3 * 3, schedule=schedule)
    by_issue: dict[str, list[tuple[int, str, str]]] = {}
    for index, issue, headline, scene in cards:
        by_issue.setdefault(issue, []).append((index // k, headline, scene))
    assert set(by_issue) == _expected(sign)
    for issue, seen in by_issue.items():
        # Appearances are consecutive counts: one per k days, nothing skipped.
        assert [step for step, _, _ in seen] == list(range(seen[0][0], seen[0][0] + len(seen)))
        headlines = [entry[1] for entry in seen]
        for start in range(len(headlines) - 6 + 1):
            assert len(set(headlines[start : start + 6])) == 6, (sign, issue)
        # ...and exactly every 6 appearances the headlines start over in the same order.
        assert all(headlines[i] == headlines[i + 6] for i in range(len(headlines) - 6))
        # Consecutive appearances differ on every axis (US-21 AC02).
        for (_, h1, s1), (_, h2, s2) in pairwise(seen):
            assert h1 != h2 and s1 != s2, (sign, issue)


@pytest.mark.parametrize("schedule", [False, True])
@pytest.mark.parametrize("sign", SIGNS)
def test_a_whole_card_never_comes_back_within_90_days(sign: str, schedule: bool) -> None:
    # Codex auto-1 on #778: fixed orders walked side by side repeat the whole card after the least
    # common multiple of the axis sizes (24 appearances for 6, 8 and 24 lines: 48 days for a
    # two-situation sign). US-21 AC03 asks for at least 90 days.
    # With the topic schedule (plan 2026-11-21, Codex P2 on #841) the appearance index is the
    # global ``day_index // len(pool)``, never a count that restarts with a block.
    cards = _full_cards(sign, 150, schedule=schedule)
    last: dict[tuple[str, str, str, str], int] = {}
    for index, issue, headline, scene, action in cards:
        key = (issue, headline, scene, action)
        if key in last:
            assert index - last[key] >= 90, (sign, key, index - last[key])
        last[key] = index


def _repeats_within_a_week(cards: list[tuple[int, str, str, str]]) -> int:
    return sum(
        1
        for i, (_, issue, headline, _) in enumerate(cards)
        if any(c[1] == issue and c[2] == headline for c in cards[max(0, i - 6) : i])
    )


@pytest.mark.parametrize("sign", ["virgo", "libra", "aries", "scorpio"])
def test_headlines_come_back_less_often_than_with_calendar_day_rotation(
    sign: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    by_appearance = _repeats_within_a_week(_days_of_cards(sign, 58))
    monkeypatch.setattr(daily_psychology, "_occurrence_index", lambda plan, pool: None)
    by_calendar_day = _repeats_within_a_week(_days_of_cards(sign, 58))

    # A headline now comes back only after the situation's other five: 12 or 18 days later.
    assert by_appearance == 0
    assert by_calendar_day > 0
