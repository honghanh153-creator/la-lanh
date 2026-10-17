"""G0: composer, allowlist, master schedule, manifest and fallback approval.

Spec: docs/foundation/la-lanh-content-grammar-spec.md §3-§7; task
docs/plans/2026-10-17-g0-grammar-composer-task.md.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest

from app.domains.grammar.build import GrammarBuildError, build_surface, catalog_sha256
from app.domains.grammar.composer import normalize, parse_code, resolve_bucket
from app.domains.grammar.gate import sentence_failures
from app.domains.grammar.models import Frame
from app.domains.grammar.runtime import GrammarStatus, load_grammar, schedule_position
from app.domains.grammar.schedule import adjacent, build_schedule

SAMPLE = Path(__file__).resolve().parents[2] / "app" / "domains" / "readings" / "grammar"
DIRECT = "daily.missing-context.advice"
ROAST = "daily.missing-context.advice.roast"


def _v(*ids: str) -> list[dict[str, str]]:
    return [{"id": i, "text": text} for i, text in (pair.split(":", 1) for pair in ids)]


def _frame(frame_id: str, **overrides: Any) -> dict[str, Any]:
    frame: dict[str, Any] = {
        "frame_id": frame_id,
        "surface": "daily",
        "part": "advice",
        "voice": "direct",
        "template": "{a} {b} {c}.",
        "slots": {
            "a": {
                "kind": "must_change",
                "values": _v("a0:Khi mở tin nhắn,", "a1:Trước khi trả lời,"),
            },
            "b": {"kind": "must_change", "values": _v("b0:hỏi lại", "b1:nhắn hỏi")},
            "c": {"kind": "must_change", "values": _v("c0:chỗ chưa rõ", "c1:chữ chưa hiểu")},
        },
        "meaning_key": "missing-context",
        "vocab_class": "action",
    }
    frame.update(overrides)
    return frame


def _roast_of(direct: dict[str, Any]) -> dict[str, Any]:
    roast: dict[str, Any] = json.loads(json.dumps(direct))
    roast.update(
        frame_id=f"{direct['frame_id']}.roast",
        voice="roast",
        roast_of=direct["frame_id"],
        template=direct["template"].replace(".", " nha."),
    )
    return roast


def _catalog(tmp_path: Path, frames: list[dict[str, Any]], **overrides: Any) -> Path:
    catalog: dict[str, Any] = {
        "surface": "daily",
        "catalog_version": "test-grammar-v1",
        "schedule_length": 2,
        "min_schedule_length": 2,
        "variants": 1,
        "min_variants": 1,
        "articles": [
            {
                "article_id": "test",
                "frames": [f["frame_id"] for f in frames if f.get("voice", "direct") == "direct"],
            }
        ],
    }
    catalog.update(overrides)
    (tmp_path / "frames").mkdir(parents=True, exist_ok=True)
    (tmp_path / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False))
    for frame in frames:
        (tmp_path / "frames" / f"{frame['frame_id']}.json").write_text(
            json.dumps(frame, ensure_ascii=False)
        )
    return tmp_path


def _refused(directory: Path) -> list[str]:
    with pytest.raises(GrammarBuildError) as error:
        build_surface(directory)
    return error.value.reasons


# ---------------------------------------------------------------- sample frame (committed)


@pytest.fixture(scope="module")
def sample() -> Any:
    return build_surface(SAMPLE)


def test_committed_build_is_current_and_not_served(sample: Any) -> None:
    for name, text in sample.outputs.items():
        assert (SAMPLE / "build" / name).read_text() == text, f"{name} drifted"
    manifest = json.loads(sample.outputs["manifest.json"])
    assert manifest["serving"] is False
    assert manifest["L"] == 90 and manifest["M"] == 4
    assert manifest["catalog_sha256"] == catalog_sha256(SAMPLE)
    assert {"spec_version", "catalog_version", "composer_version", "gate_version"} <= set(manifest)
    assert len(manifest["frames"][DIRECT]["variants"]) == 4


def test_every_variant_is_a_valid_closed_cycle_with_full_coverage(sample: Any) -> None:
    frame: Frame = sample.frames[DIRECT]
    schedules = json.loads(sample.outputs["schedules.json"])[DIRECT]
    values = {s: {v.id for v in frame.slots[s].all_values()} for s in frame.must_change}
    assert len({tuple(order) for order in schedules}) == 4
    for order in schedules:
        masters = [tuple(parse_code(code)[s] for s in frame.must_change) for code in order]
        assert len(order) == 90 and len(set(order)) == 90  # (b): unique within L
        # G-AC3: p = L-1 -> 0 is a neighbour pair like any other.
        for left, right in pairwise([*masters, masters[0]]):
            assert adjacent(left, right)
        for index, slot in enumerate(frame.must_change):  # (c)
            assert {m[index] for m in masters} == values[slot]


def test_bucket_changes_keep_a_and_b_for_both_voices() -> None:
    """G-AC2 + G-AC8: any bucket on any day, every p, both voices."""

    runtime = load_grammar(SAMPLE)
    assert runtime.status is GrammarStatus.OK
    frame = Frame.model_validate_json((SAMPLE / "frames" / f"{DIRECT}.json").read_text())
    buckets = ["lens=_default", "lens=work", "lens=relationships"]
    length = runtime.length
    for variant in range(4):
        for shift in range(len(buckets)):
            served = []
            for day in range(2 * length):
                bucket = buckets[(day * (shift + 1) + day // 7) % len(buckets)]
                direct = runtime.select(DIRECT, variant=variant, position=day, bucket=bucket)
                served.append((direct, runtime.roast(direct, ROAST)))
            for (d0, r0), (d1, r1) in pairwise(served):
                c0, c1 = parse_code(d0.code), parse_code(d1.code)
                assert all(c0[s] != c1[s] for s in frame.must_change)  # (a)
                assert r0.code == d0.code and r1.code == d1.code  # Roast is a lookup
            for start in range(len(served) - length + 1):
                window = served[start : start + length]
                for voice in (0, 1):
                    texts = [normalize(pair[voice].text).casefold() for pair in window]
                    assert len(set(texts)) == length  # (b) across bucket changes


def test_runtime_position_and_bucket_resolution_are_deterministic() -> None:
    assert schedule_position("00000005" + "0000000a" + "0" * 16, 100, 90, 4) == (1, 20)
    frame = Frame.model_validate_json((SAMPLE / "frames" / f"{DIRECT}.json").read_text())
    assert resolve_bucket(frame, {"lens": "work"}) == "lens=work"
    assert resolve_bucket(frame, {"lens": "energy"}) == "lens=_default"
    assert resolve_bucket(frame, {}) == "lens=_default"


def test_grammar_is_not_imported_by_the_serving_app() -> None:
    """G0 changes no visible content: a fresh API process never loads the grammar package."""

    probe = (
        "import sys, app.main; print(any(m.startswith('app.domains.grammar') for m in sys.modules))"
    )
    result = subprocess.run(  # noqa: S603 - fixed interpreter and code, no user input
        [sys.executable, "-c", probe],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "False"


# ---------------------------------------------------------------- refusals (G-AC4, G-AC9)


def test_codex_counterexample_allowlist_is_refused(tmp_path: Path) -> None:
    """G-AC9: {(0,0,0), (0,1,1), (1,0,1)} has no pair differing in every slot."""

    keep = {("a0", "b0", "c0"), ("a0", "b1", "c1"), ("a1", "b0", "c1")}
    constraints = [
        {"if": {"a": [a], "b": [b]}, "forbid": {"c": [c]}}
        for a in ("a0", "a1")
        for b in ("b0", "b1")
        for c in ("c0", "c1")
        if (a, b, c) not in keep
    ]
    direct = _frame("t.counter", constraints=constraints)
    reasons = _refused(_catalog(tmp_path, [direct, _roast_of(direct)]))
    assert any("infeasible" in reason for reason in reasons)


def test_feasible_small_frame_builds(tmp_path: Path) -> None:
    direct = _frame("t.ok")
    build = build_surface(_catalog(tmp_path, [direct, _roast_of(direct)]))
    assert json.loads(build.outputs["schedules.json"])["t.ok"]


def test_schedule_length_below_owner_minimum_is_refused(tmp_path: Path) -> None:
    direct = _frame("t.short")
    reasons = _refused(
        _catalog(tmp_path, [direct, _roast_of(direct)], schedule_length=60, min_schedule_length=90)
    )
    assert any("L=60" in reason for reason in reasons)


def test_schedule_longer_than_the_eligible_masters_is_refused(tmp_path: Path) -> None:
    direct = _frame("t.long")
    reasons = _refused(_catalog(tmp_path, [direct, _roast_of(direct)], schedule_length=9))
    assert any("infeasible" in reason for reason in reasons)


def test_missing_roast_frame_is_refused(tmp_path: Path) -> None:
    reasons = _refused(_catalog(tmp_path, [_frame("t.alone")]))
    assert any("Roast" in reason for reason in reasons)


def test_roast_allowlist_gap_is_refused(tmp_path: Path) -> None:
    direct = _frame("t.gap")
    roast = _roast_of(direct)
    roast["slots"]["c"]["values"][0]["text"] = "chỗ chưa rõ, làm ngay"  # gated: urgency
    reasons = _refused(_catalog(tmp_path, [direct, roast]))
    assert any("lack a Roast mapping" in reason for reason in reasons)


def test_roast_must_mirror_slots_and_value_ids(tmp_path: Path) -> None:
    direct = _frame("t.mirror")
    roast = _roast_of(direct)
    roast["slots"]["c"]["values"][1]["id"] = "c9"
    reasons = _refused(_catalog(tmp_path, [direct, roast]))
    assert any("mirror" in reason for reason in reasons)


def test_vocabulary_split_violation_is_refused(tmp_path: Path) -> None:
    action = _frame("t.action")
    headline = _frame(
        "t.headline",
        part="headline",
        vocab_class="headline",
        template="{a} {b}.",
        slots={
            "a": {"kind": "must_change", "values": _v("a0:Bạn định", "a1:Bạn muốn")},
            "b": {"kind": "must_change", "values": _v("b0:hỏi lại một chữ", "b1:đọc thêm lần nữa")},
        },
    )
    reasons = _refused(
        _catalog(tmp_path, [action, _roast_of(action), headline, _roast_of(headline)])
    )
    assert any("action vocabulary" in reason for reason in reasons)


def test_two_negative_role_frames_in_one_reading_are_refused(tmp_path: Path) -> None:
    first = _frame("t.neg1", negative_role=True)
    second = _frame("t.neg2", negative_role=True, part="scene", vocab_class="scene")
    second["slots"]["b"]["values"] = _v("b0:thấy rối", "b1:thấy chậm")
    reasons = _refused(_catalog(tmp_path, [first, _roast_of(first), second, _roast_of(second)]))
    assert any("negative_role" in reason for reason in reasons)


def test_negative_value_outside_the_negative_role_frame_is_refused(tmp_path: Path) -> None:
    direct = _frame("t.negval")
    direct["slots"]["c"]["values"][0]["negative"] = True
    reasons = _refused(_catalog(tmp_path, [direct, _roast_of(direct)]))
    assert any("negative value" in reason for reason in reasons)


def test_combination_and_bucket_limits_are_enforced(tmp_path: Path) -> None:
    direct = _frame("t.limit")
    reasons = _refused(
        _catalog(
            tmp_path,
            [direct, _roast_of(direct)],
            limits={"max_combinations_per_bucket": 7},
        )
    )
    assert any("combinations > 7" in reason for reason in reasons)


def test_template_accepts_only_plain_placeholders(tmp_path: Path) -> None:
    direct = _frame("t.format", template="{a} {b} {c.__class__}.")
    reasons = _refused(_catalog(tmp_path, [direct]))
    assert any("placeholders" in reason for reason in reasons)


def test_multi_value_repeatable_slot_is_refused_in_g0(tmp_path: Path) -> None:
    direct = _frame("t.repeat")
    direct["template"] = "{a} {b} {c} {d}."
    direct["slots"]["d"] = {"kind": "repeatable", "values": _v("d0:nhé", "d1:nha")}
    reasons = _refused(_catalog(tmp_path, [direct, _roast_of(direct)]))
    assert any("repeatable" in reason for reason in reasons)


def test_schedule_search_is_bounded() -> None:
    masters = [(a, b) for a in "xyz" for b in "pqr"]
    result = build_schedule(
        masters,
        length=9,
        required_values=[set("xyz"), set("pqr")],
        frame_id="t",
        variant=0,
        max_steps=5,
    )
    assert result.order is None and result.steps <= 6


# ---------------------------------------------------------------- gates


def test_sentence_gate_rejects_unsafe_vague_or_off_meaning_copy() -> None:
    frame = Frame.model_validate_json((SAMPLE / "frames" / f"{DIRECT}.json").read_text())
    scene = frame.model_copy(update={"part": "scene"})

    assert sentence_failures(frame, "Trước khi trả lời, hỏi lại chỗ bạn còn chưa rõ.") == []
    assert "anti_urgency" in sentence_failures(frame, "Hỏi lại chỗ chưa rõ, làm ngay.")
    assert "banned_core_fragment" in sentence_failures(frame, "Hỏi lại pattern này cho chưa rõ.")
    assert "meaning_anchor_missing" in sentence_failures(frame, "Hỏi lại về bữa trưa.")
    assert "action_not_observable" in sentence_failures(frame, "Chữ chưa rõ.")
    assert "scene_contains_advice" in sentence_failures(scene, "Hãy hỏi lại tin nhắn.")
    assert "privacy_personal_data" in sentence_failures(frame, "Hỏi lại a@b.com chỗ chưa rõ.")


# ---------------------------------------------------------------- manifest (G-AC5)


def test_missing_or_corrupt_manifest_never_composes(tmp_path: Path) -> None:
    copy = tmp_path / "grammar"
    shutil.copytree(SAMPLE, copy)
    assert load_grammar(copy).status is GrammarStatus.OK

    allowlist = copy / "build" / "allowlist.json"
    allowlist.write_text(allowlist.read_text().replace("hỏi lại", "hỏi luôn", 1))
    corrupt = load_grammar(copy)
    assert corrupt.status is GrammarStatus.MANIFEST_CORRUPT
    with pytest.raises(LookupError):
        corrupt.select(DIRECT, variant=0, position=0, bucket="lens=_default")

    shutil.copy(SAMPLE / "build" / "allowlist.json", allowlist)
    frame_file = copy / "frames" / f"{DIRECT}.json"
    frame_file.write_text(frame_file.read_text().replace("trước đã", "trước nha"))
    assert (
        load_grammar(copy).status is GrammarStatus.MANIFEST_CORRUPT
    )  # catalog changed, no rebuild

    (copy / "build" / "manifest.json").unlink()
    assert load_grammar(copy).status is GrammarStatus.MANIFEST_MISSING


# ---------------------------------------------------------------- fallback approval (§4b)


def test_fallback_approval_matches_the_live_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.domains.readings import companion
    from scripts import fallback_approval

    approved = json.loads(fallback_approval.APPROVAL.read_text())
    assert approved["approved"] == fallback_approval.current()
    assert approved["approved_release"] == "836222282dfc"

    edited = dict(companion.COMPANION_ISSUE_LINES)
    edited.pop(next(iter(edited)))
    monkeypatch.setattr(companion, "COMPANION_ISSUE_LINES", edited)
    assert fallback_approval.current() != approved["approved"]
