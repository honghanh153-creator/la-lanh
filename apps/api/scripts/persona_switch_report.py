"""Score a returning-user switch run (``persona_switch``): phase 1 + one phase-2 variant.

    python3 -I scripts/persona_switch_report.py --personas P.json --p1 RUN/p1 \
        --p2 new=RUN/p2-new --p2 old=RUN/p2-old [--json OUT.json]

Standard library only. Prints/writes counts and shares per profile type (exact, approximate,
date_only); never persona text. ``examples`` (``--examples N``) adds a few shown lines, synthetic
app copy only, for the private report.
"""

from __future__ import annotations

import argparse
import json
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

PRECISIONS = ("exact", "approximate", "date_only")
LOW_MOOD = "Đuối"
FIELDS = ("headline", "body", "action", "la_line")
ISSUE_BY_HEADLINE: dict[str, str] = {}


def norm(text: Any) -> str:
    if not text:
        return ""
    folded = " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())
    return folded.rstrip(" .!?…,;:")


def value(row: dict[str, Any], field: str) -> str:
    if row.get("status") != 200:
        return ""
    if field == "body":
        parts = [norm(row.get("thesis")), norm(row.get("scene"))]
        return " | ".join(parts) if any(parts) else ""
    return norm(row.get(field))


def load(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (path / "transcript.jsonl").open(encoding="utf-8")
        if line.strip()
    ]


def pct(n: float, d: float) -> float | None:
    return round(100.0 * n / d, 1) if d else None


def med(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 1) if xs else None


def per_persona(rows: list[dict[str, Any]], first_day: int, last_day: int) -> dict[str, Any]:
    """Repeat stats for days first_day..last_day against the person's whole history."""

    rows = sorted(rows, key=lambda r: r["day"])
    out: dict[str, Any] = {}
    for field in FIELDS:
        seen_at: dict[str, int] = {}
        seen_p1: set[str] = set()
        ever = in7 = in14 = fromp1 = days = 0
        first_repeat_day: int | None = None
        for r in rows:
            v = value(r, field)
            d = r["day"]
            if first_day <= d <= last_day and v:
                days += 1
                if v in seen_at:
                    ever += 1
                    gap = d - seen_at[v]
                    in7 += gap < 7
                    in14 += gap < 14
                    if first_repeat_day is None:
                        first_repeat_day = d
                if v in seen_p1 and r.get("phase") == 2:
                    fromp1 += 1
            if v:
                seen_at[v] = d
                if r.get("phase", 1) == 1:
                    seen_p1.add(v)
        out[field] = {
            "days": days,
            "ever": ever,
            "in7": in7,
            "in14": in14,
            "from_p1": fromp1,
            "first_repeat_day": first_repeat_day,
        }
    # 14-day topic variety: distinct situations per 14-day window inside the range. The headline
    # names its situation when the pick observer saw none (``--issue-map``).
    by_day = {
        r["day"]: r.get("situation") or ISSUE_BY_HEADLINE.get(norm(r.get("headline")))
        for r in rows
        if r.get("status") == 200
    }
    windows = []
    for start in range(first_day, last_day - 12, 14):
        topics = {by_day.get(d) for d in range(start, start + 14)} - {None}
        windows.append(len(topics))
    out["topics14"] = windows
    out["distinct_topics"] = len({by_day.get(d) for d in range(first_day, last_day + 1)} - {None})
    sel = [r for r in rows if first_day <= r["day"] <= last_day]
    out["errors"] = sum(1 for r in sel if r.get("status") != 200)
    out["low"] = sum(1 for r in sel if r.get("mood") == LOW_MOOD and r.get("status") == 200)
    out["low_lighter_shown"] = sum(
        1 for r in sel if r.get("mood") == LOW_MOOD and r.get("lighter_shown")
    )
    out["low_light"] = sum(1 for r in sel if r.get("mood") == LOW_MOOD and r.get("light"))
    return out


def safety(rows: list[dict[str, Any]], first_day: int, last_day: int) -> dict[str, Any]:
    crisis = caught = fig = fig_alarm = q = q_alarm = errors5 = 0
    for r in rows:
        if not first_day <= r["day"] <= last_day:
            continue
        for t in r.get("tarot") or []:
            if t.get("status", 0) >= 500:
                errors5 += 1
            if t["kind"] == "crisis":
                crisis += 1
                caught += bool(t.get("caught"))
            elif t["kind"] == "figurative":
                fig += 1
                fig_alarm += bool(t.get("caught"))
            else:
                q += 1
                q_alarm += bool(t.get("caught"))
    return {
        "crisis": crisis,
        "crisis_caught_pct": pct(caught, crisis),
        "figurative": fig,
        "figurative_false_alarm_pct": pct(fig_alarm, fig),
        "questions": q,
        "question_false_alarm_pct": pct(q_alarm, q),
        "tarot_5xx": errors5,
    }


def leaks(rows: list[dict[str, Any]]) -> int:
    owners: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        for t in r.get("tarot") or []:
            text = str(t.get("text") or "").strip()
            if len(text) >= 15:
                owners[text].add(r["persona"])
    found = 0
    for r in rows:
        parts = [
            r.get(k) for k in ("headline", "thesis", "scene", "la_line", "action", "why_today")
        ]
        for t in r.get("tarot") or []:
            parts += [t.get("headline"), t.get("summary")]
        shown = "\n".join(p for p in parts if isinstance(p, str))
        for text, who in owners.items():
            if r["persona"] not in who and text in shown:
                found += 1
    return found


def group(per: dict[str, dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    ids = [i for i in ids if i in per]
    m: dict[str, Any] = {"personas": len(ids)}
    for field in FIELDS:
        days = sum(per[i][field]["days"] for i in ids)
        m[field] = {
            "repeat_ever_pct": pct(sum(per[i][field]["ever"] for i in ids), days),
            "repeat_7d_pct": pct(sum(per[i][field]["in7"] for i in ids), days),
            "repeat_14d_pct": pct(sum(per[i][field]["in14"] for i in ids), days),
            "seen_in_phase1_pct": pct(sum(per[i][field]["from_p1"] for i in ids), days),
            "persona_median_repeat_ever_pct": med(
                [100.0 * per[i][field]["ever"] / max(1, per[i][field]["days"]) for i in ids]
            ),
        }
    windows = [w for i in ids for w in per[i]["topics14"]]
    m["topics14_median"] = med(windows)
    m["topics14_ge5_pct"] = pct(sum(1 for w in windows if w >= 5), len(windows))
    m["distinct_topics_median"] = med([per[i]["distinct_topics"] for i in ids])
    m["error_days"] = sum(per[i]["errors"] for i in ids)
    low = sum(per[i]["low"] for i in ids)
    m["low_mood_days"] = low
    m["low_mood_lighter_shown_pct"] = pct(sum(per[i]["low_lighter_shown"] for i in ids), low)
    m["low_mood_light_action_pct"] = pct(sum(per[i]["low_light"] for i in ids), low)
    return m


def carryover(rows: list[dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    ids_set = set(ids)
    cs = [r["carryover"] for r in rows if r.get("carryover") and r["persona"] in ids_set]
    if not cs:
        return {}
    return {
        "personas": len(cs),
        "saved_expected": sum(c["saved_expected"] for c in cs),
        "saved_found": sum(min(c["saved_found"], c["saved_expected"]) for c in cs),
        "saved_missing": sum(c["saved_missing"] for c in cs),
        "saved_without_text": sum(c["saved_without_text"] for c in cs),
        "kept_expected": sum(1 for c in cs if c["kept_expected"]),
        "kept_found": sum(1 for c in cs if c["kept_expected"] and c["kept_found"]),
        "mood_expected": sum(c["mood_expected"] for c in cs),
        "mood_found": sum(c["mood_found"] for c in cs),
        "tarot_expected": sum(c["tarot_expected"] for c in cs),
        "tarot_found": sum(c["tarot_found"] for c in cs),
        "statuses_not_200": sum(
            1
            for c in cs
            if c["saved_status"] != 200
            or c["kept_status"] != 200
            or c["retention_status"] != 200
            or c["overview_status"] != 200
        ),
        "any_5xx": sum(1 for c in cs if c["any_5xx"]),
    }


def daily_first_repeat(
    per_rows: dict[str, list[dict[str, Any]]], ids: list[str]
) -> dict[int, float]:
    """Share of people whose headline today was already shown in the previous 7 days, by day."""

    out: dict[int, float] = {}
    days = sorted({r["day"] for i in ids for r in per_rows.get(i, [])})
    for d in days:
        hits = total = 0
        for i in ids:
            rows = {r["day"]: value(r, "headline") for r in per_rows.get(i, [])}
            v = rows.get(d)
            if not v:
                continue
            total += 1
            hits += any(rows.get(d - k) == v for k in range(1, 7))
        out[d] = round(100.0 * hits / total, 1) if total else 0.0
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personas", required=True)
    parser.add_argument("--p1", required=True)
    parser.add_argument("--p2", action="append", default=[], help="name=dir")
    parser.add_argument("--json")
    parser.add_argument("--issue-map", help="JSON {normalised headline: situation key}")
    args = parser.parse_args()
    if args.issue_map:
        ISSUE_BY_HEADLINE.update(json.loads(Path(args.issue_map).read_text(encoding="utf-8")))
    personas = json.loads(Path(args.personas).read_text(encoding="utf-8"))["personas"]
    p1 = load(Path(args.p1))
    # A persona the app refused at setup (e.g. under 18 on the phase-1 start date) has no history
    # to carry over; it is left out and counted.
    served = {r["persona"] for r in p1 if r.get("status") == 200}
    groups = {
        k: [p["id"] for p in personas if p["birth"]["precision"] == k and p["id"] in served]
        for k in PRECISIONS
    }
    groups["all"] = [p["id"] for p in personas if p["id"] in served]
    result_excluded = sorted({p["id"] for p in personas} - served)
    result: dict[str, Any] = {"phase1": {}, "phase2": {}, "excluded": result_excluded}
    by1: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in p1:
        r.setdefault("phase", 1)
        by1[r["persona"]].append(r)
    per1 = {i: per_persona(rs, 0, 28) for i, rs in by1.items()}
    result["phase1"] = {
        "groups": {g: group(per1, ids) for g, ids in groups.items()},
        "safety": safety(p1, 0, 28),
        "leaks": leaks(p1),
        "headline_rep7_by_day": {
            g: daily_first_repeat(by1, ids) for g, ids in groups.items() if g != "all"
        },
    }
    for spec in args.p2:
        name, path = spec.split("=", 1)
        p2 = load(Path(path))
        both: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for i, rs in by1.items():
            both[i].extend(rs)
        for r in p2:
            both[r["persona"]].append(r)
        per2 = {i: per_persona(rs, 29, 57) for i, rs in both.items()}
        result["phase2"][name] = {
            "groups": {g: group(per2, ids) for g, ids in groups.items()},
            "carryover": {g: carryover(p2, ids) for g, ids in groups.items()},
            "safety": safety(p2, 29, 57),
            "leaks": leaks(p1 + p2),
            "headline_rep7_by_day": {
                g: daily_first_repeat(both, ids) for g, ids in groups.items() if g != "all"
            },
            "git_head": json.loads((Path(path) / "meta.json").read_text())["git_head"],
        }
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
