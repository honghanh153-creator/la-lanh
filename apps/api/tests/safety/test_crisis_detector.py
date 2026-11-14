"""Crisis detector phrase table (crisis safety layer, 14.11.2026). Synthetic phrases only."""

from __future__ import annotations

import pytest

from app.domains.content.copy_approval import OWNER_ONLY_CATEGORIES, copy_digest, load_registry
from app.domains.safety.crisis import (
    CRISIS_COPY_ID,
    CRISIS_NOTICE_TEXT,
    crisis_notice,
    detect_crisis,
    normalize,
)
from tests.safety.crisis_phrases import NEGATIVES, POSITIVES


def test_the_table_is_large_and_has_no_overlap() -> None:
    assert len(POSITIVES) + len(NEGATIVES) >= 60
    assert len(set(POSITIVES)) == len(POSITIVES)
    assert len(set(NEGATIVES)) == len(NEGATIVES)
    assert not set(POSITIVES) & set(NEGATIVES)


def test_every_positive_is_caught() -> None:
    missed = [phrase for phrase in POSITIVES if not detect_crisis(phrase)]
    assert missed == []


def test_no_negative_is_flagged() -> None:
    flagged = [phrase for phrase in NEGATIVES if detect_crisis(phrase)]
    assert flagged == []


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_text_is_not_a_match(text: str) -> None:
    assert detect_crisis(text) is False


def test_long_input_is_read_only_up_to_the_scan_limit() -> None:
    assert detect_crisis("Mình muốn chết " + "a" * 10_000)
    assert not detect_crisis("a " * 5_000 + "mình muốn chết")


def test_folded_copy_stays_aligned_with_the_accented_copy() -> None:
    accented, folded = normalize("Ừ, đúng rồi! Mình muốnnn chếttt…")
    assert len(accented) == len(folded)
    assert folded == "u . dung roi . minh muon chet ."


def test_notice_is_the_owner_approved_registry_entry() -> None:
    entry = load_registry()[CRISIS_COPY_ID]
    assert entry.category == "crisis" and "crisis" in OWNER_ONLY_CATEGORIES
    assert entry.status == "approved" and entry.approver == "owner"
    assert entry.date == "2026-11-14"
    assert entry.digest == copy_digest(CRISIS_NOTICE_TEXT)
    assert entry.text == CRISIS_NOTICE_TEXT == "Ứng dụng không hỗ trợ nội dung này."
    assert entry.servable
    assert crisis_notice().text == CRISIS_NOTICE_TEXT


def test_notice_carries_no_phone_number_or_link() -> None:
    text = crisis_notice().text
    assert not any(char.isdigit() for char in text)
    assert "tel:" not in text and "http" not in text
