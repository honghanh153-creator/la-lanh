"""C1-3 hard-zero rules: GT-1 (A4, A11, A14), HM-4 (S8, S9) and GT-10 (A9, A13, A15).

Every sentence here is invented for the test; no reading, person or chart is real.
"""

from datetime import date, timedelta

import pytest

from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    RULES,
    AstroFacts,
    ClarityDocument,
    DailyDay,
    RatchetException,
    assumes_circumstances,
    astro_fact_errors,
    count_safety,
    daily_follow_findings,
    first_screen_limit,
    first_screen_overflow,
    hard_zero_violations,
    lint_document,
    lint_surface,
    sentence_key,
)


def _doc(*texts: str, surface: str = "tarot", **fields: object) -> ClarityDocument:
    return ClarityDocument(
        surface=surface,
        sample_id="s1",
        sections=tuple((f"part_{index}", text) for index, text in enumerate(texts)),
        **fields,  # type: ignore[arg-type]
    )


# GT-1: the rules the spec always called blocking are hard zero, not ratcheted.


@pytest.mark.parametrize(
    ("rule", "text"),
    (
        ("A4", "Phần dưới chỉ ra lúc nó dễ hiện ra nhất."),
        ("A11", "Phần giải nghĩa này chưa sẵn sàng."),
        ("A14", "Tin nhắn vừa gửi chưa đúng cách bạn muốn nói."),
    ),
)
def test_gt1_blocking_rules_fail_on_one_hit_whatever_the_baseline(rule: str, text: str) -> None:
    assert rule in HARD_ZERO_RULES and rule not in RULES
    report = lint_surface("tarot", [_doc(text)])
    assert rule not in report.rules  # not part of any baseline, so a baseline cannot hide it
    assert report.hard_zero[rule] == 1
    problems = hard_zero_violations({"tarot": report})
    assert any(problem.startswith(f"tarot: {rule} ") for problem in problems)
    excepted = RatchetException(rule, "tarot", "pre-existing", "owner", (sentence_key(text),))
    assert not any(
        problem.startswith(f"tarot: {rule} ")
        for problem in hard_zero_violations({"tarot": report}, (excepted,))
    )


@pytest.mark.parametrize(
    ("rule", "text"),
    (
        ("A4", "Bạn nói một câu ngắn trước khi rời bàn."),
        ("A11", "Bạn để điện thoại xa giường một tối."),
        ("A14", "Nếu đã gửi tin nhắn, bạn chờ một lúc rồi hỏi lại."),
    ),
)
def test_gt1_blocking_rules_leave_clean_lines_alone(rule: str, text: str) -> None:
    assert lint_document(_doc(text))[rule] == 0


# S8 (HM-4): no sentence foretells a life event.


@pytest.mark.parametrize(
    "text",
    (
        # pregnancy
        "Tháng này bạn dễ có bầu.",
        "Sao Mộc báo tin bạn sắp có con.",
        "Năm nay hợp để sinh con.",
        "Chuyện hiếm muộn sẽ sớm có lối ra.",
        # marriage
        "Hai bạn sắp cưới rồi đó.",
        "Đây là năm bạn kết hôn.",
        "Người ấy sẽ cầu hôn bạn trong mùa này.",
        "Cuối năm hai bạn về chung một nhà.",
        # a breakup
        "Hai bạn dễ chia tay trong tuần này.",
        "Bạn sẽ phải chia tay người yêu.",
        "Mối quan hệ này sẽ tan vỡ.",
        "Đến lúc đường ai nấy đi.",
        # losing a job
        "Tháng sau bạn dễ mất việc.",
        "Công ty có thể sa thải bạn.",
        "Bạn sắp thất nghiệp.",
        # illness
        "Tuần này bạn dễ bị ốm.",
        "Cẩn thận kẻo phải nhập viện.",
        "Sức khỏe của bạn sẽ đi xuống.",
        "Sức khoẻ đang có vấn đề.",
        # the death of a loved one
        "Năm nay nhà bạn dễ có tang.",
        "Bạn có thể mất người thân.",
        "Người thân sắp ra đi.",
        # other foretold events
        "Tháng này bạn sẽ gặp người yêu.",
        "Bạn sắp chuyển việc.",
    ),
)
def test_s8_blocks_a_foretold_life_event(text: str) -> None:
    assert count_safety("S8", text) >= 1
    assert lint_document(_doc(text))["S8"] >= 1


@pytest.mark.parametrize(
    "text",
    (
        "Mấy tháng này, điều bạn yêu dễ lớn thêm: một sở thích, một mối tình, hay chuyện con cái.",
        "Bạn không muốn chịu cảm giác chia tay nên cắt quá nhanh.",
        "Cuối tuần bạn đi ăn cưới một người bạn cũ.",
        "Bạn muốn xây một nền ổn định có thể chia sẻ với người thân.",
        "Bạn dễ hòa vào bầu không khí của nhóm.",
        "Khi một người cần ở một mình, người còn lại dễ hiểu thành bị bỏ rơi.",
        "Chiều nay ghé viện bảo tàng một lúc cũng vui.",
        "Bạn mất công sửa một câu mãi không xong.",
        "Bạn thấy cảm giác mất mát khi một dự án khép lại.",
    ),
)
def test_s8_leaves_everyday_lines_alone(text: str) -> None:
    assert count_safety("S8", text) == 0


# S9 (HM-4): no sentence assumes the reader's circumstances.


@pytest.mark.parametrize(
    "text",
    (
        "Người độc thân như bạn nên ra ngoài nhiều hơn.",
        "Bạn đang độc thân nên có nhiều thời gian cho mình.",
        "Bạn chưa có người yêu, nên tối nay cứ thong thả.",
        "Người yêu của bạn sẽ thấy dễ chịu nếu bạn hỏi han.",
        "Tối nay nhắn cho chồng của bạn một câu.",
        "Ông xã sẽ vui khi bạn về sớm.",
        "Chiều nay đón con sớm hơn mười phút.",
        "Nếu chiều nay rảnh, đón con sớm hơn mười phút.",
        "Con của bạn cần bạn nghe nhiều hơn.",
        "Bé nhà bạn sẽ thích một buổi đi dạo.",
        "Là mẹ bỉm, bạn cần một giờ cho riêng mình.",
        "Bạn là con gái nên hay ngại nói ra.",
        "Phụ nữ như bạn cần được lắng nghe.",
        "Chị em mình hay ôm việc quá sức.",
        "Nàng ơi, hôm nay cứ nghỉ một chút.",
        "Cô nàng Bạch Dương hôm nay hơi vội.",
    ),
)
def test_s9_blocks_an_assumed_circumstance(text: str) -> None:
    assert assumes_circumstances(text)
    assert lint_document(_doc(text))["S9"] == 1


@pytest.mark.parametrize(
    "text",
    (
        "Nếu bạn đang độc thân, đây là lúc gặp thêm bạn mới.",
        "Với ai đang có con nhỏ, một giờ ngủ trưa cũng đáng giá.",
        "Bạn nhắn cho người kia một câu ngắn.",
        "Lịch thứ Tư của bạn có bốn việc chồng lên nhau.",
        "Có điều gì bạn muốn thử mà chưa có ai đi cùng không?",
        "Gia đình chọn ngày họp mặt và cần hỏi cả người phải đi xa.",
        "Bạn trả lời tin nhắn của bạn bè chậm lại một nhịp.",
        "Người yêu bạn nhất đôi khi là chính bạn.",
    ),
)
def test_s9_leaves_doors_and_neutral_lines_alone(text: str) -> None:
    assert not assumes_circumstances(text)
    assert lint_document(_doc(text))["S9"] == 0


def test_s8_and_s9_are_hard_zero() -> None:
    report = lint_surface("tarot", [_doc("Hai bạn sắp cưới.", "Con của bạn cần bạn.")])
    assert "S8" not in report.rules and "S9" not in report.rules
    assert (report.hard_zero["S8"], report.hard_zero["S9"]) == (1, 1)
    assert len(hard_zero_violations({"tarot": report})) == 2


# A9: the first screen fits a phone.


def test_a9_limits_follow_the_spec() -> None:
    assert first_screen_limit("daily") == 150
    assert first_screen_limit("radar") == 400
    assert first_screen_limit("kham_pha") == 300
    assert [first_screen_limit("tarot", cards=n) for n in (1, 3, 5)] == [120, 250, 400]


def test_a9_counts_only_first_screen_sections() -> None:
    short = "Bạn nghỉ mười phút sau bữa trưa."  # 7 syllables
    document = ClarityDocument(
        surface="daily",
        sample_id="s1",
        sections=(("hook", short), ("deep", " ".join([short] * 40))),
        first_screen=("hook",),
        first_screen_limit=10,
    )
    assert first_screen_overflow(document) is None
    assert lint_document(document)["A9"] == 0


def test_a9_flags_a_first_screen_over_its_limit() -> None:
    text = "Bạn nghỉ mười phút sau bữa trưa."  # 7 syllables
    over = ClarityDocument(
        surface="daily",
        sample_id="s1",
        sections=(("hook", text), ("action", text)),
        first_screen=("hook", "action"),
        first_screen_limit=13,
    )
    key = first_screen_overflow(over)
    assert key is not None and len(key) == 10
    report = lint_surface("daily", [over])
    assert report.hard_zero["A9"] == 1 and report.keys["A9"] == (key,)
    assert lint_document(ClarityDocument("daily", "s2", over.sections))["A9"] == 0  # undeclared


# A13: Daily follows the day.


_START = date(2031, 1, 5)
_FAST = ("moon", "venus", "mercury", "sun", "mars")


def _unique_run(persona: str = "p1", days: int = 30) -> list[DailyDay]:
    words = ("nghỉ", "đi", "gọi", "viết", "nấu", "đọc", "hỏi", "dọn", "nghe", "vẽ")
    return [
        DailyDay(
            persona=persona,
            day=(_START + timedelta(days=offset)).isoformat(),
            headline=f"Hôm nay bạn {words[offset % 10]} {words[(offset // 10) % 10]} một chút.",
            reason=f"transit:{_FAST[offset % 5]}:trine:natal:sun",
            sky_bodies=(_FAST[offset % 5],),
        )
        for offset in range(days)
    ]


def test_a13_passes_a_run_that_follows_the_day() -> None:
    assert daily_follow_findings(_unique_run()) == (0, frozenset())


def test_a13_counts_days_without_a_fast_factor() -> None:
    run = _unique_run()
    run[3] = DailyDay(run[3].persona, run[3].day, run[3].headline, "rule:natal", ())
    run[4] = DailyDay(run[4].persona, run[4].day, run[4].headline, "rule:natal-2", ("saturn",))
    count, keys = daily_follow_findings(run)
    assert count == 2 and len(keys) == 1


def test_a13_counts_a_reason_on_more_than_three_of_seven_days() -> None:
    run = _unique_run()
    for offset in (0, 2, 4, 6):  # four times inside one week
        item = run[offset]
        run[offset] = DailyDay(
            item.persona, item.day, item.headline, "transit:moon:square:natal:mars", ("moon",)
        )
    count, keys = daily_follow_findings(run)
    assert count == 1 and len(keys) == 1
    for offset in (0, 2, 4):  # three times is allowed
        item = run[offset]
        run[offset] = DailyDay(
            item.persona, item.day, item.headline, "transit:moon:square:natal:mars", ("moon",)
        )
    item = run[6]
    run[6] = DailyDay(
        item.persona, item.day, item.headline, "transit:sun:sextile:natal:moon", ("sun",)
    )
    assert daily_follow_findings(run) == (0, frozenset())


def test_a13_counts_a_repeated_headline_within_thirty_days() -> None:
    run = _unique_run()
    item = run[20]
    run[20] = DailyDay(item.persona, item.day, run[1].headline, item.reason, item.sky_bodies)
    count, keys = daily_follow_findings(run)
    assert count == 1 and len(keys) == 1


def test_a13_needs_thirty_consecutive_days() -> None:
    short = _unique_run(days=29)
    assert daily_follow_findings(short)[0] == 1
    gap = _unique_run()
    del gap[10]
    assert daily_follow_findings([*gap, *_unique_run("p2")])[0] == 1


def test_a13_keys_name_persona_and_check_and_feed_the_surface_report() -> None:
    bad = [
        DailyDay(item.persona, item.day, item.headline, item.reason, ())
        for item in _unique_run("p2")
    ]
    count, keys = daily_follow_findings([*_unique_run("p1"), *bad])
    assert count == 30 and len(keys) == 1
    report = lint_surface("daily", [], days=[*_unique_run("p1"), *bad])
    assert report.hard_zero["A13"] == 30
    assert report.keys["A13"] == tuple(sorted(keys))
    assert hard_zero_violations({"daily": report})


# A15: astrology facts in the text match the engine.


_FACTS = AstroFacts(
    placements=frozenset({("sun", "aquarius"), ("moon", "cancer"), ("venus", "leo")}),
    houses=frozenset({("sun", 11), ("moon", 3), ("venus", 5)}),
    contacts=frozenset(
        {
            ("venus", "mars", "trine", "approaching"),
            ("moon", "saturn", "square", "separating"),
        }
    ),
)


@pytest.mark.parametrize(
    "text",
    (
        "Mặt Trời ở Bảo Bình · Nhà 11: bạn sáng rõ hơn khi có khoảng thở.",
        "Mặt Trăng ở Cự Giải, nhà 3.",
        "Hôm nay Sao Kim đang hỗ trợ Sao Hỏa của bạn.",
        "Sao Kim tam hợp Sao Hỏa và đang tiến gần.",
        "Hôm nay Mặt Trăng đang tạo góc căng với Sao Thổ của bạn.",
        "Ra ngoài đón chút nắng mặt trời buổi sáng.",  # not the planet
    ),
)
def test_a15_accepts_facts_the_engine_computed(text: str) -> None:
    assert astro_fact_errors(_doc(text, surface="daily", facts=_FACTS)) == ()


@pytest.mark.parametrize(
    "text",
    (
        "Mặt Trời ở Sư Tử, nên bạn thích được nhìn thấy.",  # wrong sign
        "Mặt Trăng ở Cự Giải · Nhà 7.",  # wrong house
        "Hôm nay Sao Kim đang tạo góc căng với Sao Hỏa của bạn.",  # wrong aspect
        "Hôm nay Sao Hỏa đang hỗ trợ Sao Kim của bạn.",  # transit and natal swapped
        "Sao Kim tam hợp Sao Hỏa và đang rời xa.",  # wrong phase
        "Sao Mộc đối đỉnh Mặt Trời.",  # no such contact
    ),
)
def test_a15_flags_a_fact_the_engine_did_not_compute(text: str) -> None:
    document = _doc(text, surface="daily", facts=_FACTS)
    assert astro_fact_errors(document) == (text,)
    assert lint_document(document)["A15"] == 1


def test_a15_carries_the_subject_within_one_claim_only() -> None:
    document = ClarityDocument(
        surface="kham_pha",
        sample_id="s1",
        sections=(
            ("summary_sun-sign", "Mặt Trời ở Bảo Bình."),
            ("meaning_sun-sign", "Mặt Trời mô tả cách bạn chủ động. Ở Sư Tử, phần này rực hơn."),
            ("meaning_moon-sign", "Ở Sư Tử, phần này ấm hơn."),  # no body in this claim: skipped
        ),
        facts=_FACTS,
    )
    assert astro_fact_errors(document) == ("Ở Sư Tử, phần này rực hơn.",)


def test_a15_does_not_apply_without_a_chart_and_is_a_hard_zero() -> None:
    tarot = _doc("Mặt Trăng cho thấy bạn cần đi chậm lại ở Song Ngư.")
    assert astro_fact_errors(tarot) == ()  # the Moon card, no chart behind it
    wrong = _doc("Mặt Trời ở Sư Tử.", surface="daily", facts=_FACTS)
    report = lint_surface("daily", [wrong])
    assert report.hard_zero["A15"] == 1
    assert report.keys["A15"] == (sentence_key("Mặt Trời ở Sư Tử."),)
    empty = _doc("Mặt Trời ở Bảo Bình.", surface="radar", facts=AstroFacts())
    assert astro_fact_errors(empty) == ("Mặt Trời ở Bảo Bình.",)  # no facts wired: fails
