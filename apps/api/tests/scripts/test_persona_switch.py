"""Returning-user switch harness: the same person carries over from phase 1 to phase 2.

Runs one synthetic persona against a temporary SQLite file: two days in phase 1, then a phase 2
day on a fresh app over the same database and guest cookie (as a release switch would), and
checks that what the person saved in phase 1 still opens. Also covers the scorer's repeat rule.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import persona_sim, persona_switch
from scripts.persona_switch_report import group, per_persona

ROOT = Path(__file__).resolve().parents[4]


def _persona() -> dict[str, Any]:
    personas = json.loads((ROOT / "qa/personas/personas-100.json").read_text(encoding="utf-8"))
    return next(p for p in personas["personas"] if p["birth"]["precision"] == "date_only")


def _args(phase: int, offset: int, days: int) -> argparse.Namespace:
    return argparse.Namespace(
        phase=phase, start="2026-10-22", offset=offset, days=days, save_every=1
    )


def test_a_person_carries_over_to_a_new_app_with_the_same_database(tmp_path: Path) -> None:
    persona_sim._install_pick_observer()
    db_url = f"sqlite+aiosqlite:///{tmp_path}/switch.db"
    state: dict[str, Any] = {}
    persona = _persona()

    first = persona_switch.run_persona(persona, db_url, {}, state, _args(1, 0, 2))
    memo = json.loads(json.dumps(state))  # what the state file keeps between processes
    second = persona_switch.run_persona(persona, db_url, {}, memo, _args(2, 2, 1))

    assert [r["day"] for r in first] == [0, 1]
    assert [r["phase"] for r in first] == [1, 1]
    assert all(r["status"] == 200 and r["save_status"] in (200, 201) for r in first)
    assert [(r["day"], r["phase"], r["status"]) for r in second] == [(2, 2, 200)]
    carried = second[0]["carryover"]
    assert carried["saved_expected"] == 2
    assert carried["saved_found"] == 2
    assert carried["saved_missing"] == 0
    assert carried["mood_found"] == carried["mood_expected"] == 2
    assert not carried["any_5xx"]
    assert second[0]["date"] == "2026-10-24"


def test_repeats_count_against_the_whole_history_and_phase_one() -> None:
    def row(day: int, headline: str, phase: int) -> dict[str, Any]:
        return {"day": day, "phase": phase, "status": 200, "headline": headline, "situation": "a"}

    rows = [row(0, "A", 1), row(1, "B", 1), row(2, "A", 2), row(10, "B", 2), row(11, "C", 2)]
    stats = per_persona(rows, 2, 11)

    headline = stats["headline"]
    assert headline["days"] == 3
    assert headline["ever"] == 2  # A (seen day 0) and B (seen day 1)
    assert headline["in7"] == 1  # A after 2 days; B came back after 9
    assert headline["from_p1"] == 2
    summary = group({"p": stats}, ["p"])
    assert summary["headline"]["repeat_ever_pct"] == round(100 * 2 / 3, 1)
