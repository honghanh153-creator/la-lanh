"""One command: check the personas, run all 100 for 29 days on the local API, score the run.

    pnpm personas:run                       # name = <date>-<short sha>
    pnpm personas:run -- --name after-dot1   # any label

Output: qa/personas/runs/<name>/ (report.md, metrics.json, packets for unscored items).
Synthetic data, local SQLite, no network; never touches production.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

from scripts.persona_sim import git_head

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=None)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    name = args.name or f"{date.today().isoformat()}-{git_head()[:7]}"
    out = ROOT / "qa" / "personas" / "runs" / name
    steps = [
        [sys.executable, "-m", "scripts.persona_validate"],
        [sys.executable, "-m", "scripts.persona_sim", "--out", str(out)]
        + (["--workers", str(args.workers)] if args.workers else []),
        [sys.executable, "-m", "scripts.persona_report", "--run", str(out), "--title", name],
    ]
    for step in steps:
        subprocess.run(step, check=True)  # noqa: S603 - fixed argv built above, no shell
    print(f"report: {out.relative_to(ROOT)}/report.md")


if __name__ == "__main__":
    main()
