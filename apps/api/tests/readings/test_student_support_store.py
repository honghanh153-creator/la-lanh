"""Student support (#703): a no-contact action next to every contact action, and the
"nhiều bạn cũng vậy" line only where it fits.

Coverage, copy quality and the frozen catalogs. The sentences are pending; serving them is a
later step (API, then web). Synthetic data only.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

import app
from app.domains.content.copy_approval import (
    OWNER_ONLY_CATEGORIES,
    CopyEntry,
    copy_digest,
    load_registry,
)
from app.domains.readings import student_support
from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    MAX_SENTENCE_SYLLABLES,
    count_jargon,
    count_meta_talk,
    count_placeholders,
    count_safety,
    english_words,
    sentences,
    syllables,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import ACTION_SHAPES, within_ten_minutes
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS
from app.domains.readings.student_support import (
    ALONE_CATALOG,
    ALONE_PREFIX,
    COMMON_LINE_CATALOG,
    COMMON_LINE_ISSUES,
    COMMON_LINE_PREFIX,
    alone_action_for,
    alone_action_projection,
    alone_offer_for,
    alone_slots,
    alone_store_gaps,
    common_line_for,
    contact_issues,
    needs_contact,
)

ISSUE_KEYS = tuple(issue.key for issue in DAILY_ISSUES)
REGISTRY = load_registry()
ALONE = {key: entry for key, entry in REGISTRY.items() if key.startswith(ALONE_PREFIX)}
COMMON = {key: entry for key, entry in REGISTRY.items() if key.startswith(COMMON_LINE_PREFIX)}
NEW_COPY = {**ALONE, **COMMON}
SAFETY = tuple(rule for rule in HARD_ZERO_RULES if rule.startswith("S"))
# AC3: never assume the reader has a family to lean on.
FAMILY_WORDS = ("gia đình", "bố", "mẹ", "ba má", "người thân", "anh chị", "người nhà")
REVISION = UUID("00000000-0000-4000-8000-000000000703")


@pytest.mark.parametrize(
    ("text", "contact"),
    [
        ("Nhắn một câu hỏi về đúng chỗ bạn chưa hiểu.", True),
        ("Hỏi lại phần chưa rõ: Bạn muốn nói gì ở chỗ này?", True),
        ("Nói với người kia giờ nào mình còn gặp được.", True),
        ("Xin một người trong nhóm giải thích lại.", True),
        ("Gửi tin cho một người bạn tin.", True),
        ("Viết câu trả lời rồi đọc lại.", True),
        ("Đọc lại tin nhắn một lần thật chậm.", False),
        ("Ghi ra giấy ba việc đang dở rồi chọn một việc làm trước.", False),
        ("Mở lịch tuần này rồi đánh dấu những giờ bạn còn trống.", False),
    ],
)
def test_needs_contact(text: str, contact: bool) -> None:
    assert needs_contact(text) is contact


def test_every_issue_with_a_contact_action_has_an_alone_action() -> None:
    """AC1. The pool is read from the live Daily store, not from a list kept here."""

    with_contact = contact_issues(DAILY_ISSUES)
    assert "missing-context" in with_contact
    assert alone_store_gaps(DAILY_ISSUES) == []
    assert set(with_contact) <= set(ALONE_CATALOG) <= set(ISSUE_KEYS)


def test_coverage_goes_red_when_an_alone_action_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = contact_issues(DAILY_ISSUES)[0]
    without = {key: slots for key, slots in ALONE_CATALOG.items() if key != issue}
    monkeypatch.setattr(student_support, "ALONE_CATALOG", without)
    assert alone_store_gaps(DAILY_ISSUES) == [f"{issue}: contact action without an alone action"]

    number, digest, _shape = ALONE_CATALOG[issue][0]
    monkeypatch.setattr(
        student_support, "ALONE_CATALOG", {**ALONE_CATALOG, issue: ((number, digest, "sleep"),)}
    )
    assert alone_store_gaps(DAILY_ISSUES) == [
        f"{ALONE_PREFIX}{issue}.{number}: picture group must be one of the six"
    ]

    monkeypatch.setattr(student_support, "ALONE_CATALOG", {**ALONE_CATALOG, "no-such-issue": ()})
    assert alone_store_gaps(DAILY_ISSUES) == ["no-such-issue: not a Daily issue"]


def test_catalogs_are_exactly_the_checked_in_pending_sentences() -> None:
    """Editing, adding or dropping a sentence must be a deliberate catalog change (AC3)."""

    alone = {
        entry_id: digest for issue in ISSUE_KEYS for entry_id, digest, _shape in alone_slots(issue)
    }
    assert alone == {key: copy_digest(entry.text) for key, entry in ALONE.items()}
    assert dict(COMMON_LINE_CATALOG) == {
        key: copy_digest(entry.text) for key, entry in COMMON.items()
    }
    assert 2 <= len(COMMON_LINE_CATALOG) <= 4
    assert {entry.status for entry in NEW_COPY.values()} == {"pending"}
    assert {entry.category for entry in NEW_COPY.values()} == {"reading"}
    texts = [entry.text for entry in NEW_COPY.values()]
    others = {entry.text for key, entry in REGISTRY.items() if key not in NEW_COPY}
    assert len(set(texts)) == len(texts) and not set(texts) & others
    shapes = {shape for slots in ALONE_CATALOG.values() for _n, _d, shape in slots}
    assert shapes <= set(ACTION_SHAPES)


@pytest.mark.parametrize("key", sorted(NEW_COPY))
def test_new_copy_is_plain_short_and_assumes_no_family(key: str) -> None:
    text = NEW_COPY[key].text
    assert len(text) <= LIGHTER_ACTION_MAX_CHARS
    assert len(sentences(text)) == 1
    assert syllables(text) <= MAX_SENTENCE_SYLLABLES
    assert not any(count_safety(rule, text) for rule in SAFETY)
    assert count_jargon(text) == count_meta_talk(text) == count_placeholders(text) == 0
    assert english_words(text) == ()
    folded = text.casefold()
    assert not any(part in folded for part in (*BANNED_CORE_FRAGMENTS, *OPAQUE_CORE_FRAGMENTS))
    assert not any(word in folded.split() or word in folded for word in FAMILY_WORDS)
    assert not any(word in folded for word in ("bệnh", "trầm cảm", "lo âu", "chẩn đoán", "thuốc"))


@pytest.mark.parametrize("key", sorted(ALONE))
def test_alone_action_needs_no_contact_and_can_be_done_now(key: str) -> None:
    text = ALONE[key].text
    assert not needs_contact(text)
    assert has_observable_action(text)
    assert within_ten_minutes(text)


def _approve(monkeypatch: pytest.MonkeyPatch, entries: dict[str, CopyEntry]) -> None:
    approved = {
        key: CopyEntry(
            id=key,
            category=entry.category,
            text=entry.text,
            status="approved",
            approver="codex",
            date="2026-11-24",
            digest=copy_digest(entry.text),
        )
        for key, entry in entries.items()
    }
    monkeypatch.setattr(
        "app.domains.content.copy_approval._runtime_registry", lambda: {**REGISTRY, **approved}
    )


def test_nothing_is_served_while_the_sentences_are_pending() -> None:
    for issue in ISSUE_KEYS:
        assert alone_action_for(REVISION, f"psychology:{issue}") is None
        assert common_line_for(REVISION, f"psychology:{issue}") is None


def test_alone_action_is_the_issue_sentence_once_approved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _approve(monkeypatch, ALONE)
    for issue in ALONE_CATALOG:
        served = alone_action_for(REVISION, f"psychology:{issue}")
        assert served == ALONE[f"{ALONE_PREFIX}{issue}.01"].text
    assert alone_action_for(REVISION, None) is None
    assert alone_action_for(REVISION, "transit:any") is None


def test_alone_action_is_offered_only_next_to_a_contact_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC1. The offer names which of the card's actions ask to reach someone."""

    _approve(monkeypatch, ALONE)
    key = "psychology:missing-context"
    alone = ALONE[f"{ALONE_PREFIX}missing-context.01"].text
    contact = "Nhắn một câu hỏi về đúng chỗ bạn chưa hiểu."
    quiet = "Đọc lại tin nhắn một lần thật chậm."

    assert alone_offer_for(REVISION, key, contact) == (alone, ("card",))
    assert alone_offer_for(REVISION, key, quiet) is None
    assert alone_offer_for(REVISION, "transit:any", contact) is None

    kept = alone_action_projection(REVISION, keepable=True, mechanism_key=key, card_action=contact)
    assert kept is not None and kept.action == alone and kept.replaces == ("card",)
    assert kept.experiment is not None and kept.experiment.action == alone
    shown = alone_action_projection(
        REVISION, keepable=False, mechanism_key=key, card_action=contact
    )
    assert shown is not None and shown.experiment is None
    assert (
        alone_action_projection(REVISION, keepable=True, mechanism_key=key, card_action=quiet)
        is None
    )


def test_alone_offer_names_every_contact_action(monkeypatch: pytest.MonkeyPatch) -> None:
    _approve(monkeypatch, ALONE)
    quiet = "Đọc lại tin nhắn một lần thật chậm."
    monkeypatch.setattr(student_support, "lighter_action_for", lambda *_: "Nhắn một người bạn.")
    monkeypatch.setattr(
        student_support,
        "mood_action_for",
        lambda kind, *_: "Gọi một người bạn tin." if kind == "clear" else quiet,
    )
    offer = alone_offer_for(REVISION, "psychology:quick-reply", quiet)
    assert offer is not None and offer[1] == ("light", "clear")


def test_common_line_shows_only_with_fitting_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC2. Outside the named issues the line is never handed out, approved or not."""

    _approve(monkeypatch, COMMON)
    assert COMMON_LINE_ISSUES < set(ISSUE_KEYS)
    lines = {entry.text for entry in COMMON.values()}
    for issue in ISSUE_KEYS:
        line = common_line_for(REVISION, f"psychology:{issue}")
        assert (line in lines) if issue in COMMON_LINE_ISSUES else (line is None)
    for other in (None, "", "transit:any", "psychology:no-such-issue", "crisis", "safety:crisis"):
        assert common_line_for(REVISION, other) is None


def test_common_line_is_not_part_of_crisis_support() -> None:
    """AC2. Crisis and safety code never reaches this store, and their copy never says it."""

    root = Path(app.__file__).parent
    crisis_sources = [
        *sorted((root / "domains" / "safety").rglob("*.py")),
        root / "api" / "crisis_guard.py",
    ]
    assert crisis_sources and all(path.is_file() for path in crisis_sources)
    for path in crisis_sources:
        source = path.read_text(encoding="utf-8")
        assert "student_support" not in source and COMMON_LINE_PREFIX not in source
    sensitive = [
        entry.text.casefold()
        for entry in REGISTRY.values()
        if entry.category in OWNER_ONLY_CATEGORIES
    ]
    assert not any("nhiều bạn cũng" in text or "người duy nhất" in text for text in sensitive)
