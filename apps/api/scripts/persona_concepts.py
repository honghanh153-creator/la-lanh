"""Score the creative / viral concept package against the plan with the 1000 personas.

    uv run --directory apps/api python -m scripts.persona_concepts packets \
        --concepts <viral-concepts-mocks.md> --out <dir>
    uv run --directory apps/api python -m scripts.persona_concepts report --judged <dir> \
        [--summary <md>] --out ../../qa/personas/report-concepts.md

Design pre-registered in qa/personas/thresholds-1000.md section 6 ("Bản 2"):
- package: control (merged-plan week-6 mock) vs control + S1, S3-S10, paired, all 1000;
- single: control vs control + one concept, a stratified ~100 per concept (9 concepts);
- addon: package vs package + S2 / + S11, the same stratified 100 (conditional add-ons);
- neutral labels X / Y, label mapping and reading order balanced over batches.
Model judgement on text mocks only: not real users, not real code.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.persona_plan import MOOD_VI
from scripts.persona_top8 import BELIEF, ENTERED, SITUATIONS, assign

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "qa" / "personas"
SEED = 20261114 + 1000
CONTROL_MOCK = QA / "plan-variants" / "mocks" / "V0-codex.md"
PACKAGE = ("S1", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10")
ADDONS = ("S2", "S11")
EXTRA_SITUATIONS = {"normal": "Hôm nay là một ngày bình thường của bạn."}
ATTR_KEYS = (
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
PER_BATCH = {"package": 25, "single": 34, "addon": 34}


def load_personas(path: Path) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["personas"]
    return data


def situation_of_day(people: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """P001-P100 keep the fixed situation used in every earlier mock run; P101+ get one too."""

    first = assign([p for p in people if int(str(p["id"])[1:]) <= 100])
    out = {pid: v["situation"] for pid, v in first.items()}
    rng = random.Random(SEED)  # noqa: S311 - fixed test split
    for p in people:
        if p["id"] not in out:
            out[p["id"]] = rng.choices(["tired", "away_2w", "normal"], weights=[25, 20, 55])[0]
    return out


def mood_today(p: Mapping[str, Any], situation: str) -> str:
    return MOOD_VI["Đuối"] if situation == "tired" else MOOD_VI[p["mood_29"][28]]


def packet(p: Mapping[str, Any], situation: str) -> dict[str, Any]:
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
    out: dict[str, Any] = {k: p[k] for k in keys}
    out["life_situation"] = out.pop("situation")
    out["astrology_belief"] = BELIEF[p["traits"]["interest"]]
    out["entered_in_app"] = ENTERED[p["birth"]["precision"]]
    if p.get("attributes"):
        out["attributes"] = {k: p["attributes"][k] for k in ATTR_KEYS}
    out["today"] = {**SITUATIONS, **EXTRA_SITUATIONS}[situation]
    out["mood_today"] = mood_today(p, situation)
    return out


def split_concepts(text: str) -> dict[str, str]:
    """Sections of viral-concepts-mocks.md: intro rules plus one block per S-code."""

    parts: dict[str, str] = {}
    body = text.split("# Bản A", 1)[1] if "# Bản A" in text else text
    intro_end = body.find("## S1.")
    intro = body[:intro_end]
    rules = [
        line
        for line in intro.splitlines()
        if line.startswith("Giao diện") or line.startswith("**Ảnh để lưu")
    ]
    parts["_rules"] = "\n\n".join(rules)
    table = {
        m.group(1): m.group(2).strip()
        for m in re.finditer(r"^\| (S\d+)[^|]*\| (.+?) \|$", intro, flags=re.M)
    }
    for code, rel in table.items():
        parts[f"_rel_{code}"] = rel
    for m in re.finditer(
        r"^#{2,3} (S\d+)\. (.+?)$(.*?)(?=^#{2,3} S\d+\.|^## Thử có điều kiện|\Z)",
        body,
        flags=re.M | re.S,
    ):
        block = m.group(3).strip().rstrip("-").strip()
        parts[m.group(1)] = f"### {m.group(1)}. {m.group(2).strip()}\n\n{block}"
    missing = [c for c in (*PACKAGE, *ADDONS) if c not in parts]
    if missing:
        raise SystemExit(f"concept sections missing in mock file: {missing}")
    return parts


def control_text() -> str:
    lines = CONTROL_MOCK.read_text(encoding="utf-8").splitlines()
    # Drop the title and the "score moment B" note; keep the experience itself.
    body = [
        "Đây là trải nghiệm ở cuối tuần 6: gồm mọi thứ ở Mốc A và phần thêm ở Mốc B."
        if "Chấm trải nghiệm ở Mốc B" in ln
        else ln
        for ln in lines
        if not ln.startswith("# ")
        and not ln.startswith("Nguồn:")
        and not ln.startswith("Mô tả trung lập")
        and "[nguyên văn kế hoạch]** là câu" not in ln
    ]
    text = "\n".join(body)
    text = re.sub(r" ?\*\*\[nguyên văn kế hoạch[^\]]*\]\*\*", "", text)
    text = re.sub(r" \((?:đã có|thêm) PR [0-9\u2013-]+\)", "", text)
    return text.replace("chưa được chốt trong kế hoạch", "chưa chốt").strip()


def neutral(text: str, base: str) -> str:
    """Remove words that tell the judge which version is the control or the scored package."""

    text = text.replace("bản đối chứng", base)
    return re.sub(r",? ?không tính vào điểm bản A ?", " ", text).replace("  ", " ").strip()


def added_text(parts: Mapping[str, str], codes: Sequence[str], base: str, intro: str = "") -> str:
    rel = "\n".join(
        f"| {c} | {neutral(parts[f'_rel_{c}'], base)} |" for c in codes if f"_rel_{c}" in parts
    )
    blocks = "\n\n---\n\n".join(parts[c] for c in codes)
    intro = intro or (
        f"Bản này gồm **mọi thứ của {base}**, cộng hoặc thay các phần dưới đây. "
        "Mọi câu là ví dụ chưa duyệt. Mọi người trong mock là hư cấu."
    )
    table = f"| Phần | Quan hệ với {base} |\n|---|---|\n{rel}"
    return f"{intro}\n\n{table}\n\n{parts['_rules']}\n\n{blocks}"


def mock_for(
    kind: str, codes: Sequence[str], parts: Mapping[str, str], c_label: str
) -> tuple[str, str]:
    """(control text, treatment text). For add-ons the control is the full package."""

    if kind == "addon":
        package = (
            control_text()
            + "\n\n## Các phần mới của bản này\n\n"
            + added_text(
                parts,
                PACKAGE,
                "phần trên",
                "Ngoài phần trên, bản này cộng hoặc thay các phần dưới đây. Mọi câu là ví dụ.",
            )
        )
        extra = added_text(parts, codes, c_label)
        return package, extra
    return control_text(), added_text(parts, codes, c_label)


def stratified_order(people: Sequence[Mapping[str, Any]]) -> list[str]:
    def band(age: int) -> str:
        return "18-24" if age <= 24 else "25-34" if age <= 34 else "35+"

    rng = random.Random(SEED + 1)  # noqa: S311 - fixed test split
    strata: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for p in people:
        strata[(p["segment_label"], band(int(p["age"])), p["birth"]["precision"])].append(p["id"])
    order: list[str] = []
    for key in sorted(strata):
        ids = sorted(strata[key])
        rng.shuffle(ids)
        order += ids
    return order


def cmd_packets(personas_path: Path, concepts_md: Path, out: Path) -> None:
    people = load_personas(personas_path)
    by_id = {p["id"]: p for p in people}
    sit = situation_of_day(people)
    parts = split_concepts(concepts_md.read_text(encoding="utf-8"))
    order = stratified_order(people)
    bins: dict[int, list[str]] = defaultdict(list)
    for rank, pid in enumerate(order):
        bins[rank % 10].append(pid)
    jobs: list[tuple[str, str, tuple[str, ...], list[str]]] = [
        ("package", "package", PACKAGE, order)
    ]
    jobs += [("single", code, (code,), bins[i]) for i, code in enumerate(PACKAGE)]
    jobs += [("addon", code, (code,), bins[9]) for code in ADDONS]
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    combos = [("Bản X", "X"), ("Bản Y", "X"), ("Bản X", "Y"), ("Bản Y", "Y")]
    n_batch = 0
    for kind, name, codes, ids in jobs:
        size = PER_BATCH[kind]
        shuffled = list(ids)
        random.Random(f"{SEED}-{name}").shuffle(shuffled)  # noqa: S311 - fixed test split
        chunks = [shuffled[i : i + size] for i in range(0, len(shuffled), size)]
        for j, chunk in enumerate(chunks):
            c_label, first = combos[(n_batch + j) % 4]
            control, treat = mock_for(kind, codes, parts, c_label)
            texts = {c_label: control, ("Bản Y" if c_label == "Bản X" else "Bản X"): treat}
            first_label = f"Bản {first}"
            second_label = "Bản Y" if first == "X" else "Bản X"
            mock = (
                "# Hai bản app, mô tả bằng chữ\n\nChỉ có chữ, không phải thiết kế cuối, "
                "không có code. Mọi câu là ví dụ.\n\n"
                f"# {first_label}\n\n{texts[first_label]}\n\n# {second_label}\n\n"
                f"{texts[second_label]}\n"
            )
            bdir = out / f"{name}-{j + 1:02d}"
            bdir.mkdir(exist_ok=True)
            (bdir / "mock.md").write_text(mock, encoding="utf-8")
            people_out = []
            for pid in chunk:
                pk = packet(by_id[pid], sit[pid])
                pk["read_first"] = first
                people_out.append(pk)
            (bdir / "personas.json").write_text(
                json.dumps(people_out, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            manifest.append(
                {
                    "batch": bdir.name,
                    "kind": kind,
                    "codes": list(codes),
                    "control_label": c_label[-1],
                    "read_first": first,
                    "personas": chunk,
                }
            )
        n_batch += len(chunks)
    codex = order[::25][:40]
    codex_batches = []
    for j, (c_label, first) in enumerate((combos[0], combos[3])):
        chunk = codex[j * 20 : (j + 1) * 20]
        control, treat = mock_for("package", PACKAGE, parts, c_label)
        texts = {c_label: control, ("Bản Y" if c_label == "Bản X" else "Bản X"): treat}
        first_label, second_label = f"Bản {first}", ("Bản Y" if first == "X" else "Bản X")
        bdir = out / f"codex-{j + 1:02d}"
        bdir.mkdir(exist_ok=True)
        (bdir / "mock.md").write_text(
            "# Hai bản app, mô tả bằng chữ\n\nChỉ có chữ, không phải thiết kế cuối, "
            "không có code. Mọi câu là ví dụ.\n\n"
            f"# {first_label}\n\n{texts[first_label]}\n\n# {second_label}\n\n"
            f"{texts[second_label]}\n",
            encoding="utf-8",
        )
        (bdir / "personas.json").write_text(
            json.dumps(
                [{**packet(by_id[pid], sit[pid]), "read_first": first} for pid in chunk],
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        codex_batches.append(
            {
                "batch": bdir.name,
                "kind": "package",
                "codes": list(PACKAGE),
                "control_label": c_label[-1],
                "read_first": first,
                "personas": chunk,
            }
        )
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "batches": manifest,
                "codex_batches": codex_batches,
                "situation": sit,
                "codex_sample": codex,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"{len(manifest)} batches; codex sample {len(codex)}")


FLAGS = ("blame", "pressure", "privacy", "dependence", "must_check_la")
FLAG_VI = {
    "blame": "bị trách",
    "pressure": "bị ép",
    "privacy": "lo riêng tư",
    "dependence": "phụ thuộc",
    "must_check_la": "phải xem Lá mới dám quyết",
}
WEAK = {
    "final_year_job_hunt": "Năm cuối tìm việc",
    "money_tight": "Tiền eo hẹp",
    "family_pressure": "Áp lực gia đình",
    "part_time_job": "Vừa học vừa làm",
}


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}".replace(".", ",")


def _gain(rows: Sequence[Mapping[str, Any]], key: str) -> str:
    return _fmt(_mean([float(r["treat"][key]) - float(r["control"][key]) for r in rows]))


def _send_rate(rows: Sequence[Mapping[str, Any]], side: str) -> float:
    return sum(1 for r in rows if r[side]["send_or_post"] or r[side]["invite"]) / max(len(rows), 1)


def _pct(n: int, d: int) -> str:
    return "—" if not d else f"{100 * n / d:.1f}%".replace(".", ",")


def paired_rows(judged: Path, manifest: Mapping[str, Any], prefix: str) -> list[dict[str, Any]]:
    """One row per persona with 'control' and 'treat' blocks, labels resolved by the manifest."""

    rows: list[dict[str, Any]] = []
    for batch in manifest["batches"]:
        path = judged / f"{prefix}{batch['batch']}.json"
        if not path.exists():
            continue
        c = batch["control_label"]
        t = "Y" if c == "X" else "X"
        for r in json.loads(path.read_text(encoding="utf-8")):
            rows.append(
                {
                    "persona": r["persona"],
                    "batch": batch["batch"],
                    "kind": batch["kind"],
                    "codes": batch["codes"],
                    "read_first": batch["read_first"],
                    "control_first": batch["read_first"] == c,
                    "control": r[c],
                    "treat": r[t],
                    "concepts": r.get("concepts", {}),
                    "complaint": r.get("complaint", ""),
                    "still_missing": r.get("still_missing", ""),
                }
            )
    return rows


def condition_table(
    rows: Sequence[Mapping[str, Any]],
    people: Mapping[str, Mapping[str, Any]],
    sit: Mapping[str, str],
) -> tuple[list[str], list[bool]]:
    def m(side: str, key: str, sub: Sequence[Mapping[str, Any]] = rows) -> float | None:
        return _mean([float(r[side][key]) for r in sub])

    def diff(key: str, sub: Sequence[Mapping[str, Any]] = rows) -> float | None:
        return _mean([float(r["treat"][key]) - float(r["control"][key]) for r in sub])

    n = len(rows)
    out: list[str] = []
    ok: list[bool] = []

    def line(no: str, text: str, value: str, passed: bool) -> None:
        out.append(f"| {no} | {text} | {value} | {'đạt' if passed else 'trượt'} |")
        ok.append(passed)

    und = m("treat", "understood")
    line("1", "Hiểu mình của gói ≥ 3,7", _fmt(und), (und or 0) >= 3.7)
    la, pe = m("treat", "less_alone"), m("treat", "peaceful")
    line(
        "2",
        "Bớt một mình ≥ 3,5 và bình yên ≥ 3,5",
        f"{_fmt(la)} / {_fmt(pe)}",
        (la or 0) >= 3.5 and (pe or 0) >= 3.5,
    )
    weak_vals = {
        label: m("treat", "understood", [r for r in rows if people[r["persona"]]["segment"] == seg])
        for seg, label in WEAK.items()
    }
    line(
        "3",
        "4 nhóm sinh viên yếu, mỗi nhóm ≥ 3,5",
        "; ".join(f"{k} {_fmt(v)}" for k, v in weak_vals.items()),
        all((v or 0) >= 3.5 for v in weak_vals.values()),
    )
    sends = [r for r in rows if r["treat"]["send_or_post"] or r["treat"]["invite"]]
    specific = [r for r in sends if str(r["treat"].get("share_specific", "")).strip()]
    line(
        "4",
        "Gửi/đăng hoặc rủ ≥ 35% và nêu cụ thể ≥ 30%",
        f"{_pct(len(sends), n)} / {_pct(len(specific), n)}",
        n > 0 and len(sends) / n >= 0.35 and len(specific) / n >= 0.30,
    )
    flag_n = {f: sum(1 for r in rows if r["treat"].get(f)) for f in FLAGS}
    players = [r for r in rows if r["treat"].get("game_played")]
    hurt = sum(1 for r in players if r["treat"].get("game_hurt"))
    unsafe = sum(1 for r in rows if r["treat"].get("unsafe_content"))
    line(
        "5",
        "Mỗi cờ hại ≤ 3%; trò chơi chạm nỗi đau ≤ 1% người đã chơi; 0 nội dung nguy hiểm",
        ", ".join(f"{FLAG_VI[f]} {_pct(v, n)}" for f, v in flag_n.items())
        + f"; đau {hurt}/{len(players)}; nguy hiểm {unsafe}",
        all(v <= 0.03 * n for v in flag_n.values())
        and hurt <= 0.01 * max(len(players), 1)
        and unsafe == 0,
    )
    dpe = diff("peaceful")
    line("6", "Bình yên không tụt so với đối chứng (chênh ≥ -0,05)", _fmt(dpe), (dpe or 0) >= -0.05)
    dun = diff("understood")
    line("7", "Hiểu mình cao hơn đối chứng ≥ +0,2 (theo cặp)", _fmt(dun), (dun or 0) >= 0.2)
    groups = {
        "Dùng chung máy": [
            r
            for r in rows
            if (people[r["persona"]].get("attributes") or {}).get("shared_phone")
            or sit[r["persona"]] == "shared_phone"
        ],
        "Không có ai an toàn": [
            r
            for r in rows
            if (people[r["persona"]].get("attributes") or {}).get("no_safe_person")
            or sit[r["persona"]] == "no_safe_person"
        ],
    }
    parts, good = [], True
    for name, sub in groups.items():
        u, dp, dl = m("treat", "understood", sub), diff("peaceful", sub), diff("less_alone", sub)
        parts.append(
            f"{name} ({len(sub)}): hiểu mình {_fmt(u)}, chênh bình yên {_fmt(dp)}, "
            f"chênh bớt một mình {_fmt(dl)}"
        )
        good = good and (u or 0) >= 3.5 and (dp or 0) >= -0.05 and (dl or 0) >= -0.05
    line(
        "8",
        "Dùng chung máy và không có ai an toàn: hiểu mình ≥ 3,5; không tụt quá 0,05",
        "; ".join(parts),
        good,
    )
    expo = sum(1 for r in rows if r["treat"].get("privacy_exposure"))
    line("9", "Lộ dữ liệu riêng đã xác nhận: 0 ca", str(expo), expo == 0)
    return out, ok


def cmd_report(personas_path: Path, judged: Path, out: Path, summary: str | None) -> None:
    people = {p["id"]: p for p in load_personas(personas_path)}
    manifest = json.loads((judged / "manifest.json").read_text(encoding="utf-8"))
    sit = manifest["situation"]
    rows = paired_rows(judged, manifest, "out-")
    pkg = [r for r in rows if r["kind"] == "package"]
    single = [r for r in rows if r["kind"] == "single"]
    addon = [r for r in rows if r["kind"] == "addon"]
    codex = paired_rows(
        judged,
        {"batches": [{**b, "batch": b["batch"]} for b in manifest.get("codex_batches", [])]},
        "out-",
    )
    lines = [
        "# Gói concept sáng tạo, lan truyền: chấm trên 1000 người giả (14.11.2026)",
        "",
        "**Mô phỏng trên người giả, giám khảo là mô hình AI, chấm trên mô tả bằng chữ.** "
        "Không phải người dùng thật, không phải code thật. 1000 người giả không phải 1000 "
        "quan sát độc lập. Mock là mức trần.",
        "",
        "- Ngưỡng ghi trước: `thresholds-1000.md` mục 6 (bản 1 + bản 2).",
        "- Mỗi người giả đọc hai bản gọi là X và Y; nhãn và thứ tự đọc cân bằng giữa các lô. "
        "Giám khảo viết đường bấm trước rồi mới chấm.",
        f"- Gói: {len(pkg)} cặp. Từng concept: {len(single)} cặp. Phần thử có điều kiện (S2, S11): "
        f"{len(addon)} cặp. Codex: {len(codex)} cặp.",
        "",
    ]
    if summary:
        lines += [Path(summary).read_text(encoding="utf-8").rstrip(), ""]
    table, ok = condition_table(pkg, people, sit)
    lines += [
        "## Gói đề xuất so với đối chứng: 9 điều kiện",
        "",
        "| # | Điều kiện | Kết quả | |",
        "|---|---|---|---|",
        *table,
        "",
        f"**Gói {'đạt' if all(ok) else 'chưa đạt'}** ({sum(ok)}/{len(ok)} điều kiện).",
        "",
    ]

    def side_stats(side: str, sub: Sequence[Mapping[str, Any]]) -> list[str]:
        keys = (
            "understood",
            "less_alone",
            "peaceful",
            "want_return",
            "return_next_week",
            "share_score",
        )
        return [_fmt(_mean([float(r[side][k]) for r in sub])) for k in keys]

    lines += [
        "| | Hiểu mình | Bớt một mình | Bình yên | Muốn quay lại | Tuần sau quay lại "
        "| Muốn chia sẻ |",
        "|---|---|---|---|---|---|---|",
        "| Đối chứng | " + " | ".join(side_stats("control", pkg)) + " |",
        "| Gói | " + " | ".join(side_stats("treat", pkg)) + " |",
        "",
    ]
    for side, name in (("control", "Đối chứng"), ("treat", "Gói")):
        n = len(pkg)
        lines.append(
            f"- {name}: lưu ảnh {_pct(sum(1 for r in pkg if r[side]['save_image']), n)}, "
            f"gửi/đăng {_pct(sum(1 for r in pkg if r[side]['send_or_post']), n)}, "
            f"rủ một người {_pct(sum(1 for r in pkg if r[side]['invite']), n)}; "
            f"chơi trò chơi {sum(1 for r in pkg if r[side].get('game_played'))}; "
            "cờ "
            + ", ".join(f"{FLAG_VI[f]} {sum(1 for r in pkg if r[side].get(f))}" for f in FLAGS)
        )
    for first, label in ((True, "đọc đối chứng trước"), (False, "đọc gói trước")):
        sub = [r for r in pkg if r["control_first"] is first]
        lines.append(
            f"- Thứ tự đọc, {label} ({len(sub)}): chênh hiểu mình "
            f"{_fmt(_mean([r['treat']['understood'] - r['control']['understood'] for r in sub]))}"
        )
    dist = {
        side: [sum(1 for r in pkg if int(r[side]["understood"]) == k) for k in range(1, 6)]
        for side in ("control", "treat")
    }
    lines += [
        f"- Phân bố hiểu mình 1/2/3/4/5: đối chứng {'/'.join(map(str, dist['control']))}; "
        f"gói {'/'.join(map(str, dist['treat']))}.",
        "",
        "## Từng concept",
        "",
        "| Concept | Dùng trong gói | Hiểu mình của người dùng (gói) | Chia sẻ từ concept (gói) "
        "| Riêng lẻ: chênh hiểu mình | Riêng lẻ: chênh gửi/rủ | Riêng lẻ: cờ hại | Giữ? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for code in PACKAGE:
        used = [r for r in pkg if (r["concepts"].get(code) or {}).get("used")]
        u_und = _mean(
            [
                float(r["concepts"][code]["understood"])
                for r in used
                if r["concepts"][code].get("understood") is not None
            ]
        )
        shared = sum(1 for r in used if r["concepts"][code].get("shared"))
        srows = [r for r in single if code in r["codes"]]
        d_und = _mean([r["treat"]["understood"] - r["control"]["understood"] for r in srows])

        d_share = (
            round(100 * (_send_rate(srows, "treat") - _send_rate(srows, "control")), 1)
            if srows
            else None
        )
        harm = sum(1 for r in srows if any(r["treat"].get(f) for f in FLAGS))
        keep = (
            (u_und or 0) >= 3.5
            and harm <= 0.03 * max(len(srows), 1)
            and ((d_und or 0) >= 0.2 or (d_share or 0) >= 5)
        )
        share_txt = "—" if d_share is None else f"{d_share:+.1f} điểm %".replace(".", ",")
        lines.append(
            f"| {code} | {len(used)}/{len(pkg)} | {_fmt(u_und)} | {shared} | {_fmt(d_und)} "
            f"({len(srows)} cặp) | {share_txt} "
            f"| {harm} | {'giữ' if keep else 'chưa'} |"
        )
    lines += ["", "## Phần thử có điều kiện (không tính vào điểm gói)", ""]
    for code in ADDONS:
        arows = [r for r in addon if code in r["codes"]]
        lines.append(
            f"- {code} ({len(arows)} cặp, so với gói): chênh hiểu mình "
            f"{_gain(arows, 'understood')}, chênh bình yên {_gain(arows, 'peaceful')}, "
            f"cờ lo riêng tư {sum(1 for r in arows if r['treat'].get('privacy'))}, "
            f"lộ dữ liệu {sum(1 for r in arows if r['treat'].get('privacy_exposure'))}."
        )
    if codex:
        ctable, _ = condition_table(codex, people, sit)
        by = {r["persona"]: r for r in pkg}
        both = [(c, by[c["persona"]]) for c in codex if c["persona"] in by]
        lines += [
            "",
            f"## Codex chấm đối chiếu ({len(codex)} người giả, chọn đều theo nhóm)",
            "",
            "| # | Điều kiện | Codex | |",
            "|---|---|---|---|",
            *ctable,
            "",
            "Trên cùng người giả: chênh hiểu mình (gói trừ đối chứng) Claude "
            f"{_gain([x for _, x in both], 'understood')}, "
            f"Codex {_gain([c for c, _ in both], 'understood')}. "
            "Điều kiện Claude đạt mà Codex trượt ghi là **chưa kết luận**.",
        ]
    lines += [
        "",
        "## Giới hạn",
        "",
        "- Người giả và giám khảo là mô hình AI, đọc chữ. Kết quả là mức trần.",
        "- Mỗi người giả chấm một ngày với một tình huống; nhóm nhỏ dưới 20 người ghi mẫu nhỏ.",
        "- Giám khảo thấy hai bản cùng lúc; gói có nhiều phần hơn nên có thể được cộng điểm vì "
        "mới. Thiết kế giảm bằng nhãn trung tính, thứ tự cân bằng, và chấm từng concept riêng.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("packets")
    pk.add_argument("--personas", default=str(QA / "personas-1000.json"))
    pk.add_argument("--concepts", required=True)
    pk.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--personas", default=str(QA / "personas-1000.json"))
    rp.add_argument("--judged", required=True)
    rp.add_argument("--summary", default=None)
    rp.add_argument("--out", default=str(QA / "report-concepts.md"))
    args = parser.parse_args()
    if args.cmd == "packets":
        cmd_packets(Path(args.personas), Path(args.concepts), Path(args.out))
    else:
        cmd_report(Path(args.personas), Path(args.judged), Path(args.out), args.summary)


if __name__ == "__main__":
    main()
