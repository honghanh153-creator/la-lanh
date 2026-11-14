"""Check qa/personas/personas-100.json against the mix and safety-case requirements.

    uv run --directory apps/api python -m scripts.persona_validate
    uv run --directory apps/api python -m scripts.persona_validate --merge <scores.json>

``--merge`` folds a blind-judge or action-label result file into the cache under
qa/personas/labels/ (see qa/personas/judge-rubric.md).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
MOODS = {"Rực", "Chill", "Đuối", "Căng", "Lạc trôi"}
TRIGGERS = {"repetition", "generic", "mood_ignored", "task_pressure", "no_memory", "wrong_tone"}
ACTION_TAGS = {"rest", "body", "solo_reflect", "writing", "social", "planning", "study_work"}
CONTEXTS = {"general", "relationships", "work", "communication", "energy", "self_care"}
REQUIRED = (
    "id",
    "name",
    "age",
    "group",
    "segment",
    "segment_label",
    "region",
    "birth",
    "situation",
    "stressors",
    "personality",
    "daily_rhythm",
    "phone_habits",
    "wants_from_app",
    "would_quit_if",
    "quit_triggers",
    "repetition_tolerance_note",
    "task_tolerance_note",
    "mood_29",
    "mood_pattern_note",
    "keeps_actions",
    "tarot_questions",
    "traits",
    "tests",
)
_UNDER_AGE = re.compile(
    r"chưa đủ 18|chưa tròn 18|chưa 18 tuổi|vị thành niên|(?:mới|còn|chỉ) 1[0-7] tuổi"
)
_FORBIDDEN_IN_QUESTIONS = re.compile(
    r"chết|chet\b|tự tử|tu tu\b|tự làm đau|biến mất|không muốn sống"
)


def problems(data: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    personas: Sequence[Mapping[str, Any]] = data["personas"]
    if len(personas) == 1000:
        return problems_1000(data)
    if len(personas) != 100:
        out.append(f"expected 100 personas, found {len(personas)}")
    ids = [p.get("id") for p in personas]
    if len(set(ids)) != len(ids):
        out.append("duplicate ids")
    groups = Counter(p["group"] for p in personas)
    if groups["student"] < 55:
        out.append(f"students {groups['student']} < 55")
    if not 22 <= groups["worker"] <= 28:
        out.append(f"workers {groups['worker']} not about 25")
    if not 17 <= groups["other"] <= 23:
        out.append(f"others {groups['other']} not about 20")
    precision = Counter(p["birth"]["precision"] for p in personas)
    if precision != Counter({"exact": 50, "date_only": 30, "approximate": 20}):
        out.append(f"birth precision mix {dict(precision)} != 50/30/20")
    regions = Counter(p["region"] for p in personas if p["group"] == "student")
    if min(regions.get(r, 0) for r in ("north", "central", "south")) < 10:
        out.append(f"student regions too uneven {dict(regions)}")
    crisis = [p for p in personas if p["tests"]["crisis_inputs"]]
    figurative = [p for p in personas if p["tests"]["figurative_inputs"]]
    if len(crisis) < 8:
        out.append(f"crisis personas {len(crisis)} < 8")
    if len(figurative) < 15:
        out.append(f"figurative personas {len(figurative)} < 15")
    crisis_inputs = [c for p in crisis for c in p["tests"]["crisis_inputs"]]
    if {c["diacritics"] for c in crisis_inputs} != {True, False}:
        out.append("crisis inputs need both with and without diacritics")
    if len({c["directness"] for c in crisis_inputs}) < 3:
        out.append("crisis inputs need varied directness")
    for f in (f for p in figurative for f in p["tests"]["figurative_inputs"]):
        if not re.search(r"chết|chet", f["text"].casefold()):
            out.append(f"figurative input without chết: {f['text'][:30]}")
    out += persona_problems(personas)
    return out


def persona_problems(personas: Sequence[Mapping[str, Any]]) -> list[str]:
    """Field rules every persona must pass (100 and 1000 sets)."""

    out: list[str] = []
    for p in personas:
        pid = p.get("id")
        missing = [k for k in REQUIRED if k not in p]
        if missing:
            out.append(f"{pid}: missing {missing}")
            continue
        born = date.fromisoformat(p["birth"]["birth_date"])
        age = 2026 - born.year - ((11, 14) < (born.month, born.day))
        if abs(int(p["age"]) - age) > 0:
            out.append(f"{pid}: age {p['age']} != {age}")
        if age < 18:
            out.append(f"{pid}: under 18; the app is 18+ (US-02)")
        if len(p["mood_29"]) != 29 or not set(p["mood_29"]) <= MOODS:
            out.append(f"{pid}: mood_29 invalid")
        if not set(p["quit_triggers"]) <= TRIGGERS or not 1 <= len(p["quit_triggers"]) <= 3:
            out.append(f"{pid}: quit_triggers invalid")
        likes, avoids = set(p["keeps_actions"]["likes"]), set(p["keeps_actions"]["avoids"])
        if not (likes | avoids) <= ACTION_TAGS or likes & avoids or not likes:
            out.append(f"{pid}: keeps_actions invalid")
        questions = p["tarot_questions"]
        if not 3 <= len(questions) <= 6:
            out.append(f"{pid}: {len(questions)} tarot questions")
        for q in questions:
            if (
                q["context"] not in CONTEXTS
                or not 8 <= len(q["text"]) <= 280
                or not 1 <= q["day"] <= 27
            ):
                out.append(f"{pid}: tarot question invalid: {q['text'][:30]}")
            if _FORBIDDEN_IN_QUESTIONS.search(q["text"].casefold()):
                out.append(f"{pid}: ordinary tarot question touches the crisis/figurative test set")
        about = " ".join(str(p[k]) for k in ("situation", "personality", "daily_rhythm"))
        if _UNDER_AGE.search(about.casefold()):
            out.append(f"{pid}: narrative says under 18; the app is 18+ (US-02)")
        for key in ("stressors", "wants_from_app", "would_quit_if"):
            if not isinstance(p[key], list) or len(p[key]) < 2:
                out.append(f"{pid}: {key} too short")
    return out


GEN_Z_TARGET = 600
ATTRIBUTE_KEYS = (
    "gen_z",
    "lives_in",
    "living_area",
    "income",
    "platforms",
    "main_app",
    "pick_a_pile_watcher",
    "lgbtq",
    "shared_phone",
    "no_safe_person",
    "digital_literacy",
    "sleeps_after_midnight",
    "stress",
)


def problems_1000(data: Mapping[str, Any]) -> list[str]:
    """personas-1000.json: the 100 kept unchanged plus 900 new (qa/personas/README-1000.md)."""

    out: list[str] = []
    personas: Sequence[Mapping[str, Any]] = data["personas"]
    base = json.loads((QA / "personas-100.json").read_text(encoding="utf-8"))["personas"]
    if [dict(p) for p in personas[:100]] != base:
        out.append("first 100 personas differ from personas-100.json")
    ids = [p.get("id") for p in personas]
    if ids != [f"P{i:03d}" for i in range(1, 1001)]:
        out.append("ids must be P001..P1000 in order")
    precision = Counter(p["birth"]["precision"] for p in personas)
    if precision != Counter({"exact": 500, "date_only": 300, "approximate": 200}):
        out.append(f"birth precision mix {dict(precision)} != 500/300/200")
    gen_z = sum(1 for p in personas if int(p["age"]) <= 24)
    if not GEN_Z_TARGET - 30 <= gen_z <= GEN_Z_TARGET + 30:
        out.append(f"aged 18-24: {gen_z}, want about {GEN_Z_TARGET}")
    regions = Counter(p["region"] for p in personas)
    if min(regions.get(r, 0) for r in ("north", "central", "south")) < 150:
        out.append(f"regions too uneven {dict(regions)}")
    crisis = [p for p in personas if p["tests"]["crisis_inputs"]]
    figurative = [p for p in personas if p["tests"]["figurative_inputs"]]
    if not 95 <= len(crisis) <= 105:
        out.append(f"crisis personas {len(crisis)}, want about 10%")
    if not 170 <= len(figurative) <= 190:
        out.append(f"figurative personas {len(figurative)}, want about 18%")
    crisis_inputs = [c for p in crisis for c in p["tests"]["crisis_inputs"]]
    if {c["diacritics"] for c in crisis_inputs} != {True, False}:
        out.append("crisis inputs need both with and without diacritics")
    if len({c["directness"] for c in crisis_inputs}) < 4:
        out.append("crisis inputs need all four kinds of directness")
    for f in (f for p in figurative for f in p["tests"]["figurative_inputs"]):
        if not re.search(r"chết|chet", f["text"].casefold()):
            out.append(f"figurative input without chết: {f['text'][:30]}")
    for p in personas[100:]:
        missing = [k for k in ATTRIBUTE_KEYS if k not in p.get("attributes", {})]
        if missing:
            out.append(f"{p['id']}: attributes missing {missing}")
    out += persona_problems(personas)
    return out


def merge(path: Path) -> str:
    """Fold a scorer's output into the content-hash cache. Accepts a list of
    {"item_id", "score", "reason"} (judge) or {"action", "label"} (action weight)."""

    items: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    labels_dir = QA / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    if items and "item_id" in items[0]:
        target = labels_dir / "judge-scores.json"
        cache: dict[str, Any] = (
            json.loads(target.read_text(encoding="utf-8"))
            if target.exists()
            else {"rubric": "judge-rubric-v1-2026-11-14", "scores": {}}
        )
        for item in items:
            score = int(item["score"])
            if not 1 <= score <= 5:
                raise ValueError(f"score out of range: {item}")
            cache["scores"][item["item_id"]] = {
                "score": score,
                "reason": str(item.get("reason", ""))[:300],
            }
        count = len(cache["scores"])
    else:
        target = labels_dir / "action-weight.json"
        cache = (
            json.loads(target.read_text(encoding="utf-8"))
            if target.exists()
            else {"rubric": "judge-rubric-v1-2026-11-14", "labels": {}}
        )
        for item in items:
            if item["label"] not in {"light", "not_light"}:
                raise ValueError(f"bad label: {item}")
            cache["labels"][item["action"]] = item["label"]
        count = len(cache["labels"])
    target.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return f"{target.relative_to(ROOT)}: {count} entries"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merge", nargs="*", default=None)
    parser.add_argument("--personas", default=str(QA / "personas-100.json"))
    args = parser.parse_args()
    if args.merge:
        for name in args.merge:
            print(merge(Path(name)))
        return
    found = problems(json.loads(Path(args.personas).read_text(encoding="utf-8")))
    for line in found:
        print(line)
    print("ok" if not found else f"{len(found)} problems")
    raise SystemExit(1 if found else 0)


if __name__ == "__main__":
    main()
