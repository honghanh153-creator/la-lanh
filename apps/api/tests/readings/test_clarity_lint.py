"""Layer A plain-language rules (docs/research/2026-11-01-content-clarity-gate.md, section 3)."""

import json
from typing import Any

import pytest

from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    RULES,
    SAFETY_RULES,
    ClarityDocument,
    RatchetException,
    SurfaceReport,
    baseline_document,
    baseline_raises,
    count_coined_labels,
    count_house_sign_aspect_words,
    count_jargon,
    count_long_sentences,
    count_meta_talk,
    count_past_action_claims,
    count_placeholders,
    count_safety,
    dump_baseline,
    effective_baseline,
    english_words,
    excess_engine_metaphors,
    excess_hedges,
    hard_zero_violations,
    keys_digest,
    lint_document,
    lint_document_keys,
    lint_surface,
    near_duplicate_pairs,
    normalize_text,
    parse_exceptions,
    ratchet_regressions,
    sentence_key,
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


@pytest.mark.parametrize(
    "text",
    (
        "Sao Thủy đi lùi nên bạn dễ nói nhầm ý.",
        "Mặt Trăng trùng tụ Sao Kim hôm nay.",
        "Cung Mọc Bọ Cạp làm bạn kín đáo hơn.",
        "Sao Hỏa xung chiếu Sao Kim, công việc hơi căng.",
        "Sao Thổ đang giao hội với Sao Kim.",
        "Chủ tinh của bạn hôm nay đổi chỗ.",
        "Thiên Đỉnh của bạn được nhắc tới.",
        "Mặt Trăng đi qua nhà thứ bảy.",
        "Mặt Trăng đi qua nhà Bảy.",
        "Góc 120 giữa Mặt Trời và Sao Mộc giúp bạn tự tin.",
    ),
)
def test_a1_counts_synonyms_of_the_listed_terms(text: str) -> None:
    assert count_jargon(text) == 1


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


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("Mặt Trăng trùng tụ Sao Kim ở nhà thứ bảy của bạn.", 2),
        ("Chủ tinh nhà Bảy đang giao hội với Sao Thổ.", 3),
        ("Sao Hỏa xung chiếu Thiên Đỉnh, cung Mọc thì yên.", 3),
        ("Mặt Trời ở Nhà 10, góc 90 với Sao Thổ, tam hợp Sao Mộc.", 3),
        ("Sao Thủy đi lùi, Sao Kim nghịch hành, hai sao lục hợp rồi vuông góc.", 4),
        ("Mặt Trời và Sao Kim đối đỉnh; Sao Hỏa đồng cung Sao Thổ.", 2),
        ("Bạn về nhà một mình, ghé nhà ba mẹ, về nhà bảy giờ, nhà hai bên đều vui.", 0),
        ("Nhà bạn có bốn người; mua nhà mười năm trước.", 0),
        ("Bạn ngồi ở góc phòng, nói chuyện với người trong nhà.", 0),
    ),
)
def test_a16_counts_house_ruler_and_aspect_words(text: str, expected: int) -> None:
    assert count_house_sign_aspect_words(text) == expected


def test_a16_is_a_ratcheted_rule_measured_per_reading() -> None:
    counts = lint_document(_doc("Sao Kim ở nhà thứ bảy.", "Chủ tinh đổi chỗ."))
    assert counts["A16"] == 2
    assert "A16" in RULES


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


def test_a6_skips_fixed_titles_but_other_rules_still_lint_them() -> None:
    title = "Đây là tiêu đề cố định của một phần"
    docs = [
        ClarityDocument(
            surface="radar",
            sample_id=f"s{index}",
            sections=(
                ("why_title", title),
                ("scene_why_title", title),
                ("why_body", f"Bài số {index} kể một chuyện rất riêng."),
            ),
        )
        for index in range(10)
    ]
    report = lint_surface("radar", docs)
    # The body template repeats (numbers are normalised); the title, seen in 10/10, does not count.
    assert shared_sentences(docs) == ("bài số # kể một chuyện rất riêng",)
    assert report.rules["A6"] == 1
    # The same title in a body section is still a shared sentence.
    body_docs = [
        ClarityDocument(surface="radar", sample_id=f"s{index}", sections=(("why_body", title),))
        for index in range(10)
    ]
    assert lint_surface("radar", body_docs).rules["A6"] == 1
    # Titles keep every other rule: a placeholder in a title is still caught.
    titled = ClarityDocument(surface="radar", sample_id="t", sections=(("why_title", "{name} ơi"),))
    assert lint_document(titled) == lint_document(_doc("{name} ơi"))


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
        ("Nguyen tien viet khuyen quynh ngoeo khuya", ()),
        ("Hôm nay hợp để healing và detox cảm xúc.", ("healing", "detox")),
        ("Đừng ghost người ta, cứ inbox nói rõ.", ("ghost", "inbox")),
        ("Lilith ở Ascendant làm bạn hơi toxic.", ("lilith", "ascendant", "toxic")),
        ("Drama chỉ là trend, giữ mindset.", ("drama", "trend", "mindset")),
        ("Check-in trước deadline nhé, mood ổn.", ("check", "deadline", "mood")),
        ("Hôm nay vibe nhẹ.", ("vibe",)),  # only the capitalised product label is allowed
        ("Bạn mở tab mới xem video, đúng kiểu plot twist.", ("tab", "video", "plot", "twist")),
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
        ("Bạn hợp với {partnerName} hôm nay.", 1),
        ("Xin chào {{ name }}.", 1),
        ("Bạn và %s nên nói chuyện.", 1),
        ("Bạn và %(name)s nên nói chuyện.", 1),
        ("Hôm nay None sẽ giúp bạn.", 1),
        ("Hôm nay undefined khá căng.", 1),
        ("Giá trị null.", 1),
        ("Bạn nhắn cho <tên người nhận> nhé.", 1),
        ("Lĩnh vực: [TÊN LĨNH VỰC] · 17h30.", 1),
        ("Bạn đã sẵn sàng nói chuyện với người kia.", 0),
        ("Khoảng 50% số việc là của bạn.", 0),
        ("Bạn mỉm cười [nhẹ thôi].", 0),
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
        ("Hôm qua bạn đã cãi nhau với người thân.", 1),
        ("Bạn vừa nhận một tin không vui.", 1),
        ("Sáng nay bạn đã gặp lại người cũ.", 1),
        ("Tuần trước sếp mới nhắn bạn về lịch.", 1),
        ("Người kia đã hứa sẽ gọi lại.", 1),
        # "lúc nãy"/"khi nãy" are past times, not condition words.
        ("Lúc nãy bạn vừa nói hơi gắt với người kia.", 1),
        ("Khi nãy tin nhắn vừa gửi chưa đúng ý.", 1),
        ("Nếu hôm qua bạn ngủ muộn, tối nay đi ngủ sớm hơn.", 0),
        # "vừa … vừa …" is "both … and …"; "đã/mới" in a relative clause is not a claim.
        ("Bạn vừa muốn hỏi lịch gặp, vừa hỏi lý do ít nhắn.", 0),
        ("Sự đáng tin đến từ việc giữ lời đã nói.", 0),
        ("Có những điều cần thời gian mới nói ra.", 0),
    ),
)
def test_a14_flags_a_past_action_stated_as_fact(sentence: str, expected: int) -> None:
    assert count_past_action_claims((sentence,)) == expected


def test_text_is_normalised_before_linting() -> None:
    assert normalize_text("a\u00a0b\u202fc") == "a b c"
    assert normalize_text("\uff33\uff41\uff54\uff55\uff52\uff4e") == "Saturn"
    assert normalize_text("x\u200by\u200dz\u202e\u2066") == "xyz"
    decomposed = "Go\u0301c đo\u0302\u0301i đi\u0309nh"
    assert normalize_text(decomposed) == "Góc đối đỉnh"


@pytest.mark.parametrize(
    "variant",
    (
        "Góc đối đỉnh với Saturn, phần dưới chỉ ra cách gỡ.",
        "Go\u0301c đo\u0302\u0301i đi\u0309nh với Saturn, phần dưới chỉ ra cách gỡ.",  # NFD
        "Góc đối\u00a0đỉnh với Saturn, phần\u00a0dưới chỉ ra cách gỡ.",  # no-break spaces
        "Góc đối đỉnh với \uff33\uff41\uff54\uff55\uff52\uff4e, phần dưới chỉ ra cách gỡ.",
    ),
)
def test_lookalike_characters_do_not_hide_a_match(variant: str) -> None:
    counts = lint_document(_doc(variant))
    assert (counts["A1"], counts["A4"], counts["A10"]) == (1, 1, 1)


def test_lint_document_reports_every_rule_but_the_surface_rules() -> None:
    counts = lint_document(_doc("Bạn nghỉ sớm một chút tối nay."))
    assert set(counts) == (set(RULES) | set(HARD_ZERO_RULES)) - {"A6", "A13"}
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
    del baseline["surfaces"]["tarot"]["rules"]["A16"]
    problems = ratchet_regressions({"tarot": _report(A10=1, A16=1)}, baseline, minimum_samples={})
    assert problems == (
        "tarot: A10 tiếng Anh rose to 1 (baseline 0)",
        "tarot: A16 chữ nhà/cung/chủ tinh/góc rose to 1 (baseline 0)",
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


def _daily(index: int, *texts: str) -> ClarityDocument:
    return ClarityDocument("daily", f"s{index}", tuple((f"p{k}", t) for k, t in enumerate(texts)))


_FILL = [_daily(i, f"Bạn đi bộ mười phút sau bữa trưa số {i}.") for i in range(10)]


def test_sentence_keys_are_short_stable_hashes_of_normalised_sentences() -> None:
    key = sentence_key("Tin nhắn vừa gửi chưa đúng ý.")
    assert len(key) == 10
    assert int(key, 16) >= 0  # hex only, no prose
    assert sentence_key("  TIN nhắn vừa gửi chưa đúng ý ") == key
    assert sentence_key(normalize_text("Tin nha\u0306\u0301n vừa gửi chưa đúng ý.")) == key
    assert sentence_key("Bài số 1.") == sentence_key("Bài số 22.")
    assert sentence_key("Tin nhắn đã gửi chưa đúng ý.") != key


def test_document_keys_name_the_violating_sentences() -> None:
    keys = lint_document_keys(
        _doc("Bạn nghỉ sớm.", "Tin nhắn vừa gửi chưa đúng ý.", "Sao Kim ở nhà thứ bảy.")
    )
    assert keys["A14"] == {sentence_key("Tin nhắn vừa gửi chưa đúng ý.")}
    assert keys["A16"] == {sentence_key("Sao Kim ở nhà thứ bảy.")}
    assert keys["A1"] == keys["A16"]
    assert keys["A8"] == frozenset()


def test_ratchet_fails_on_a_new_violation_hidden_behind_a_fix() -> None:
    # Audit loophole 1 (GT-3): fix one A10 sentence, add a different one; the count is unchanged.
    before = [_daily(0, "Bạn check lại lịch hôm nay."), *_FILL[1:]]
    after = [*_FILL[:9], _daily(9, "Tối nay bạn chill một chút.")]
    baseline = baseline_document({"daily": lint_surface("daily", before)})
    report = lint_surface("daily", after)
    assert report.rules["A10"] == baseline["surfaces"]["daily"]["rules"]["A10"] == 1
    problems = ratchet_regressions({"daily": report}, baseline, minimum_samples={})
    new_key = sentence_key("Tối nay bạn chill một chút.")
    assert problems == (
        f"daily: A10 tiếng Anh: 1 new violating sentence(s) not in the baseline ({new_key})",
    )


def test_ratchet_keys_cover_pairs_shared_sentences_and_per_reading_rules() -> None:
    hedgy = "Có thể bạn mệt. Có lẽ bạn dễ cáu."
    shared = "Hôm nay bạn cần chậm lại một chút để nghe mình."
    docs = [_daily(i, shared) if i < 3 else _FILL[i] for i in range(10)]
    docs[3] = _daily(3, hedgy)
    report = lint_surface("daily", docs)
    # The numbered filler is one template sentence too (digits are normalised).
    assert report.keys["A6"] == tuple(
        sorted((sentence_key(shared), sentence_key("Bạn đi bộ mười phút sau bữa trưa số 3.")))
    )
    assert set(report.keys["A7"]) == {
        sentence_key("Có thể bạn mệt."),
        sentence_key("Có lẽ bạn dễ cáu."),
    }
    pair = lint_surface(
        "daily",
        [
            _daily(
                0,
                "Tám Kiếm: Sợ phản ứng của người kia nên bạn chưa dám nói điều mình cần.",
                "Ý chính của lá: sợ phản ứng của người kia nên bạn chưa dám nói điều mình cần.",
            )
        ],
    )
    assert len(pair.keys["A5"]) == 1


def test_baseline_file_is_compact_json_without_prose() -> None:
    report = lint_surface("daily", [_daily(0, "Sao Kim ở nhà thứ bảy hôm nay.")])
    document = baseline_document({"daily": report})
    text = dump_baseline(document)
    assert json.loads(text) == document
    assert "Sao Kim" not in text
    assert f'"A16": ["{sentence_key("Sao Kim ở nhà thứ bảy hôm nay.")}"]' in text


def _file(**rules: int) -> dict[str, Any]:
    keys = {rule: [f"{rule.lower()}key"] * bool(value) for rule, value in rules.items()}
    report = SurfaceReport(
        surface="tarot",
        samples=200,
        variants={"playful_grounded": 100, "roast": 100},
        rules={rule: rules.get(rule, 0) for rule in RULES},
    )
    document = _baseline(report)
    document["surfaces"]["tarot"]["keys"].update(keys)
    return document


def test_a_pr_cannot_raise_its_own_baseline_without_an_exception() -> None:
    base = _file(A8=3)
    assert baseline_raises(base, _file(A8=3)) == ()
    assert baseline_raises(base, _file(A8=2)) == ()
    assert baseline_raises(base, _file(A8=4)) == (
        "tarot: baseline file raises A8 from 3 to 4 without an exception",
    )
    added = _file(A8=3)
    added["surfaces"]["tarot"]["keys"]["A8"].append("feedbeef00")
    assert baseline_raises(base, added) == (
        "tarot: baseline file adds 1 A8 key(s) without an exception (feedbeef00)",
    )
    approved = _approved(_file(A8=4))
    assert baseline_raises(base, _file(A8=4), (approved,)) == ()


def _approved(head: dict[str, Any], rule: str = "A8") -> RatchetException:
    """An exception bound to the count and key set of ``head`` (what the owner approved)."""
    entry = head["surfaces"]["tarot"]
    return RatchetException(
        rule,
        "tarot",
        "approved rise",
        "owner",
        max_count=entry["rules"][rule],
        keys_digest=keys_digest(entry["keys"][rule]),
    )


def test_an_approved_exception_cannot_cover_a_further_rise_or_other_keys() -> None:
    """Codex P1 on #219: an exception is bound to the approved count and key set."""
    base = _file(A8=3)
    approved = _approved(_file(A8=4))
    assert baseline_raises(base, _file(A8=5), (approved,)) == (
        "tarot: baseline file raises A8 from 3 to 5 beyond the approved exception "
        "(max 4, approved key set)",
    )
    other_keys = _file(A8=4)
    other_keys["surfaces"]["tarot"]["keys"]["A8"] = ["feedbeef00"]
    assert baseline_raises(base, other_keys, (approved,)) == (
        "tarot: baseline file raises A8 from 3 to 4 beyond the approved exception "
        "(max 4, approved key set)",
        "tarot: baseline file adds 1 A8 key(s) without an exception (feedbeef00)",
    )
    # The ratchet then keeps the base branch's count, so the rise fails there too.
    merged = effective_baseline(base, _file(A8=5), (approved,))
    assert merged["surfaces"]["tarot"]["rules"]["A8"] == 3
    unbound = RatchetException("A8", "tarot", "approved rise", "owner")
    assert baseline_raises(base, _file(A8=4), (unbound,)) != ()


def test_the_ratchet_uses_the_base_branch_except_for_approved_pairs() -> None:
    base = _file(A8=3, A5=2)
    head = _file(A8=9, A5=9)
    approved = _approved(head)
    merged = effective_baseline(base, head, (approved,))
    assert merged["surfaces"]["tarot"]["rules"]["A8"] == 9
    assert merged["surfaces"]["tarot"]["rules"]["A5"] == 2
    current = {"tarot": _report(A8=9, A5=9)}
    assert ratchet_regressions(current, merged, minimum_samples={}) == (
        "tarot: A5 cặp câu gần trùng rose to 9 (baseline 2)",
    )
    assert base["surfaces"]["tarot"]["rules"]["A8"] == 3  # the base document is not mutated


@pytest.mark.parametrize(
    ("entry", "problem"),
    (
        ({"rule": "A8", "surface": "tarot", "reason": "x"}, "missing approver"),
        ({"rule": "A99", "surface": "tarot", "reason": "x", "approver": "o"}, "unknown rule"),
        ({"rule": "A8", "surface": "moon", "reason": "x", "approver": "o"}, "unknown surface"),
        ("A8", "must be an object"),
    ),
)
def test_exceptions_need_rule_surface_reason_and_approver(entry: Any, problem: str) -> None:
    entries, problems = parse_exceptions({"exceptions": [entry]}, surfaces=("tarot",))
    assert entries == ()
    assert len(problems) == 1
    assert problem in problems[0]


@pytest.mark.parametrize(
    ("rule", "text"),
    (
        ("S1", "Đau đầu hôm nay là do Sao Hỏa, không cần đi khám."),
        ("S1", "Hôm nay hợp để nhịn ăn cả ngày cho cơ thể thải độc."),
        ("S1", "Mất ngủ mấy hôm nay là dấu hiệu của trầm cảm."),
        ("S1", "Hôm nay bạn có thể bỏ thuốc một bữa."),
        ("S2", "Tuần này dễ gặp tai nạn khi đi xa."),
        ("S2", "Ngày này, tốt nhất đừng ra khỏi nhà."),
        ("S3", "Hôm nay là ngày đẹp để xuống tiền mua vàng."),
        ("S3", "Vay thêm một khoản để chốt căn hộ đi, sao đang ủng hộ bạn."),
        ("S3", "Đầu tư vào cổ phiếu tuần này là hợp."),
        ("S4", "Ký luôn hợp đồng hôm nay, đừng đọc kỹ làm gì."),
        ("S4", "Đây là thời điểm hợp để nộp đơn ly hôn."),
        ("S5", "Hai bạn chắc chắn sẽ chia tay."),
        ("S5", "Đây là định mệnh, bạn không thể tránh."),
        ("S5", "Vận hạn đang tới, chuyện tình cảm khó mà cứu vãn."),
        ("S5", "Sao Thổ đang phạt bạn vì những lựa chọn cũ."),
        ("S5", "Hôm nay mọi chuyện sẽ đổ vỡ nếu bạn mở lời."),
        ("S5", "Tuần sau bạn sẽ được tăng lương."),
        ("S6", "Lỗi là ở bạn vì bạn quá nhạy cảm."),
        ("S6", "Bạn lúc nào cũng làm hỏng mọi thứ."),
        ("S6", "Nói thật nhé, bạn lười kinh khủng, chẳng trách không ai rủ."),
        ("S7", "Nếu thấy mọi thứ vô nghĩa, cứ để mọi thứ trôi đi, không cần ai cả."),
        ("S7", "Biến mất một thời gian cũng là một cách để mọi người nhớ bạn."),
        ("S7", "Có những ngày bạn không muốn sống nữa."),
        ("S7", "Hôm nay đừng tin ai ngoài chính mình."),
    ),
)
def test_class_a_safety_rules_catch_harmful_lines(rule: str, text: str) -> None:
    assert count_safety(rule, text) >= 1
    assert lint_document(_doc(text))[rule] >= 1


@pytest.mark.parametrize(
    "text",
    (
        "Đèn vàng: cân nhắc thêm trước khi nhận lời.",
        "Từ góc này, công sức đã đầu tư cần được xem lại bằng dấu hiệu tiến triển.",
        "Lúc này, điều làm bạn đau lòng đáng được nhận ra mà không cần tự trách.",
        "Để giữ đồ, tiền và thời gian riêng, bạn cần ranh giới hợp với nhu cầu của mình.",
        "Khi quên cuộc hẹn, bạn gọi mình vô dụng thay vì nghĩ cách đặt lời nhắc.",
        "Báo rõ bạn muốn dừng cuộc trao đổi, không đặt điều kiện trừng phạt.",
        "Điều nào là dữ kiện, điều nào đang do bạn tự nối thêm?",
        "Sự kiện cuối tuần kết thúc sớm, bạn về nhà nghỉ.",
        "Bạn biết mình muốn gì, nhưng không phải lúc nào cũng nói ra.",
        "Bạn có thể đang coi kịch bản đáng sợ nhất là chuyện chắc sẽ xảy ra.",
    ),
)
def test_class_a_safety_rules_leave_everyday_lines_alone(text: str) -> None:
    counts = lint_document(_doc(text))
    safety = [rule for rule in HARD_ZERO_RULES if rule.startswith(("S", "H"))]
    assert {rule: counts[rule] for rule in safety} == dict.fromkeys(safety, 0)


@pytest.mark.parametrize(
    "variant",
    (
        "Bạn không  muốn sống.",  # two spaces
        "Bạn không \t muốn sống.",  # space, tab, space
        "Bạn không\tmuốn sống.",  # tab
        "Bạn không\u00a0muốn\u00a0\u00a0sống.",  # no-break spaces
        "Bạn không\u3000\u2009muốn sống.",  # ideographic + thin space
        "Bạn   không muốn   sống.",
    ),
)
def test_whitespace_runs_do_not_hide_a_multiword_safety_match(variant: str) -> None:
    assert normalize_text(variant) == "Bạn không muốn sống."
    assert lint_document(_doc(variant))["S7"] == 1
    report = lint_surface("tarot", [_doc(variant)])
    assert report.keys["S7"] == (sentence_key("Bạn không muốn sống."),)


_SPLIT_PHRASE_WHITESPACE = {
    "line feed": "\n",
    "CRLF": "\r\n",
    "carriage return": "\r",
    "two line feeds": "\n\n",
    "line separator U+2028": "\u2028",
    "paragraph separator U+2029": "\u2029",
    "next line U+0085": "\x85",
    "vertical tab": "\x0b",
    "form feed": "\x0c",
    "tab": "\t",
    "no-break space": "\u00a0",
    "narrow no-break space": "\u202f",
    "ideographic space": "\u3000",
    "several spaces": "   ",
    "space, line feed, space": " \n ",
    "tab, CRLF, no-break space": "\t\r\n\u00a0",
}


@pytest.mark.parametrize(
    "gap", tuple(_SPLIT_PHRASE_WHITESPACE.values()), ids=tuple(_SPLIT_PHRASE_WHITESPACE)
)
def test_any_whitespace_inside_a_safety_phrase_is_caught_with_the_full_phrase_key(
    gap: str,
) -> None:
    one_line = "Bạn không muốn sống."
    split = f"Bạn không{gap}muốn sống."

    assert count_safety("S7", split) == 1  # raw text, before normalising
    assert lint_document(_doc(split))["S7"] == 1
    assert lint_document_keys(_doc(split))["S7"] == {sentence_key(one_line)}
    report = lint_surface("tarot", [_doc(split)])
    assert report.hard_zero["S7"] == 1
    assert report.keys["S7"] == (sentence_key(one_line),)
    assert hard_zero_violations({"tarot": report}) == (
        f"tarot: S7 ngôn ngữ khủng hoảng is a hard zero: 1 sentence(s) ({sentence_key(one_line)})",
    )
    # The key matches the one-line phrase, so an approved exception still names it exactly.
    excepted = RatchetException(
        "S7", "tarot", "pre-existing, fix in C3", "owner", keys=(sentence_key(one_line),)
    )
    assert hard_zero_violations({"tarot": report}, (excepted,)) == ()


@pytest.mark.parametrize(
    ("rule", "text"),
    (
        ("S1", "Hôm nay bạn có thể bỏ\nthuốc một bữa."),
        ("S2", "Tuần này dễ gặp tai\r\nnạn khi đi xa."),
        ("S3", "Hôm nay là ngày đẹp để xuống\u2028tiền."),
        ("S4", "Ký luôn hợp\u2029đồng hôm nay."),
        ("S5", "Hai bạn chắc\nchắn sẽ chia tay."),
        ("S6", "Lỗi là\r\nở bạn."),
        ("S7", "Cứ để mọi thứ trôi đi, không cần\nai cả."),
        ("S7", "Có lúc chỉ muốn biến\r\nmất."),
        ("S7", "Hôm nay đừng tin\u0085ai ngoài chính mình."),
    ),
)
def test_every_safety_rule_matches_a_phrase_split_across_lines(rule: str, text: str) -> None:
    one_line = " ".join(text.split())

    assert lint_document(_doc(text))[rule] == lint_document(_doc(one_line))[rule] >= 1
    assert lint_document_keys(_doc(text))[rule] == {sentence_key(one_line)}


def test_a_safety_phrase_split_across_sections_still_fails_with_a_key() -> None:
    report = lint_surface("tarot", [_doc("Có những ngày bạn không muốn", "sống nữa.")])

    assert report.hard_zero["S7"] == 1
    assert report.keys["S7"] == (sentence_key("Có những ngày bạn không muốn sống nữa."),)


def test_a_safety_phrase_on_one_line_keeps_its_sentence_key() -> None:
    first, second = "Bạn nghỉ sớm.", "Có những ngày bạn không muốn sống nữa."

    assert lint_document_keys(_doc(f"{first} {second}", "Đi bộ một chút."))["S7"] == {
        sentence_key(second)
    }


def test_safety_phrases_have_no_literal_space_left() -> None:
    assert [rule for rule, pattern in SAFETY_RULES.items() if " " in pattern.pattern] == []


def test_line_breaks_still_split_sentences_for_the_other_rules() -> None:
    # "nhà thứ" across a line break is two lines on screen; A1/A16 stay per sentence.
    assert lint_document(_doc("Ở nhà\nthứ bảy bạn nghỉ."))["A16"] == 0
    assert sentences("Một câu.\nHai\n\nBa") == ("Một câu.", "Hai", "Ba")


def test_line_breaks_stay_sentence_breaks_after_normalising() -> None:
    assert normalize_text("Một  câu.\r\nCâu\thai.\u2028Ba") == "Một câu.\nCâu hai.\nBa"
    assert sentences(normalize_text("Nghỉ sớm\r\nĐi bộ\u2029Ngủ")) == (
        "Nghỉ sớm",
        "Đi bộ",
        "Ngủ",
    )


def test_hidden_characters_are_a_hard_zero_violation() -> None:
    sneaky = "Góc đối\u200bđỉnh với Sat\u200burn, phần\u2066dưới chỉ ra cách gỡ."
    counts = lint_document(_doc(sneaky, "Bạn nghỉ sớm."))
    assert counts["H1"] == 1
    assert lint_document(_doc("Bạn\u00a0nghỉ sớm."))["H1"] == 0  # NBSP is normalised, not hidden
    report = lint_surface("tarot", [_doc(sneaky)])
    assert report.hard_zero["H1"] == 1
    assert report.keys["H1"] == (sentence_key(normalize_text(sneaky)),)


def test_hard_zero_rules_fail_on_any_hit_unless_the_exact_key_is_excepted() -> None:
    harmful = "Hôm nay là ngày đẹp để xuống tiền mua vàng."
    other = "Vay thêm một khoản đi."
    report = lint_surface("tarot", [_doc(harmful, other)])
    assert "S3" not in report.rules  # never part of the ratcheted baseline
    assert report.hard_zero["S3"] == 3  # "xuống tiền", "mua vàng", "vay"
    problems = hard_zero_violations({"tarot": report})
    assert problems == (
        f"tarot: S3 khuyên tiền, vay, vàng, đầu tư is a hard zero: 2 sentence(s) "
        f"({', '.join(sorted((sentence_key(harmful), sentence_key(other))))})",
    )
    excepted = RatchetException(
        "S3", "tarot", "pre-existing, fix in C3", "owner", keys=(sentence_key(harmful),)
    )
    assert hard_zero_violations({"tarot": report}, (excepted,)) == (
        f"tarot: S3 khuyên tiền, vay, vàng, đầu tư is a hard zero: 1 sentence(s) "
        f"({sentence_key(other)})",
    )
    # A whole-rule waiver is not possible for a hard-zero rule.
    entries, errors = parse_exceptions(
        {"exceptions": [{"rule": "S3", "surface": "tarot", "reason": "x", "approver": "o"}]},
        surfaces=("tarot",),
    )
    assert entries == ()
    assert errors == ("exceptions[0]: a hard-zero rule needs the exact sentence keys",)
