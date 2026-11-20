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


def test_an_unsaved_older_mood_is_expected_gone_and_a_saved_one_stays(tmp_path: Path) -> None:
    persona_sim._install_pick_observer()
    db_url = f"sqlite+aiosqlite:///{tmp_path}/switch.db"
    state: dict[str, Any] = {}
    persona = _persona()
    args = argparse.Namespace(
        phase=1, start="2026-10-22", offset=0, days=3, save_every=2
    )  # saves days 0 and 2; day 1 is neither saved nor the latest
    persona_switch.run_persona(persona, db_url, {}, state, args)
    memo = json.loads(json.dumps(state))
    (row,) = persona_switch.run_persona(persona, db_url, {}, memo, _args(2, 3, 1))

    carried = row["carryover"]
    assert carried["mood_found"] == carried["mood_expected"] == 2
    assert carried["mood_expired_expected"] == 1
    assert carried["mood_expired_still_open"] == 0


def _run(path: Path, rows: list[dict[str, Any]], offset: int, days: int) -> Path:
    path.mkdir()
    (path / "transcript.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    meta = {"git_head": "x", "offset": offset, "days": days}
    (path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return path


def test_the_report_reads_phase_windows_and_keeps_unexpected_failures(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from scripts import persona_switch_report

    personas = json.loads((ROOT / "qa/personas/personas-100.json").read_text(encoding="utf-8"))
    ok, broken, refused = (p["id"] for p in personas["personas"][:3])

    def day(pid: str, d: int, headline: str | None, status: int = 200, error: str = "") -> Any:
        return {
            "persona": pid,
            "day": d,
            "phase": 1 if d < 2 else 2,
            "status": status,
            "headline": headline,
            "situation": "a",
            "error": error,
        }

    p1 = _run(
        tmp_path / "p1",
        [
            day(ok, 0, "A"),
            day(ok, 1, "B"),
            day(broken, 0, None, 500),
            day(broken, 1, None, 500),
            *(day(refused, d, None, 0, "HTTPStatusError: BIRTH_DATE_OUT_OF_RANGE") for d in (0, 1)),
        ],
        0,
        2,
    )
    p2 = _run(tmp_path / "p2", [day(ok, 2, "A"), day(broken, 2, None, 500)], 2, 1)
    out = tmp_path / "out.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--personas",
            str(ROOT / "qa/personas/personas-100.json"),
            "--p1",
            str(p1),
            "--p2",
            f"new={p2}",
            "--json",
            str(out),
        ],
    )
    persona_switch_report.main()
    result = json.loads(out.read_text(encoding="utf-8"))

    assert result["excluded"] == [refused]
    groups = result["phase2"]["new"]["groups"]["all"]
    assert groups["headline"]["repeat_ever_pct"] == 100.0  # day 2 repeats day 0
    assert groups["error_days"] == 1  # the broken persona is still counted
    assert result["phase1"]["groups"]["all"]["error_days"] == 2
