"""The legacy-copy release comparison is a real gate (Codex P3 on #29).

No git history is needed: the "historical" files are copies of the current sources, so the
comparison starts identical and each negative control changes one current value.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.domains.tarot import examples, relationship_readings, voice
from scripts import compare_tarot_release_copy as compare

SOURCE = Path(compare.__file__).resolve().parents[1] / "app" / "domains" / "tarot"


@pytest.fixture
def historical(tmp_path: Path) -> Path:
    for name in compare.MODULES:
        shutil.copy(SOURCE / f"{name}.py", tmp_path / f"{name}.py")
    return tmp_path


def test_identical_sources_exit_zero(historical: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert compare.main(["--historical-dir", str(historical)]) == 0
    assert capsys.readouterr().out.rstrip().endswith("ALL IDENTICAL")


def test_historical_examples_import_the_historical_relationship_table(historical: Path) -> None:
    loaded = compare.load_historical(historical)
    old_examples = loaded["examples"].RELATIONSHIP_EXAMPLES
    assert old_examples is loaded["relationship_readings"].RELATIONSHIP_EXAMPLES
    assert old_examples is not relationship_readings.RELATIONSHIP_EXAMPLES


def test_negative_control_changed_relationship_examples_are_caught(
    historical: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Before the fix the historical examples imported the current table, so this row compared
    the current dictionary with itself and still said identical."""

    edited = dict(relationship_readings.RELATIONSHIP_EXAMPLES)
    key = next(iter(edited))
    edited[key] = f"{edited[key]} (sửa)"
    monkeypatch.setattr(relationship_readings, "RELATIONSHIP_EXAMPLES", edited)
    monkeypatch.setattr(examples, "RELATIONSHIP_EXAMPLES", edited)
    assert compare.main(["--historical-dir", str(historical)]) == 1
    out = capsys.readouterr().out
    assert "examples.RELATIONSHIP_EXAMPLES: DIFFERENT" in out
    assert "relationship_readings.RELATIONSHIP_EXAMPLES: DIFFERENT" in out
    assert "MISMATCH" in out


def test_negative_control_a_mismatch_exits_non_zero(
    historical: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Before the fix a mismatch printed MISMATCH but exited 0."""

    edited = dict(voice.ROAST_HEADLINES)
    key = next(iter(edited))
    edited[key] = f"{edited[key]} (sửa)"
    monkeypatch.setattr(voice, "ROAST_HEADLINES", edited)
    assert compare.main(["--historical-dir", str(historical)]) == 1
    out = capsys.readouterr().out
    assert "voice.ROAST_HEADLINES: DIFFERENT" in out and "MISMATCH (1)" in out


def test_release_must_be_a_commit_hash(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="commit hash"):
        compare.export("HEAD; rm -rf /", tmp_path)
