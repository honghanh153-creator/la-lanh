"""Accents decide the reading (Codex auto-2 P1 on PR #505, 16.11.2026). Synthetic phrases only.

Folded text cannot tell "tự sát" from "tủ sắt". Each Vietnamese rule lists the accented spellings
of its key word, so ordinary phrases that fold to the same letters pass, while the crisis phrase
still matches typed with accents or without any.
"""

from __future__ import annotations

import unicodedata

import pytest

from app.domains.safety.crisis import _RULES, detect_crisis, fold

# Each was flagged before this fix (red at 6461dd6), one or more per rule.
ORDINARY_WITH_ACCENTS = (
    "Mình có nên mua tủ sắt cho phòng mới không?",
    "Từ Hải bản thân cũng là một người cô độc, đúng không?",
    "Mình tự làm dầu gội, có nên mở cửa hàng nhỏ không?",
    "Bạn ấy hay tự gây hài trong lớp, mình có nên làm quen?",
    "Chuyện làm dâu bản thân mình thấy chưa sẵn sàng",
    "Mình uống cả vị thuốc bắc này được không?",
    "Bao giờ thì kết thúc cuộc dời này?",
    "Đồ cũ mình muốn tất cả dùng lại luôn, có nên không?",
    "Khi em đi mãi mới về, anh ấy vui quá hôn em",
    "Mình muốn rời khỏi đồi này trước khi trời tối",
    "Mình có nên viết thư tư biệt thự cho chủ nhà không?",
    "Có nên tha chết cho con chuột trong bếp không?",
    "Ngồi cả ngày đau mông chết đi được, có nên mua ghế mới?",
    "Mình ngu mãi mãi môn toán à?",
)

# One crisis phrase per changed rule, typed with accents and without.
CRISIS_BOTH_WAYS = (
    ("Mình nghĩ đến chuyện tự sát", "minh nghi den chuyen tu sat"),
    ("Mình hay tự hại bản thân", "minh hay tu hai ban than"),
    ("Em hay tự làm tổn thương", "em hay tu lam ton thuong"),
    ("Mình lại tự gây đau", "minh lai tu gay dau"),
    ("Mình muốn gây hại chính mình", "minh muon gay hai chinh minh"),
    ("Mình định uống thuốc độc", "minh dinh uong thuoc doc"),
    ("Mình định uống hết vỉ thuốc", "minh dinh uong het vi thuoc"),
    ("Đêm nay thuốc ngủ cho xong", "dem nay thuoc ngu cho xong"),
    ("Mình muốn kết thúc cuộc đời mình", "minh muon ket thuc cuoc doi minh"),
    ("Mình muốn chấm dứt mạng sống", "minh muon cham dut mang song"),
    ("Mình muốn kết thúc tất cả", "minh muon ket thuc tat ca"),
    ("Mình muốn mọi thứ dừng lại mãi mãi", "minh muon moi thu dung lai mai mai"),
    (
        "Nếu mình biến mất mọi người sẽ nhẹ nhõm hơn",
        "neu minh bien mat moi nguoi se nhe nhom hon",
    ),
    ("Mình muốn rời khỏi cuộc đời này", "minh muon roi khoi cuoc doi nay"),
    ("Mình đã viết thư tuyệt mệnh", "minh da viet thu tuyet menh"),
    ("Mình sẽ đi xa mãi mãi", "minh se di xa mai mai"),
    (
        "Đây là lần cuối, mình tặng hết đồ đạc cho bạn",
        "day la lan cuoi minh tang het do dac cho ban",
    ),
    ("Thà chết còn hơn", "tha chet con hon"),
    ("Mình mong được chết", "minh mong duoc chet"),
    ("Chắc mình đi bán muối luôn", "chac minh di ban muoi luon"),
    ("Mình muốn ngủ mãi mãi", "minh muon ngu mai mai"),
)


@pytest.mark.parametrize("text", ORDINARY_WITH_ACCENTS)
def test_ordinary_phrase_with_other_accents_is_not_a_crisis(text: str) -> None:
    assert detect_crisis(text) is False


@pytest.mark.parametrize(("accented", "plain"), CRISIS_BOTH_WAYS)
def test_crisis_phrase_matches_with_and_without_accents(accented: str, plain: str) -> None:
    assert fold(accented.casefold()).replace(",", "") == plain
    assert detect_crisis(accented) is True
    assert detect_crisis(plain) is True


def test_every_vietnamese_rule_lists_accented_spellings() -> None:
    english = [rule for rule in _RULES if not rule.forms]
    # English rules only: their patterns hold no Vietnamese key words.
    assert len(english) == 9
    for rule in english:
        assert any(
            word in rule.pattern.pattern
            for word in ("kill", "kms", "suicid", "self", "unalive", "die", "life", "live")
        )
    for rule in _RULES:
        for spelling in rule.forms:
            assert spelling == unicodedata.normalize("NFC", spelling).casefold()
            assert spelling != fold(spelling), spelling  # carries accents
            assert fold(spelling).replace(" ", "").isascii()
