from datetime import UTC, datetime

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    GateFailureCode,
    ReadingCandidate,
    ReadingPlan,
    ReadingPurpose,
    SemanticRequirement,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer


def _daily_candidate() -> tuple[ReadingPlan, ReadingCandidate]:
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        CalculationConfig.western_recommended(),
    )
    plan = ReadingPlanner().plan(chart, purpose=ReadingPurpose.DAILY_NOTE)
    return plan, DeterministicVietnameseRenderer().render(plan)


def test_meaning_gate_allows_clearer_prose_with_required_concept_coverage() -> None:
    plan, candidate = _daily_candidate()
    assert candidate.semantic_blueprint is not None
    blueprint = candidate.semantic_blueprint.model_copy(
        update={
            "requirements": (
                SemanticRequirement(
                    key="missing_context",
                    markers=("tin nhắn", "câu trả lời", "chưa rõ"),
                ),
            )
        }
    )
    rewritten = candidate.model_copy(
        update={
            "hook": "Một câu trả lời chưa rõ có thể khiến bạn nghĩ thêm nhiều chuyện.",
            "manifestation": (
                "Một tin nhắn ngắn hơn thường lệ dễ khiến bạn tự điền phần còn thiếu."
            ),
            "semantic_blueprint": blueprint,
        }
    )

    evaluation = evaluate_candidate(plan, rewritten)

    assert GateFailureCode.MEANING_BLUEPRINT_MISMATCH not in evaluation.failure_codes
    assert GateFailureCode.MEANING_REQUIRED_CONCEPT not in evaluation.failure_codes


def test_meaning_gate_rejects_rewrite_that_drops_required_concept() -> None:
    plan, candidate = _daily_candidate()
    assert candidate.semantic_blueprint is not None
    blueprint = candidate.semantic_blueprint.model_copy(
        update={
            "requirements": (
                SemanticRequirement(
                    key="missing_context",
                    markers=("tin nhắn", "câu trả lời", "chưa rõ"),
                ),
            )
        }
    )
    drifted = candidate.model_copy(
        update={
            "hook": "Bạn có thể muốn đổi toàn bộ kế hoạch hôm nay.",
            "manifestation": "Một lịch trình dày khiến bạn muốn bỏ bớt đầu việc.",
            "semantic_blueprint": blueprint,
        }
    )

    assert (
        GateFailureCode.MEANING_REQUIRED_CONCEPT in evaluate_candidate(plan, drifted).failure_codes
    )


def test_deterministic_renderer_emits_closed_semantic_requirements() -> None:
    plan, candidate = _daily_candidate()

    assert candidate.semantic_blueprint is not None
    assert candidate.semantic_blueprint.requirements
    assert evaluate_candidate(plan, candidate).accepted is True
