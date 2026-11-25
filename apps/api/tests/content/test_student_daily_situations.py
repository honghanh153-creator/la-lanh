"""Student Daily bundles and their approval gate (#704). Synthetic render inputs only.

Editorial groups describe the copy, never the reader. This CI gate is scoped to these four
bundles: approving any part requires the whole bundle and both frozen light slots together.
"""

from __future__ import annotations

import json
from dataclasses import replace
from itertools import combinations
from uuid import UUID

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import (
    BUNDLE_PARTS,
    REGISTRY_PATH,
    CopyEntry,
    approved_bundles,
    copy_digest,
    load_registry,
    parse_registry,
    registry_problems,
)
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings import action_tags, companion_pool, daily_psychology, lighter_action
from app.domains.readings.action_tags import ActionTag
from app.domains.readings.application import _companion_line
from app.domains.readings.companion import COMPANION_ISSUE_LINES
from app.domains.readings.daily_personalization import PLACEMENT_MEANINGS, SupportedSituation
from app.domains.readings.daily_psychology import DAILY_ISSUES, lead_scene
from app.domains.readings.lighter_action import ACTION_SHAPES, light_slots, lighter_action_for
from app.domains.readings.models import BackgroundLens, ReadingPurpose, SemanticArena
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.voice import DailySections, ReadingVoice, apply_content_voice
from tests.content.test_daily_variants import (
    _check_action,
    _check_clarity,
    _check_headline,
    _check_scene,
    _check_scene_anchor,
)
from tests.readings.test_daily_rotation import _date_only_plan
from tests.readings.test_voice import _content

# bundle id -> (editorial group, normal picture group, light picture groups in frozen order)
STUDENT_BUNDLES = {
    "daily.bundle.perfect-before-start.13": ("job_search", "connection", ("body", "rest")),
    "daily.bundle.defend-old-choice.13": ("job_search", "study_work", ("body", "rest")),
    "daily.bundle.changed-plan.13": ("study_and_work", "boundary", ("rest", "body")),
    "daily.bundle.decision-fatigue.13": ("study_and_work", "study_work", ("body", "rest")),
}
ISSUES = {issue.key: issue for issue in DAILY_ISSUES}
REVISIONS = tuple(UUID(int=n) for n in range(1, 65))


def _issue(bundle: str) -> str:
    return bundle.split(".")[2]


def _light_ids(bundle: str) -> tuple[str, str]:
    prefix = f"lighter.issue.{_issue(bundle)}"
    return f"{prefix}.01", f"{prefix}.02"


def _approved(entry: CopyEntry) -> CopyEntry:
    return replace(
        entry,
        status="approved",
        approver="codex",
        date="2026-11-25",
        digest=copy_digest(entry.text),
    )


def _pending_registry() -> dict[str, CopyEntry]:
    entries = load_registry()
    for bundle in STUDENT_BUNDLES:
        for key in (*(f"{bundle}.{part}" for part in BUNDLE_PARTS), *_light_ids(bundle)):
            entries[key] = replace(
                entries[key], status="pending", approver=None, date=None, digest=None
            )
    return entries


def _approve(entries: dict[str, CopyEntry], bundle: str) -> None:
    for key in (*(f"{bundle}.{part}" for part in BUNDLE_PARTS), *_light_ids(bundle)):
        entries[key] = _approved(entries[key])


def _assert_student_unlock(entries: dict[str, CopyEntry], monkeypatch: pytest.MonkeyPatch) -> None:
    assert registry_problems(entries) == []
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    for bundle, (_group, shape, light_shapes) in STUDENT_BUNDLES.items():
        part_ids = tuple(f"{bundle}.{part}" for part in BUNDLE_PARTS)
        assert all(key in entries for key in part_ids), f"{bundle}: missing part"
        action_id = f"{bundle}.action"
        assert action_tags.normal_tags().get(action_id) == (
            copy_digest(entries[action_id].text),
            shape,
        )
        assert action_tags.tag_of(action_id, (_issue(bundle),)) == ActionTag("normal", shape)
        if not any(entries[key].servable for key in part_ids):
            continue
        assert all(entries[key].servable for key in part_ids), f"{bundle}: partial approval"
        slots = light_slots(_issue(bundle))
        assert tuple(key for key, _digest, _shape in slots) == _light_ids(bundle)
        assert tuple(slot_shape for _key, _digest, slot_shape in slots) == light_shapes
        for key, digest, slot_shape in slots:
            assert key in entries, f"{bundle}: missing light slot"
            assert entries[key].servable, f"{key}: light slot not servable"
            assert copy_digest(entries[key].text) == digest, f"{key}: frozen digest mismatch"
            assert slot_shape in ACTION_SHAPES
            assert action_tags.tag_of(key, (_issue(bundle),)) == ActionTag("light", slot_shape)
        expected = {entries[key].text for key in _light_ids(bundle)}
        offered = {
            lighter_action_for(revision, f"psychology:{_issue(bundle)}") for revision in REVISIONS
        }
        assert offered == expected, f"{bundle}: both light slots must pass runtime"


def test_student_inventory_required_fields_tags_and_light_slots() -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = parse_registry(raw)  # Also rejects duplicate IDs and missing/non-string fields.
    assert registry_problems(entries) == []
    assert {value[0] for value in STUDENT_BUNDLES.values()} == {"job_search", "study_and_work"}
    for bundle, (_group, shape, light_shapes) in STUDENT_BUNDLES.items():
        for part in BUNDLE_PARTS:
            key = f"{bundle}.{part}"
            assert key in entries
            assert entries[key].id == key and entries[key].category == "reading"
            if part in ("headline", "scene"):
                assert entries[key].text.startswith("Khi "), key
            _check_clarity(key, entries[key].text)
        _check_headline(f"{bundle}.headline", entries[f"{bundle}.headline"].text)
        _check_scene(f"{bundle}.scene", entries[f"{bundle}.scene"].text)
        _check_scene_anchor(f"{bundle}.scene", entries[f"{bundle}.scene"].text)
        _check_action(f"{bundle}.action", entries[f"{bundle}.action"].text)
        assert action_tags.normal_tags()[f"{bundle}.action"] == (
            copy_digest(entries[f"{bundle}.action"].text),
            shape,
        )
        assert action_tags.tag_of(f"{bundle}.action", (_issue(bundle),)) == ActionTag(
            "normal", shape
        )
        slots = light_slots(_issue(bundle))
        assert tuple(key for key, _digest, _shape in slots) == _light_ids(bundle)
        assert tuple(slot_shape for _key, _digest, slot_shape in slots) == light_shapes
        for key, digest, slot_shape in slots:
            assert entries[key].category == "reading"
            assert copy_digest(entries[key].text) == digest
            assert slot_shape in ACTION_SHAPES
            assert action_tags.tag_of(key, (_issue(bundle),)) == ActionTag("light", slot_shape)


def test_student_unlock_gate_on_checked_in_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _assert_student_unlock(load_registry(), monkeypatch)


def test_unservable_student_parts_never_enter_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = load_registry()
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    for bundle in STUDENT_BUNDLES:
        parts = [entries[f"{bundle}.{part}"] for part in BUNDLE_PARTS]
        if not all(entry.servable for entry in parts):
            assert tuple(entry.text for entry in parts) not in approved_bundles(_issue(bundle))
        for entry in parts:
            if not entry.servable:
                assert copy_approval.approved_copy(entry.id) is None


def test_pending_student_bundles_do_not_block_older_served_bundles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    old = "daily.bundle.changed-plan.01"
    for part in BUNDLE_PARTS:
        entries[f"{old}.{part}"] = _approved(entries[f"{old}.{part}"])
    _assert_student_unlock(entries, monkeypatch)
    assert tuple(entries[f"{old}.{part}"].text for part in BUNDLE_PARTS) in approved_bundles(
        "changed-plan"
    )
    assert all(
        not entries[key].servable for bundle in STUDENT_BUNDLES for key in _light_ids(bundle)
    )


@pytest.mark.parametrize("bundle", STUDENT_BUNDLES)
def test_one_complete_student_bundle_unlocks_without_the_others(
    bundle: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    _assert_student_unlock(entries, monkeypatch)
    assert tuple(entries[f"{bundle}.{part}"].text for part in BUNDLE_PARTS) in approved_bundles(
        _issue(bundle)
    )


@pytest.mark.parametrize("bundle", STUDENT_BUNDLES)
@pytest.mark.parametrize(
    "parts", [parts for count in (1, 2) for parts in combinations(BUNDLE_PARTS, count)]
)
def test_gate_rejects_partial_bundle_approval(
    bundle: str,
    parts: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    for part in parts:
        entries[f"{bundle}.{part}"] = _approved(entries[f"{bundle}.{part}"])
    with pytest.raises(AssertionError, match="partial approval"):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize("bundle", STUDENT_BUNDLES)
@pytest.mark.parametrize("slot", (0, 1))
@pytest.mark.parametrize("failure", ("pending", "missing", "edited"))
def test_gate_rejects_unavailable_or_reworded_light_slot(
    bundle: str,
    slot: int,
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    key = _light_ids(bundle)[slot]
    if failure == "pending":
        entries[key] = replace(entries[key], status="pending")
    elif failure == "missing":
        del entries[key]
    else:
        entries[key] = _approved(replace(entries[key], text="Ngồi yên một phút rồi thở chậm."))
        assert entries[key].servable  # Fresh approval cannot bypass the frozen catalog.
    with pytest.raises(AssertionError, match=r"light slot|frozen digest"):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize("part", BUNDLE_PARTS)
def test_gate_rejects_missing_bundle_part(part: str, monkeypatch: pytest.MonkeyPatch) -> None:
    entries = _pending_registry()
    del entries[f"daily.bundle.changed-plan.13.{part}"]
    with pytest.raises(AssertionError):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize("field", ("digest", "approver", "date", "status"))
def test_registry_gate_rejects_invalid_approval_even_when_not_servable(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    key = "daily.bundle.changed-plan.13.headline"
    valid = _approved(entries[key])
    entries[key] = {
        "digest": replace(valid, digest="0" * 64),
        "approver": replace(valid, approver=None),
        "date": replace(valid, date=None),
        "status": replace(valid, status="ready"),
    }[field]
    assert not entries[key].servable
    assert registry_problems(entries)
    with pytest.raises(AssertionError):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize("failure", ("missing", "shape", "digest", "weight"))
def test_gate_rejects_invalid_normal_action_tag(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = _pending_registry()
    key = "daily.bundle.changed-plan.13.action"
    tags = dict(action_tags.normal_tags())
    if failure == "missing":
        del tags[key]
    elif failure == "shape":
        tags[key] = (tags[key][0], "study_work")
    elif failure == "digest":
        tags[key] = ("0" * 64, tags[key][1])
    else:
        original = action_tags.tag_of
        monkeypatch.setattr(
            action_tags,
            "tag_of",
            lambda entry_id, issues: (
                ActionTag("light", "boundary") if entry_id == key else original(entry_id, issues)
            ),
        )
    monkeypatch.setattr(action_tags, "normal_tags", lambda: tags)
    with pytest.raises(AssertionError):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize("failure", ("missing", "shape", "weight"))
def test_gate_rejects_broken_light_catalog(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    entries = _pending_registry()
    bundle = "daily.bundle.changed-plan.13"
    _approve(entries, bundle)
    catalog = dict(lighter_action.ISSUE_LIGHT_CATALOG)
    slots = catalog["changed-plan"]
    if failure == "weight":
        original = action_tags.tag_of
        key = _light_ids(bundle)[0]
        monkeypatch.setattr(
            action_tags,
            "tag_of",
            lambda entry_id, issues: (
                ActionTag("normal", "rest") if entry_id == key else original(entry_id, issues)
            ),
        )
    else:
        catalog["changed-plan"] = (
            slots[:1]
            if failure == "missing"
            else ((slots[0][0], slots[0][1], "study_work"), slots[1])
        )
    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", catalog)
    with pytest.raises(AssertionError):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize(
    "text", ("Ngồi yên sáu phút rồi thở chậm.", "Ngồi yên " + "thật lâu " * 30 + "rồi nghỉ.")
)
def test_gate_checks_runtime_limits_beyond_approval_and_digest(
    text: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    bundle = "daily.bundle.changed-plan.13"
    _approve(entries, bundle)
    key = _light_ids(bundle)[0]
    entries[key] = _approved(replace(entries[key], text=text))
    assert entries[key].servable
    # Only this negative fixture revises the catalog too, so the runtime check must catch it.
    catalog = dict(lighter_action.ISSUE_LIGHT_CATALOG)
    slots = catalog["changed-plan"]
    catalog["changed-plan"] = ((slots[0][0], copy_digest(text), slots[0][2]), slots[1])
    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", catalog)
    with pytest.raises(AssertionError, match="both light slots must pass runtime"):
        _assert_student_unlock(entries, monkeypatch)


@pytest.mark.parametrize(
    "bundle,arena,voice",
    [
        (bundle, arena, voice)
        for bundle in STUDENT_BUNDLES
        for arena in (SemanticArena.GENERAL, *ISSUES[_issue(bundle)].arenas)
        for voice in ReadingVoice
    ],
)
def test_student_card_renders_whole_in_each_arena_voice_and_light_slot(
    bundle: str,
    arena: SemanticArena,
    voice: ReadingVoice,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    # Isolate this bundle so the real selector has to pick it, without changing production copy.
    selected = {
        key: entry
        for key, entry in entries.items()
        if key.startswith(f"{bundle}.") or key in _light_ids(bundle)
    }
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: selected)
    issue = _issue(bundle)
    supported = SupportedSituation(
        issue_key=issue,
        meaning=PLACEMENT_MEANINGS[issue],
        factor_refs=(),
        rule_key="student-fixture",
        rank=(1, 0, 0),
    )
    monkeypatch.setattr(daily_psychology, "eligible_daily_situations", lambda _plan: (supported,))
    lens = None if arena is SemanticArena.GENERAL else BackgroundLens(arena.value)
    plan = _date_only_plan(None).model_copy(update={"background_lens": lens})
    candidate = DeterministicVietnameseRenderer().render(plan)
    headline, scene, action = (entries[f"{bundle}.{part}"].text for part in BUNDLE_PARTS)
    lead = daily_psychology._ARENA_LEADS.get(arena)
    assert (candidate.hook, candidate.manifestation, candidate.micro_action) == (
        headline,
        lead_scene(lead, scene) if lead else scene,
        action,
    )
    blueprint = candidate.semantic_blueprint
    assert blueprint is not None and blueprint.daily_meaning is not None
    assert blueprint.scene_key == blueprint.action_key == f"psychology:{issue}:bundle-0"
    assert blueprint.daily_meaning.observation_question == ISSUES[issue].observation_question
    assert blueprint.daily_meaning.reader_takeaway == ISSUES[issue].takeaway
    assert blueprint.daily_meaning.core_meaning.endswith(ISSUES[issue].meaning)
    assert candidate.companion is candidate.companion_roast is None
    assert companion_pool.EXTRA_LINE_SELECTION_ENABLED is False
    companion = _companion_line(candidate, ReadingPurpose.DAILY_NOTE)
    assert companion == COMPANION_ISSUE_LINES[issue].line.direct
    content = _content(
        DailySections(candidate.hook, candidate.thesis, candidate.manifestation, action),
        purpose=ReadingPurpose.DAILY_NOTE,
    )
    content = content.model_copy(
        update={"sections": content.sections.model_copy(update={"companion": companion})}
    )
    shown = apply_content_voice(content, voice).sections
    assert (shown.hook, shown.manifestation, shown.micro_action) == (
        headline,
        candidate.manifestation,
        action,
    )
    assert shown.companion == getattr(COMPANION_ISSUE_LINES[issue].line, voice.value)
    assert shown.companion is not None
    # Rewrite's direct companion budget differs from the authored roast budget.
    if voice is ReadingVoice.DIRECT:
        report = evaluate_daily_rewrite(
            {
                "title": shown.hook,
                "scene": shown.manifestation,
                "action": action,
                "companion": shown.companion,
            },
            meaning_brief=blueprint.daily_meaning,
            companion_brief=COMPANION_ISSUE_LINES[issue],
        )
        assert report.passed, report.failure_codes
    offered = {lighter_action_for(revision, blueprint.mechanism_key) for revision in REVISIONS}
    assert offered == {entries[key].text for key in _light_ids(bundle)}
