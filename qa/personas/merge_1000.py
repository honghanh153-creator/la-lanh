"""Merge personas-100.json, the 900 seeded skeletons and the writers' narrative batches.

    python3 qa/personas/merge_1000.py <dir with out-NN.json> > qa/personas/personas-1000.json

The skeleton is rebuilt from build_skeleton_1000.py (deterministic), so only the writers'
narrative fields come from the batch files. Skeleton fields always win over anything a writer
returned under the same key.
"""

from __future__ import annotations

import glob
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_skeleton_1000  # noqa: E402

NARRATIVE = (
    "name", "situation", "stressors", "personality", "daily_rhythm", "phone_habits",
    "wants_from_app", "would_quit_if", "quit_triggers", "repetition_tolerance_note",
    "task_tolerance_note", "mood_pattern_note", "keeps_actions", "tarot_questions",
)
ORDER = (
    "id", "name", "age", "group", "segment", "segment_label", "region", "hometown", "major",
    "birth", "attributes", "situation", "stressors", "personality", "daily_rhythm",
    "phone_habits", "wants_from_app", "would_quit_if", "quit_triggers",
    "repetition_tolerance_note", "task_tolerance_note", "traits", "mood_kind", "mood_29",
    "mood_pattern_note", "keeps_actions", "tarot_questions", "tests",
)


def main() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        build_skeleton_1000.main()
    skeleton = json.loads(buf.getvalue())["personas"]
    written: dict[str, dict] = {}
    for path in sorted(glob.glob(str(Path(sys.argv[1]) / "out-*.json"))):
        for item in json.loads(Path(path).read_text(encoding="utf-8")):
            written[item["id"]] = item
    merged = []
    for sk in skeleton:
        w = written[sk["id"]]
        row = {**{k: w[k] for k in NARRATIVE}, **sk}
        merged.append({k: row[k] for k in ORDER if k in row})
    base = json.loads((HERE / "personas-100.json").read_text(encoding="utf-8"))
    out = {
        "version": "personas-1000-v1-2026-11-14",
        "note": "P001-P100 = personas-100.json unchanged; P101-P1000 from build_skeleton_1000.py "
        "plus blind writer batches. All fictional.",
        "personas": base["personas"] + merged,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
