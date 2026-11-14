"""Score concept mocks v7 (v6 + LN Lá nhây + H Học theo bạn + 5 fixes) on personas-1000.

    uv run --directory apps/api python -m scripts.persona_concepts7 packets \
        --v6 <mocks-v6.md> --v7 <mocks-v7.md> --out <dir>
    uv run --directory apps/api python -m scripts.persona_concepts7 report --judged <dir> \
        [--v6-judged ../../qa/personas/concepts/judged-1000] --out <md>

Design (viral-concepts-thresholds-preregistered.md, Bản 3 + Bản 4):
- package7: control (merged-plan week-6 mock) vs the v7 package, a stratified 300
  (rank % 10 < 3 of the same stratified order as v6), 25 per batch;
- part7: v6 package vs v6 package + LN / + H (each without its pointer to the other),
  and v6 package vs the v7 package without LN and H (the 5 fixes only);
  rank % 10 == 3 / 4 / 5 (about 100 each), 34 per batch.
Package conditions are the same 9 as v6. Judges use concepts-pair-judge-v2.
Model judgement on text mocks only: not real users, not real code.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_concepts import (
    ADDONS,
    FLAGS,
    PACKAGE,
    QA,
    SEED,
    _fmt,
    _gain,
    _mean,
    _pct,
    _send_rate,
    added_text,
    condition_table,
    control_text,
    load_personas,
    packet,
    paired_rows,
    situation_of_day,
    split_concepts,
    stratified_order,
)

PACKAGE7 = (*PACKAGE[:-1], "LN", "H", PACKAGE[-1])
PARTS = ("LN", "H", "FIX")
PART_VI = {"LN": "Lá nhây riêng", "H": "Học theo bạn riêng", "FIX": "5 điểm sửa riêng"}
PER_BATCH = {"package7": 25, "part7": 34}
HEAD = (
    "# Hai bản app, mô tả bằng chữ\n\nChỉ có chữ, không phải thiết kế cuối, "
    "không có code. Mọi câu là ví dụ.\n\n"
)
FIX_HOME = (
    "Màn đầu chỉ có 3 khối, không thêm khối nào khác, từ trên xuống: (1) Lá pixel và một câu "
    "ngắn của Lá theo mood, kèm nút nhỏ [Lá yên chút] (xem LN); (2) thẻ"
)
FIX_STICKER = "ba chỗ: sau khi xong một việc, trong mục Chơi, và khi chạm Lá; xem LN"


def full_version(parts: Mapping[str, str]) -> str:
    """The control experience plus a whole package, as one self-contained version."""

    return (
        control_text()
        + "\n\n## Các phần mới của bản này\n\n"
        + added_text(
            parts,
            PACKAGE,
            "phần trên",
            "Ngoài phần trên, bản này cộng hoặc thay các phần dưới đây. Mọi câu là ví dụ.",
        )
    )


def fix_only(parts7: Mapping[str, str]) -> dict[str, str]:
    """v7 sections with the LN and H parts and every pointer to them removed."""

    out = {k: v for k, v in parts7.items() if k not in ("LN", "H", "_rel_LN", "_rel_H")}
    rules = out["_rules"]
    if FIX_HOME not in rules:
        raise SystemExit("v7 home-screen rule changed; update FIX_HOME")
    out["_rules"] = rules.replace(
        FIX_HOME, "Màn đầu chỉ có 2 khối, không thêm khối nào khác, từ trên xuống: (1) thẻ"
    ).replace("(S1); (3) note", "(S1); (2) note")
    s10 = out["S10"]
    if FIX_STICKER not in s10:
        raise SystemExit("v7 sticker line changed; update FIX_STICKER")
    out["S10"] = s10.replace(FIX_STICKER, "hai chỗ: sau khi xong một việc và trong mục Chơi")
    out["S1"] = "\n".join(ln for ln in out["S1"].splitlines() if "(xem H)" not in ln)
    leftover = [
        k
        for k, v in out.items()
        if any(w in v for w in ("xem LN", "xem H)", "Lá yên chút", "Lá nhây", "[Xem bài]"))
    ]
    if leftover:
        raise SystemExit(f"LN/H pointers left in the fixes-only version: {leftover}")
    return out


def versions(
    kind: str, name: str, parts6: Mapping[str, str], parts7: Mapping[str, str], c_label: str
) -> tuple[str, str]:
    """(control text, treatment text)."""

    if kind == "package7":
        return control_text(), added_text(parts7, PACKAGE7, c_label)
    base = full_version(parts6)
    if name == "FIX":
        return base, full_version(fix_only(parts7))
    return base, added_text(alone(parts7, name), (name,), c_label)


def alone(parts7: Mapping[str, str], code: str) -> dict[str, str]:
    """LN or H on its own: drop the line that points at the other one."""

    out = dict(parts7)
    other = "(xem H)" if code == "LN" else "(LN)**"
    out[code] = "\n".join(ln for ln in parts7[code].splitlines() if other not in ln)
    if ("xem H" if code == "LN" else "(LN)") in out[code]:
        raise SystemExit(f"{code} still points at the other part; update alone()")
    return out


def write_batch(
    bdir: Path, control: str, treat: str, c_label: str, first: str, people: list[dict[str, Any]]
) -> None:
    texts = {c_label: control, ("Bản Y" if c_label == "Bản X" else "Bản X"): treat}
    first_label = f"Bản {first}"
    second_label = "Bản Y" if first == "X" else "Bản X"
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "mock.md").write_text(
        f"{HEAD}# {first_label}\n\n{texts[first_label]}\n\n# {second_label}\n\n"
        f"{texts[second_label]}\n",
        encoding="utf-8",
    )
    (bdir / "personas.json").write_text(
        json.dumps(people, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def cmd_packets(personas_path: Path, v6: Path, v7: Path, out: Path) -> None:
    people = load_personas(personas_path)
    by_id = {p["id"]: p for p in people}
    sit = situation_of_day(people)
    parts6 = split_concepts(v6.read_text(encoding="utf-8"))
    parts7 = split_concepts(v7.read_text(encoding="utf-8"), (*PACKAGE7, *ADDONS))
    fix_only(parts7)  # fail early if the v7 text moved
    order = stratified_order(people)
    sample = [pid for r, pid in enumerate(order) if r % 10 < 3]
    jobs: list[tuple[str, str, list[str], list[str]]] = [
        ("package7", "package7", list(PACKAGE7), sample)
    ]
    for i, name in enumerate(PARTS):
        ids = [pid for r, pid in enumerate(order) if r % 10 == 3 + i]
        jobs.append(("part7", name, [] if name == "FIX" else [name], ids))
    combos = [("Bản X", "X"), ("Bản Y", "X"), ("Bản X", "Y"), ("Bản Y", "Y")]
    manifest = []
    n_batch = 0
    for kind, name, codes, ids in jobs:
        shuffled = list(ids)
        random.Random(f"{SEED}-v7-{name}").shuffle(shuffled)  # noqa: S311 - fixed test split
        size = PER_BATCH[kind]
        chunks = [shuffled[i : i + size] for i in range(0, len(shuffled), size)]
        for j, chunk in enumerate(chunks):
            c_label, first = combos[(n_batch + j) % 4]
            control, treat = versions(kind, name, parts6, parts7, c_label)
            batch = f"{name}-{j + 1:02d}"
            write_batch(
                out / batch,
                control,
                treat,
                c_label,
                first,
                [{**packet(by_id[pid], sit[pid]), "read_first": first} for pid in chunk],
            )
            manifest.append(
                {
                    "batch": batch,
                    "kind": kind,
                    "part": name,
                    "codes": codes,
                    "control_label": c_label[-1],
                    "read_first": first,
                    "personas": chunk,
                }
            )
        n_batch += len(chunks)
    (out / "manifest.json").write_text(
        json.dumps(
            {"judge_version": 2, "batches": manifest, "situation": sit},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"{len(manifest)} batches")


def _rate(rows: Sequence[Mapping[str, Any]], side: str) -> str:
    return _pct(round(_send_rate(rows, side) * len(rows)), len(rows))


MIN_REACHED = 30


def _verdict(reached: int, passed: bool) -> str:
    """Codex round 7: fewer than 30 personas reaching a feature is not enough to conclude."""

    if reached < MIN_REACHED:
        return f"chưa đủ bằng chứng (dưới {MIN_REACHED} người)"
    return "đạt" if passed else "trượt"


def _count(rows: Sequence[Mapping[str, Any]], key: str) -> int:
    return sum(1 for r in rows if r["treat"].get(key))


def cmd_report(personas_path: Path, judged: Path, v6_judged: Path | None, out: Path) -> None:
    people = {p["id"]: p for p in load_personas(personas_path)}
    manifest = json.loads((judged / "manifest.json").read_text(encoding="utf-8"))
    sit = manifest["situation"]
    rows = paired_rows(judged, manifest, "out-")
    part_of = {b["batch"]: b["part"] for b in manifest["batches"]}
    pkg = [r for r in rows if r["kind"] == "package7"]
    table, ok = condition_table(pkg, people, sit)
    keys = ("understood", "less_alone", "peaceful", "want_return", "return_next_week")
    lines = [
        "# Gói concept bản 7 (bản 6 + Lá nhây + Học theo bạn + 5 điểm sửa): chấm trên người giả",
        "",
        "**Mô phỏng trên người giả, giám khảo là mô hình AI, chấm trên mô tả bằng chữ.** "
        "Không phải người dùng thật, không phải code thật. Mock là mức trần.",
        "",
        "- Ngưỡng ghi trước: `viral-concepts-thresholds-preregistered.md` bản 3 và bản 4 "
        "(9 điều kiện của gói giữ nguyên như bản 6).",
        f"- Gói bản 7 so với đối chứng: {len(pkg)} cặp (mẫu phân tầng 300 trong 1000). "
        f"Từng phần so với gói bản 6: "
        + ", ".join(
            f"{PART_VI[p]} {sum(1 for r in rows if part_of[r['batch']] == p)} cặp" for p in PARTS
        )
        + ".",
        "",
        "## Gói bản 7 so với đối chứng: 9 điều kiện",
        "",
        "| # | Điều kiện | Kết quả | |",
        "|---|---|---|---|",
        *table,
        "",
        f"**Gói bản 7 {'đạt' if all(ok) else 'chưa đạt'}** ({sum(ok)}/{len(ok)} điều kiện).",
        "",
        "| | Hiểu mình | Bớt một mình | Bình yên | Muốn quay lại | Tuần sau quay lại |",
        "|---|---|---|---|---|---|",
    ]
    for side, label in (("control", "Đối chứng"), ("treat", "Gói bản 7")):
        vals = " | ".join(_fmt(_mean([float(r[side][k]) for r in pkg])) for k in keys)
        lines.append(f"| {label} | {vals} |")
    if v6_judged and (v6_judged / "manifest.json").exists():
        m6 = json.loads((v6_judged / "manifest.json").read_text(encoding="utf-8"))
        v6 = {r["persona"]: r for r in paired_rows(v6_judged, m6, "out-") if r["kind"] == "package"}
        same = [(r, v6[r["persona"]]) for r in pkg if r["persona"] in v6]
        vals = " | ".join(_fmt(_mean([float(b["treat"][k]) for _, b in same])) for k in keys)
        lines += [
            f"| Gói bản 6 (cùng {len(same)} người, lượt chấm trước) | {vals} |",
            "",
            "Gói bản 6 và bản 7 được chấm ở hai lượt khác nhau; chênh giữa chúng chỉ để tham khảo.",
        ]
    lines += [
        "",
        f"- Gửi/đăng hoặc rủ: đối chứng {_rate(pkg, 'control')}, "
        f"gói bản 7 {_rate(pkg, 'treat')}; "
        f'gửi thẻ "Bạn đáp câu nào?" {_count(pkg, "quiz_card_shared")}.',
        "",
        "## Từng phần so với gói bản 6",
        "",
        "| Phần | Cặp | Chênh hiểu mình | Chênh bớt một mình | Chênh bình yên "
        "| Chênh muốn quay lại | Chênh gửi/rủ | Cờ hại (bản có phần mới) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in PARTS:
        prow = [r for r in rows if part_of[r["batch"]] == p]
        diff = 100 * (_send_rate(prow, "treat") - _send_rate(prow, "control"))
        d_share = f"{diff:+.1f} điểm %".replace(".", ",") if prow else "—"
        harm = sum(1 for r in prow if any(r["treat"].get(f) for f in FLAGS))
        lines.append(
            f"| {PART_VI[p]} | {len(prow)} | {_gain(prow, 'understood')} | "
            f"{_gain(prow, 'less_alone')} | {_gain(prow, 'peaceful')} | "
            f"{_gain(prow, 'want_return')} | {d_share} | {harm} |"
        )
    ln_rows = pkg + [r for r in rows if part_of[r["batch"]] == "LN"]
    teased, wrong = _count(ln_rows, "teased"), _count(ln_rows, "la_nhay_wrong_time")
    low = [r for r in ln_rows if r["treat"].get("teased")]
    lesson = [
        r
        for r in rows
        if part_of[r["batch"]] in ("package7", "H") and r["treat"].get("lesson_entry")
    ]
    entry = Counter(r["treat"]["lesson_entry"] for r in lesson)
    chart = Counter(
        r["treat"]["chart_line"] for r in rows if r["treat"].get("chart_line") is not None
    )
    h_und = _mean([float(r["treat"]["understood"]) for r in lesson])
    h_pe = _mean([float(r["treat"]["peaceful"]) for r in lesson])
    h_press = sum(1 for r in lesson if r["treat"].get("lesson_pressure"))
    h_rows = [r for r in rows if part_of[r["batch"]] in ("package7", "H")]
    seen = sum(1 for r in h_rows if r["treat"].get("lesson_seen"))
    finished = sum(1 for r in lesson if r["treat"].get("lesson_finished"))
    lines += [
        "",
        "## Lá nhây (mốc bản 3, siết còn 3%)",
        "",
        f"- Thấy Lá chọc, phán xét hoặc ra lệnh cho mình: {_pct(teased, len(ln_rows))} "
        f"({teased}/{len(ln_rows)}); mốc ≤ 3%: "
        f"{_verdict(len(ln_rows), teased <= 0.03 * len(ln_rows))}.",
        f'- Lá nhây sai lúc (mood thấp, "Chỉ cần được nghe", phần hỗ trợ): {wrong}; mốc 0: '
        f"{_verdict(len(ln_rows), wrong == 0)}.",
        "",
        "## Học theo bạn (mốc bản 3)",
        "",
        f"- Thấy lối vào bài: {seen}; mở bài: {len(lesson)} (từ lời mời của Lá "
        f"{entry.get('la', 0)}, từ ba lô {entry.get('ba_lo', 0)}, từ Khám phá "
        f"{entry.get('kham_pha', 0)}); đọc hết tới phần việc thử: {finished}.",
        f"- Hiểu mình {_fmt(h_und)}, bình yên {_fmt(h_pe)} (mốc mỗi số ≥ 3,5): "
        f"{_verdict(len(lesson), (h_und or 0) >= 3.5 and (h_pe or 0) >= 3.5)}.",
        f"- Bài học làm thấy bị ép hoặc bị dắt: {h_press}; mốc 0: "
        f"{_verdict(len(lesson), h_press == 0)}.",
        f"- Dòng lý do theo lá số: thấy hợp {chart.get('right', 0)}, thấy nói quá "
        f"{chart.get('overclaim', 0)}, không để ý {chart.get('unnoticed', 0)}.",
    ]
    if low:
        lines += ["", "Ví dụ câu bị coi là chọc:", ""] + [
            f"- {r['treat']['quotes'].get('teased', '')}" for r in low[:5]
        ]
    lines += [
        "",
        "## Giới hạn",
        "",
        "- Người giả và giám khảo là mô hình AI, đọc chữ. Kết quả là mức trần.",
        "- Mẫu gói bản 7 là 300 người, không phải 1000; từng phần khoảng 100 người.",
        "- Phần riêng lẻ so với gói bản 6, không so với đối chứng.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("packets")
    pk.add_argument("--personas", default=str(QA / "personas-1000.json"))
    pk.add_argument("--v6", required=True)
    pk.add_argument("--v7", required=True)
    pk.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--personas", default=str(QA / "personas-1000.json"))
    rp.add_argument("--judged", required=True)
    rp.add_argument("--v6-judged", default=str(QA / "concepts" / "judged-1000"))
    rp.add_argument("--out", default=str(QA / "report-concepts-v7.md"))
    args = parser.parse_args()
    if args.cmd == "packets":
        cmd_packets(Path(args.personas), Path(args.v6), Path(args.v7), Path(args.out))
    else:
        cmd_report(Path(args.personas), Path(args.judged), Path(args.v6_judged), Path(args.out))


if __name__ == "__main__":
    main()
