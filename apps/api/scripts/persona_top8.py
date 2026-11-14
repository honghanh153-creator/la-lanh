"""Judge the TOP 8 ideas (docs: 2026-11-14 debate) with the 100 synthetic personas.

    uv run --directory apps/api python -m scripts.persona_top8 packets --out <dir>
    uv run --directory apps/api python -m scripts.persona_top8 report --claude <json>... \
        [--codex <json>...] --out ../../qa/personas/report-top8-ideas.md

``packets`` writes one judge packet per batch (personas with their fixed situation of the
day and their astrology belief) plus the stratified Codex sample. ``report`` checks every
judged row against the per-idea pass rules below and writes the Markdown report.
Model judgement on text mocks only: not real users, not product code.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_report import table_row

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
SEED = 20261114
IDEAS = {
    1: "Note sát chuyện sinh viên, xoay chủ đề, nói thật vì sao có note này",
    2: "Mood, góc đọc, nút 'không giống mình' đổi việc nhỏ ngay",
    3: "Mở app chọn nghỉ / gỡ / chơi; quay lại sau thời gian vắng không phải giải thích",
    4: "Hỏi lại việc đã giữ, một lần, bỏ qua được",
    5: "Chuyện ngắn minh họa về cảm giác lạc lõng",
    6: "Gửi một lá cho người quen, kèm mẫu câu mở lời",
    7: "'Điều từng giúp mình': tự đánh dấu, tự bỏ dấu",
    8: "Trò chơi chọn kết thúc chuyện vui đời sinh viên",
}
SITUATIONS = {
    "tired": "Hôm nay bạn rất mệt, gần như hết sức, chỉ muốn nằm.",
    "away_2w": "Bạn vừa mở lại app sau hai tuần không dùng.",
    "shared_phone": "Điện thoại này thỉnh thoảng người nhà hoặc bạn cùng phòng cầm dùng.",
    "no_safe_person": (
        "Lúc này bạn không có ai an toàn để tâm sự (gia đình căng, bạn bè chưa thân)."
    ),
}
BELIEF = {
    "high": "tin chiêm tinh khá nhiều",
    "mid": "nửa tin nửa ngờ, đọc cho vui",
    "low": "không tin chiêm tinh, chỉ thử app",
}
ENTERED = {
    "date_only": "chỉ nhập ngày sinh",
    "approximate": "ngày sinh, giờ khoảng và nơi sinh",
    "exact": "ngày, giờ và nơi sinh chính xác",
}
GROUPS = {
    "first_year_away": "Năm nhất xa nhà",
    "dorm_boarding": "Năm nhất xa nhà",
    "exam_season": "Áp lực học",
    "family_pressure": "Áp lực học",
    "social_comparison": "Áp lực học",
    "part_time_job": "Vừa học vừa làm",
    "money_tight": "Vừa học vừa làm",
    "final_year_job_hunt": "Năm cuối / việc đầu tiên",
    "first_job": "Năm cuối / việc đầu tiên",
    "shift_work": "Người đi làm trẻ",
    "deadline_heavy": "Người đi làm trẻ",
    "difficult_boss": "Người đi làm trẻ",
    "older_adult": "Nhóm khác",
    "parent": "Nhóm khác",
    "lgbtq": "Nhóm khác",
    "low_digital": "Nhóm khác",
}
NO_SAFE = "Không có ai an toàn (tình huống)"
CHECKS: dict[int, tuple[str, ...]] = {
    1: ("reason_vs_interpretation_clear", "feels_relevant"),
    2: ("fits_after_change", "contradiction_fixed"),
    3: ("found_right_path", "could_stop", "felt_blamed_for_absence"),
    4: ("asked_once_no_penalty", "answer_changes_next"),
    5: ("mistook_for_real_testimony", "felt_difficulty_denied", "felt_false_promise"),
    6: ("saw_preview", "worried_private_info_attached", "recipient_needs_account", "would_send"),
    7: ("could_find_again", "could_remove", "worried_auto_saved"),
    8: ("understood_how_to_play", "joke_hurt", "could_stop"),
}
# (check, wanted value, minimum share of personas). Share 1.0 = "mọi ca" in the debate doc.
RULES: dict[int, list[tuple[str, bool, float]]] = {
    1: [("reason_vs_interpretation_clear", True, 0.90)],
    2: [("fits_after_change", True, 0.85), ("contradiction_fixed", True, 1.0)],
    3: [
        ("found_right_path", True, 0.90),
        ("could_stop", True, 1.0),
        ("felt_blamed_for_absence", False, 1.0),
    ],
    4: [("asked_once_no_penalty", True, 1.0), ("answer_changes_next", True, 1.0)],
    5: [
        ("mistook_for_real_testimony", False, 1.0),
        ("felt_difficulty_denied", False, 1.0),
        ("felt_false_promise", False, 1.0),
    ],
    6: [
        ("saw_preview", True, 1.0),
        ("worried_private_info_attached", False, 1.0),
        ("recipient_needs_account", False, 1.0),
    ],
    7: [
        ("could_find_again", True, 0.90),
        ("could_remove", True, 1.0),
        ("worried_auto_saved", False, 1.0),
    ],
    8: [
        ("understood_how_to_play", True, 0.90),
        ("joke_hurt", False, 1.0),
        ("could_stop", True, 1.0),
    ],
}
NOT_TESTABLE = {
    1: (
        "Phần mô phỏng 42 ngày (4 nhóm tình huống mỗi 7 ngày, 5 tình huống mỗi 14 ngày, "
        "không lặp tiêu đề 7 ngày, không lặp nguyên note 14 ngày) cần code; baseline hiện tại "
        "trượt (trung vị 1 tình huống mỗi 14 ngày)."
    ),
    2: "Mock chỉ có một ca mâu thuẫn (câu 'đang hăng' khi chọn Đuối); mọi ca phải thử bằng code.",
    4: "'Câu trả lời làm đổi gợi ý lần sau' chỉ kiểm thật được khi có code.",
    6: (
        "Không kèm mood/ngày sinh và người nhận không cần tài khoản phải kiểm trên app thật "
        "bằng dữ liệu giả."
    ),
    7: "Xóa được thật và không tự lưu mood/Tarot phải kiểm trên app thật.",
}


def personas() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((QA / "personas-100.json").read_text(encoding="utf-8"))[
        "personas"
    ]
    return data


def assign(people: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    """Fixed situation of the day (25 each) and belief from the persona's interest trait."""

    order = [p["id"] for p in people]
    random.Random(SEED).shuffle(order)  # noqa: S311 - fixed test split
    keys = list(SITUATIONS)
    situation = {pid: keys[i % len(keys)] for i, pid in enumerate(order)}
    return {
        p["id"]: {"situation": situation[p["id"]], "belief": p["traits"]["interest"]}
        for p in people
    }


def packet(p: Mapping[str, Any], extra: Mapping[str, str]) -> dict[str, Any]:
    keys = (
        "id",
        "name",
        "age",
        "segment_label",
        "situation",
        "stressors",
        "personality",
        "daily_rhythm",
        "phone_habits",
        "wants_from_app",
        "would_quit_if",
    )
    out = {k: p[k] for k in keys}
    out["life_situation"] = out.pop("situation")
    out["astrology_belief"] = BELIEF[extra["belief"]]
    out["entered_in_app"] = ENTERED[p["birth"]["precision"]]
    out["today"] = SITUATIONS[extra["situation"]]
    return out


def codex_sample(
    people: Sequence[Mapping[str, Any]], extra: Mapping[str, Mapping[str, str]]
) -> list[str]:
    """20 personas: about 3 per persona group, each situation of the day represented."""

    by_group: dict[str, list[str]] = defaultdict(list)
    for p in people:
        by_group[GROUPS[p["segment"]]].append(p["id"])
    rng = random.Random(SEED + 8)  # noqa: S311 - fixed test split
    chosen: list[str] = []
    for group in sorted(by_group):
        ids = sorted(by_group[group])
        rng.shuffle(ids)
        chosen += ids[:3]
    rest = [p["id"] for p in people if p["id"] not in chosen]
    rng.shuffle(rest)
    while len(chosen) < 20:
        chosen.append(rest.pop())
    return sorted(chosen[:20])


def cmd_packets(out: Path, batches: int) -> None:
    people = personas()
    extra = assign(people)
    out.mkdir(parents=True, exist_ok=True)
    rows = [packet(p, extra[p["id"]]) for p in people]
    order = list(rows)
    random.Random(SEED + 1).shuffle(order)  # noqa: S311 - fixed test split
    for i in range(batches):
        (out / f"claude-{i + 1}.json").write_text(
            json.dumps(order[i::batches], ensure_ascii=False, indent=1), encoding="utf-8"
        )
    sample = codex_sample(people, extra)
    picked = [r for r in rows if r["id"] in sample]
    half = len(picked) // 2
    (out / "codex-1.json").write_text(
        json.dumps(picked[:half], ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out / "codex-2.json").write_text(
        json.dumps(picked[half:], ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out / "assignment.json").write_text(
        json.dumps({"extra": extra, "codex_sample": sample}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(
        f"{len(rows)} personas in {batches} batches; codex sample {len(sample)}:",
        Counter(extra[s]["situation"] for s in sample),
    )


def load_rows(paths: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rows += data["rows"] if isinstance(data, dict) else data
    return rows


def share(rows: Sequence[Mapping[str, Any]], check: str, wanted: bool) -> tuple[int, int]:
    answered = [r for r in rows if check in r.get("checks", {})]
    return sum(1 for r in answered if bool(r["checks"][check]) is wanted), len(answered)


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return round(statistics.fmean(items), 2) if items else None


def cmd_report(claude: list[str], codex: list[str], out: Path, summary: str | None) -> None:
    people = {p["id"]: p for p in personas()}
    extra = assign(list(people.values()))
    rows = load_rows(claude)
    crows = load_rows(codex) if codex else []
    seen = Counter((r["persona"], int(r["idea"])) for r in rows)
    missing = [(pid, i) for pid in people for i in IDEAS if seen[(pid, i)] == 0]
    for r in rows + crows:
        r["idea"] = int(r["idea"])
        p = people[r["persona"]]
        r["group"] = GROUPS[p["segment"]]
        r["situation_today"] = extra[r["persona"]]["situation"]
        r["belief"] = extra[r["persona"]]["belief"]
        r["precision"] = p["birth"]["precision"]
    group_names = [*sorted(set(GROUPS.values())), NO_SAFE]

    def in_group(r: Mapping[str, Any], g: str) -> bool:
        return bool(r["situation_today"] == "no_safe_person" if g == NO_SAFE else r["group"] == g)

    def help_return(subset: Sequence[Mapping[str, Any]]) -> tuple[float | None, float | None]:
        return mean(r["help"] for r in subset), mean(r["return"] for r in subset)

    lines = [
        "# 8 ý tưởng qua 100 người giả (14.11.2026)",
        "",
        "**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** "
        "Không phải người dùng thật, không phải app thật.",
        "",
        "- Mỗi ý được mô tả 3-6 màn bằng chữ: [top8/mocks.md](top8/mocks.md).",
        "- 100 người giả hư cấu. Mỗi người có một tình huống hôm nay cố định, 25 người mỗi loại: "
        "rất mệt, vừa quay lại sau hai tuần, điện thoại dùng chung, không có ai an toàn. "
        "Mức tin chiêm tinh lấy theo hồ sơ.",
        f"- Giám khảo: 7 Claude subagent riêng chấm {len(rows)} cặp (100 người x 8 ý). "
        f"Codex chấm độc lập {len(crows)} cặp (20 người chọn đều theo nhóm x 8 ý).",
        "- Câu hỏi chấm: [top8/judge-instructions.md](top8/judge-instructions.md). "
        "Ngưỡng: bảng TOP 8 trong `docs/reviews/2026-11-14-ket-qua-tranh-luan.md`.",
        "",
    ]
    if missing:
        lines += [f"Thiếu {len(missing)} cặp chưa chấm: {missing[:10]}", ""]
    if summary:
        lines += [Path(summary).read_text(encoding="utf-8").rstrip(), ""]
    lines += [
        "## Bảng tổng",
        "",
        table_row(
            "Ý",
            "Ngưỡng phần người giả",
            "Giúp mình (1-5)",
            "Muốn quay lại (1-5)",
            "Có cờ trách / ép / lo riêng tư / phụ thuộc",
            "Codex: giúp / quay lại",
        ),
        table_row(*["---"] * 6),
    ]
    detail: list[str] = []
    for i, title in IDEAS.items():
        ir = [r for r in rows if r["idea"] == i]
        cr = [r for r in crows if r["idea"] == i]
        verdicts = []
        for check, wanted, need in RULES[i]:
            ok_n, n = share(ir, check, wanted)
            verdicts.append((check, wanted, need, ok_n, n, n > 0 and ok_n / n >= need))
        group_ok = True
        if i == 2:
            for g in group_names:
                ok_n, n = share([r for r in ir if in_group(r, g)], "fits_after_change", True)
                group_ok = group_ok and not (n and ok_n / n < 0.80)
        passed = all(v[-1] for v in verdicts) and group_ok
        verdict = ("ĐẠT" if passed else "TRƯỢT") + (" (phần 42 ngày chưa thử)" if i == 1 else "")
        flags = sum(1 for r in ir if any(r.get(f) for f in FLAGS))
        h, rt = help_return(ir)
        ch, crt = help_return(cr)
        lines.append(
            table_row(f"{i}. {title}", verdict, h, rt, f"{flags}/{len(ir)}", f"{ch} / {crt}")
        )
        detail += [
            f"## Ý {i}. {title}",
            "",
            f"Kết luận theo ngưỡng phần người giả: **{verdict}**.",
            "",
        ]
        for check, wanted, need, ok_n, n, ok in verdicts:
            detail.append(
                f"- `{check}` = {str(wanted).lower()}: {ok_n}/{n} "
                f"(cần ≥ {int(need * 100)}%) → {'đạt' if ok else 'trượt'}"
            )
        if i == 2:
            detail.append(f"- Mỗi nhóm ≥ 80% thấy hợp: {'đạt' if group_ok else 'trượt'}")
        if i in NOT_TESTABLE:
            detail.append(f"- Chưa thử được bằng mock: {NOT_TESTABLE[i]}")
        detail += ["", table_row("Nhóm", "Người", "Giúp", "Quay lại"), table_row(*["---"] * 4)]
        for g in group_names:
            gr = [r for r in ir if in_group(r, g)]
            detail.append(table_row(g, len(gr), *help_return(gr)))
        for label, key in (("tin chiêm tinh", "high"), ("nửa tin", "mid"), ("không tin", "low")):
            br = [r for r in ir if r["belief"] == key]
            detail.append(table_row(f"({label})", len(br), *help_return(br)))
        do = [r for r in ir if r["precision"] == "date_only"]
        detail.append(table_row("(chỉ nhập ngày sinh)", len(do), *help_return(do)))
        counts = {f: sum(1 for r in ir if r.get(f)) for f in FLAGS}
        detail += [
            "",
            f"Cờ: bị trách {counts['blame']}, bị ép {counts['pressure']}, "
            f"lo riêng tư {counts['privacy']}, phụ thuộc {counts['dependence']}.",
        ]
        quotes = Counter(r["quote"].strip() for r in ir if r.get("quote", "").strip())
        if quotes:
            top = "; ".join(f"'{q}' ({n})" for q, n in quotes.most_common(3))
            detail.append(f"Câu trong mock bị chỉ ra nhiều nhất: {top}")
        complaints = [
            r["complaint"].strip()
            for r in sorted(ir, key=lambda r: (r["help"], r["persona"]))
            if r.get("complaint", "").strip()
        ]
        detail += ["", "Lời chê ở các cặp điểm thấp nhất:", ""]
        detail += [f"- {c}" for c in list(dict.fromkeys(complaints))[:3]]
        if cr:
            detail += ["", *codex_compare(i, ir, cr)]
        detail.append("")
    lines += ["", *detail, *LIMITS]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def codex_compare(
    idea: int, claude_rows: Sequence[Mapping[str, Any]], codex_rows: Sequence[Mapping[str, Any]]
) -> list[str]:
    by_persona = {r["persona"]: r for r in claude_rows}
    pairs = [(c, by_persona[c["persona"]]) for c in codex_rows if c["persona"] in by_persona]
    if not pairs:
        return []
    disagree = [
        f"{c['persona']}/{chk}"
        for c, x in pairs
        for chk in CHECKS[idea]
        if chk in c.get("checks", {})
        and chk in x.get("checks", {})
        and bool(c["checks"][chk]) != bool(x["checks"][chk])
    ]
    far = [c["persona"] for c, x in pairs if abs(c["help"] - x["help"]) >= 2]
    lines = [
        f"Codex so với Claude trên cùng {len(pairs)} người giả: "
        f"giúp {mean(c['help'] for c, _ in pairs)} so với {mean(x['help'] for _, x in pairs)}, "
        f"quay lại {mean(c['return'] for c, _ in pairs)} "
        f"so với {mean(x['return'] for _, x in pairs)}. "
        f"Lệch trung bình: giúp {mean(abs(c['help'] - x['help']) for c, x in pairs)}, "
        f"quay lại {mean(abs(c['return'] - x['return']) for c, x in pairs)}.",
        f"- Người giả lệch điểm giúp từ 2 trở lên: {', '.join(far) if far else 'không có'}.",
        f"- Câu kiểm trả lời ngược nhau: {', '.join(disagree[:8]) if disagree else 'không có'}.",
    ]
    complaint = next((c["complaint"] for c, _ in pairs if c.get("complaint")), "")
    if complaint:
        lines.append(f"- Một lời chê của Codex: {complaint}")
    return lines


FLAGS = ("blame", "pressure", "privacy", "dependence")
LIMITS = [
    "## Giới hạn",
    "",
    "- Người giả và giám khảo đều là mô hình AI, chấm mô tả bằng chữ chứ không dùng app thật. "
    "Kết quả cho biết hướng, không chứng minh người thật sẽ vui hơn hay quay lại.",
    "- Mỗi người giả chỉ chấm một tình huống hôm nay. Ý hợp với người mệt có thể khác với ý "
    "hợp với người vắng lâu.",
    "- Ngưỡng 'mọi ca' trong bản tranh luận là yêu cầu thiết kế; ở đây nó được đo bằng cảm nhận "
    "của từng người giả, nên một người hiểu nhầm là đủ để trượt.",
    "- Các ngưỡng về lưu dữ liệu, xóa, thu hồi link, không ghi log phải kiểm trên app thật bằng "
    "dữ liệu giả khi có code.",
    "",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("packets")
    pk.add_argument("--out", required=True)
    pk.add_argument("--batches", type=int, default=7)
    rp = sub.add_parser("report")
    rp.add_argument("--claude", nargs="+", required=True)
    rp.add_argument("--codex", nargs="*", default=[])
    rp.add_argument("--out", default=str(QA / "report-top8-ideas.md"))
    rp.add_argument("--summary", default=None, help="hand-written Markdown inserted at the top")
    args = parser.parse_args()
    if args.cmd == "packets":
        cmd_packets(Path(args.out), args.batches)
    else:
        cmd_report(args.claude, args.codex, Path(args.out), args.summary)


if __name__ == "__main__":
    main()
