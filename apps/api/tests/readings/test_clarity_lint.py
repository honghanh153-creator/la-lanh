"""Layer A plain-language rules (docs/research/2026-11-01-content-clarity-gate.md, section 3)."""

from typing import Any

import pytest

from app.domains.readings.clarity_lint import (
    RULES,
    ClarityDocument,
    SurfaceReport,
    baseline_document,
    count_coined_labels,
    count_jargon,
    count_long_sentences,
    count_meta_talk,
    count_past_action_claims,
    count_placeholders,
    english_words,
    excess_engine_metaphors,
    excess_hedges,
    lint_document,
    lint_surface,
    near_duplicate_pairs,
    ratchet_regressions,
    sentences,
    shared_sentences,
    syllables,
)


def _doc(*texts: str, sample_id: str = "s1", variant: str = "default") -> ClarityDocument:
    return ClarityDocument(
        surface="tarot",
        sample_id=sample_id,
        variant=variant,
        sections=tuple((f"part_{index}", text) for index, text in enumerate(texts)),
    )


def test_sentences_split_on_end_punctuation_and_count_syllables() -> None:
    parts = sentences("Bạn nghỉ sớm. Mai nói tiếp nhé!\nCâu ba…")
    assert parts == ("Bạn nghỉ sớm.", "Mai nói tiếp nhé!", "Câu ba…")
    assert syllables("Mặt Trời ở Bạch Dương · Nhà 10") == 7


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Góc đối đỉnh gần nhất với Saturn tạo thêm một điểm kéo-ngược cần điều tiết.", 1),
        ("Mặt Trời ở Bạch Dương · Nhà 10: bạn sáng rõ hơn khi bắt đầu sớm.", 1),
        ("Sao Kim tam hợp Sao Hỏa, orb 1.4°.", 3),
        ("Mặt Trăng nằm trong nakshatra Ashwini, pada 2.", 2),
        ("Bạn hay trả lời tin nhắn ngay cả khi đang bận.", 0),
        ("Nhà bạn ở gần trường, nên sáng nào cũng đi bộ.", 0),
    ),
)
def test_a1_counts_astrology_and_engine_terms(text: str, expected: int) -> None:
    assert count_jargon(text) == expected


def test_a1_still_counts_a_term_explained_in_the_next_sentence() -> None:
    # Current behaviour, documented on purpose: the CDC-7 refinement (a term followed by its plain
    # meaning for "bạn") is TODO(A1+), so an explained term still counts today.
    text = "Sao Thổ tam hợp Sao Kim của bạn. Nghĩa là bạn giữ lời hẹn dễ hơn."
    assert count_jargon(text) == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Hai bạn đang ở mức Bắt sóng, còn chỗ Lực cấn thì cần nói rõ.", 2),
        ("Mở Trạm Bắt Sóng để xem Bản đồ Lá của hai bạn.", 2),
        ("Hai bạn dễ hiểu ý nhau khi nói chuyện về kế hoạch cuối tuần.", 0),
    ),
)
def test_a2_counts_coined_labels(text: str, expected: int) -> None:
    assert count_coined_labels(text) == expected


def test_a3_allows_two_engine_metaphors_per_reading() -> None:
    assert excess_engine_metaphors("Hai bạn khác nhịp. Tín hiệu này rõ.") == 0
    text = "Hai bạn khác nhịp. Tín hiệu này chạm vào lớp sâu, tạo một vùng năng lượng."
    assert excess_engine_metaphors(text) == 4
    assert excess_engine_metaphors("Bạn bắt sóng nhanh.") == 0  # A2 label, not double counted


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Phần dưới chỉ ra lúc nó căng; mở phần dưới để xem cách gỡ.", 2),
        ("Ý chính của lá: sợ phản ứng của người kia.", 1),
        ("Mặt Trời không nói bạn là gì; nó mô tả cách bạn chủ động.", 1),
        ("Ví dụ: với người kia.", 1),
        ("Bạn sợ người kia phản ứng nên chưa nói điều mình cần.", 0),
    ),
)
def test_a4_counts_talk_about_the_reading_or_app(text: str, expected: int) -> None:
    assert count_meta_talk(text) == expected


def test_a5_catches_a_summary_that_restates_the_meaning() -> None:
    summary = "Tám Kiếm: Sợ phản ứng của người kia nên bạn chưa dám nói điều mình cần."
    meaning = "Ý chính của lá: sợ phản ứng của người kia nên bạn chưa dám nói điều mình cần."
    assert near_duplicate_pairs((summary, meaning)) == 1
    assert lint_document(_doc(summary, meaning))["A5"] == 1


def test_a5_ignores_distinct_and_short_sentences() -> None:
    assert (
        near_duplicate_pairs(
            (
                "Bạn muốn trả lời ngay để người kia khỏi chờ lâu.",
                "Tối nay hãy để điện thoại ngoài phòng ngủ trước mười giờ.",
            )
        )
        == 0
    )
    assert near_duplicate_pairs(("Thử hỏi lại.", "Thử hỏi lại.")) == 0


def test_a6_counts_sentences_in_more_than_a_fifth_of_readings() -> None:
    shared = "Đây là câu dùng chung cho rất nhiều bài."
    pair = "Câu này chỉ có trong hai bài thôi."
    docs = [
        _doc(f"Bài số {index} nói về một chuyện riêng của bạn.", sample_id=f"s{index}")
        for index in range(10)
    ]
    docs[0] = _doc(shared, pair, sample_id="s0")
    docs[1] = _doc(shared, pair, sample_id="s1")
    docs[2] = _doc(shared, sample_id="s2")
    # 3/10 > 20% counts; 2/10 is exactly 20% and does not. Numbers are normalised, so the
    # "Bài số N" template sentence is one sentence seen in 7/10 readings.
    assert shared_sentences(docs) == (
        "bài số # nói về một chuyện riêng của bạn",
        "đây là câu dùng chung cho rất nhiều bài",
    )
    report = lint_surface("tarot", docs)
    assert report.rules["A6"] == 2
    assert report.readings_flagged["A6"] == 10


def test_a7_hedges_above_three_per_ten_sentences() -> None:
    assert excess_hedges("Bạn có thể thấy mệt. Có lẽ bạn dễ bỏ cuộc.", 2) == 3
    text = "Bạn thấy mệt sau giờ làm. Bạn nghỉ mười phút. Bạn đi bộ. Bạn có thể ngủ sớm."
    assert excess_hedges(text, 4) == 0
    assert lint_document(_doc(text))["A7"] == 0


def test_a8_flags_sentences_longer_than_25_syllables() -> None:
    twenty_five = " ".join(["một"] * 24) + " câu."
    twenty_six = " ".join(["một"] * 25) + " câu."
    assert count_long_sentences((twenty_five,)) == 0
    assert count_long_sentences((twenty_six,)) == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Chart của bạn có mood khá flirt.", ("chart", "mood", "flirt")),
        ("Góc vuông với Saturn và True_Node.", ("saturn", "true", "node")),
        ("Mini test, check nhẹ một nhịp.", ("mini", "test", "check")),
        ("Vibe hôm nay nhẹ, Radar và Luna đều nghỉ.", ()),
        ("Con cho nha minh nghi som", ()),  # unaccented Vietnamese is not English
    ),
)
def test_a10_finds_english_words(text: str, expected: tuple[str, ...]) -> None:
    assert english_words(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Phần giải nghĩa riêng chưa sẵn sàng.", 1),
        ("Nội dung đang cập nhật.", 1),
        ("TODO viết lại câu này.", 1),
        ("Bạn hợp với {partner_name}.", 1),
        ("Bạn đã sẵn sàng nói chuyện với người kia.", 0),
    ),
)
def test_a11_counts_placeholders(text: str, expected: int) -> None:
    assert count_placeholders(text) == expected


@pytest.mark.parametrize(
    ("sentence", "expected"),
    (
        ("Tin nhắn vừa gửi chưa đúng cách bạn muốn nói.", 1),
        ("Bạn gửi rồi mới thấy câu mình hơi gắt.", 1),
        ("Bạn đã gửi lời đăng ký và cứ kiểm hộp thư.", 1),
        ("Nếu tin nhắn vừa gửi chưa đúng ý, bạn nói lại một câu ngắn.", 0),
        ("Khi đã gửi xong, bạn úp điện thoại xuống mười phút.", 0),
        ("Bạn gửi một tin ngắn trước giờ ăn tối.", 0),
    ),
)
def test_a14_flags_a_past_action_stated_as_fact(sentence: str, expected: int) -> None:
    assert count_past_action_claims((sentence,)) == expected


def test_lint_document_reports_every_rule_but_a6() -> None:
    counts = lint_document(_doc("Bạn nghỉ sớm một chút tối nay."))
    assert set(counts) == set(RULES) - {"A6"}
    assert all(value == 0 for value in counts.values())


def _report(
    surface: str = "tarot",
    *,
    samples: int = 200,
    variants: dict[str, int] | None = None,
    **rules: int,
) -> SurfaceReport:
    return SurfaceReport(
        surface=surface,
        samples=samples,
        variants=variants or {"playful_grounded": samples // 2, "roast": samples // 2},
        rules={rule: rules.get(rule, 0) for rule in RULES},
    )


def _baseline(*reports: SurfaceReport) -> dict[str, Any]:
    return baseline_document({report.surface: report for report in reports})


def test_ratchet_passes_when_counts_hold_or_fall() -> None:
    baseline = _baseline(_report(A5=10, A8=3))
    assert ratchet_regressions({"tarot": _report(A5=10, A8=3)}, baseline, minimum_samples={}) == ()
    assert ratchet_regressions({"tarot": _report(A5=4)}, baseline, minimum_samples={}) == ()


def test_ratchet_fails_when_a_count_rises() -> None:
    baseline = _baseline(_report(A5=10))
    problems = ratchet_regressions({"tarot": _report(A5=11)}, baseline, minimum_samples={})
    assert problems == ("tarot: A5 cặp câu gần trùng rose to 11 (baseline 10)",)


def test_ratchet_treats_a_zero_or_missing_baseline_as_a_hard_block() -> None:
    baseline = _baseline(_report())
    del baseline["surfaces"]["tarot"]["rules"]["A14"]
    problems = ratchet_regressions({"tarot": _report(A11=1, A14=1)}, baseline, minimum_samples={})
    assert problems == (
        "tarot: A11 placeholder rose to 1 (baseline 0)",
        "tarot: A14 khẳng định việc đã xảy ra rose to 1 (baseline 0)",
    )


def test_ratchet_fails_when_coverage_drops() -> None:
    baseline = _baseline(_report(samples=240), _report("radar", samples=96, variants={"crush": 96}))
    current = {
        "tarot": _report(samples=200, variants={"playful_grounded": 200}),
        "radar": _report("radar", samples=96, variants={"crush": 96}),
    }
    problems = ratchet_regressions(current, baseline, minimum_samples={"tarot": 200})
    assert problems == (
        "tarot: 200 samples, needs at least 240",
        "tarot: variant roast has 0 samples, baseline 120",
    )
    missing = ratchet_regressions(
        {"tarot": _report(samples=240)}, baseline, minimum_samples={"kham_pha": 80}
    )
    assert "kham_pha: surface is no longer reviewed" in missing
    assert "radar: surface is no longer reviewed" in missing


def test_ratchet_enforces_the_spec_minimum_even_with_a_lower_baseline() -> None:
    baseline = _baseline(_report(samples=30))
    problems = ratchet_regressions(
        {"tarot": _report(samples=30)}, baseline, minimum_samples={"tarot": 200}
    )
    assert problems == ("tarot: 30 samples, needs at least 200",)
