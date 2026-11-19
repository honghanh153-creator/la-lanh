"""A birth date alone rotates two Daily situations, not one (#626, US-21 AC07)."""

from __future__ import annotations

from datetime import date, timedelta
from itertools import pairwise
from uuid import UUID

import pytest

from app.domains.astro.models import DateOnlySunResult, ZodiacSign
from app.domains.readings.daily_personalization import (
    PLACEMENT_ISSUES,
    SIGN_ELEMENTS,
    SUN_ISSUES,
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
# Signs whose own situation and their element's situation are the same one.
SINGLE_SITUATION_SIGNS = {"aries", "taurus", "cancer", "aquarius"}


def _source(sign: str, status: str = "certain") -> DateOnlySunResult:
    """A made-up person who gave a birth date only, with the Sun in ``sign``."""

    result = _date_only_snapshot(GUEST, OWNER).result
    assert isinstance(result, DateOnlySunResult)
    zodiac = ZodiacSign(sign)
    return result.model_copy(update={"status": status, "sign": zodiac, "candidates": (zodiac,)})


def _variety(local_date: date) -> DailyVariety:
    return DailyVariety(
        key_version=VARIETY_KEY_VERSION,
        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
        seed=SEED,
        day_index=day_index(local_date),
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
    return {SUN_ISSUES[sign], PLACEMENT_ISSUES["sun"][SIGN_ELEMENTS[sign]]}


def test_the_single_situation_signs_are_exactly_the_ones_the_tables_give() -> None:
    assert {sign for sign in SIGNS if len(_expected(sign)) == 1} == SINGLE_SITUATION_SIGNS


@pytest.mark.parametrize("sign", sorted(set(SIGNS) - SINGLE_SITUATION_SIGNS))
def test_a_birth_date_alone_meets_two_situations_in_a_month(sign: str) -> None:
    issues = _month_of_issues(sign)

    # Before #626 this was one situation on all 29 days.
    assert set(issues) == _expected(sign)
    assert len(set(issues)) == 2
    # US-21 AC05: never a third day in a row; with two situations they take turns.
    assert all(a != b for a, b in pairwise(issues))


@pytest.mark.parametrize("sign", sorted(SINGLE_SITUATION_SIGNS))
def test_a_sign_whose_element_gives_the_same_situation_stays_on_it(sign: str) -> None:
    assert set(_month_of_issues(sign)) == {SUN_ISSUES[sign]}


@pytest.mark.parametrize("sign", SIGNS)
def test_plans_without_the_daily_rotation_keep_the_signs_own_situation(sign: str) -> None:
    assert set(_month_of_issues(sign, rotated=False)) == {SUN_ISSUES[sign]}


@pytest.mark.parametrize("sign", SIGNS)
def test_plans_without_the_daily_rotation_get_no_element_situation(sign: str) -> None:
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


def test_a_sun_on_a_sign_border_still_gets_no_sign_or_element_situation() -> None:
    assert set(_month_of_issues("pisces", status="candidates")) == {FALLBACK_ISSUE_KEY}


@pytest.mark.parametrize("sign", SIGNS)
def test_the_second_situation_rests_on_the_sun_factor_alone(sign: str) -> None:
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
