"""R01/R06 (audit 2026-10-22): the US-22 AC01-AC03 gate measures the real requirement and is red
on the current Hợp gu content. Strict: once the R03 content passes, this test fails until the
marker is removed and the gate joins ``pnpm check``."""

from __future__ import annotations

import json

import pytest

from scripts.audit_radar_us22 import FIXTURES, contact_specific, us22_gate


@pytest.fixture(scope="module")
def gate() -> tuple[list[str], dict[str, object]]:
    return us22_gate(json.loads(FIXTURES.read_text()))


@pytest.mark.xfail(strict=True, reason="R03 content not written yet (US-22 AC01-AC03 open)")
def test_us22_gate_passes(gate: tuple[list[str], dict[str, object]]) -> None:
    failures, _ = gate
    assert failures == []


def test_gate_measures_every_reading_of_the_fifty_pairs(
    gate: tuple[list[str], dict[str, object]],
) -> None:
    _, report = gate
    assert report["pairs"] == 50 and report["readings"] == 800
    assert set(report) >= {
        "AC01_readings_below_two_specific",
        "AC02_context_change_mean",
        "AC02_voice_change_mean",
        "AC03_cross_pair_overlap",
    }


PN = ("pluto", "square", "neptune")
MM = ("mars", "trine", "moon")
VS = ("venus", "square", "sun")
GENERIC = "một chuyện nhỏ có thể chạm đúng nút nhạy của cả hai"
K1, K2 = ("p1", "crush", "roast"), ("p2", "crush", "roast")


def test_incidental_shared_contact_gives_no_credit() -> None:
    """Codex #47 negative control: two pairs show the same generic line and happen to share
    Pluto square Neptune; nothing declares that contact as the line's source."""

    contacts = {"p1": {PN, MM}, "p2": {PN, VS}}
    visible = {K1: [GENERIC], K2: [GENERIC]}
    assert contact_specific(visible, contacts, {}) == {K1: set(), K2: set()}


def test_declared_provenance_must_be_real_cited_visible_and_unique() -> None:
    contacts = {"p1": {PN, MM}, "p2": {PN, VS}}
    line = "mars của bạn chạm moon của người kia theo góc tam hợp"
    cited = frozenset({MM})
    ok = {K1: [(line, MM, cited)]}
    assert contact_specific({K1: [line], K2: []}, contacts, ok)[K1] == {line}
    # Not cited by the highlight that shows it.
    assert (
        contact_specific({K1: [line], K2: []}, contacts, {K1: [(line, MM, frozenset({PN}))]})[K1]
        == set()
    )
    # A contact this pair does not have, or the reverse direction.
    reverse = ("moon", "trine", "mars")
    assert (
        contact_specific(
            {K1: [line], K2: []}, contacts, {K1: [(line, reverse, frozenset({reverse}))]}
        )[K1]
        == set()
    )
    # Declared but not visible.
    assert contact_specific({K1: [], K2: []}, contacts, ok)[K1] == set()
    # The same text declared for two contacts is generic.
    both = {K1: [(line, MM, cited)], K2: [(line, VS, frozenset({VS}))]}
    assert contact_specific({K1: [line], K2: [line]}, contacts, both)[K1] == set()
    # Shown in a reading whose pair lacks the declared contact.
    assert contact_specific({K1: [line], K2: [line]}, contacts, ok)[K1] == set()


def test_current_content_declares_no_contact_lines(
    gate: tuple[list[str], dict[str, object]],
) -> None:
    _, report = gate
    assert report["AC01_specific_sentences_mean"] == 0.0
