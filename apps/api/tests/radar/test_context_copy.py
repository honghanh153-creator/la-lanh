"""Đồng nghiệp and Gia đình lines (Hợp gu AL1, 20.11.2026).

Every line a coworker or family reading can ask for exists in the copy registry, pending until
approved, and follows the same rules as the approved tables: plain words, no chart jargon in the
default view, never what the absent person thinks or feels, no fate claims. Once approved, a full
reading built from them still meets the readable contract.
"""

from datetime import UTC, datetime

import pytest

from app.domains.content.copy_approval import load_registry
from app.domains.radar import reading as radar
from app.domains.radar.readable import readable_violations
from app.domains.radar.reading import build_radar_reading
from tests.radar.test_reading import FORBIDDEN, JARGON, _bundle


def _paths() -> set[str]:
    themes = set(radar.THEME_PLAIN)
    paths = {f"tier.{key}" for key, _ in radar.TIER_BANDS} | {"tier.unclear"}
    paths |= {f"area.{key}" for key, _, _ in radar.AREAS["someone"]}
    paths |= {f"headline.{theme}" for theme in themes} | {"headline.unclear"}
    paths |= {f"fit.{theme}" for theme in themes} | {f"tension.{theme}" for theme in themes}
    paths |= {f"suggestion.{theme}.{part}" for theme in themes for part in ("action", "question")}
    paths |= {"low_signal.action", "low_signal.question"}
    return paths


@pytest.mark.parametrize("context", sorted(radar.FALLBACK_CONTEXTS))
def test_every_line_a_new_context_asks_for_is_registered(context: str) -> None:
    registry = load_registry()
    found = {
        key.removeprefix(f"radar.{context}.")
        for key in registry
        if key.startswith(f"radar.{context}.")
    }
    assert found == _paths()
    for path in found:
        entry = registry[f"radar.{context}.{path}"]
        assert entry.category == "reading"
        low = entry.text.lower()
        assert not [term for term in FORBIDDEN if term in low], entry.text
        assert not [term for term in JARGON if term in low], entry.text


def test_new_context_lines_are_their_own_sentences() -> None:
    registry = load_registry()
    texts = [
        entry.text
        for key, entry in registry.items()
        # Tier and area names are labels, shared on purpose ("Chưa đủ dữ kiện để xếp bậc").
        if key.startswith(("radar.coworker.", "radar.family."))
        and ".tier." not in key
        and ".area." not in key
    ]
    sentences = [text for text in texts if len(text.split()) >= 4]
    assert len(set(sentences)) == len(sentences)
    approved = {
        str(cell)
        for table in (radar.HEADLINES, radar.FIT_COPY, radar.TENSION_COPY)
        for row in table.values()
        for cell in row.values()
    }
    assert not approved & set(sentences)


@pytest.mark.parametrize("context", sorted(radar.FALLBACK_CONTEXTS))
def test_readings_built_from_the_lines_meet_the_readable_contract(
    context: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = load_registry()

    def as_if_approved(entry_id: str, fallback: str) -> str:
        entry = registry.get(entry_id)
        return entry.text if entry is not None else fallback

    monkeypatch.setattr(radar, "copy_text", as_if_approved)
    for hour in range(0, 24, 3):
        reading = build_radar_reading(
            _bundle(datetime(1993, 4, 1 + hour, hour, 10, tzinfo=UTC)), context=context
        )
        assert readable_violations(reading) == []
        assert (
            reading["pair_signature"]["tier"]["label"]
            == registry[f"radar.{context}.tier.{reading['pair_signature']['tier']['key']}"].text
        )
