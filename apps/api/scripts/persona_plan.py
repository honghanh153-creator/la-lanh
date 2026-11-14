"""Score the merged 6-week plan (docs: 2026-11-14 kế hoạch triển khai gộp) with the 100 personas.

    uv run --directory apps/api python -m scripts.persona_plan packets --out <dir>
    uv run --directory apps/api python -m scripts.persona_plan report --claude <json>... \
        [--codex <json>...] [--summary <md>] --out ../../qa/personas/report-merged-plan.md

``packets`` writes judge packets (persona, fixed situation of the day, mood of the day,
astrology belief) in shuffled batches plus the same stratified 20-persona Codex sample as the
TOP 8 run. ``report`` checks the plan's week-4 / week-6 targets that a text mock can judge and
compares with the baseline. Model judgement on text mocks only: not real users, not real code.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_metrics import JUDGED_DAYS
from scripts.persona_report import item_id, table_row
from scripts.persona_top8 import GROUPS, NO_SAFE, assign, codex_sample, packet, personas

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
SEED = 20261114
BASELINE_RUN = QA / "runs" / "baseline-2026-11-14"
MOOD_VI = {
    "Rực": "Vui, có sức",
    "Chill": "Bình thường",
    "Đuối": "Mệt",
    "Căng": "Căng thẳng",
    "Lạc trôi": "Rối, không rõ mình muốn gì",
}
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
    "felt_checked": "bị kiểm tra",
}
WEAK_STUDENT = {
    "final_year_job_hunt": "Năm cuối tìm việc",
    "money_tight": "Tiền eo hẹp",
    "family_pressure": "Áp lực gia đình",
    "part_time_job": "Vừa học vừa làm",
}
PRECISION_VI = {
    "date_only": "Chỉ ngày sinh",
    "approximate": "Giờ khoảng",
    "exact": "Giờ và nơi chính xác",
}
SITUATION_VI = {
    "tired": "Rất mệt",
    "away_2w": "Quay lại sau 2 tuần",
    "shared_phone": "Điện thoại dùng chung",
    "no_safe_person": "Không có ai an toàn",
}
# (label, check, wanted, minimum share, moments). Share 1.0 = "100%" in the plan.
TARGETS: list[tuple[str, str, bool, float, tuple[str, ...]]] = [
    ("PR 3: tìm đúng chỗ chọn mood và đổi góc đọc", "found_mood_and_angle", True, 0.90, ("A",)),
    ("PR 7: thấy việc nhỏ hợp sau khi đổi", "fits_after_change", True, 0.85, ("A",)),
    ("PR 7: ca mâu thuẫn được sửa", "contradiction_fixed", True, 1.0, ("A",)),
    (
        "PR 10: phân biệt lý do với phần diễn giải",
        "reason_vs_interpretation_clear",
        True,
        0.90,
        ("A",),
    ),
    ("PR 12: tìm đúng đường", "found_right_path", True, 0.90, ("A",)),
    ("PR 12: dừng được", "could_stop", True, 1.0, ("A",)),
    ("PR 13: hiểu là chuyện minh họa", "story_understood_as_illustration", True, 1.0, ("B",)),
    ("PR 13: không thấy bị phủ nhận nỗi khó", "story_denied_difficulty", False, 1.0, ("B",)),
    ("PR 13: không thấy bị hứa suông", "story_false_promise", False, 1.0, ("B",)),
    ("PR 14: hiểu cách chơi", "game_understood", True, 0.90, ("B",)),
    ("PR 14: dừng chơi được", "game_could_stop", True, 1.0, ("B",)),
    ("PR 14: không thấy bị chạm nỗi đau", "game_hurt", False, 1.0, ("B",)),
]
CODE_ONLY = [
    "Chống lặp 4 điều kiện qua 42 ngày, với cả 3 loại hồ sơ (PR 9)",
    "Lời của Lá lặp ≤ 20%, có ca một mood giữ suốt 42 ngày",
    "Ngày 'Đuối' được việc nhẹ ≥ 90% (giám khảo độc lập chấm 48 việc rất nhẹ)",
    "Không câu nào trái mood qua mọi ngày (mock chỉ có một ca)",
    "Lớp khủng hoảng: bắt / báo nhầm / không bài đọc / không lưu / không log / đúng câu",
    "Database: không bảng, cột hay bản ghi mới sau khi chọn góc đọc hoặc lối vào (PR 7, 8, 12)",
    "PR 2: 0 lời mời đăng nhập ở mọi màn; câu thông báo đúng nguyên văn (mã băm)",
    "PR 4: nút 'Giữ' và nút đóng bấm trọn ở khổ 390 px và nhỏ hơn",
    "PR 7: ≤ 2 thao tác và ≤ 70 chữ trước khi thấy việc nhỏ "
    "(mock được viết để đạt, phải đo trên giao diện)",
    "PR 12: lượt mở 30 giây không bị chặn",
    "Quay lại sau 7 / 28 ngày (mô hình, chỉ tham khảo)",
]
LIMITS = [
    "## Giới hạn",
    "",
    "- Người giả và giám khảo đều là mô hình AI. Giám khảo đọc mô tả bằng chữ, không dùng app "
    "thật và không có code thật. Điểm cho biết hướng, không chứng minh người thật thấy được "
    "hiểu hay quay lại.",
    "- Số nền 2,23 được chấm trên **nội dung thật từng ngày** do app sinh ra. Điểm mới chấm trên "
    "**mock**, nơi người viết mock chọn ví dụ tốt. Hai con số khác công cụ đo, nên mức tăng là "
    "giới hạn trên của điều kế hoạch có thể mang lại, không phải số đo trước-sau.",
    "- Nhãn mood, nhãn góc đọc và nội dung note trong mock là ví dụ; kế hoạch chưa chốt chúng. "
    "Kết quả phụ thuộc nhiều vào chất lượng câu thật sau này.",
    "- 'Bớt thấy một mình' và 'thấy bình yên' chưa có số nền (kế hoạch lấy nền ở PR 0), nên chỉ "
    "so được với mức 3,5, chưa so được điều kiện tăng ≥ 0,5.",
    "- Mỗi người giả chỉ chấm một tình huống hôm nay. Nhóm người lớn tuổi chỉ có 5 người.",
    "- Giám khảo có thể chấm dễ hơn khi thấy mock viết cẩn thận. Codex chấm đối chiếu 20 người "
    "để bắt chỗ này.",
    "",
]


def mood_today(p: Mapping[str, Any], situation: str, moment: str) -> str:
    if situation == "tired":
        return MOOD_VI["Đuối"]
    return MOOD_VI[p["mood_29"][27 if moment == "A" else 28]]


def cmd_packets(out: Path, batches: int) -> None:
    people = personas()
    extra = assign(people)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in people:
        row = packet(p, extra[p["id"]])
        situation = extra[p["id"]]["situation"]
        row["mood_today_moment_A"] = mood_today(p, situation, "A")
        row["mood_today_moment_B"] = mood_today(p, situation, "B")
        rows.append(row)
    order = list(rows)
    random.Random(SEED + 42).shuffle(order)  # noqa: S311 - fixed test split
    for i in range(batches):
        (out / f"claude-{i + 1}.json").write_text(
            json.dumps(order[i::batches], ensure_ascii=False, indent=1), encoding="utf-8"
        )
    sample = codex_sample(people, extra)
    picked = [r for r in rows if r["id"] in sample]
    half = len(picked) // 2
    for n, part in ((1, picked[:half]), (2, picked[half:])):
        (out / f"codex-{n}.json").write_text(
            json.dumps(part, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    print(f"{len(rows)} personas in {batches} batches; codex sample {len(sample)}")


def load_rows(paths: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rows += data["rows"] if isinstance(data, dict) else data
    return rows


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return round(statistics.fmean(items), 2) if items else None


def fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}".replace(".", ",")


def baseline_understood() -> dict[str, float]:
    """Per-persona mean of the baseline blind judge (days 1, 8, 15, 22 of the 29-day run)."""

    scores = json.loads((QA / "labels" / "judge-scores.json").read_text(encoding="utf-8"))
    by_id = {k: float(v["score"]) for k, v in scores["scores"].items()}
    plain = BASELINE_RUN / "transcript.jsonl"
    text = (
        plain.read_text(encoding="utf-8")
        if plain.exists()
        else gzip.decompress((BASELINE_RUN / "transcript.jsonl.gz").read_bytes()).decode()
    )
    per: dict[str, list[float]] = defaultdict(list)
    for line in text.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("day") in JUDGED_DAYS and row.get("status") == 200:
            key = item_id(row)
            if key in by_id:
                per[row["persona"]].append(by_id[key])
    return {pid: statistics.fmean(v) for pid, v in per.items()}


def share(rows: Sequence[Mapping[str, Any]], check: str, wanted: bool) -> tuple[int, int]:
    answered = [r for r in rows if check in r.get("checks", {})]
    return sum(1 for r in answered if bool(r["checks"][check]) is wanted), len(answered)


def pct_str(ok: int, n: int) -> str:
    return f"{ok}/{n}"


def quotes_for(rows: Sequence[Mapping[str, Any]], flag: str) -> Counter[str]:
    return Counter(
        str(r.get("quotes", {}).get(flag, "")).strip()
        for r in rows
        if r.get(flag) and str(r.get("quotes", {}).get(flag, "")).strip()
    )


def cmd_report(claude: list[str], codex: list[str], out: Path, summary: str | None) -> None:
    people = {p["id"]: p for p in personas()}
    extra = assign(list(people.values()))
    base = baseline_understood()
    rows = load_rows(claude)
    crows = load_rows(codex) if codex else []
    for r in rows + crows:
        p = people[r["persona"]]
        r["group"] = GROUPS[p["segment"]]
        r["segment"] = p["segment"]
        r["segment_label"] = p["segment_label"]
        r["situation_today"] = extra[r["persona"]]["situation"]
        r["belief"] = extra[r["persona"]]["belief"]
        r["precision"] = p["birth"]["precision"]
    seen = Counter((r["persona"], r["moment"]) for r in rows)
    missing = [(pid, m) for pid in people for m in ("A", "B", "ask") if seen[(pid, m)] == 0]
    by_m = {m: [r for r in rows if r["moment"] == m] for m in ("A", "B", "ask")}
    cby_m = {m: [r for r in crows if r["moment"] == m] for m in ("A", "B", "ask")}

    def persona_means(subset: Sequence[Mapping[str, Any]], key: str) -> dict[str, float]:
        per: dict[str, list[float]] = defaultdict(list)
        for r in subset:
            per[r["persona"]].append(float(r[key]))
        return {pid: statistics.fmean(v) for pid, v in per.items()}

    lines = [
        "# Kế hoạch gộp 6 tuần qua 100 người giả (14.11.2026)",
        "",
        "**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** Không phải người dùng thật, "
        "không phải code thật. Kế hoạch chưa được làm; đây là thử trước xem trải nghiệm "
        "kế hoạch hứa có đủ để đạt mốc hay không.",
        "",
        "- Kế hoạch: `docs/reviews/2026-11-14-ke-hoach-trien-khai-gop.md` (bản 3).",
        "- Mock hai mốc và biến thể hỏi lại: [merged-plan/mocks.md](merged-plan/mocks.md). "
        "Câu hỏi chấm: [merged-plan/judge-instructions.md](merged-plan/judge-instructions.md).",
        "- 100 người giả hư cấu. Tình huống hôm nay giữ như lần chấm 8 ý (25 người mỗi loại: "
        "rất mệt, quay lại sau 2 tuần, điện thoại dùng chung, không có ai an toàn). "
        "Loại hồ sơ theo người giả: 30 chỉ ngày sinh, 20 giờ khoảng, 50 giờ và nơi chính xác.",
        f"- Giám khảo: 7 Claude subagent riêng, mù với ngưỡng và số nền, chấm {len(rows)} mục. "
        f"Codex chấm độc lập {len(crows)} mục (20 người chọn đều theo nhóm, cùng mẫu lần trước).",
        "",
    ]
    if missing:
        lines += [f"Thiếu {len(missing)} mục chưa chấm: {missing[:10]}", ""]
    if summary:
        lines += [Path(summary).read_text(encoding="utf-8").rstrip(), ""]

    # Score targets.
    a_und = persona_means(by_m["A"], "understood")
    b_und = persona_means(by_m["B"], "understood")
    lines += [
        "## Mục tiêu của kế hoạch đo được bằng mock",
        "",
        table_row("Chỉ số", "Nền (v1)", "Mốc tuần 4", "Mock mốc A", "Đích tuần 6", "Mock mốc B"),
        table_row(*["---"] * 6),
    ]

    def verdict(value: float | None, need: float) -> str:
        if value is None:
            return "—"
        return f"{fmt(value)} ({'đạt' if value >= need else 'trượt'})"

    base_mean = mean(base.values())
    a_mean, b_mean = (
        mean(r["understood"] for r in by_m["A"]),
        mean(r["understood"] for r in by_m["B"]),
    )
    a_ge3 = sum(1 for v in a_und.values() if v >= 3)
    b_ge3 = sum(1 for v in b_und.values() if v >= 3)
    lines.append(
        table_row(
            "Hiểu mình (trung bình)",
            fmt(base_mean),
            "≥ 3,0",
            verdict(a_mean, 3.0),
            "≥ 3,5",
            verdict(b_mean, 3.5),
        )
    )
    lines.append(
        table_row(
            "Người giả có điểm hiểu mình ≥ 3",
            f"{sum(1 for v in base.values() if v >= 3)}/100",
            "≥ 50",
            f"{a_ge3}/{len(a_und)} ({'đạt' if a_ge3 >= 50 else 'trượt'})",
            "≥ 70",
            f"{b_ge3}/{len(b_und)} ({'đạt' if b_ge3 >= 70 else 'trượt'})",
        )
    )
    for key in ("less_alone", "peaceful"):
        lines.append(
            table_row(
                SCORE_VI[key],
                "chưa có (lấy ở PR 0)",
                "—",
                fmt(mean(r[key] for r in by_m["A"])),
                "≥ 3,5 và tăng ≥ 0,5",
                verdict(mean(r[key] for r in by_m["B"]), 3.5) + "; chưa so được mức tăng",
            )
        )
    for seg, label in WEAK_STUDENT.items():
        bs = [v for pid, v in base.items() if people[pid]["segment"] == seg]
        am = mean(r["understood"] for r in by_m["A"] if r["segment"] == seg)
        bm = mean(r["understood"] for r in by_m["B"] if r["segment"] == seg)
        lines.append(
            table_row(
                f"Hiểu mình: {label} ({len(bs)} người)",
                fmt(mean(bs)),
                "≥ 3,0",
                verdict(am, 3.0),
                "≥ 3,5",
                verdict(bm, 3.5),
            )
        )
    for moment, rs in (("A", by_m["A"]), ("B", by_m["B"])):
        n = sum(1 for r in rs if r.get("must_check_la"))
        lines.append(
            table_row(
                f"Cờ 'phải xem Lá mới dám quyết' (mốc {moment})",
                "chưa đo",
                "0",
                f"{n} ({'đạt' if n == 0 else 'trượt'})" if moment == "A" else "",
                "0",
                f"{n} ({'đạt' if n == 0 else 'trượt'})" if moment == "B" else "",
            )
        )
    lines += [
        "",
        table_row("Tiêu chí PR", "Cần", "Mốc A", "Mốc B"),
        table_row(*["---"] * 4),
    ]
    for label, check, wanted, need, _moments in TARGETS:
        cells = []
        for m in ("A", "B"):
            ok, n = share(by_m[m], check, wanted)
            cells.append(f"{ok}/{n} ({'đạt' if n and ok / n >= need else 'trượt'})" if n else "—")
        lines.append(table_row(label, "100%" if need >= 1.0 else f"≥ {int(need * 100)}%", *cells))
    away = {m: [r for r in by_m[m] if r["situation_today"] == "away_2w"] for m in ("A", "B")}
    for m in ("A", "B"):
        blamed = sum(1 for r in away[m] if r["checks"].get("felt_blamed_for_absence"))
        left = sum(1 for r in away[m] if r["checks"].get("leftover_after_absence"))
        lines.append(
            table_row(
                f"PR 12: quay lại sau 2 tuần không bị trách, không việc tồn (mốc {m})",
                "100%",
                f"bị trách {blamed}/{len(away[m])}, việc tồn {left}/{len(away[m])}"
                + (" (đạt)" if blamed == 0 and left == 0 else " (trượt)"),
                "",
            )
        )
    group_names = [*sorted(set(GROUPS.values())), NO_SAFE]

    def in_group(r: Mapping[str, Any], g: str) -> bool:
        return bool(r["situation_today"] == "no_safe_person" if g == NO_SAFE else r["group"] == g)

    worst_fit = []
    for g in group_names:
        ok, n = share([r for r in by_m["A"] if in_group(r, g)], "fits_after_change", True)
        if n and ok / n < 0.80:
            worst_fit.append(f"{g} {ok}/{n}")
    lines.append(
        table_row(
            "PR 7: mỗi nhóm ≥ 80% thấy hợp (mốc A)",
            "mỗi nhóm",
            "đạt" if not worst_fit else "trượt: " + ", ".join(worst_fit),
            "",
        )
    )
    ask = by_m["ask"]
    checked = sum(1 for r in ask if r.get("felt_checked"))
    pressured = sum(1 for r in ask if r.get("pressure"))
    lines += [
        "",
        "### Biến thể hỏi lại việc đã giữ (chỉ xây nếu qua)",
        "",
        f"- Thấy bị kiểm tra: **{checked}/{len(ask)}** (cần ≤ 5). "
        f"Thấy bị ép: {pressured}/{len(ask)}. "
        f"Lo riêng tư: {sum(1 for r in ask if r.get('privacy'))}/{len(ask)}. "
        f"Phụ thuộc: {sum(1 for r in ask if r.get('dependence'))}/{len(ask)}.",
        f"- Giúp mình {fmt(mean(r['help'] for r in ask))}, muốn quay lại "
        f"{fmt(mean(r['want_return'] for r in ask))}.",
        "- Sẽ bấm: "
        + ", ".join(
            f"{k} {v}" for k, v in Counter(r.get("would_answer", "none") for r in ask).most_common()
        )
        + ".",
        f"- Kết luận theo ngưỡng phần mock: **{'qua' if checked <= 5 else 'không qua'}**. "
        "Kế hoạch còn cần owner xác nhận mục đích lưu câu trả lời.",
    ]
    q = Counter(
        str(v).strip()
        for r in ask
        if r.get("felt_checked") or r.get("pressure")
        for v in r.get("quotes", {}).values()
        if str(v).strip()
    )
    if q:
        lines.append(
            "- Câu bị chỉ ra: " + "; ".join(f"'{t}' ({n})" for t, n in q.most_common(3)) + "."
        )
    lines += ["", "### Chỉ đo được bằng code", ""]
    lines += [f"- {item}: chỉ đo được bằng code." for item in CODE_ONLY]

    # Breakdown tables.
    def block(
        title: str,
        keys: Sequence[str],
        pick: Callable[[Mapping[str, Any], str], bool],
        base_pick: Callable[[str, str], bool] | None,
    ) -> list[str]:
        out_lines = [
            "",
            f"## {title}",
            "",
            table_row(
                "Nhóm",
                "Người",
                "Hiểu mình: nền",
                "A",
                "B",
                "Bớt một mình B",
                "Bình yên B",
                "Muốn quay lại B",
            ),
            table_row(*["---"] * 8),
        ]
        for k in keys:
            ra = [r for r in by_m["A"] if pick(r, k)]
            rb = [r for r in by_m["B"] if pick(r, k)]
            bs = [v for pid, v in base.items() if base_pick and base_pick(pid, k)]
            out_lines.append(
                table_row(
                    k,
                    len(rb),
                    fmt(mean(bs)) if base_pick else "—",
                    fmt(mean(r["understood"] for r in ra)),
                    fmt(mean(r["understood"] for r in rb)),
                    fmt(mean(r["less_alone"] for r in rb)),
                    fmt(mean(r["peaceful"] for r in rb)),
                    fmt(mean(r["want_return"] for r in rb)),
                )
            )
        return out_lines

    def group_of(pid: str) -> str:
        return GROUPS[people[pid]["segment"]]

    lines += block(
        "Theo nhóm người giả",
        group_names,
        in_group,
        lambda pid, g: (
            extra[pid]["situation"] == "no_safe_person" if g == NO_SAFE else group_of(pid) == g
        ),
    )
    seg_labels = sorted({p["segment_label"] for p in people.values()})
    lines += block(
        "Theo hoàn cảnh chi tiết",
        seg_labels,
        lambda r, k: r["segment_label"] == k,
        lambda pid, k: people[pid]["segment_label"] == k,
    )
    lines += block(
        "Theo loại hồ sơ",
        list(PRECISION_VI.values()),
        lambda r, k: PRECISION_VI[r["precision"]] == k,
        lambda pid, k: PRECISION_VI[people[pid]["birth"]["precision"]] == k,
    )
    lines += block(
        "Theo tình huống hôm nay",
        list(SITUATION_VI.values()),
        lambda r, k: SITUATION_VI[r["situation_today"]] == k,
        lambda pid, k: SITUATION_VI[extra[pid]["situation"]] == k,
    )
    lines += [
        "",
        "Lượt nền không có tình huống hôm nay; cột nền ở bảng này và dòng "
        "'Không có ai an toàn' là điểm nền của chính những người giả đó.",
    ]
    belief_vi = {"high": "Tin chiêm tinh", "mid": "Nửa tin", "low": "Không tin"}
    lines += block(
        "Theo mức tin chiêm tinh",
        list(belief_vi.values()),
        lambda r, k: belief_vi[r["belief"]] == k,
        lambda pid, k: belief_vi[extra[pid]["belief"]] == k,
    )

    # Worst three detailed groups at moment B.
    seg_scores = []
    for k in seg_labels:
        rb = [r for r in by_m["B"] if r["segment_label"] == k]
        if rb:
            seg_scores.append((mean(r["understood"] for r in rb) or 0.0, k, rb))
    seg_scores.sort(key=lambda t: (t[0], t[1]))
    lines += ["", "## 3 nhóm vẫn thấp nhất ở mốc B (theo hiểu mình)", ""]
    for score, k, rb in seg_scores[:3]:
        bs = [v for pid, v in base.items() if people[pid]["segment_label"] == k]
        complaints = [
            r["complaint"].strip()
            for r in sorted(rb, key=lambda r: (r["understood"], r["persona"]))
            if r.get("complaint", "").strip()
        ]
        lines += [
            f"**{k}** ({len(rb)} người): hiểu mình {fmt(score)} (nền {fmt(mean(bs))}), "
            f"bớt một mình {fmt(mean(r['less_alone'] for r in rb))}, "
            f"bình yên {fmt(mean(r['peaceful'] for r in rb))}, "
            f"muốn quay lại {fmt(mean(r['want_return'] for r in rb))}.",
            "",
            *[f'- "{c}"' for c in list(dict.fromkeys(complaints))[:3]],
            "",
        ]

    # Flags.
    lines += ["## Cờ và câu bị chỉ ra", ""]
    for m in ("A", "B"):
        counts = ", ".join(f"{FLAG_VI[f]} {sum(1 for r in by_m[m] if r.get(f))}" for f in FLAGS)
        lines.append(f"- Mốc {m}: {counts}.")
        for f in FLAGS:
            top = quotes_for(by_m[m], f).most_common(2)
            if top:
                lines.append(f"  - {FLAG_VI[f]}: " + "; ".join(f"'{t}' ({n})" for t, n in top))

    # Codex comparison.
    if crows:
        lines += ["", "## Codex so với Claude trên cùng 20 người giả", ""]
        lines += [table_row("Mục", "Claude", "Codex", "Lệch TB / người"), table_row(*["---"] * 4)]
        for m in ("A", "B"):
            claude_by = {r["persona"]: r for r in by_m[m]}
            pairs = [(c, claude_by[c["persona"]]) for c in cby_m[m] if c["persona"] in claude_by]
            for key in SCORES:
                lines.append(
                    table_row(
                        f"{SCORE_VI[key]} (mốc {m})",
                        fmt(mean(x[key] for _, x in pairs)),
                        fmt(mean(c[key] for c, _ in pairs)),
                        fmt(mean(abs(c[key] - x[key]) for c, x in pairs)),
                    )
                )
        ok_c, n_c = share(cby_m["A"], "fits_after_change", True)
        lines += [
            "",
            f"- Codex: thấy việc nhỏ hợp sau khi đổi (mốc A) **{ok_c}/{n_c}**. Kế hoạch cần từ "
            "11/20 lên ≥ 17/20.",
        ]
        cask = cby_m["ask"]
        lines.append(
            "- Codex, biến thể hỏi lại: thấy bị kiểm tra "
            f"{sum(1 for r in cask if r.get('felt_checked'))}/{len(cask)}, "
            f"giúp {fmt(mean(r['help'] for r in cask))}."
        )
        for m in ("A", "B"):
            claude_by = {r["persona"]: r for r in by_m[m]}
            disagree: Counter[str] = Counter()
            for c in cby_m[m]:
                x = claude_by.get(c["persona"])
                if not x:
                    continue
                for chk, val in c.get("checks", {}).items():
                    if chk in x.get("checks", {}) and bool(val) != bool(x["checks"][chk]):
                        disagree[chk] += 1
            far = [
                c["persona"]
                for c in cby_m[m]
                if c["persona"] in claude_by
                and abs(c["understood"] - claude_by[c["persona"]]["understood"]) >= 2
            ]
            lines.append(
                f"- Mốc {m}: câu kiểm trả lời ngược nhau: "
                + (", ".join(f"`{k}` {v}" for k, v in disagree.most_common()) or "không có")
                + f". Lệch điểm hiểu mình từ 2 trở lên: {', '.join(far) or 'không có'}."
            )
            cf = Counter(f for c in cby_m[m] for f in FLAGS if c.get(f))
            xf = Counter(
                f
                for c in cby_m[m]
                if c["persona"] in claude_by
                for f in FLAGS
                if claude_by[c["persona"]].get(f)
            )
            lines.append(
                "  - Cờ trên 20 người: Codex "
                + ", ".join(f"{FLAG_VI[f]} {cf[f]}" for f in FLAGS)
                + "; Claude "
                + ", ".join(f"{FLAG_VI[f]} {xf[f]}" for f in FLAGS)
                + "."
            )
        complaints = [c["complaint"] for c in cby_m["B"] if c.get("complaint")]
        if complaints:
            lines.append("- Vài lời chê của Codex (mốc B):")
            lines += [f'  - "{c}"' for c in complaints[:3]]
    lines += ["", *LIMITS]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("packets")
    pk.add_argument("--out", required=True)
    pk.add_argument("--batches", type=int, default=7)
    rp = sub.add_parser("report")
    rp.add_argument("--claude", nargs="+", required=True)
    rp.add_argument("--codex", nargs="*", default=[])
    rp.add_argument("--out", default=str(QA / "report-merged-plan.md"))
    rp.add_argument("--summary", default=None, help="hand-written Markdown inserted at the top")
    args = parser.parse_args()
    if args.cmd == "packets":
        cmd_packets(Path(args.out), args.batches)
    else:
        cmd_report(args.claude, args.codex, Path(args.out), args.summary)


if __name__ == "__main__":
    main()
