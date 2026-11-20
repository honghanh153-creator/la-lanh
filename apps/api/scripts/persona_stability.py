"""Is the persona measurement itself stable? (issue #689, 7-week plan, week 1 "Bộ đo")

Judges score the same 100 fixed personas on the same app build more than once. This module
builds the blind packets, compares two scoring passes and writes the report.

    pnpm personas:stability -- packets --run qa/personas/runs/<name> --out <dir>
    pnpm personas:stability -- report --run qa/personas/runs/<name> \
        --first <files…> --again <files…> --second <files…>

The marks were written before any scoring (docs/plans/2026-11-15-ke-hoach-7-tuan-moc-do.md,
week 1) and are read here in their stricter sense:

- re-scoring: for every score, the mean moves by at most 0.15;
- at most 10% of personas have any score that moves by 2 points or more;
- harm flags are the same for every persona;
- two judges on the same cases: agreement is recorded (no mark was set for it).

A persona that one pass did not score is reported as missing and fails the check; nothing is
guessed. The people to score come from the persona file: a run where one of them lacks a judged
day, has it twice or got an error on it is refused by both commands. Pure functions, no app
imports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_metrics import judged_days
from scripts.persona_report import JUDGE_PROFILE_KEYS, PRECISION_VI, load_jsonl

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
RUBRIC_VERSION = "app-judge-v1-2026-11-20"
SCORES = ("understood", "less_alone", "peaceful", "want_return")
SCORE_VI = {
    "understood": "Hiểu mình",
    "less_alone": "Bớt thấy một mình",
    "peaceful": "Thấy bình yên",
    "want_return": "Muốn quay lại",
}
FLAGS = ("blame", "pressure", "privacy", "dependence", "must_check_la")
FLAG_VI = {
    "blame": "bị trách",
    "pressure": "bị ép",
    "privacy": "lo riêng tư",
    "dependence": "phụ thuộc",
    "must_check_la": "phải xem Lá mới dám quyết",
}
PASSES = ("first", "again", "second")
MAX_MEAN_SHIFT = 0.15
FAR_POINTS = 2
MAX_FAR_PERSONAS_PCT = 10.0
DAY_KEYS = (
    ("mood_they_picked", "mood"),
    ("headline", "headline"),
    ("explanation", "thesis"),
    ("real_life_scene", "scene"),
    ("small_action", "action"),
    ("la_line", "la_line"),
    ("why_today", "why_today"),
    ("la_reaction_to_mood", "mood_reaction"),
)


def run_gaps(personas: Sequence[Mapping[str, Any]], rows: Iterable[Mapping[str, Any]]) -> list[str]:
    """What the run lacks for a fair measurement; empty when nothing is missing.

    The people to score are the ones in the persona file, not the ones the run happens to
    hold: each needs every judged day exactly once, answered with status 200. Otherwise a run
    that lost a persona or a week would be scored on fewer people and still read "stable".
    """

    seen: dict[tuple[str, int], list[object]] = {}
    for row in rows:
        seen.setdefault((row["persona"], row["day"]), []).append(row.get("status"))
    gaps: list[str] = []
    for persona in personas:
        pid = persona["id"]
        for day in judged_days(pid):
            statuses = seen.get((pid, day), [])
            if not statuses:
                gaps.append(f"{pid} thiếu ngày {day}")
            elif len(statuses) > 1:
                gaps.append(f"{pid} có ngày {day} hai lần trở lên")
            elif statuses[0] != 200:
                gaps.append(f"{pid} ngày {day} bị lỗi ({statuses[0]})")
    return gaps


def build_packets(
    personas: Sequence[Mapping[str, Any]], rows: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """One packet per persona: who they are and what the app showed on their judged days.

    A packet carries no build, run or pass name, so a judge cannot tell which version it reads.
    A run with a missing, failed or repeated judged day is refused (see ``run_gaps``).
    """

    rows = list(rows)
    gaps = run_gaps(personas, rows)
    if gaps:
        more = f" (và {len(gaps) - 5} chỗ nữa)" if len(gaps) > 5 else ""
        raise ValueError(
            "Lần chạy không đủ để đo, hãy chạy lại người giả: " + "; ".join(gaps[:5]) + more
        )
    by_persona: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        if row["day"] in judged_days(row["persona"]):
            by_persona.setdefault(row["persona"], []).append(row)
    packets: list[dict[str, Any]] = []
    for persona in personas:
        days = sorted(by_persona[persona["id"]], key=lambda r: r["day"])
        profile = {key: persona.get(key) for key in JUDGE_PROFILE_KEYS}
        profile["what_they_entered"] = PRECISION_VI[persona["birth"]["precision"]]
        packets.append(
            {
                "persona": persona["id"],
                "profile": profile,
                "days": [{out: row.get(key) for out, key in DAY_KEYS} for row in days],
            }
        )
    return packets


def split_for_pass(
    packets: Sequence[Mapping[str, Any]], pass_name: str, batches: int
) -> list[list[Mapping[str, Any]]]:
    """The packets in an order of this pass's own, cut into ``batches`` files.

    Each pass reads the personas in a different order and in different company, so a score
    that depends on what the judge read just before shows up as a difference between passes.
    """

    seed = int.from_bytes(hashlib.sha256(f"{RUBRIC_VERSION}:{pass_name}".encode()).digest()[:8])
    order = list(packets)
    random.Random(seed).shuffle(order)  # noqa: S311 - a fixed reading order, not a secret
    return [order[i::batches] for i in range(batches)]


def parse_scores(items: object) -> dict[str, dict[str, Any]]:
    """Validate one judge output: 4 whole scores 1-5 and 5 true/false flags per persona."""

    if not isinstance(items, list):
        raise ValueError("judge output must be a JSON list")
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("persona"), str):
            raise ValueError(f"judge item needs a persona id: {item!r}"[:200])
        pid = item["persona"]
        if pid in out:
            raise ValueError(f"{pid}: scored twice in one pass")
        record: dict[str, Any] = {}
        for key in SCORES:
            value = item.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise ValueError(f"{pid}: {key} must be a whole number 1-5")
            record[key] = value
        for key in FLAGS:
            if not isinstance(item.get(key), bool):
                raise ValueError(f"{pid}: {key} must be true or false")
            record[key] = item[key]
        out[pid] = record
    return out


def load_pass(paths: Iterable[str]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for path in paths:
        scores = parse_scores(json.loads(Path(path).read_text(encoding="utf-8")))
        twice = sorted(set(scores) & set(merged))
        if twice:
            raise ValueError(f"{path}: personas already scored in this pass: {twice[:5]}")
        merged.update(scores)
    return merged


def weighted_kappa(pairs: Sequence[tuple[int, int]]) -> float | None:
    """Quadratic-weighted Cohen's kappa on the 1-5 scale; None when it is undefined.

    Undefined means no pairs, or both judges gave one and the same score to everyone (there is
    no spread to agree about).
    """

    if not pairs:
        return None
    n = len(pairs)
    left = [sum(1 for a, _ in pairs if a == k) / n for k in range(1, 6)]
    right = [sum(1 for _, b in pairs if b == k) / n for k in range(1, 6)]
    observed = sum((a - b) ** 2 for a, b in pairs) / n
    expected = sum(left[i] * right[j] * (i - j) ** 2 for i in range(5) for j in range(5))
    return None if expected == 0 else 1 - observed / expected


def compare(
    a: Mapping[str, Mapping[str, Any]],
    b: Mapping[str, Mapping[str, Any]],
    expected: Sequence[str],
) -> dict[str, Any]:
    """Two scoring passes over the same personas, score by score and flag by flag."""

    both = [pid for pid in expected if pid in a and pid in b]
    scores: dict[str, Any] = {}
    for key in SCORES:
        pairs = [(int(a[pid][key]), int(b[pid][key])) for pid in both]
        gaps = [abs(x - y) for x, y in pairs]
        mean_a = statistics.fmean(x for x, _ in pairs) if pairs else None
        mean_b = statistics.fmean(y for _, y in pairs) if pairs else None
        scores[key] = {
            "mean_a": mean_a,
            "mean_b": mean_b,
            "mean_shift": None if mean_a is None or mean_b is None else abs(mean_a - mean_b),
            "mean_abs_gap": statistics.fmean(gaps) if gaps else None,
            "same_pct": 100 * sum(1 for g in gaps if g == 0) / len(gaps) if gaps else None,
            "within_1_pct": 100 * sum(1 for g in gaps if g <= 1) / len(gaps) if gaps else None,
            "far": sum(1 for g in gaps if g >= FAR_POINTS),
            "kappa": weighted_kappa(pairs),
        }
    far_personas = [
        pid
        for pid in both
        if any(abs(int(a[pid][k]) - int(b[pid][k])) >= FAR_POINTS for k in SCORES)
    ]
    flags: dict[str, dict[str, Any]] = {
        key: {
            "a": sum(1 for pid in both if a[pid][key]),
            "b": sum(1 for pid in both if b[pid][key]),
            "differ": [pid for pid in both if a[pid][key] != b[pid][key]],
        }
        for key in FLAGS
    }
    return {
        "expected": len(expected),
        "compared": len(both),
        "missing_a": [pid for pid in expected if pid not in a],
        "missing_b": [pid for pid in expected if pid not in b],
        "scores": scores,
        "far_personas": far_personas,
        "far_personas_pct": 100 * len(far_personas) / len(both) if both else None,
        "flags": flags,
        "flag_personas_differ": sorted({pid for f in flags.values() for pid in f["differ"]}),
    }


def stability_checks(cmp: Mapping[str, Any]) -> list[tuple[str, str, bool]]:
    """The week-1 marks for a re-scoring pass: (mark, result, passed)."""

    complete = cmp["compared"] == cmp["expected"] and cmp["expected"] > 0
    # Rounded so that a shift of exactly 0.15 is not failed by binary floating point.
    shifts = {
        k: round(v["mean_shift"], 9)
        for k, v in cmp["scores"].items()
        if v["mean_shift"] is not None
    }
    worst = max(shifts, key=lambda k: shifts[k]) if shifts else None
    far_pct = cmp["far_personas_pct"]
    differ = cmp["flag_personas_differ"]
    return [
        (
            "Chấm đủ mọi người ở cả hai lượt",
            f"{cmp['compared']}/{cmp['expected']} người",
            complete,
        ),
        (
            "Trung bình mỗi điểm lệch không quá 0,15",
            "chưa có điểm"
            if worst is None
            else f'lệch nhiều nhất {vi(shifts[worst])} ở "{SCORE_VI[worst]}"',
            complete and worst is not None and shifts[worst] <= MAX_MEAN_SHIFT,
        ),
        (
            "Không quá 10% số người có điểm lệch từ 2",
            "chưa có điểm"
            if far_pct is None
            else f"{vi(far_pct, 1)}% ({len(cmp['far_personas'])} người)",
            complete and far_pct is not None and far_pct <= MAX_FAR_PERSONAS_PCT,
        ),
        (
            "Cờ hại trùng nhau ở mọi người",
            f"{len(differ)} người có cờ khác nhau",
            complete and not differ,
        ),
    ]


def vi(value: float | None, digits: int = 2) -> str:
    """A number the Vietnamese way (decimal comma); "—" when there is none."""

    return "—" if value is None else f"{value:.{digits}f}".replace(".", ",")


def table(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render_pair(title: str, cmp: Mapping[str, Any], names: tuple[str, str]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        f"So được {cmp['compared']}/{cmp['expected']} người."
        + (
            f" Thiếu ở {names[0]}: {len(cmp['missing_a'])}; thiếu ở {names[1]}: "
            f"{len(cmp['missing_b'])}."
            if cmp["missing_a"] or cmp["missing_b"]
            else ""
        ),
        "",
        table(
            "Điểm",
            f"Trung bình {names[0]}",
            f"Trung bình {names[1]}",
            "Trung bình lệch",
            "Mỗi người lệch trung bình",
            "Trùng điểm",
            "Lệch trong 1 điểm",
            "Số người lệch từ 2",
            "Kappa có trọng số",
        ),
        table(*["---"] * 9),
    ]
    for key in SCORES:
        s = cmp["scores"][key]
        lines.append(
            table(
                SCORE_VI[key],
                vi(s["mean_a"]),
                vi(s["mean_b"]),
                vi(s["mean_shift"]),
                vi(s["mean_abs_gap"]),
                f"{vi(s['same_pct'], 1)}%",
                f"{vi(s['within_1_pct'], 1)}%",
                s["far"],
                vi(s["kappa"]),
            )
        )
    lines += [
        "",
        f"Người có ít nhất một điểm lệch từ 2: {len(cmp['far_personas'])} "
        f"({vi(cmp['far_personas_pct'], 1)}%).",
        "",
        table(
            "Cờ hại", f"Số người bị cờ ở {names[0]}", f"Ở {names[1]}", "Số người hai lượt khác nhau"
        ),
        table(*["---"] * 4),
    ]
    for key in FLAGS:
        f = cmp["flags"][key]
        lines.append(table(FLAG_VI[key], f["a"], f["b"], len(f["differ"])))
    lines.append("")
    return lines


def render(
    run: Mapping[str, Any],
    again: Mapping[str, Any],
    second: Mapping[str, Any] | None,
    notes: str | None,
) -> str:
    checks = stability_checks(again)
    passed = all(ok for _, _, ok in checks)
    lines = [
        "# Bộ đo có ổn định không: chấm lại cùng 100 người giả",
        "",
        f"Rubric: `{RUBRIC_VERSION}` (qa/personas/judge-rubric-app.md). "
        f"Code được chấm: `{str(run.get('git_head', ''))[:12]}`, {run.get('personas')} người giả, "
        "nội dung do API thật sinh ra trên máy với dữ liệu giả.",
        'Mốc lấy từ kế hoạch 7 tuần (tuần 1, việc "Bộ đo"), ghi trước khi chấm.',
        "",
        f"**Kết luận chấm lại: {'ĐẠT' if passed else 'CHƯA ĐẠT'}.**",
        "",
        table("Mốc", "Kết quả", ""),
        table("---", "---", "---"),
        *[table(mark, result, "ĐẠT" if ok else "TRƯỢT") for mark, result, ok in checks],
        "",
    ]
    if notes:
        lines += [notes.strip(), ""]
    lines += render_pair("Chấm lại (cùng cách chấm, lượt 1 và lượt 2)", again, ("lượt 1", "lượt 2"))
    if second is None:
        lines += ["## Hai giám khảo", "", "Chưa đo.", ""]
    else:
        lines += render_pair(
            "Hai giám khảo trên cùng 100 người", second, ("giám khảo 1", "giám khảo 2")
        )
    lines += [
        "## Giới hạn",
        "",
        "- Người giả và giám khảo đều là mô hình AI. Số này nói bộ đo có lặp lại được không, "
        "không nói người thật thấy thế nào.",
        "- Giám khảo đọc chữ của Daily trong 4 ngày (1, 8, 15, 22). Chưa đọc các màn khác, "
        "chưa nhìn màn hình.",
        '- Kappa không tính được khi một giám khảo cho mọi người cùng một điểm; khi đó ô ghi "—".',
        "",
    ]
    return "\n".join(lines)


def cmd_packets(
    run: Path, personas_path: Path, out: Path, passes: Sequence[str], batches: int
) -> None:
    personas = json.loads(personas_path.read_text(encoding="utf-8"))["personas"]
    packets = build_packets(personas, load_jsonl(run / "transcript.jsonl"))
    out.mkdir(parents=True, exist_ok=True)
    for name in passes:
        for index, batch in enumerate(split_for_pass(packets, name, batches), start=1):
            (out / f"{name}-{index}.json").write_text(
                json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
            )
    print(f"{len(packets)} personas x {len(passes)} passes in {batches} batches each: {out}")


def cmd_report(
    run: Path,
    personas_path: Path,
    first: Sequence[str],
    again: Sequence[str],
    second: Sequence[str],
    out: Path,
    notes: Path | None,
) -> bool:
    personas = json.loads(personas_path.read_text(encoding="utf-8"))["personas"]
    # Everyone in the persona file is expected; an incomplete run is refused, never shrunk.
    build_packets(personas, load_jsonl(run / "transcript.jsonl"))
    expected = [p["id"] for p in personas]
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
    base = load_pass(first)
    cmp_again = compare(base, load_pass(again), expected)
    cmp_second = compare(base, load_pass(second), expected) if second else None
    out.write_text(
        render(meta, cmp_again, cmp_second, notes.read_text(encoding="utf-8") if notes else None),
        encoding="utf-8",
    )
    (run / "stability.json").write_text(
        json.dumps(
            {
                "rubric": RUBRIC_VERSION,
                "git_head": meta.get("git_head"),
                "again": cmp_again,
                "second": cmp_second,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    checks = stability_checks(cmp_again)
    for mark, result, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {mark}: {result}")
    return all(ok for _, _, ok in checks)


def from_root(name: str) -> Path:
    """A path as typed at the repo root (``pnpm`` runs this module from ``apps/api``)."""

    path = Path(name)
    return path if path.is_absolute() or name.startswith(".") else ROOT / path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pk = sub.add_parser("packets")
    rp = sub.add_parser("report")
    for each in (pk, rp):
        each.add_argument("--run", required=True)
        each.add_argument("--personas", default=str(QA / "personas-100.json"))
    pk.add_argument("--out", required=True)
    pk.add_argument("--passes", nargs="+", default=list(PASSES))
    pk.add_argument("--batches", type=int, default=4)
    rp.add_argument("--first", nargs="+", required=True)
    rp.add_argument("--again", nargs="+", required=True)
    rp.add_argument("--second", nargs="*", default=[])
    rp.add_argument("--out", default=str(QA / "report-stability.md"))
    rp.add_argument("--notes", default=None, help="hand-written Markdown placed under the table")
    args = parser.parse_args()
    run, personas = from_root(args.run), from_root(args.personas)
    if args.command == "packets":
        cmd_packets(run, personas, from_root(args.out), args.passes, args.batches)
        return
    ok = cmd_report(
        run,
        personas,
        [str(from_root(name)) for name in args.first],
        [str(from_root(name)) for name in args.again],
        [str(from_root(name)) for name in args.second],
        from_root(args.out),
        from_root(args.notes) if args.notes else None,
    )
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
