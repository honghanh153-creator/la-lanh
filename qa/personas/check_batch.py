"""Check one writer batch for personas-1000 against its skeleton.

    python3 check_batch.py skeleton-NN.json out-NN.json

Prints "ok" or one problem per line. Same field rules as apps/api/scripts/persona_validate.py.
"""

from __future__ import annotations

import json
import re
import sys

TRIGGERS = {"repetition", "generic", "mood_ignored", "task_pressure", "no_memory", "wrong_tone"}
ACTION_TAGS = {"rest", "body", "solo_reflect", "writing", "social", "planning", "study_work"}
CONTEXTS = {"general", "relationships", "work", "communication", "energy", "self_care"}
FORBIDDEN = re.compile(r"chết|chet\b|tự tử|tu tu\b|tự làm đau|biến mất|không muốn sống")
TEXT = ("name", "situation", "personality", "daily_rhythm", "phone_habits",
        "repetition_tolerance_note", "task_tolerance_note", "mood_pattern_note")
LISTS = ("stressors", "wants_from_app", "would_quit_if")
NARRATIVE = TEXT + LISTS + ("quit_triggers", "keeps_actions", "tarot_questions")


def problems(skeleton: list[dict], written: list[dict]) -> list[str]:
    out: list[str] = []
    want = {p["id"] for p in skeleton}
    got = [w.get("id") for w in written]
    if set(got) != want or len(got) != len(want):
        out.append(f"ids differ: missing {sorted(want - set(got))}, extra {sorted(set(got) - want)}")
    for w in written:
        pid = w.get("id")
        for k in NARRATIVE:
            if k not in w:
                out.append(f"{pid}: missing {k}")
        if any(k not in w for k in NARRATIVE):
            continue
        for k in TEXT:
            if not isinstance(w[k], str) or len(w[k].strip()) < 2:
                out.append(f"{pid}: {k} empty")
        for k in LISTS:
            if not isinstance(w[k], list) or len(w[k]) < 2:
                out.append(f"{pid}: {k} needs at least 2 items")
        if not set(w["quit_triggers"]) <= TRIGGERS or not 1 <= len(w["quit_triggers"]) <= 3:
            out.append(f"{pid}: quit_triggers invalid")
        ka = w["keeps_actions"]
        likes, avoids = set(ka.get("likes", [])), set(ka.get("avoids", []))
        if not (likes | avoids) <= ACTION_TAGS or likes & avoids or not likes or "note" not in ka:
            out.append(f"{pid}: keeps_actions invalid")
        qs = w["tarot_questions"]
        if not 3 <= len(qs) <= 6:
            out.append(f"{pid}: needs 3-6 tarot questions")
        for q in qs:
            if (q.get("context") not in CONTEXTS or not 8 <= len(q.get("text", "")) <= 280
                    or not 1 <= int(q.get("day", 0)) <= 27):
                out.append(f"{pid}: tarot question invalid: {q.get('text', '')[:30]}")
            if FORBIDDEN.search(q.get("text", "").casefold()):
                out.append(f"{pid}: tarot question uses a forbidden word: {q['text'][:30]}")
        blob = " ".join(str(w[k]) for k in TEXT + LISTS)
        if FORBIDDEN.search(blob.casefold()):
            out.append(f"{pid}: narrative uses a crisis/forbidden word")
    return out


def main() -> None:
    skeleton = json.load(open(sys.argv[1], encoding="utf-8"))
    skeleton = skeleton["personas"] if isinstance(skeleton, dict) else skeleton
    written = json.load(open(sys.argv[2], encoding="utf-8"))
    found = problems(skeleton, written)
    print("\n".join(found) if found else "ok")


if __name__ == "__main__":
    main()
