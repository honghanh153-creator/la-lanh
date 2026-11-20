"""Khám phá sentences per planet and sign (new-user persona run 20.11.2026, #773).

Two planets in one sign used to print the same "Ngoài đời" and "Khi căng" sentence. Each planet
and sign now has its own pair in the copy registry; they stay pending until Codex approves them.
"""

from __future__ import annotations

from app.domains.content import copy_approval
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS
from app.domains.readings.service import CLAIM_BODIES, SIGN_VI

KINDS = ("everyday", "watch")


def _entries() -> dict[str, copy_approval.CopyEntry]:
    entries = copy_approval.load_registry()
    return {key: entry for key, entry in entries.items() if key.startswith("insight.")}


def test_every_overview_planet_and_sign_has_its_own_pair() -> None:
    entries = _entries()
    for body in CLAIM_BODIES:
        for sign in SIGN_VI:
            for kind in KINDS:
                entry = entries.get(f"insight.{kind}.{body.value}.{sign}")
                assert entry is not None, (kind, body, sign)
                assert entry.category == "reading"
    assert len(entries) == len(CLAIM_BODIES) * len(SIGN_VI) * len(KINDS)


def test_no_two_planet_sentences_are_the_same() -> None:
    texts = [entry.text for entry in _entries().values()]
    assert len(texts) == len(set(texts))


def test_planet_sentences_are_short_plain_and_shaped_for_their_section() -> None:
    for key, entry in _entries().items():
        text = entry.text
        folded = text.casefold()
        assert len(text.split()) <= 22, key
        assert text.endswith((".", "?")), key
        assert not any(fragment in folded for fragment in BANNED_CORE_FRAGMENTS), key
        assert not any(fragment in folded for fragment in OPAQUE_CORE_FRAGMENTS), key
        if ".watch." in key:
            assert text.startswith("Khi căng, bạn dễ "), key
        else:
            assert not text.startswith("Khi căng"), key
