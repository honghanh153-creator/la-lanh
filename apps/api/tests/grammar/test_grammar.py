"""G0: composer, allowlist, master schedule, manifest and fallback approval.

Spec: docs/foundation/la-lanh-content-grammar-spec.md §3-§7; task
docs/plans/2026-10-17-g0-grammar-composer-task.md.
"""

from __future__ import annotations

import itertools
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
    assert approved["approved_release"] == "89ebdb0cf6b9"  # production release 2026-10-26 (#75)

    edited = dict(companion.COMPANION_ISSUE_LINES)
    edited.pop(next(iter(edited)))
    monkeypatch.setattr(companion, "COMPANION_ISSUE_LINES", edited)
    assert fallback_approval.current() != approved["approved"]


def test_fallback_approval_pins_the_framed_tarot_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Owner approval 2026-10-18 (docs/reviews/2026-10-18-b2-tarot-owner-approval.md): the B2
    copy modules and versions are pinned, so an unapproved edit fails grammar:check."""

    from app.domains.tarot import roles, stance
    from scripts import fallback_approval

    tarot = fallback_approval.current()["tarot"]
    assert tarot["framed_renderer_version"] == "tarot-renderer-v7"
    assert tarot["framed_knowledge_version"] == "tarot-knowledge-v5"
    assert tarot["gate_version"] == "tarot-gates-v5"
    for module in ("question_frame", "roles", "stance", "variants"):
        assert any(key.startswith(f"app.domains.tarot.{module}.") for key in tarot["tables"])
    approved = json.loads(fallback_approval.APPROVAL.read_text())["approved"]
    for table, edit in (
        ("ROAST_HEADLINES", {**stance.ROAST_HEADLINES, "open": ("a", "b", "c")}),
        ("LEADS", {**roles.LEADS, next(iter(roles.LEADS)): ("a", "b", "c", "d", "e")}),
    ):
        owner = stance if table == "ROAST_HEADLINES" else roles
        with monkeypatch.context() as patched:
            patched.setattr(owner, table, edit)
            assert fallback_approval.current() != approved, table


_LEGACY_TAROT_TABLES = (
    ("meaning_brief", "_GOALS"),
    ("meaning_brief", "_DEFAULT_GOAL"),
    ("meaning_brief", "_GOAL_ACTIONS"),
    ("meaning_brief", "_GOAL_FEELING_ACTION"),
    ("meaning_brief", "_GOAL_NEED_ACTIONS"),
    ("meaning_brief", "_GOAL_AGENCY_ACTIONS"),
    ("meaning_brief", "_GOAL_BOUNDARY_ACTIONS"),
    ("meaning_brief", "_STAGE_TWO_POSITIONS"),
    ("meaning_brief", "_LINKS"),
    ("meaning_brief", "BRIEF_LIMITS"),
    ("voice", "ROAST_HEADLINES"),
    ("voice", "GENTLE_HEADLINES"),
    ("voice", "ROAST_MEANING_TAILS"),
    ("voice", "GENTLE_MEANING_TAILS"),
    ("voice", "ROAST_ACTION_FRAMES"),
    ("voice", "GENTLE_ACTION_FRAMES"),
    ("voice", "_MEANING_GROUPS"),
    ("examples", "CARD_EXAMPLES"),
    ("examples", "CONTEXT_EXAMPLES"),
)


def _mutated(value: Any) -> Any:
    """A minimal edit of a pinned value: one changed string, wherever it sits."""

    import dataclasses

    if isinstance(value, str):
        return value + " (sửa)"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.replace(value, meaning=value.meaning + " (sửa)")  # type: ignore[attr-defined]
    if isinstance(value, dict):
        key = next(iter(value))
        return {**value, key: _mutated(value[key])}
    if isinstance(value, frozenset):
        return value | {"sửa"}
    if isinstance(value, tuple):
        return (_mutated(value[0]), *value[1:])
    raise AssertionError(f"no mutation for {type(value)}")


@pytest.mark.parametrize(("module_name", "table"), _LEGACY_TAROT_TABLES)
def test_fallback_approval_pins_reused_legacy_tarot_copy(
    module_name: str, table: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex #28 follow-up: older copy the Tarot renderers reuse is fingerprinted; any edit to
    it breaks the approval (docs/reviews/2026-10-18-tarot-legacy-copy-pin.md)."""

    import importlib

    from scripts import fallback_approval

    owner = importlib.import_module(f"app.domains.tarot.{module_name}")
    approved = json.loads(fallback_approval.APPROVAL.read_text())["approved"]
    assert fallback_approval.current() == approved
    monkeypatch.setattr(owner, table, _mutated(getattr(owner, table)))
    assert fallback_approval.current() != approved


def test_a_goal_action_edit_changes_the_reading_and_the_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex's example: editing _GOAL_ACTIONS changed a framed reading's small action while the
    approval stayed identical. Now both change."""

    from app.domains.tarot import meaning_brief
    from app.domains.tarot.models import TarotSpreadMap
    from scripts import fallback_approval
    from tests.tarot.test_provenance import _reading

    question = "Mình nên nói gì để chia việc và bàn giao rõ hơn?"
    before = _reading(question, TarotSpreadMap.THREE_UNBLOCK).positions[-1].small_action
    approved = json.loads(fallback_approval.APPROVAL.read_text())["approved"]
    actions = dict(meaning_brief._GOAL_ACTIONS)
    first, second, third = actions["task_handoff"]
    actions["task_handoff"] = (first, second, f"{third} (sửa)")
    monkeypatch.setattr(meaning_brief, "_GOAL_ACTIONS", actions)
    after = _reading(question, TarotSpreadMap.THREE_UNBLOCK).positions[-1].small_action
    assert before != after
    assert fallback_approval.current() != approved


def test_goal_action_output_is_unchanged_by_the_table_move() -> None:
    """The literals moved out of goal_action into pinned tables; every output is identical
    (snapshot taken before the move, equal to release 836222282dfc)."""

    from hashlib import sha256

    from app.domains.tarot.engine import _POSITIONS
    from app.domains.tarot.meaning_brief import GOAL_KEYS, goal_action, goal_by_key

    keys = sorted({key for positions in _POSITIONS.values() for key, _ in positions} | {"unknown"})
    outputs = {
        f"{goal}|{key}": goal_action(goal_by_key(goal), key)
        for goal in sorted(GOAL_KEYS)
        for key in keys
    }
    text = json.dumps(outputs, ensure_ascii=False, sort_keys=True)
    assert len(outputs) == 189
    assert (
        sha256(text.encode()).hexdigest()
        == "86698546666ec66f598b21ccfe2c1795d5a65d325b7413ee029092b06e3b31ce"
    )


# ---------------------------------------------------------------- Codex P2 regressions (PR #22)


def _diagonal(
    frame_id: str, a_texts: list[str], b_texts: list[str], template: str = "{a} {b}"
) -> dict[str, Any]:
    """Masters (a_i, b_i) only: id constraints require matching indices."""

    n = len(a_texts)
    return _frame(
        frame_id,
        meaning_key="test-issue",  # not a Daily issue: no anchor rule, only the generic gates
        template=template,
        slots={
            "a": {
                "kind": "must_change",
                "values": [{"id": f"a{i}", "text": a_texts[i]} for i in range(n)],
            },
            "b": {
                "kind": "must_change",
                "values": [{"id": f"b{i}", "text": b_texts[i]} for i in range(n)],
            },
        },
        constraints=[{"if": {"a": [f"a{i}"]}, "require": {"b": [f"b{i}"]}} for i in range(n)],
    )


_MINIMA = {"schedule_length": 90, "min_schedule_length": 90, "variants": 4, "min_variants": 4}


def test_p2_1_must_change_ids_with_the_same_text_are_refused(tmp_path: Path) -> None:
    same = ["Trước khi trả lời,"] * 90
    actions = [f"hỏi lại câu số {i} cho rõ." for i in range(90)]
    direct = _diagonal("t.sametext", same, actions)
    reasons = _refused(_catalog(tmp_path / "direct", [direct, _roast_of(direct)], **_MINIMA))
    assert any("t.sametext.a: must-change values repeat" in r for r in reasons)

    distinct = [f"Lúc {i} giờ," for i in range(90)]
    clean = _diagonal("t.roastsame", distinct, actions)
    roast = _roast_of(_diagonal("t.roastsame", same, actions))
    reasons = _refused(_catalog(tmp_path / "roast", [clean, roast], **_MINIMA))
    assert any("t.roastsame.roast.a: must-change values repeat" in r for r in reasons)


def test_p2_2_sentence_identity_follows_the_measurement_normalisation(tmp_path: Path) -> None:
    from app.domains.grammar.composer import build_allowlist, dedupe_key
    from scripts.variety_baseline import normalize as measured

    for text in ("Hỏi lại chỗ chưa rõ.", "hỏi  lại chỗ chưa rõ!", "Hỏi lại chỗ chưa rõ …", "A, b;"):
        assert dedupe_key(text) == measured(text)

    # 45 sentence pairs that differ only by "." / "!", with every slot text distinct.
    a_texts, b_texts = [], []
    for k in range(45):
        a_texts += [f"Lúc {k} giờ, hỏi lại", f"Lúc {k} giờ,"]
        b_texts += [f"chỗ chưa rõ {k}.", f"hỏi lại chỗ chưa rõ {k}!"]
    direct = _diagonal("t.punct", a_texts, b_texts)
    frame = Frame.model_validate(direct)
    allowlist = build_allowlist(frame, 200_000, {})
    texts = list(allowlist.entries["_all"].values())
    assert len(texts) == 45 and len({measured(t) for t in texts}) == 45
    assert allowlist.duplicate_dropped == 45
    reasons = _refused(_catalog(tmp_path / "direct", [direct, _roast_of(direct)], **_MINIMA))
    assert any("infeasible" in r for r in reasons)

    # The same collision only in the Roast voice is a missing Roast mapping.
    plain = _diagonal("t.rpunct", [f"Lúc {k} giờ, ghi" for k in range(90)], b_texts)
    roast = _roast_of(_diagonal("t.rpunct", a_texts, b_texts))
    roast["template"] = "{a} {b}"
    reasons = _refused(_catalog(tmp_path / "roast", [plain, roast], **_MINIMA))
    assert any("lack a Roast mapping" in r for r in reasons)


def test_p2_2_a_sentence_never_moves_to_another_master_across_buckets() -> None:
    from app.domains.grammar.composer import build_allowlist

    frame = Frame.model_validate(
        _frame(
            "t.bucketpunct",
            meaning_key="test-issue",
            template="{a} {b}{tail}",
            slots={
                "a": {"kind": "must_change", "values": _v("a0:Lúc đó, hỏi lại", "a1:Lúc đó,")},
                "b": {
                    "kind": "must_change",
                    "values": _v("b0:chỗ chưa rõ", "b1:hỏi lại chỗ chưa rõ"),
                },
                "tail": {
                    "kind": "bucket",
                    "by": "lens",
                    "buckets": {"_default": _v("t0:."), "work": _v("t1:!")},
                },
            },
            # Each bucket keeps one of the two masters, so they only meet across buckets.
            constraints=[
                {"if": {"a": ["a1"]}, "forbid": {"tail": ["t0"]}},
                {"if": {"a": ["a0"]}, "forbid": {"tail": ["t1"]}},
            ],
        )
    )
    allowlist = build_allowlist(frame, 200_000, {})
    by_identity: dict[str, set[str]] = {}
    for codes in allowlist.entries.values():
        for code, text in codes.items():
            master = code.split("|tail=")[0]
            by_identity.setdefault(text.rstrip(".!").casefold(), set()).add(master)
    # "Lúc đó, hỏi lại chỗ chưa rõ." (a0,b0) in one bucket would collide with
    # "Lúc đó, hỏi lại chỗ chưa rõ!" (a1,b1) in the other: one master keeps the sentence.
    assert all(len(masters) == 1 for masters in by_identity.values())
    assert allowlist.duplicate_dropped >= 1


def test_p2_3_schedule_search_does_no_unbudgeted_quadratic_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.domains.grammar import schedule

    calls = 0
    real = schedule.adjacent

    def counting(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
        nonlocal calls
        calls += 1
        return real(left, right)

    monkeypatch.setattr(schedule, "adjacent", counting)
    small = [(f"x{a}", f"y{b}", f"z{c}") for a in range(10) for b in range(10) for c in range(5)]
    required = [
        {f"x{i}" for i in range(10)},
        {f"y{i}" for i in range(10)},
        {f"z{i}" for i in range(5)},
    ]
    result = schedule.build_schedule(
        small, length=90, required_values=required, frame_id="t", variant=0, max_steps=1
    )
    assert result.order is None and calls <= 2

    calls = 0
    axes = [[f"{axis}{i}" for i in range(11)] for axis in "vwxyz"]
    large = list(itertools.product(*axes))
    assert len(large) == 161_051  # within the 200 000 combination cap
    result = schedule.build_schedule(
        large,
        length=90,
        required_values=[set(axis) for axis in axes],
        frame_id="t",
        variant=0,
        max_steps=10_000,
    )
    assert calls <= 10_002
    assert result.order is not None  # dense domains still build within the budget


def test_p2_4_published_variant_count_matches_the_manifest(tmp_path: Path) -> None:
    direct = _frame("t.variants")
    reasons = _refused(_catalog(tmp_path, [direct, _roast_of(direct)], variants=5, min_variants=4))
    assert any("need M=5" in r for r in reasons)

    runtime = load_grammar(SAMPLE)
    assert runtime.manifest is not None
    for variant in range(runtime.manifest["M"]):
        assert runtime.select(DIRECT, variant=variant, position=0, bucket="lens=_default").text
    with pytest.raises(LookupError):
        runtime.select(DIRECT, variant=runtime.manifest["M"], position=0, bucket="lens=_default")


def _rewrite(build: Path, name: str, data: Any) -> None:
    from app.domains.grammar.build import canonical_json, digest

    text = canonical_json(data)
    (build / name).write_text(text)
    if name != "manifest.json":
        manifest = json.loads((build / "manifest.json").read_text())
        manifest["files"][name] = digest(text)
        (build / "manifest.json").write_text(canonical_json(manifest))


@pytest.mark.parametrize(
    "corruption",
    ["zero_dimensions", "string_length", "dropped_variant", "short_order", "missing_frame"],
)
def test_p2_5_inconsistent_manifest_dimensions_are_corrupt(tmp_path: Path, corruption: str) -> None:
    copy = tmp_path / "grammar"
    shutil.copytree(SAMPLE, copy)
    build = copy / "build"
    manifest = json.loads((build / "manifest.json").read_text())
    schedules = json.loads((build / "schedules.json").read_text())
    if corruption == "zero_dimensions":
        manifest.update(L=0, M=0)
        _rewrite(build, "manifest.json", manifest)
    elif corruption == "string_length":
        manifest["L"] = "90"
        _rewrite(build, "manifest.json", manifest)
    elif corruption == "dropped_variant":
        schedules[DIRECT] = schedules[DIRECT][:3]
        _rewrite(build, "schedules.json", schedules)
    elif corruption == "short_order":
        schedules[DIRECT][0] = schedules[DIRECT][0][:89]
        _rewrite(build, "schedules.json", schedules)
    else:
        manifest["frames"].pop(ROAST)
        _rewrite(build, "manifest.json", manifest)

    runtime = load_grammar(copy)
    assert runtime.status is GrammarStatus.MANIFEST_CORRUPT
    with pytest.raises(LookupError):
        runtime.select(DIRECT, variant=0, position=0, bucket="lens=_default")


def _internal_space_frame(frame_id: str, a1_text: str) -> dict[str, Any]:
    """Codex's P2-1 follow-up: two triggers, 18 verbs, 6 objects, 108 masters at L=90/M=4.

    ``a0`` may use b0-b8 and ``a1`` b9-b17, so whole-sentence de-duplication cannot hide
    two trigger values that render to the same text.
    """

    constraints = [
        {"if": {"a": ["a0"]}, "require": {"b": [f"b{i}" for i in range(9)]}},
        {"if": {"a": ["a1"]}, "require": {"b": [f"b{i}" for i in range(9, 18)]}},
    ]
    return _frame(
        frame_id,
        meaning_key="test-issue",
        slots={
            "a": {
                "kind": "must_change",
                "values": [
                    {"id": "a0", "text": "Đọc lại tin nhắn, trước khi trả lời,"},
                    {"id": "a1", "text": a1_text},
                ],
            },
            "b": {
                "kind": "must_change",
                "values": [{"id": f"b{i}", "text": f"hỏi lại lần {i}"} for i in range(18)],
            },
            "c": {
                "kind": "must_change",
                "values": [{"id": f"c{j}", "text": f"về chỗ thứ {j}"} for j in range(6)],
            },
        },
        constraints=constraints,
    )


def test_p2_1_values_that_render_the_same_are_refused(tmp_path: Path) -> None:
    spaced = "Đọc lại tin nhắn , trước khi trả lời,"  # renders exactly like a0
    clean = "Mở lại tin nhắn, rồi mới trả lời,"

    control = _internal_space_frame("t.space", clean)
    build = build_surface(_catalog(tmp_path / "ok", [control, _roast_of(control)], **_MINIMA))
    assert len(json.loads(build.outputs["schedules.json"])["t.space"]) == 4

    direct = _internal_space_frame("t.space", spaced)
    reasons = _refused(_catalog(tmp_path / "direct", [direct, _roast_of(direct)], **_MINIMA))
    assert any("t.space.a: must-change values repeat" in r for r in reasons)

    roast = _roast_of(_internal_space_frame("t.space", spaced))
    reasons = _refused(_catalog(tmp_path / "roast", [control, roast], **_MINIMA))
    assert any("t.space.roast.a: must-change values repeat" in r for r in reasons)
