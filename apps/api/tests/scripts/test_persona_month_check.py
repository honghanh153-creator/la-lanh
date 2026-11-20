"""The 1000-persona month check runs end to end on a few personas (US-25 AC14)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]


def test_month_check_runs_clean_on_a_few_personas(tmp_path: Path) -> None:
    # A subprocess: the check serves pending copy as approved and lifts the admission limit by
    # patching modules, which must never leak into this test process.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "scripts.persona_month_check",
            "--out",
            str(tmp_path),
            "--limit",
            "6",
            "--workers",
            "1",
        ],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["personas"] == 6
    assert summary["failures"] == {}
    assert summary["topic_answers"] == 36
    assert summary["crisis"]["missed"] == 0
