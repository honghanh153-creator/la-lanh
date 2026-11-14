"""python3 check_judged.py BATCH OUT.json  -> prints ok or problems (run from the conc1000 folder)."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
batch = sys.argv[1]
out = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
entry = next(b for b in man["batches"] + man.get("codex_batches", []) if b["batch"] == batch)
want = [p["id"] for p in json.loads((HERE / batch / "personas.json").read_text(encoding="utf-8"))]
codes = set(entry.get("codes") or [])
V2 = man.get("judge_version") == 2
SCORES = ("understood", "less_alone", "peaceful", "want_return", "return_next_week", "share_score")
BOOLS = ("save_image", "send_or_post", "invite", "blame", "pressure", "privacy", "dependence",
         "must_check_la", "privacy_exposure", "unsafe_content", "game_played")
probs = []
got = [r.get("persona") for r in out]
if sorted(got) != sorted(want):
    probs.append(f"personas differ: missing {sorted(set(want) - set(got))}, extra {sorted(set(got) - set(want))}")
for r in out:
    pid = r.get("persona")
    for k in ("path_X", "path_Y", "complaint", "still_missing"):
        if not isinstance(r.get(k), str) or not r[k].strip():
            probs.append(f"{pid}: {k} empty")
    for side in ("X", "Y"):
        b = r.get(side) or {}
        for k in SCORES:
            if not isinstance(b.get(k), int) or not 1 <= b[k] <= 5:
                probs.append(f"{pid} {side}: {k} must be int 1-5")
        for k in BOOLS:
            if not isinstance(b.get(k), bool):
                probs.append(f"{pid} {side}: {k} must be true/false")
        if b.get("game_played") is False and any(b.get(k) is not None for k in
                                                  ("game_understood", "game_could_stop", "game_hurt")):
            probs.append(f"{pid} {side}: game fields must be null when game_played is false")
        if V2:
            for k in ("teased", "la_nhay_wrong_time", "quiz_card_shared"):
                if not isinstance(b.get(k), bool):
                    probs.append(f"{pid} {side}: {k} must be true/false")
            if b.get("lesson_entry", "x") not in ("ba_lo", "kham_pha", None):
                probs.append(f"{pid} {side}: lesson_entry must be ba_lo, kham_pha or null")
            if (b.get("lesson_entry") is None) != (b.get("lesson_pressure", "x") is None) or (
                    b.get("lesson_pressure") not in (True, False, None)):
                probs.append(f"{pid} {side}: lesson_pressure is true/false when a lesson was opened, else null")
            if b.get("chart_line", "x") not in ("right", "overclaim", "unnoticed", None):
                probs.append(f"{pid} {side}: chart_line must be right, overclaim, unnoticed or null")
        if not isinstance(b.get("quotes"), dict):
            probs.append(f"{pid} {side}: quotes must be an object")
    have = set((r.get("concepts") or {}).keys())
    if codes and have != codes:
        probs.append(f"{pid}: concepts keys {sorted(have)} != {sorted(codes)}")
print("\n".join(probs[:40]) if probs else "ok")
