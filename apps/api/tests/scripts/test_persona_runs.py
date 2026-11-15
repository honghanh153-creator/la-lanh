"""Persona runs: baselines rebuild from their .gz transcripts; workers leave no database."""

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts import persona_report, persona_sim

RUNS = persona_report.QA / "runs"


def test_the_1000_baseline_transcript_loads_from_its_gz_copy(tmp_path: Path) -> None:
    """Full rebuild of this run takes ~100 s, so the suite checks the load path and row count;
    the 100-persona run below is rebuilt in full through the same code."""

    src = RUNS / "baseline-1000-2026-11-14"
    shutil.copy(src / "transcript.jsonl.gz", tmp_path / "transcript.jsonl.gz")
    rows = persona_report.load_jsonl(tmp_path / "transcript.jsonl")
    meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
    assert len(rows) == meta["rows"] == 29000


@pytest.mark.parametrize(("run", "personas"), [("baseline-2026-11-14", "personas-100.json")])
def test_committed_baselines_rebuild_from_the_compressed_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run: str, personas: str
) -> None:
    src = RUNS / run
    dst = tmp_path / run
    dst.mkdir()
    for name in ("meta.json", "transcript.jsonl.gz"):
        shutil.copy(src / name, dst / name)  # a fresh checkout has no plain transcript.jsonl
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "persona_report",
            "--run",
            str(dst),
            "--personas",
            str(persona_report.QA / personas),
            "--title",
            run,
        ],
    )
    persona_report.main()
    for name in ("report.md", "metrics.json"):
        assert (dst / name).read_text(encoding="utf-8") == (src / name).read_text(encoding="utf-8")


def test_pct_is_not_rounded_before_the_threshold_check() -> None:
    assert persona_report.pct(1999, 2000) == pytest.approx(99.95)
    assert persona_report.fmt(persona_report.pct(1999, 2000)) == "100%"


def test_worker_removes_its_temporary_database(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_run(persona: dict[str, Any], db_url: str, labels: dict[str, str]) -> list[Any]:
        path = Path(db_url.removeprefix("sqlite+aiosqlite:///"))
        path.write_text("x")
        seen.append(str(path.parent))
        return [{"persona": persona["id"]}]

    monkeypatch.setattr(persona_sim, "_install_pick_observer", lambda: None)
    monkeypatch.setattr(persona_sim, "_labels", dict)
    monkeypatch.setattr(persona_sim, "run_persona", fake_run)
    assert persona_sim._worker([{"id": "P001"}]) == [{"persona": "P001"}]
    assert seen and not Path(seen[0]).exists()
