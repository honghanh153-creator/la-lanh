import re
from datetime import date, timedelta

from app.domains.astro.models import DateOnlySunResult, EngineProvenance, ZodiacSign
from app.domains.readings.daily_psychology import (
    DAILY_ISSUES,
    DAILY_PSYCHOLOGY_MATRIX_VERSION,
    PSYCHOLOGY_SOURCES,
    issue_source_ids,
    source_ids,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import BackgroundLens, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer


def _date_only() -> DateOnlySunResult:
    return DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.CANCER,
        candidates=(ZodiacSign.CANCER,),
        provenance=EngineProvenance(version="2.10.03", profile="psychology-matrix-test"),
    )


def test_psychology_source_registry_has_ten_bounded_editorial_anchors() -> None:
    assert len(PSYCHOLOGY_SOURCES) == len(source_ids()) == 10
    assert issue_source_ids() <= source_ids()
    assert all(source.editorial_use and source.guardrail for source in PSYCHOLOGY_SOURCES)
    assert all(issue.source_ids for issue in DAILY_ISSUES)


def test_daily_matrix_replays_same_day_and_keeps_scene_separate_from_advice() -> None:
    plan = ReadingPlanner().plan(
        _date_only(),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed="2026-10-02",
    )
    renderer = DeterministicVietnameseRenderer()

    first = renderer.render(plan)
    second = renderer.render(plan)

    assert first == second
    assert first.semantic_blueprint is not None
    assert first.semantic_blueprint.scene_key.startswith("psychology:")
    assert first.semantic_blueprint.action_key.startswith("psychology:")
    assert not re.search(
        r"(?:^|[.!?]\s+)(?:hãy|thử|nên|đừng)\s+",
        f"{first.hook} {first.manifestation}",
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"(?:hỏi|viết|đợi|đọc|chọn|đặt|tắt|nói|giảm|hoãn|gửi|nhờ|xin|thử)",
        first.micro_action,
        flags=re.IGNORECASE,
    )
    assert evaluate_candidate(plan, first).accepted is True


def test_daily_matrix_produces_365_distinct_accepted_cards_without_history() -> None:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    start = date(2026, 10, 2)
    cards: set[tuple[str, str, str]] = set()

    for offset in range(365):
        plan = planner.plan(
            _date_only(),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=(start + timedelta(days=offset)).isoformat(),
        )
        candidate = renderer.render(plan)
        assert evaluate_candidate(plan, candidate).accepted is True
        cards.add((candidate.hook, candidate.manifestation, candidate.micro_action))

    assert len(cards) == 365


def test_each_user_selected_context_gets_a_concrete_matching_scene() -> None:
    markers = {
        BackgroundLens.RELATIONSHIPS: ("mối quan hệ", "người kia"),
        BackgroundLens.COMMUNICATION: ("cuộc nói chuyện", "đoạn chat"),
        BackgroundLens.WORK: ("công việc", "chuyện học"),
        BackgroundLens.ENERGY: ("cơ thể", "quá tải"),
        BackgroundLens.SELF_CARE: ("chăm mình", "nghỉ ngơi"),
    }
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()

    for lens, expected in markers.items():
        plan = planner.plan(
            _date_only(),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-10-02",
            background_lens=lens,
        )
        candidate = renderer.render(plan)
        assert any(marker in candidate.manifestation.casefold() for marker in expected)
        assert evaluate_candidate(plan, candidate).accepted is True


def test_reading_detail_does_not_replace_astrology_with_daily_psychology() -> None:
    plan = ReadingPlanner().plan(_date_only(), purpose=ReadingPurpose.READING_DETAIL)

    candidate = DeterministicVietnameseRenderer().render(plan)

    assert candidate.semantic_blueprint is not None
    assert not candidate.semantic_blueprint.scene_key.startswith("psychology:")
    assert DAILY_PSYCHOLOGY_MATRIX_VERSION not in candidate.model_dump_json()
