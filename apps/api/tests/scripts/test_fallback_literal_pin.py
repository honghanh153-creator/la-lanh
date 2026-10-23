"""O04 (audit 2026-10-22): copy written inside functions is pinned byte for byte."""

from __future__ import annotations

import inspect
import json
from types import ModuleType

import pytest

from app.domains.radar import reading as radar_reading
from scripts.fallback_approval import APPROVAL, current, source_literals

SAMPLE = '''
"""Module docstring with chữ Việt is not copy."""

def headline(name):
    """Docstring có dấu is not copy."""
    def inner():
        return "Câu lồng bên trong"
    return f"Chào {name}, hôm nay ổn chứ?" + "key_ascii" + inner()
'''


def test_only_in_function_non_ascii_literals_are_collected_once() -> None:
    assert sorted(source_literals(SAMPLE)) == ["Chào {}, hôm nay ổn chứ?", "Câu lồng bên trong"]


@pytest.mark.parametrize(
    ("change", "same"),
    [
        (lambda s: s.replace("hôm nay ổn", "hôm nay ốn"), False),  # one diacritic
        (lambda s: s.replace("Câu lồng", "Câu  lồng"), False),  # whitespace inside copy
        (lambda s: s.replace("{name}", "{name.upper()}"), True),  # placeholder expression only
        (lambda s: s.replace("Docstring có dấu", "Docstring đổi"), True),
        (lambda s: s.replace("def headline", "\n# comment\ndef headline"), True),
    ],
)
def test_mutations(change, same: bool) -> None:  # type: ignore[no-untyped-def]
    before = sorted(source_literals(SAMPLE))
    assert (sorted(source_literals(change(SAMPLE))) == before) is same


def test_approved_file_pins_every_module_and_matches() -> None:
    approved = json.loads(APPROVAL.read_text())["approved"]
    assert approved == current()
    keys = [
        k for block in approved.values() if isinstance(block, dict) for k in block.get("tables", {})
    ]
    pinned = {k.split("#")[0] for k in keys if k.endswith("#function_literals")}
    assert {
        "app.domains.radar.reading",
        "app.domains.readings.renderers",
        "app.domains.tarot.engine",
        "app.domains.tarot.stance",
    } <= pinned


def test_changing_one_radar_sentence_breaks_the_check(monkeypatch: pytest.MonkeyPatch) -> None:
    original = inspect.getsource(radar_reading)
    literal = next(
        text
        for text in source_literals(original)
        if len(text) > 20 and "{" not in text and original.count(text) == 1
    )
    mutated = original.replace(literal, literal[:-1] + ("x" if literal[-1] != "x" else "y"), 1)
    real = inspect.getsource

    def fake(obj: object) -> str:
        if isinstance(obj, ModuleType) and obj is radar_reading:
            return mutated
        return real(obj)  # type: ignore[arg-type]

    monkeypatch.setattr("inspect.getsource", fake)
    approved = json.loads(APPROVAL.read_text())["approved"]
    computed = current()
    assert computed["radar"]["tables"] != approved["radar"]["tables"]
    assert computed["tarot"] == approved["tarot"] and computed["daily"] == approved["daily"]
