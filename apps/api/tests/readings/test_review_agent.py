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


def test_release_review_covers_daily_natal_and_tarot_for_all_ten_personas() -> None:
    samples = build_synthetic_samples()

    assert len(samples) == PERSONA_COUNT * 3 == 30
    assert {sample.persona_id for sample in samples} == {
        f"persona-{index:02d}" for index in range(1, PERSONA_COUNT + 1)
    }
    for persona_id in {sample.persona_id for sample in samples}:
        assert {sample.surface for sample in samples if sample.persona_id == persona_id} == {
            "daily",
            "natal",
            "tarot",
        }
    assert all(sample.evidence_validated for sample in samples)


@pytest.mark.parametrize(
    "retired_phrase",
    (
        "pattern này",
        "điều đang chạy bên dưới",
        "một cách khác để thử",
        "một việc chưa hoàn hảo có thể nằm yên",
        "giành phần ưu tiên",
        "mối liên hệ này rõ và dễ nhận ra ngoài đời",
    ),
)
def test_review_agent_rejects_retired_abstract_copy(retired_phrase: str) -> None:
    result = ContentReviewAgent().review(
        (
            _sample(
                scene=(
                    f"Khi một người trả lời ngắn hơn thường lệ, {retired_phrase} có thể xuất hiện."
                )
            ),
        )
    )

    assert result.passed is False
    assert "retired-or-abstract-copy" in {finding.rule_id for finding in result.findings}


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


def test_review_agent_rejects_opaque_or_translated_copy() -> None:
    result = ContentReviewAgent().review(
        (
            _sample(
                scene=(
                    "Khi lịch đổi vào phút cuối, cơ chế này có thể khiến bạn "
                    "giữ nhịp cũ thay vì hỏi lại ưu tiên."
                )
            ),
        )
    )

    assert result.passed is False
    assert "opaque-or-translated-copy" in {finding.rule_id for finding in result.findings}


def test_review_agent_rejects_dense_or_repeated_sentences() -> None:
    dense = (
        "Khi một người trả lời ngắn hơn thường lệ, bạn có thể dừng lại, xem lại toàn bộ "
        "cuộc trò chuyện, nhớ những lần trước, tự đoán thêm nguyên nhân và tiếp tục chờ "
        "thay vì hỏi thẳng điều vừa thay đổi."
    )
    repeated = "Thử hỏi một câu rõ để kiểm tra. Thử hỏi một câu rõ để kiểm tra."
    sample = replace(
        _sample(),
        sections=(("hook", "Nói câu chính trước."), ("scene", dense), ("action", repeated)),
    )

    result = ContentReviewAgent().review((sample,))

    assert {finding.rule_id for finding in result.findings} >= {
        "sentence-too-dense",
        "repeated-sentence",
    }


def test_review_agent_rejects_sentence_repeated_across_headline_and_body() -> None:
    repeated = "Bạn muốn được lắng nghe trước khi phải giải thích thêm."
    sample = replace(
        _sample(),
        surface="natal",
        sections=(
            ("hook", repeated),
            ("thesis", f"{repeated} Hai nhu cầu này đang kéo bạn về hai phía."),
            (
                "scene",
                "Khi một người trả lời ngắn hơn thường lệ, bạn có thể dừng lại "
                "trước khi đoán ý họ.",
            ),
            ("action", "Hỏi một câu rõ để kiểm tra điều đang xảy ra."),
        ),
    )

    result = ContentReviewAgent().review((sample,))

    assert "repeated-sentence-across-sections" in {finding.rule_id for finding in result.findings}


def test_review_agent_accepts_each_tarot_position_as_its_own_scene_and_action() -> None:
    tarot_sample = replace(
        _sample(),
        surface="tarot",
        sections=(
            ("headline", "Tách điều đã xảy ra khỏi điều bạn đang đoán."),
            (
                "scene_clear",
                "Khi tin nhắn đến chậm, bạn có thể đọc lại đúng câu đã được gửi trước đó.",
            ),
            ("action_clear", "Viết một dòng về điều bạn đã biết chắc."),
            (
                "scene_next",
                "Khi hai người nói chuyện tiếp, bạn có thể nghe xem câu trả lời có rõ hơn không.",
            ),
            ("action_next", "Hỏi một câu có thể được trả lời thẳng."),
        ),
    )

    result = ContentReviewAgent().review((tarot_sample,))

    assert result.passed is True


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


def test_review_agent_rejects_advice_that_leaks_into_scene() -> None:
    result = ContentReviewAgent().review(
        (
            _sample(
                scene=(
                    "Khi một người trả lời ngắn hơn thường lệ, hãy hỏi ngay xem họ đang nghĩ gì."
                )
            ),
        )
    )

    assert "advice-inside-scene" in {finding.rule_id for finding in result.findings}


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
