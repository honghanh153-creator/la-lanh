"""Money lens copy for the four sub-stories (#710): pending, whole-set serving, AC2 wording."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import (
    CopyEntry,
    copy_digest,
    load_registry,
    registry_problems,
)
from app.domains.content_rewrite.gates import _ACTION_VERBS, _fold
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import within_five_minutes
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS
from app.domains.readings.money_lens_copy import (
    MONEY_COPY_PARTS,
    MONEY_LENS_PREFIX,
    MONEY_SITUATIONS,
    MoneyCopy,
    money_copy,
    money_copy_id,
)
from scripts.persona_metrics import light_by_rule
from tests.content.test_daily_variants import _check_clarity, _shared_failures

IDS = tuple(
    money_copy_id(situation, part) for situation in MONEY_SITUATIONS for part in MONEY_COPY_PARTS
)
# Stories that say nothing about how much money the reader has (decision 25.11, section 2).
NO_SHORTAGE_STORIES = ("family_remittance", "costly_social_invitation")

# AC2. No amount is asked or named; nobody is told they are short, in debt or in crisis; nobody
# is blamed for keeping their money; no large money decision is suggested.
_AMOUNT = re.compile(r"\d|\b(?:đồng|nghìn|ngàn|triệu|tỷ|tỉ|bao nhiêu tiền|số tiền|mấy trăm)\b")
_SHORTAGE = re.compile(
    r"\b(?:thiếu|hết tiền|cạn|túng|nghèo|khó khăn|nợ|vỡ nợ|khủng hoảng|chật vật|kẹt tiền)\b"
)
_BLAME = re.compile(r"\b(?:keo kiệt|ích kỷ|bủn xỉn|tiếc tiền|hà tiện|tính toán quá|nên rộng rãi)\b")
_BIG_DECISION = re.compile(
    r"\b(?:vay|mượn tiền|đầu tư|bán|cầm đồ|trả góp|nghỉ học|bỏ học|bảo lưu|chuyển trọ|"
    r"thẻ tín dụng|xin việc|nghỉ việc)\b"
)
_PREDICTION = re.compile(r"\b(?:sẽ có tiền|sẽ hết|sắp có|sắp hết|rồi sẽ|chắc chắn)\b")
_SENSITIVE = re.compile(r"\b(?:đồng ý cho|quyền riêng tư|dữ liệu|đường dây|khẩn cấp|tự hại)\b")


def _approved(entry: CopyEntry) -> CopyEntry:
    return replace(
        entry,
        status="approved",
        approver="codex",
        date="2026-11-28",
        digest=copy_digest(entry.text),
    )


def _text(entries: dict[str, CopyEntry], situation: str, part: str) -> str:
    return entries[money_copy_id(situation, part)].text


def test_ids_cover_the_four_stories_and_nothing_else() -> None:
    entries = load_registry()
    assert registry_problems(entries) == []
    in_store = {key for key in entries if key.startswith(MONEY_LENS_PREFIX)}
    assert in_store == set(IDS) and len(IDS) == 16
    assert MONEY_SITUATIONS == (
        "tuition_or_rent_shortfall",
        "month_end_shortfall",
        "family_remittance",
        "costly_social_invitation",
    )
    with pytest.raises(ValueError):
        money_copy_id("debt", "note")
    with pytest.raises(ValueError):
        money_copy_id("family_remittance", "amount")


def test_batch_is_pending_and_unserved_before_approval() -> None:
    """Replace this pre-approval check only in the PR carrying the review receipt."""
    entries = load_registry()
    for key in IDS:
        entry = entries[key]
        assert entry.category == "reading", key
        assert entry.status == "pending" and not entry.servable, key
        assert entry.approver is entry.date is entry.digest is None, key
        assert copy_approval.approved_copy(key) is None, key
    assert all(money_copy(situation) is None for situation in MONEY_SITUATIONS)


@pytest.mark.parametrize("key", IDS)
def test_every_sentence_is_plain_and_keeps_ac2(key: str) -> None:
    text = load_registry()[key].text
    lowered = text.casefold()
    for rule in (_AMOUNT, _BLAME, _BIG_DECISION, _PREDICTION, _SENSITIVE):
        assert not rule.search(lowered), (key, rule.pattern)
    assert _shared_failures(text) == [] or key.endswith((".light", ".action")), key
    assert "nhà " not in lowered, key
    if not key.endswith(".label"):
        _check_clarity(key, text)


@pytest.mark.parametrize("situation", MONEY_SITUATIONS)
def test_parts_have_their_shape(situation: str) -> None:
    entries = load_registry()
    label, note, light, action = (_text(entries, situation, part) for part in MONEY_COPY_PARTS)
    assert 3 <= len(label.split()) <= 7 and not label.endswith(".")
    assert note.startswith("Khi ") and "bạn dễ" in note
    assert _shared_failures(note) == []
    assert len(light) <= LIGHTER_ACTION_MAX_CHARS
    assert has_observable_action(light) and light_by_rule(light) and within_five_minutes(light)
    assert any(_fold(action).startswith(_fold(verb)) for verb in _ACTION_VERBS)
    assert has_observable_action(action)
    assert len({label, note, light, action}) == 4


@pytest.mark.parametrize("situation", NO_SHORTAGE_STORIES)
def test_remittance_and_invitation_never_assume_shortage(situation: str) -> None:
    entries = load_registry()
    for part in MONEY_COPY_PARTS:
        text = _text(entries, situation, part).casefold()
        assert not _SHORTAGE.search(text), (situation, part)
        assert "còn ít" not in text and "chưa đủ" not in text, (situation, part)


def test_shortage_stories_name_only_what_the_reader_chose() -> None:
    entries = load_registry()
    for situation in ("tuition_or_rent_shortfall", "month_end_shortfall"):
        for part in MONEY_COPY_PARTS:
            text = _text(entries, situation, part).casefold()
            assert not re.search(r"\b(?:nợ|vỡ nợ|khủng hoảng|nghèo|túng)\b", text), situation


def test_wording_rules_catch_bad_lines() -> None:
    assert _AMOUNT.search("ghi số tiền bạn còn")
    assert _AMOUNT.search("còn 200 nghìn")
    assert _SHORTAGE.search("khi bạn thiếu tiền gửi về")
    assert _BLAME.search("đừng keo kiệt với bạn bè")
    assert _BIG_DECISION.search("hỏi vay một người quen")
    assert _PREDICTION.search("tháng sau bạn sẽ có tiền")


def test_no_line_repeats_another_registry_sentence() -> None:
    """AC4: the lens set shares no sentence with the rest of the store (#705 included)."""
    entries = load_registry()
    others = {entry.text for key, entry in entries.items() if key not in IDS}
    mine = [entries[key].text for key in IDS]
    assert len(set(mine)) == len(mine)
    assert not others & set(mine)


@pytest.mark.parametrize("situation", MONEY_SITUATIONS)
def test_one_whole_set_unlocks_without_the_others(
    situation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = load_registry()
    for part in MONEY_COPY_PARTS:
        key = money_copy_id(situation, part)
        entries[key] = _approved(entries[key])
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    assert money_copy(situation) == MoneyCopy(
        *(_text(entries, situation, part) for part in MONEY_COPY_PARTS)
    )
    assert all(money_copy(other) is None for other in MONEY_SITUATIONS if other != situation)


@pytest.mark.parametrize("missing", MONEY_COPY_PARTS)
def test_partial_approval_serves_nothing(missing: str, monkeypatch: pytest.MonkeyPatch) -> None:
    entries = load_registry()
    situation = "family_remittance"
    for part in MONEY_COPY_PARTS:
        if part != missing:
            key = money_copy_id(situation, part)
            entries[key] = _approved(entries[key])
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    assert money_copy(situation) is None


@pytest.mark.parametrize(
    "text", ("Ngồi yên sáu phút rồi thở chậm.", "Ngồi yên " + "thật lâu " * 30 + "rồi nghỉ.")
)
def test_light_action_outside_runtime_limits_serves_nothing(
    text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = load_registry()
    situation = "month_end_shortfall"
    for part in MONEY_COPY_PARTS:
        key = money_copy_id(situation, part)
        entries[key] = _approved(entries[key])
    light = money_copy_id(situation, "light")
    entries[light] = _approved(replace(entries[light], text=text))
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    assert money_copy(situation) is None
