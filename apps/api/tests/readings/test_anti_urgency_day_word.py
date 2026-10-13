"""Anti-urgency must not confuse "ngày" (day) with "ngay" (right now)."""

import pytest

from app.domains.readings.gates import anti_influence_gate
from app.domains.readings.models import GateFailureCode, ReadingCandidate, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_daily_psychology import _date_only


def _with_hook(hook: str) -> ReadingCandidate:
    plan = ReadingPlanner().plan(
        _date_only(), purpose=ReadingPurpose.DAILY_NOTE, editorial_seed="2026-10-13"
    )
    return DeterministicVietnameseRenderer().render(plan).model_copy(update={"hook": hook})


@pytest.mark.parametrize(
    "hook",
    [
        "Hãy làm ngay việc này.",
        "LÀM NGAY đi.",
        "lam ngay di.",
        "Trả lời ngay lập tức.",
        "Tra loi ngay lap tuc.",
    ],
)
def test_real_urgency_is_still_blocked(hook: str) -> None:
    assert GateFailureCode.ANTI_URGENCY in anti_influence_gate(_with_hook(hook)).failure_codes


@pytest.mark.parametrize(
    "hook",
    [
        "Nhận lời nhanh không làm ngày của bạn dài ra.",
        "Việc đó không LÀM NGÀY của bạn ngắn lại.",
    ],
)
def test_the_word_for_day_is_not_urgency(hook: str) -> None:
    assert GateFailureCode.ANTI_URGENCY not in anti_influence_gate(_with_hook(hook)).failure_codes
