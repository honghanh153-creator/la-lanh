"""Date-only pool widening (#841 follow-up): more Sun-sign angles, pending in the registry."""

from __future__ import annotations

import re
from datetime import date
from uuid import UUID

import pytest

from app.domains.astro.models import DateOnlySunResult, ZodiacSign
from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import daily_psychology
from app.domains.readings.daily_personalization import (
    PLACEMENT_ISSUES,
    SIGN_ELEMENTS,
    SIGN_MODALITIES,
    SUN_EXTRA_ISSUES,
    SUN_ISSUES,
    SUN_MODALITY_ISSUES,
    SupportedSituation,
    eligible_daily_situations,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES, DAILY_PSYCHOLOGY_MATRIX_VERSION
from app.domains.readings.daily_rotation import VARIETY_KEY_VERSION, day_index
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import DailyVariety, ReadingPlan, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_application import _date_only_snapshot

DAY = date(2026, 11, 21)
WORDS = re.compile(r"\b(?:sẽ|chắc chắn|định mệnh|số phận|vũ trụ|năng lượng)\b", re.IGNORECASE)


def _source(sign: str) -> DateOnlySunResult:
    result = _date_only_snapshot(UUID(int=1), UUID(int=2)).result
    assert isinstance(result, DateOnlySunResult)
    zodiac = ZodiacSign(sign)
    return result.model_copy(update={"status": "certain", "sign": zodiac, "candidates": (zodiac,)})


def _plan(sign: str) -> ReadingPlan:
    return ReadingPlanner().plan(
        _source(sign),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=DAY.isoformat(),
        daily_variety=DailyVariety(
            key_version=VARIETY_KEY_VERSION,
            catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
            seed="0" * 32,
            day_index=day_index(DAY),
        ),
    )


def _base(sign: str) -> set[str]:
    return {
        SUN_ISSUES[sign],
        PLACEMENT_ISSUES["sun"][SIGN_ELEMENTS[sign]],
        SUN_MODALITY_ISSUES[SIGN_MODALITIES[sign]],
    }


def _approve(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [
        {
            "id": entry.id,
            "category": entry.category,
            "text": entry.text,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-21",
            "digest": copy_digest(entry.text),
        }
        for entry in load_registry().values()
        if entry.id.startswith("situation.sun.")
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def test_every_sign_gets_new_angles_with_plain_pending_sentences() -> None:
    registry = load_registry()
    issues = {issue.key for issue in DAILY_ISSUES}
    assert set(SUN_EXTRA_ISSUES) == set(SUN_ISSUES)
    for sign, extras in SUN_EXTRA_ISSUES.items():
        assert extras and not set(extras) & _base(sign), sign
        assert len(_base(sign) | set(extras)) == 4, sign
        for issue in extras:
            assert issue in issues
            entry = registry[f"situation.sun.{sign}.{issue}"]
            assert entry.category == "reading" and entry.status == "pending"
            text = entry.text
            assert text.startswith("Bạn ") and text.endswith(".") and text.count(".") == 1, text
            assert len(text.split()) <= 16 and not WORDS.search(text), text


@pytest.mark.parametrize("sign", tuple(SUN_ISSUES))
def test_pending_angles_never_enter_the_pool(sign: str) -> None:
    keys = {situation.issue_key for situation in eligible_daily_situations(_plan(sign))}
    assert keys == _base(sign)


@pytest.mark.parametrize("sign", tuple(SUN_ISSUES))
def test_approved_angles_give_every_sign_four_situations_and_accepted_cards(
    sign: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _approve(monkeypatch)
    plan = _plan(sign)
    situations = eligible_daily_situations(plan)
    assert len({situation.issue_key for situation in situations}) == 4
    for situation in situations:
        if situation.issue_key not in SUN_EXTRA_ISSUES[sign]:
            continue

        # Serve this angle and check the card passes the gates.
        def pick(
            _: ReadingPlan, pool: list[SupportedSituation], chosen: SupportedSituation = situation
        ) -> SupportedSituation:
            return chosen

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(daily_psychology, "_pick", pick)
            card = DeterministicVietnameseRenderer().render(plan)
        assert card.semantic_blueprint is not None
        assert card.semantic_blueprint.mechanism_key == f"psychology:{situation.issue_key}"
        assert evaluate_candidate(plan, card).accepted, (sign, situation.issue_key)
