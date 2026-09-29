from dataclasses import replace

import pytest

from app.domains.readings.review_agent import ContentReviewAgent, ReviewSample
from scripts.review_content_release import PERSONA_COUNT, build_synthetic_samples


def _sample(*, persona_id: str = "persona-01", scene: str | None = None) -> ReviewSample:
    return ReviewSample(
        persona_id=persona_id,
        surface="daily",
        sections=(
            ("hook", "Nói câu chính trước khi giải thích."),
            (
                "scene",
                scene
                or (
                    "Khi một người trả lời ngắn hơn thường lệ, bạn có thể dừng lại "
                    "trước khi đoán ý họ."
                ),
            ),
            ("action", "Thử hỏi một câu rõ để kiểm tra điều đang xảy ra."),
        ),
        disclaimer="Nội dung dùng để tự soi; quyền quyết định vẫn thuộc về bạn.",
        provenance_ids=("knowledge-v1",),
        evidence_validated=True,
    )


def test_review_agent_accepts_concrete_private_sample() -> None:
    result = ContentReviewAgent().review((_sample(),))

    assert result.passed is True
    assert result.findings == ()


def test_release_review_covers_daily_and_tarot_for_all_ten_personas() -> None:
    samples = build_synthetic_samples()

    assert len(samples) == PERSONA_COUNT * 2 == 20
    assert {sample.persona_id for sample in samples} == {
        f"persona-{index:02d}" for index in range(1, PERSONA_COUNT + 1)
    }
    for persona_id in {sample.persona_id for sample in samples}:
        assert {sample.surface for sample in samples if sample.persona_id == persona_id} == {
            "daily",
            "tarot",
        }
    assert all(sample.evidence_validated for sample in samples)


def test_review_agent_rejects_retired_abstract_copy() -> None:
    result = ContentReviewAgent().review(
        (_sample(scene="Trong đời thường, pattern này có thể lộ ra theo một cách nào đó."),)
    )

    assert result.passed is False
    assert {finding.rule_id for finding in result.findings} >= {
        "retired-or-abstract-copy",
        "scene-not-observable",
    }


def test_review_agent_keeps_disclaimer_out_of_core_copy() -> None:
    result = ContentReviewAgent().review(
        (
            _sample(
                scene=(
                    "Khi lịch đổi vào phút cuối, bạn cần hỏi lại ưu tiên. "
                    "Đây không phải chỉ dẫn cố định."
                )
            ),
        )
    )

    assert result.passed is False
    assert "disclaimer-inside-core-copy" in {finding.rule_id for finding in result.findings}


def test_review_agent_reports_metadata_without_source_prose() -> None:
    first = _sample(persona_id="persona-01")
    second = _sample(persona_id="persona-02")

    result = ContentReviewAgent().review((first, second))

    assert result.passed is False
    assert "duplicate-core-reading" in {finding.rule_id for finding in result.findings}
    assert all(not hasattr(finding, "prose") for finding in result.findings)


def test_review_agent_rejects_missing_or_unvalidated_evidence() -> None:
    missing = replace(
        _sample(),
        provenance_ids=(),
        evidence_validated=False,
    )

    result = ContentReviewAgent().review((missing,))

    assert {finding.rule_id for finding in result.findings} >= {
        "missing-provenance",
        "evidence-not-validated",
    }


@pytest.mark.parametrize(
    ("field", "value", "rule_id"),
    [
        ("disclaimer", "Ngắn.", "weak-disclaimer"),
        ("scene", "Một cảm giác lạ xuất hiện.", "scene-not-observable"),
        ("action", "Cứ cân nhắc thêm.", "action-not-testable"),
    ],
)
def test_review_agent_blocks_each_release_rule_in_isolation(
    field: str, value: str, rule_id: str
) -> None:
    sample = _sample()
    if field == "disclaimer":
        changed = replace(sample, disclaimer=value)
    else:
        changed = replace(
            sample,
            sections=tuple(
                (name, value if name == field else prose) for name, prose in sample.sections
            ),
        )

    result = ContentReviewAgent().review((changed,))

    assert rule_id in {finding.rule_id for finding in result.findings}
