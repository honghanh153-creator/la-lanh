"""The month sentences: complete, pending until approved, and never a prediction or a date."""

from __future__ import annotations

import re

from app.domains.content.copy_approval import load_registry
from app.domains.month_answer.answer import required_copy_ids
from app.domains.month_answer.facts import ANSWER_PLANETS, Topic

from .conftest import registry_texts

DATE_LIKE = re.compile(r"\b\d{1,2}\s*[./-]\s*\d{1,2}\b|\bngày \d|\bmùng \d|\btháng \d")
# An answer may say what a month leans towards ("dễ", "hợp để"); it never says what will happen.
PREDICTION = re.compile(
    r"chắc chắn|sẽ được|sẽ có|sẽ gặp|sẽ đến|sẽ xảy ra|khả năng cao|nhất định|chắc là|"
    r"ngày xấu|ngày tốt|kiêng|tránh ngày|xui|vận hạn|vận đen|điềm",
    re.IGNORECASE,
)
# No part may open like a yes/no verdict, even "Có một chuyện…" reads as "Yes" at a glance.
YES_NO = re.compile(r"^(có|không|được|chưa)\b", re.IGNORECASE)


def test_every_topic_and_planet_has_three_parts() -> None:
    texts = registry_texts("month.")
    for cid in required_copy_ids():
        assert cid in texts, cid
    assert len([cid for cid in texts if cid.startswith("month.theme.")]) == len(Topic) * len(
        ANSWER_PLANETS
    )


def test_month_copy_is_pending_and_sensitive_copy_is_owner_only() -> None:
    registry = load_registry()
    for key, entry in registry.items():
        if key.startswith("month."):
            assert entry.category == "reading"
    assert registry["consent.month.typed_question"].category == "consent"
    assert registry["crisis.self_harm.notice.month"].category == "crisis"
    # Nobody but the owner approves these two (R2 kind 3); this PR leaves them pending.
    assert registry["consent.month.typed_question"].status == "pending"
    assert registry["crisis.self_harm.notice.month"].status == "pending"


def test_no_prediction_no_date_no_yes_no() -> None:
    for cid, text in registry_texts("month.").items():
        if cid == "month.line.disclaimer":
            continue  # "không phải điều chắc chắn sẽ xảy ra" says the opposite of a prediction
        assert not DATE_LIKE.search(text), cid
        assert not PREDICTION.search(text), cid
        if cid.startswith(("month.theme.", "month.act.", "month.say.")):
            assert not YES_NO.search(text), cid


def test_window_line_offers_easier_days_only() -> None:
    texts = registry_texts("month.line.")
    assert texts["month.line.window"] == "Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút."
    assert texts["month.line.disclaimer"] == (
        "Đây là một góc nhìn để bạn tự quyết, không phải điều chắc chắn sẽ xảy ra."
    )


def test_sentences_are_short() -> None:
    for cid, text in registry_texts("month.").items():
        assert len(text) <= 130, cid
        if cid.startswith("month.say."):
            assert text.count(".") + text.count("?") <= 2, cid
