"""Re-run tarot-question-bank-v1 against the current TarotReadingEngine safety intake.

Usage (from the repo root, after `make -C vendor/swisseph`):
    cd apps/api && PYTHONPATH=. uv run python ../../docs/fixtures/validate_tarot_question_bank.py

Reports the CURRENT engine's behaviour. Expected values in the fixture describe the T2 target
(US-20); a mismatch here is not a failure of the fixture. Items with context null use "general".
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import TarotContext

BANK = Path(__file__).resolve().parent / "tarot-question-bank-v1.json"


def group(item: dict) -> str:
    kind = item["id"].split(".")[0]
    if kind == "reject":
        return f"reject.{item['id'].split('.')[1]}"
    if item.get("form") == "timing":
        return "timing.edge" if kind == "edge" else "timing.regular"
    return "edge.non_timing" if kind == "edge" else "regular.non_timing"


def main() -> None:
    engine = TarotReadingEngine()
    bank = json.loads(BANK.read_text())
    tally: dict[str, Counter] = {}
    for item in bank["items"]:
        context = TarotContext(item["context"]) if item["context"] else TarotContext.GENERAL
        accepted = engine.assess_question(item["question"], context).accepted
        tally.setdefault(group(item), Counter())["accepted" if accepted else "rejected"] += 1
    total = Counter()
    for name in sorted(tally):
        counts = tally[name]
        total.update(counts)
        n = counts["accepted"] + counts["rejected"]
        print(f"{name:22} accepted {counts['accepted']:3}/{n:3}  rejected {counts['rejected']:3}/{n:3}")
    print(f"{'all':22} accepted {total['accepted']:3}/{sum(total.values()):3}  rejected {total['rejected']:3}")


if __name__ == "__main__":
    main()
