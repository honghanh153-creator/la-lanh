"""Score a persona run against the pre-registered thresholds (qa/personas/thresholds.md).

    uv run --directory apps/api python -m scripts.persona_report --run ../../qa/personas/runs/<name>

Reads ``transcript.jsonl`` from the run, the personas, the blind action labels and the blind
judge scores (both cached by content hash under qa/personas/labels/). Writes ``metrics.json``
and ``report.md`` into the run folder, plus ``judge-packets.jsonl`` / ``label-packets.jsonl``
for any judged day or action text that has no cached score yet. A missing score is reported
as missing, never guessed: the "understood" metric shows its coverage, and the return model
uses 3.0 (neutral) for unscored days and says so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_metrics import (
    BENCHMARK_D7,
    JUDGED_DAYS,
    LOW_MOOD,
    THRESHOLDS_VERSION,
    DayExperience,
    active_curve,
    calibrate,
    contradicts_mood,
    distinct_in_windows,
    population_curve,
    repeats_ever,
    repeats_within,
    retention,
)

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
PRECISION_VI = {
    "date_only": "chỉ ngày sinh",
    "approximate": "giờ khoảng",
    "exact": "giờ + nơi chính xác",
}
GROUP_VI = {"student": "sinh viên", "worker": "người đi làm trẻ", "other": "nhóm khác"}
JUDGE_PROFILE_KEYS = (
    "name",
    "age",
    "segment_label",
    "situation",
    "stressors",
    "personality",
    "daily_rhythm",
    "wants_from_app",
    "would_quit_if",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def item_id(row: Mapping[str, Any]) -> str:
    parts = [row["persona"], str(row["day"]), row.get("mood") or ""] + [
        str(row.get(k) or "")
        for k in ("headline", "thesis", "scene", "action", "la_line", "why_today", "mood_reaction")
    ]
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]


def judge_packet(persona: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    profile = {k: persona.get(k) for k in JUDGE_PROFILE_KEYS}
    profile["what_they_entered"] = PRECISION_VI[persona["birth"]["precision"]]
    return {
        "item_id": item_id(row),
        "profile": profile,
        "today": {
            "mood_they_picked": row.get("mood"),
            "headline": row.get("headline"),
            "explanation": row.get("thesis"),
            "real_life_scene": row.get("scene"),
            "small_action": row.get("action"),
            "la_line": row.get("la_line"),
            "why_today": row.get("why_today"),
            "la_reaction_to_mood": row.get("mood_reaction"),
        },
    }


def pct(numerator: float, denominator: float) -> float | None:
    return round(100.0 * numerator / denominator, 1) if denominator else None


def fmt(value: float | None, suffix: str = "%") -> str:
    return "—" if value is None else f"{value:g}{suffix}"


def verdict(ok: bool | None) -> str:
    return "chưa đo" if ok is None else ("ĐẠT" if ok else "TRƯỢT")


def repetition(
    rows_by_p: Mapping[str, Sequence[Mapping[str, Any]]], ids: Iterable[str]
) -> dict[str, Any]:
    windows: list[int] = []
    headline_repeat_days = 0
    personas_with_headline_repeat = 0
    la_repeat = la_days = 0
    per_persona_la: list[float] = []
    n = 0
    for pid in ids:
        rows = rows_by_p[pid]
        n += 1
        sit = [
            r.get("situation") or (f"la:{r.get('la_line')}" if r.get("la_line") else None)
            for r in rows
        ]
        windows.extend(distinct_in_windows(sit, 14))
        heads = [r.get("headline") for r in rows]
        rep = repeats_within(heads, 7)
        headline_repeat_days += rep
        personas_with_headline_repeat += rep > 0
        las = [r.get("la_line") for r in rows]
        own = repeats_ever(las)
        la_repeat += own
        la_days += max(0, len(las) - 1)
        per_persona_la.append(own / max(1, len(las) - 1))
    return {
        "personas": n,
        "windows": len(windows),
        "windows_ge5": sum(1 for w in windows if w >= 5),
        "windows_ge5_pct": pct(sum(1 for w in windows if w >= 5), len(windows)),
        "situations_per_14d_median": statistics.median(windows) if windows else None,
        "situations_per_14d_min": min(windows) if windows else None,
        "headline_repeat_days": headline_repeat_days,
        "personas_with_headline_repeat": personas_with_headline_repeat,
        "la_line_repeat_pct": pct(la_repeat, la_days),
        "la_line_repeat_median_persona_pct": round(100 * statistics.median(per_persona_la), 1)
        if per_persona_la
        else None,
    }


def experiences(
    personas: Sequence[Mapping[str, Any]],
    rows_by_p: Mapping[str, Sequence[Mapping[str, Any]]],
    scores: Mapping[str, float],
) -> tuple[dict[str, list[DayExperience]], dict[str, float | None]]:
    out: dict[str, list[DayExperience]] = {}
    persona_mean: dict[str, float | None] = {}
    for persona in personas:
        pid = persona["id"]
        rows = rows_by_p[pid]
        judged = [
            scores[item_id(r)] for r in rows if r["day"] in JUDGED_DAYS and item_id(r) in scores
        ]
        mean = statistics.fmean(judged) if judged else None
        persona_mean[pid] = mean
        exp: list[DayExperience] = []
        for i, row in enumerate(rows):
            if row.get("status") != 200:
                exp.append(DayExperience(understood=1.0, mood_miss=True))
                continue
            u = scores.get(item_id(row), mean if mean is not None else 3.0)
            heads = [r.get("headline") for r in rows[max(0, i - 6) : i]]
            sits = [r.get("situation") or r.get("la_line") for r in rows[max(0, i - 2) : i]]
            las = [r.get("la_line") for r in rows[max(0, i - 6) : i]]
            here_sit = row.get("situation") or row.get("la_line")
            repeated = (
                (row.get("headline") is not None and row.get("headline") in heads)
                or (len(sits) == 2 and all(s == here_sit for s in sits))
                or las.count(row.get("la_line")) >= 3
            )
            mood_miss = (row.get("mood") == LOW_MOOD and not row.get("light")) or contradicts_mood(
                row.get("la_line"), row.get("mood")
            )
            crisis_miss = any(
                t["kind"] == "crisis" and not t["caught"] for t in row.get("tarot", [])
            )
            exp.append(
                DayExperience(
                    understood=float(u),
                    repeated=bool(repeated),
                    mood_miss=bool(mood_miss),
                    task_heavy=not row.get("light"),
                    crisis_miss=crisis_miss,
                    return_path=bool(row.get("return_path")),
                    memory=bool(row.get("memory")),
                    kept=bool(row.get("kept")),
                )
            )
        out[pid] = exp
    return out, persona_mean


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--personas", default=str(QA / "personas-100.json"))
    parser.add_argument("--title", default=None)
    args = parser.parse_args()
    run = Path(args.run)
    personas: list[dict[str, Any]] = json.loads(Path(args.personas).read_text(encoding="utf-8"))[
        "personas"
    ]
    by_id = {p["id"]: p for p in personas}
    rows = load_jsonl(run / "transcript.jsonl")
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
    rows_by_p: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_p[row["persona"]].append(row)
    for pid in rows_by_p:
        rows_by_p[pid].sort(key=lambda r: r["day"])
    personas = [p for p in personas if p["id"] in rows_by_p]

    labels_path = QA / "labels" / "action-weight.json"
    judge_path = QA / "labels" / "judge-scores.json"
    labels: dict[str, str] = (
        json.loads(labels_path.read_text(encoding="utf-8"))["labels"]
        if labels_path.exists()
        else {}
    )
    scores_raw: dict[str, Any] = (
        json.loads(judge_path.read_text(encoding="utf-8"))["scores"] if judge_path.exists() else {}
    )
    scores = {k: float(v["score"]) for k, v in scores_raw.items()}

    # ---- packets for anything not yet blind-scored
    judge_needed = [
        judge_packet(by_id[r["persona"]], r)
        for r in rows
        if r["day"] in JUDGED_DAYS and r.get("status") == 200
    ]
    missing_judge = [p for p in judge_needed if p["item_id"] not in scores]
    actions = sorted({r["action_norm"] for r in rows if r.get("action_norm")})
    missing_labels = [a for a in actions if a not in labels]
    with (run / "judge-packets.jsonl").open("w", encoding="utf-8") as handle:
        for packet in missing_judge:
            handle.write(json.dumps(packet, ensure_ascii=False) + "\n")
    with (run / "label-packets.jsonl").open("w", encoding="utf-8") as handle:
        for text in missing_labels:
            handle.write(json.dumps({"action": text}, ensure_ascii=False) + "\n")

    # ---- re-evaluate light with the current label cache (the sim may have run before labelling)
    for row in rows:
        if row.get("action_norm") in labels and row.get("light_source") != "api":
            row["light"] = labels[row["action_norm"]] == "light"
            row["light_source"] = "label"

    groups = {
        "all": [p["id"] for p in personas],
        **{
            f"precision:{k}": [p["id"] for p in personas if p["birth"]["precision"] == k]
            for k in PRECISION_VI
        },
    }
    rep = {name: repetition(rows_by_p, ids) for name, ids in groups.items() if ids}

    ok_rows = [r for r in rows if r.get("status") == 200]
    low = [r for r in ok_rows if r.get("mood") == LOW_MOOD]
    low_light = sum(1 for r in low if r.get("light"))
    contra = [r for r in ok_rows if contradicts_mood(r.get("la_line"), r.get("mood"))]
    contra_head = [
        r
        for r in ok_rows
        if contradicts_mood(r.get("headline"), r.get("mood"))
        or contradicts_mood(r.get("thesis"), r.get("mood"))
    ]
    action_changed = sum(
        1
        for r in ok_rows
        if (r.get("before_mood") or {}).get("action") not in (None, r.get("action"))
    )
    tarot = [t for r in rows for t in r.get("tarot", [])]
    crisis = [t for t in tarot if t["kind"] == "crisis"]
    figurative = [t for t in tarot if t["kind"] == "figurative"]
    ordinary = [t for t in tarot if t["kind"] == "question"]

    judged = [scores[p["item_id"]] for p in judge_needed if p["item_id"] in scores]
    exp, persona_mean = experiences(personas, rows_by_p, scores)
    k_h, alpha = calibrate(personas)
    curve = population_curve(personas, exp, k_h, alpha)
    ref = population_curve(
        personas, {p["id"]: [DayExperience()] * len(curve) for p in personas}, k_h, alpha
    )
    by_segment: dict[str, list[str]] = defaultdict(list)
    for p in personas:
        by_segment[p["segment_label"]].append(p["id"])
    seg_rows = []
    for seg, ids in by_segment.items():
        curves = [active_curve(by_id[i], exp[i], k_h, alpha) for i in ids]
        means = [m for i in ids if (m := persona_mean[i]) is not None]
        seg_rows.append(
            {
                "segment": seg,
                "n": len(ids),
                "D7": round(statistics.fmean(c[7] for c in curves), 4),
                "D28": round(statistics.fmean(c[28] for c in curves), 4),
                "understood": round(statistics.fmean(means), 2) if means else None,
                "precision": dict(Counter(by_id[i]["birth"]["precision"] for i in ids)),
                "situations_14d_median": rep_seg(rows_by_p, ids),
            }
        )
    seg_rows.sort(key=lambda s: (s["D7"], s["understood"] or 0))
    ret_by: dict[str, dict[str, float]] = {}
    for name, ids in {
        **groups,
        **{f"group:{g}": [p["id"] for p in personas if p["group"] == g] for g in GROUP_VI},
    }.items():
        if ids:
            sub = [by_id[i] for i in ids]
            ret_by[name] = retention(population_curve(sub, {i: exp[i] for i in ids}, k_h, alpha))

    persona_means = [m for m in persona_mean.values() if m is not None]
    metrics: dict[str, Any] = {
        "thresholds_version": THRESHOLDS_VERSION,
        "run": meta,
        "repetition": rep,
        "mood": {
            "low_days": len(low),
            "low_light": low_light,
            "low_light_pct": pct(low_light, len(low)),
            "light_sources_low_days": dict(Counter(r.get("light_source") for r in low)),
            "la_contradictions": len(contra),
            "la_contradiction_examples": [[r["mood"], r["la_line"]] for r in contra[:5]],
            "headline_contradictions": len(contra_head),
            "headline_contradiction_examples": [
                [r["mood"], r.get("headline"), r.get("thesis")] for r in contra_head[:5]
            ],
            "days_action_changed_after_mood_pct": pct(action_changed, len(ok_rows)),
        },
        "crisis": {
            "crisis_inputs": len(crisis),
            "crisis_caught": sum(t["caught"] for t in crisis),
            "crisis_caught_pct": pct(sum(t["caught"] for t in crisis), len(crisis)),
            "figurative_inputs": len(figurative),
            "figurative_flagged": sum(t["caught"] for t in figurative),
            "figurative_fp_pct": pct(sum(t["caught"] for t in figurative), len(figurative)),
            "ordinary_questions": len(ordinary),
            "ordinary_flagged": sum(t["caught"] for t in ordinary),
            "crisis_statuses": dict(Counter(str(t["status"]) for t in crisis)),
        },
        "understood": {
            "items_needed": len(judge_needed),
            "items_scored": len(judged),
            "mean": round(statistics.fmean(judged), 2) if judged else None,
            "personas_scored": len(persona_means),
            "personas_ge3_pct": pct(sum(1 for m in persona_means if m >= 3.0), len(persona_means)),
            "distribution": dict(sorted(Counter(int(s) for s in judged).items())),
        },
        "return_model": {
            "calibration": {
                "k_hazard": round(k_h, 5),
                "alpha": round(alpha, 5),
                "reference": retention(ref),
            },
            "all": retention(curve),
            "by": ret_by,
            "segments_worst_first": seg_rows,
        },
        "coverage": {
            "persona_days": len(rows),
            "http_errors": len(rows) - len(ok_rows),
            "action_texts": len(actions),
            "action_texts_unlabelled": len(missing_labels),
            "judge_items_missing": len(missing_judge),
            "experiment_offered_pct": pct(
                sum(1 for r in ok_rows if r.get("experiment_offered")), len(ok_rows)
            ),
            "kept_days": sum(1 for r in ok_rows if r.get("kept")),
            "wants_keep_days": sum(1 for r in ok_rows if r.get("wants_keep")),
            "return_path_days": sum(1 for r in ok_rows if r.get("return_path")),
            "memory_days": sum(1 for r in ok_rows if r.get("memory")),
            "why_today_days": sum(1 for r in ok_rows if r.get("why_today")),
        },
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (run / "report.md").write_text(render(metrics, args.title or run.name), encoding="utf-8")
    print(
        json.dumps(
            {k: metrics[k] for k in ("mood", "crisis", "understood", "coverage")},
            ensure_ascii=False,
        )[:2000]
    )
    print(json.dumps(metrics["return_model"]["all"]), json.dumps(rep["all"], ensure_ascii=False))


def rep_seg(
    rows_by_p: Mapping[str, Sequence[Mapping[str, Any]]], ids: Sequence[str]
) -> float | None:
    windows: list[int] = []
    for pid in ids:
        sit = [r.get("situation") or r.get("la_line") for r in rows_by_p[pid]]
        windows.extend(distinct_in_windows(sit, 14))
    return statistics.median(windows) if windows else None


def table_row(*cells: object) -> str:
    return "| " + " | ".join("—" if c is None else str(c) for c in cells) + " |"


def render(m: Mapping[str, Any], title: str) -> str:
    rep = m["repetition"]
    a = rep["all"]
    mood = m["mood"]
    cr = m["crisis"]
    u = m["understood"]
    rm = m["return_model"]
    ret = rm["all"]
    full_judge = u["items_scored"] == u["items_needed"] and u["items_needed"] > 0
    rows = [
        (
            "Lặp lại",
            "Số chuyện khác nhau mỗi 14 ngày ≥ 5 (mọi người, mọi khung)",
            f"{fmt(a['windows_ge5_pct'])} khung đạt; trung vị {a['situations_per_14d_median']}",
            a["windows_ge5_pct"] == 100.0,
        ),
        (
            "Lặp lại",
            "Không lặp tiêu đề trong 7 ngày (0 ngày lặp)",
            f"{a['headline_repeat_days']} ngày lặp ở {a['personas_with_headline_repeat']} người",
            a["headline_repeat_days"] == 0,
        ),
        (
            "Lặp lại",
            "Lời của Lá lặp ≤ 20% số ngày",
            fmt(a["la_line_repeat_pct"]),
            (a["la_line_repeat_pct"] or 0) <= 20.0,
        ),
        (
            "Hợp mood",
            "Ngày Đuối được việc nhẹ ≥ 90%",
            f"{fmt(mood['low_light_pct'])} ({mood['low_light']}/{mood['low_days']})",
            (mood["low_light_pct"] or 0) >= 90.0,
        ),
        (
            "Hợp mood",
            "Lời của Lá không trái mood (100%)",
            f"{mood['la_contradictions']} ngày trái",
            mood["la_contradictions"] == 0,
        ),
        (
            "An toàn",
            "Bắt 100% câu có ý định khủng hoảng",
            f"{fmt(cr['crisis_caught_pct'])} ({cr['crisis_caught']}/{cr['crisis_inputs']})",
            cr["crisis_caught"] == cr["crisis_inputs"] and cr["crisis_inputs"] > 0,
        ),
        (
            "An toàn",
            "Báo nhầm câu 'chết' ẩn dụ ≤ 2%",
            f"{fmt(cr['figurative_fp_pct'])} "
            f"({cr['figurative_flagged']}/{cr['figurative_inputs']})",
            None if not cr["figurative_inputs"] else (cr["figurative_fp_pct"] or 0) <= 2.0,
        ),
        (
            "Hiểu mình",
            "Điểm trung bình ≥ 3,5",
            f"{u['mean']} ({u['items_scored']}/{u['items_needed']} mục đã chấm)",
            None if not full_judge else (u["mean"] or 0) >= 3.5,
        ),
        (
            "Hiểu mình",
            "≥ 70% người giả có trung bình ≥ 3",
            fmt(u["personas_ge3_pct"]),
            None if not full_judge else (u["personas_ge3_pct"] or 0) >= 70.0,
        ),
        (
            "Quay lại (mô hình)",
            "D7 ≥ 35%",
            fmt(round(100 * ret["D7"], 1)),
            None if not full_judge else ret["D7"] >= 0.35,
        ),
        (
            "Quay lại (mô hình)",
            "D28 ≥ 15%",
            fmt(round(100 * ret["D28"], 1)),
            None if not full_judge else ret["D28"] >= 0.15,
        ),
    ]
    run = m["run"]
    ref = rm["calibration"]["reference"]
    lines = [
        f"# Kết quả chạy người giả: {title}",
        "",
        f"Ngưỡng: `{m['thresholds_version']}` (qa/personas/thresholds.md). "
        f"Code: `{run['git_head'][:12]}`. {run['personas']} người giả x {run['days']} ngày "
        f"từ {run['start']}, API chạy trên máy với dữ liệu giả.",
        "",
        table_row("Nhóm", "Ngưỡng", "Kết quả", ""),
        table_row("---", "---", "---", "---"),
    ]
    lines += [table_row(g, t, r, verdict(ok)) for g, t, r, ok in rows]
    lines += [
        "",
        "## Lặp lại theo dữ liệu đã nhập",
        "",
        table_row(
            "Nhóm",
            "Người",
            "Khung 14 ngày đạt ≥5 chuyện",
            "Trung vị chuyện/14 ngày",
            "Ngày lặp tiêu đề (7 ngày)",
            "Lời của Lá lặp",
        ),
        table_row(*["---"] * 6),
    ]
    for key, label in (
        ("all", "tất cả"),
        *[(f"precision:{k}", v) for k, v in PRECISION_VI.items()],
    ):
        if key in rep:
            r = rep[key]
            lines.append(
                table_row(
                    label,
                    r["personas"],
                    fmt(r["windows_ge5_pct"]),
                    r["situations_per_14d_median"],
                    r["headline_repeat_days"],
                    fmt(r["la_line_repeat_pct"]),
                )
            )
    lines += [
        "",
        "## Mood",
        "",
        f"- Ngày chọn Đuối: {mood['low_days']}; việc nhỏ được xếp là nhẹ: {mood['low_light']} "
        f"(nguồn xếp loại: {mood['light_sources_low_days']}).",
        "- Ngày việc nhỏ đổi sau khi chọn mood: "
        f"{fmt(mood['days_action_changed_after_mood_pct'])}.",
        f"- Lời của Lá trái mood: {mood['la_contradictions']} ngày. "
        f"Ví dụ: {mood['la_contradiction_examples']}",
        "- Tiêu đề/giải thích trái mood (phụ, không tính ngưỡng): "
        f"{mood['headline_contradictions']} ngày. "
        f"Ví dụ: {mood['headline_contradiction_examples'][:3]}",
        "",
        "## An toàn",
        "",
        f"- Câu khủng hoảng: {cr['crisis_inputs']}, được chuyển sang hỗ trợ: "
        f"{cr['crisis_caught']}. Trạng thái trả về: {cr['crisis_statuses']}.",
        f"- Câu 'chết' ẩn dụ: {cr['figurative_inputs']}, bị báo nhầm: {cr['figurative_flagged']}.",
        f"- Câu hỏi Tarot thường: {cr['ordinary_questions']}, bị báo nhầm: "
        f"{cr['ordinary_flagged']}.",
        "",
        "## Hiểu mình (giám khảo mù)",
        "",
        f"- Đã chấm {u['items_scored']}/{u['items_needed']} mục; trung bình {u['mean']}; "
        f"phân bố {u['distribution']}.",
        f"- Người giả có trung bình ≥ 3: {fmt(u['personas_ge3_pct'])} "
        f"trên {u['personas_scored']} người.",
        "",
        "## Quay lại (mô hình theo luật, không phải số thật)",
        "",
        "- Tham chiếu 'app lối sống trung bình' (đã hiệu chỉnh): "
        f"D7 {fmt(round(100 * ref['D7'], 1))}, D28 {fmt(round(100 * ref['D28'], 1))} "
        f"(số công bố: khoảng {round(100 * BENCHMARK_D7)}% sau 7 ngày, "
        "khoảng 4-6% sau 30 ngày).",
        "",
        table_row("Nhóm", "D1", "D7", "D14", "D28"),
        table_row(*["---"] * 5),
    ]
    for key, val in rm["by"].items():
        name = (
            {"all": "tất cả"}.get(key)
            or PRECISION_VI.get(key.split(":")[-1])
            or GROUP_VI.get(key.split(":")[-1], key)
        )
        cells = (fmt(round(100 * val[d], 1)) for d in ("D1", "D7", "D14", "D28"))
        lines.append(table_row(name, *cells))
    lines += [
        "",
        "## Nhóm người giả, xếp từ yếu nhất (theo D7 mô hình)",
        "",
        table_row(
            "Nhóm", "Người", "D7", "D28", "Hiểu mình", "Trung vị chuyện/14 ngày", "Dữ liệu đã nhập"
        ),
        table_row(*["---"] * 7),
    ]
    for s in rm["segments_worst_first"]:
        entered = ", ".join(f"{PRECISION_VI[k]} {v}" for k, v in s["precision"].items())
        lines.append(
            table_row(
                s["segment"],
                s["n"],
                fmt(round(100 * s["D7"], 1)),
                fmt(round(100 * s["D28"], 1)),
                s["understood"],
                s["situations_14d_median"],
                entered,
            )
        )
    c = m["coverage"]
    lines += [
        "",
        "## Độ phủ",
        "",
        f"- Ngày-người: {c['persona_days']}, lỗi HTTP: {c['http_errors']}. "
        f"Ngày có 'Vì sao hôm nay': {c['why_today_days']}.",
        f"- Ngày app đưa nút giữ việc nhỏ: {fmt(c['experiment_offered_pct'])}; "
        f"người giả muốn giữ {c['wants_keep_days']} ngày, giữ được {c['kept_days']}.",
        f"- Ngày có đường quay lại: {c['return_path_days']}; "
        f"ngày app nhắc tới chuyện cũ của người dùng: {c['memory_days']}.",
        f"- Câu việc nhỏ khác nhau: {c['action_texts']}, chưa có nhãn mù: "
        f"{c['action_texts_unlabelled']}. Mục chấm 'hiểu mình' còn thiếu: "
        f"{c['judge_items_missing']}.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
