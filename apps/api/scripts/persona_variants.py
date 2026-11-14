"""Compare cumulative week-6 variants (V0-V4) of the merged plan with the 100 personas.

    uv run --directory apps/api python -m scripts.persona_variants \
        [--summary <md>] [--out ../../qa/personas/report-plan-variants.md]

V0 reuses the merged-plan moment-B scores. V1-V4 are read from
``qa/personas/plan-variants/judged/out-V<n>-*.json`` and Codex files from
``out-codex-V<n>.json``. Model judgement on text mocks only: not real users, not real code.
"""

from __future__ import annotations

import argparse
import glob
import json
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_plan import FLAG_VI, FLAGS, PRECISION_VI, SCORE_VI, SCORES, WEAK_STUDENT
from scripts.persona_report import table_row
from scripts.persona_top8 import GROUPS, NO_SAFE, assign, personas

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
VARIANTS_DIR = QA / "plan-variants"
VARIANTS = ("V0", "V1", "V2", "V3", "V4")
LABELS = {
    "V0": "Kế hoạch bản 3, như đã chấm",
    "V1": "V0 + các sửa sau persona (bản 4)",
    "V2": "V1 + ô 'Kể ra' (dùng một lần, không lưu)",
    "V3": "V2 + 'Lá nhớ 7 ngày' (tùy chọn, chỉ trên máy)",
    "V4": "V3 + nút 'Đã thử' do người dùng tự bấm",
}
NEW_DATA = {
    "V2": "Dùng mới: chữ người dùng tự gõ, xử lý một lần để chọn chuyện. Cần owner quyết.",
    "V3": "Dùng mới: lưu mood và việc đã giữ 7 ngày trên máy. Cần owner quyết.",
    "V4": "Dựa trên dữ liệu của V3 (nếu bật nhớ 7 ngày).",
}
# Bar asked by the owner 14.11: margin above the plan's 3,5 because mocks are a ceiling.
BAR_MEAN = 3.7
BAR_GE3 = 70
BAR_VALUE = 3.5
BAR_WEAK = 3.5


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return round(statistics.fmean(items), 2) if items else None


def fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}".replace(".", ",")


def load(paths: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows += json.loads(Path(path).read_text(encoding="utf-8"))
    return rows


def variant_rows() -> dict[str, list[dict[str, Any]]]:
    merged = sorted(glob.glob(str(QA / "merged-plan" / "judged" / "out-claude-*.json")))
    out = {"V0": [r for r in load(merged) if r["moment"] == "B"]}
    for v in VARIANTS[1:]:
        out[v] = load(sorted(glob.glob(str(VARIANTS_DIR / "judged" / f"out-{v}-*.json"))))
    return out


def codex_rows() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for v in VARIANTS:
        path = VARIANTS_DIR / "judged" / f"out-codex-{v}.json"
        if path.exists():
            out[v] = load([str(path)])
    return out


def summary_of(
    rows: Sequence[Mapping[str, Any]], people: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    weak = {
        label: mean(r["understood"] for r in rows if people[r["persona"]]["segment"] == seg)
        for seg, label in WEAK_STUDENT.items()
    }
    result: dict[str, Any] = {
        "n": len(rows),
        "understood": mean(r["understood"] for r in rows),
        "ge3": sum(1 for r in rows if r["understood"] >= 3),
        "less_alone": mean(r["less_alone"] for r in rows),
        "peaceful": mean(r["peaceful"] for r in rows),
        "want_return": mean(r["want_return"] for r in rows),
        "weak": weak,
        "flags": {f: sum(1 for r in rows if r.get(f)) for f in FLAGS},
        "dist": dict(sorted(Counter(int(r["understood"]) for r in rows).items())),
    }
    result["meets"] = bool(
        len(rows) == 100
        and (result["understood"] or 0) >= BAR_MEAN
        and result["ge3"] >= BAR_GE3
        and (result["less_alone"] or 0) >= BAR_VALUE
        and (result["peaceful"] or 0) >= BAR_VALUE
        and all((v or 0) >= BAR_WEAK for v in weak.values())
    )
    return result


def mark(value: float | None, bar: float) -> str:
    if value is None:
        return "—"
    return fmt(value) + (" ✓" if value >= bar else "")


def build(summary_path: str | None, out: Path) -> None:
    people = {p["id"]: p for p in personas()}
    extra = assign(list(people.values()))
    data = variant_rows()
    codex = codex_rows()
    stats = {v: summary_of(rows, people) for v, rows in data.items() if rows}
    smallest = next((v for v in VARIANTS if v in stats and stats[v]["meets"]), None)
    lines = [
        "# Năm bản trải nghiệm tuần 6: cần thêm gì để đạt mục tiêu (14.11.2026)",
        "",
        "**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** Không phải người dùng thật, "
        "không phải code thật. Mock là trường hợp tốt nhất, nên điểm ở đây là **trần**.",
        "",
        "- Mỗi bản cộng dồn lên bản trước. Mock: [plan-variants/mocks/](plan-variants/mocks/) "
        "(V0 là mốc B trong [merged-plan/mocks.md](merged-plan/mocks.md)). "
        "Câu hỏi chấm: [plan-variants/judge-instructions.md](plan-variants/judge-instructions.md).",
        "- Mỗi bản V1-V4: 3 Claude subagent riêng chấm 100 người giả; mỗi giám khảo chỉ thấy "
        "**một** bản, không biết có bản khác. V0 dùng lại điểm mốc B đã chấm, không chấm lại.",
        "- Tình huống hôm nay và mood giữ như các lần trước (25 người mỗi tình huống).",
        f"- Ngưỡng 'đủ' (owner 14.11): hiểu mình ≥ {fmt(BAR_MEAN)} (kế hoạch cần 3,5, cộng "
        f"biên vì mock là trần), ≥ {BAR_GE3}/100 người từ 3 trở lên, bớt một mình và bình yên "
        f"≥ {fmt(BAR_VALUE)}, mỗi nhóm trong 4 nhóm sinh viên yếu ≥ {fmt(BAR_WEAK)}.",
        "",
    ]
    if summary_path:
        lines += [Path(summary_path).read_text(encoding="utf-8").rstrip(), ""]
    lines += [
        "## Bảng so sánh",
        "",
        table_row("Chỉ số", *[f"{v}" for v in VARIANTS if v in stats]),
        table_row(*["---"] * (1 + len(stats))),
        table_row("Bản", *[LABELS[v] for v in VARIANTS if v in stats]),
        table_row(
            f"Hiểu mình (cần ≥ {fmt(BAR_MEAN)})",
            *[mark(stats[v]["understood"], BAR_MEAN) for v in stats],
        ),
        table_row(
            f"Người ≥ 3 (cần ≥ {BAR_GE3})",
            *[
                f"{stats[v]['ge3']}/{stats[v]['n']}" + (" ✓" if stats[v]["ge3"] >= BAR_GE3 else "")
                for v in stats
            ],
        ),
        table_row(
            "Bớt thấy một mình (cần ≥ 3,5)",
            *[mark(stats[v]["less_alone"], BAR_VALUE) for v in stats],
        ),
        table_row(
            "Thấy bình yên (cần ≥ 3,5)", *[mark(stats[v]["peaceful"], BAR_VALUE) for v in stats]
        ),
        table_row("Muốn quay lại", *[fmt(stats[v]["want_return"]) for v in stats]),
    ]
    for label in WEAK_STUDENT.values():
        lines.append(
            table_row(
                f"Hiểu mình: {label} (cần ≥ 3,5)",
                *[mark(stats[v]["weak"][label], BAR_WEAK) for v in stats],
            )
        )
    lines.append(
        table_row(
            "Phân bố điểm hiểu mình 1/2/3/4/5",
            *["/".join(str(stats[v]["dist"].get(k, 0)) for k in range(1, 6)) for v in stats],
        )
    )
    for f in FLAGS:
        lines.append(table_row(f"Cờ: {FLAG_VI[f]}", *[stats[v]["flags"][f] for v in stats]))
    lines.append(
        table_row(
            "Đạt cả 5 điều kiện", *["**có**" if stats[v]["meets"] else "không" for v in stats]
        )
    )
    lines += [
        "",
        "**Bản nhỏ nhất đạt đủ:** "
        + (
            f"{smallest} ({LABELS[smallest]})."
            if smallest
            else "**không bản nào đạt đủ cả 5 điều kiện.**"
        ),
        "",
        "## Dữ liệu mới mỗi bản dùng",
        "",
    ]
    lines += [f"- **{v}:** {NEW_DATA[v]}" for v in NEW_DATA]
    # Breakdown by group, situation, profile type.
    group_names = [*sorted(set(GROUPS.values())), NO_SAFE]

    def in_group(pid: str, g: str) -> bool:
        if g == NO_SAFE:
            return extra[pid]["situation"] == "no_safe_person"
        return GROUPS[people[pid]["segment"]] == g

    sections: list[tuple[str, list[str], Any]] = [
        ("Theo nhóm người giả", group_names, in_group),
        (
            "Theo hoàn cảnh chi tiết",
            sorted({p["segment_label"] for p in people.values()}),
            lambda pid, k: people[pid]["segment_label"] == k,
        ),
        (
            "Theo loại hồ sơ",
            list(PRECISION_VI.values()),
            lambda pid, k: PRECISION_VI[people[pid]["birth"]["precision"]] == k,
        ),
        (
            "Theo tình huống hôm nay",
            ["tired", "away_2w", "shared_phone", "no_safe_person"],
            lambda pid, k: extra[pid]["situation"] == k,
        ),
    ]
    sit_vi = {
        "tired": "Rất mệt",
        "away_2w": "Quay lại sau 2 tuần",
        "shared_phone": "Điện thoại dùng chung",
        "no_safe_person": "Không có ai an toàn",
    }
    for title, keys, pick in sections:
        lines += [
            "",
            f"## {title} (hiểu mình)",
            "",
            table_row("Nhóm", "Người", *[v for v in stats]),
            table_row(*["---"] * (2 + len(stats))),
        ]
        for k in keys:
            n = sum(1 for pid in people if pick(pid, k))
            lines.append(
                table_row(
                    sit_vi.get(k, k),
                    n,
                    *[
                        fmt(mean(r["understood"] for r in data[v] if pick(r["persona"], k)))
                        for v in stats
                    ],
                )
            )
    # Flags with quotes for the best scored variant.
    best = max(stats, key=lambda v: stats[v]["understood"] or 0)
    lines += ["", f"## Cờ và câu bị chỉ ra ({', '.join(v for v in stats if v != 'V0')})", ""]
    for v in stats:
        if v == "V0":
            continue
        for f in FLAGS:
            quotes = Counter(
                str(r.get("quotes", {}).get(f, "")).strip()
                for r in data[v]
                if r.get(f) and str(r.get("quotes", {}).get(f, "")).strip()
            )
            if quotes:
                top = "; ".join(f"'{q}' ({n})" for q, n in quotes.most_common(2))
                lines.append(f"- {v}, {FLAG_VI[f]} {stats[v]['flags'][f]}: {top}")
    # Remaining wishes in the best variant.
    lines += [
        "",
        f"## Điều người giả vẫn muốn ở bản điểm cao nhất ({best})",
        "",
        "Lời của những người chấm hiểu mình ≤ 3, mỗi nhóm hoàn cảnh tối đa một câu:",
        "",
    ]
    seen: set[str] = set()
    for r in sorted(data[best], key=lambda r: (r["understood"], r["persona"])):
        seg = people[r["persona"]]["segment_label"]
        wish = str(r.get("still_missing", "")).strip()
        if r["understood"] <= 3 and wish and seg not in seen:
            seen.add(seg)
            lines.append(f'- {seg}: "{wish}"')
    if codex:
        lines += ["", "## Codex chấm đối chiếu trên cùng 20 người giả", ""]
        lines += [
            table_row("Bản", "Mục", "Claude", "Codex", "Lệch TB / người"),
            table_row(*["---"] * 5),
        ]
        for v, crows in codex.items():
            by = {r["persona"]: r for r in data[v]}
            pairs = [(c, by[c["persona"]]) for c in crows if c["persona"] in by]
            for key in SCORES:
                lines.append(
                    table_row(
                        v,
                        SCORE_VI[key],
                        fmt(mean(x[key] for _, x in pairs)),
                        fmt(mean(c[key] for c, _ in pairs)),
                        fmt(mean(abs(c[key] - x[key]) for c, x in pairs)),
                    )
                )
            ge3_c = sum(1 for c, _ in pairs if c["understood"] >= 3)
            ge3_x = sum(1 for _, x in pairs if x["understood"] >= 3)
            cf = ", ".join(f"{FLAG_VI[f]} {sum(1 for c, _ in pairs if c.get(f))}" for f in FLAGS)
            lines.append(
                table_row(
                    v, "Người ≥ 3 / cờ Codex", f"{ge3_x}/{len(pairs)}", f"{ge3_c}/{len(pairs)}", cf
                )
            )
    lines += [
        "",
        "## Giới hạn",
        "",
        "- Người giả và giám khảo đều là mô hình AI, chấm mô tả bằng chữ. Không chứng minh người "
        "thật thấy được hiểu hay quay lại.",
        "- V0 được chấm trong cùng lượt với mốc A và biến thể hỏi lại; V1-V4 được chấm riêng từng "
        "bản. Khác bối cảnh chấm có thể làm lệch một chút giữa V0 và các bản sau. "
        "Codex chấm lại V0 theo đúng cách chấm của V1-V4 để kiểm chỗ này.",
        "- Mỗi người giả chấm một tình huống hôm nay. Nhóm người lớn tuổi chỉ 5 người; mỗi nhóm "
        "sinh viên yếu 6-8 người, nên một người đổi điểm làm trung bình nhóm đổi 0,13-0,17.",
        "- Câu ví dụ trong mock (đáp lại đoạn kể, câu nhắc 7 ngày) là câu tốt nhất người viết mock "
        "nghĩ ra. Câu thật sau này có thể kém hơn.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out, "smallest:", smallest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--out", default=str(QA / "report-plan-variants.md"))
    args = parser.parse_args()
    build(args.summary, Path(args.out))


if __name__ == "__main__":
    main()
