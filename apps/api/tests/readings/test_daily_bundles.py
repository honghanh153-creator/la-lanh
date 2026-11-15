"""Daily bundles (owner decision 10.11.2026): one matched headline/scene/action per day.

Synthetic sentences only; no personal data.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from typing import Any

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import (
    BUNDLE_PARTS,
    bundle_problems,
    copy_digest,
    load_registry,
    parse_registry,
)
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings import renderers
from app.domains.readings.companion import COMPANION_ISSUE_LINES
from app.domains.readings.daily_psychology import (
    _ARENA_LEADS,
    DAILY_ISSUES,
    apply_daily_psychology,
    daily_content_fingerprint,
    lead_scene,
)
from app.domains.readings.knowledge import full_frame
from app.domains.readings.models import DailyMeaningBrief, SemanticArena
from tests.readings.test_application import MemoryReadingRepository, _date_only_snapshot
from tests.readings.test_daily_rotation import (
    GUEST,
    OWNER_A,
    OWNER_B,
    START,
    _date_only_plan,
    _open,
    _service,
    _variety,
)

ISSUES = tuple(issue.key for issue in DAILY_ISSUES)


def _line(situation: str, number: str, part: str, *, approved: bool = True) -> dict[str, Any]:
    text = f"Câu thử {part} bộ {number} của {situation}."
    entry: dict[str, Any] = {
        "id": f"daily.bundle.{situation}.{number}.{part}",
        "category": "daily",
        "text": text,
        "status": "pending",
    }
    if approved:
        entry.update(
            status="approved", approver="codex", date="2026-11-10", digest=copy_digest(text)
        )
    return entry


def _use(monkeypatch: pytest.MonkeyPatch, entries: list[dict[str, Any]]) -> None:
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _all_bundles(count: int = 3) -> list[dict[str, Any]]:
    return [
        _line(issue, f"{n:02d}", part)
        for issue in ISSUES
        for n in range(1, count + 1)
        for part in BUNDLE_PARTS
    ]


def _notes(owner: Any = OWNER_A, days: int = 20) -> list[tuple[str, str, str, str]]:
    notes = []
    for offset in range(days):
        plan = _date_only_plan(_variety(owner, START + timedelta(days=offset)))
        frame = apply_daily_psychology(plan, full_frame(plan))
        notes.append((frame.scene_key, frame.hook, frame.manifestation, frame.micro_action))
    return notes


def test_no_bundles_keeps_todays_output(monkeypatch: pytest.MonkeyPatch) -> None:
    # Baseline from an empty synthetic registry, so approved bundles in the real
    # registry never change what this test compares against (#415).
    _use(monkeypatch, [])
    before = _notes()
    _use(monkeypatch, [_line(issue, "01", "headline") for issue in ISSUES])  # incomplete
    assert _notes() == before
    assert all(":bundle-" not in key for key, *_ in before)


def test_bundle_is_served_whole_and_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _all_bundles())
    notes = _notes(days=30)
    assert notes == _notes(days=30)
    assert notes != _notes(OWNER_B, days=30)
    for key, hook, scene, action in notes:
        assert ":bundle-" in key
        marker = hook.split(" bộ ", 1)[1]  # "<nn> của <situation>."
        assert marker in scene and action.endswith(marker)
        assert key.split(":")[1] in marker


def test_legacy_plan_without_variety_picks_a_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, _all_bundles())
    plan = _date_only_plan(None)
    frame = apply_daily_psychology(plan, full_frame(plan))
    marker = frame.hook.split(" bộ ", 1)[1]
    assert frame.micro_action.endswith(marker) and marker in frame.manifestation


def test_pending_line_keeps_the_bundle_out(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [
        _line(issue, "01", part, approved=part != "action")
        for issue in ISSUES
        for part in BUNDLE_PARTS
    ]
    _use(monkeypatch, entries)
    assert copy_approval.approved_bundles(ISSUES[0]) == ()
    assert all(":bundle-" not in key for key, *_ in _notes())


def test_only_complete_approved_bundles_rotate(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [*_all_bundles(2), _line(ISSUES[0], "03", "headline")]
    _use(monkeypatch, entries)
    assert [b[0] for b in copy_approval.approved_bundles(ISSUES[0])] == [
        f"Câu thử headline bộ 0{n} của {ISSUES[0]}." for n in (1, 2)
    ]


def test_bundle_problems_flags_missing_parts_and_bad_ids() -> None:
    entries = parse_registry(
        {
            "version": copy_approval.REGISTRY_VERSION,
            "entries": [
                _line("work", "01", "headline"),
                _line("work", "01", "scene"),
                {**_line("work", "02", "scene"), "id": "daily.bundle.work.scene"},
            ],
        }
    )
    problems = bundle_problems(entries)
    assert any("work.01: missing action" in p for p in problems)
    assert any("daily.bundle.work.scene:" in p for p in problems)


def test_registry_bundles_are_complete_and_name_a_real_situation() -> None:
    entries = load_registry()
    assert bundle_problems(entries) == []
    for key in entries:
        if key.startswith(copy_approval.BUNDLE_PREFIX):
            assert key.split(".")[2] in ISSUES, key


def test_fingerprint_changes_when_a_bundle_is_approved_or_revised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = [_line(ISSUES[0], "01", part, approved=False) for part in BUNDLE_PARTS]
    _use(monkeypatch, pending)
    before = daily_content_fingerprint()

    approved = [_line(ISSUES[0], "01", part) for part in BUNDLE_PARTS]
    _use(monkeypatch, approved)
    after_approval = daily_content_fingerprint()
    assert after_approval != before

    revised = [*approved[:2], _line(ISSUES[0], "01", "action")]
    revised[2]["text"] = "Câu thử action đã sửa của bộ này."
    revised[2]["digest"] = copy_digest(revised[2]["text"])
    _use(monkeypatch, revised)
    assert daily_content_fingerprint() not in {before, after_approval}


def test_stored_note_reopens_stable_under_the_same_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _use(monkeypatch, _all_bundles())
    fingerprint = daily_content_fingerprint()
    first = _notes(days=10)
    # Reopening the same day's note with the same registry renders identically.
    assert daily_content_fingerprint() == fingerprint
    assert _notes(days=10) == first


def _restart(monkeypatch: pytest.MonkeyPatch, entries: list[dict[str, Any]]) -> None:
    """A process start: the renderer freezes the fingerprint of the registry it loads."""

    _use(monkeypatch, entries)
    monkeypatch.setattr(
        renderers, "DAILY_PSYCHOLOGY_CONTENT_FINGERPRINT", daily_content_fingerprint()
    )


def _stored(repository: MemoryReadingRepository) -> dict[str, str]:
    return {r.revision_key: r.renderer_version for r in repository.revisions.values()}


def _scene_key(projection: Any, repository: MemoryReadingRepository) -> str:
    revision = repository.revisions[(GUEST, OWNER_A, projection.active.revision_id)]
    candidate = revision.evaluation.publishable_candidate
    assert candidate is not None and candidate.semantic_blueprint is not None
    return candidate.semantic_blueprint.scene_key


def _gate_passing_bundle() -> list[dict[str, Any]]:
    """One approved bundle for START's situation, built from lines that already pass
    the Daily meaning gates, so the restarted service can publish it."""

    empty = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": []})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(copy_approval, "_runtime_registry", lambda: empty)
        plan = _date_only_plan(_variety(OWNER_A, START))
        frame = apply_daily_psychology(plan, full_frame(plan))
    situation = frame.scene_key.split(":")[1]
    texts = {"headline": frame.hook, "scene": frame.manifestation, "action": frame.micro_action}
    return [
        {**_line(situation, "01", part), "text": text, "digest": copy_digest(text)}
        for part, text in texts.items()
    ]


async def test_persisted_note_survives_a_bundle_approval_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#415: approving a bundle after a note was stored gives the bundle its own
    revision key (never a replay of the old key with new text), and a later restart
    under the same registry replays that revision unchanged."""

    repository = MemoryReadingRepository()
    snapshot = _date_only_snapshot(GUEST, OWNER_A)

    _restart(monkeypatch, [])
    opened = await _open(_service(repository, START), snapshot, START)
    before = _stored(repository)
    assert len(before) == 1
    assert ":bundle-" not in _scene_key(opened, repository)
    original_id = (GUEST, OWNER_A, opened.active.revision_id)
    original = deepcopy(repository.revisions[original_id])

    bundle = _gate_passing_bundle()
    _restart(monkeypatch, bundle)
    served = await _open(_service(repository, START), snapshot, START, hour=10)
    after = _stored(repository)
    new_keys = set(after) - set(before)
    assert len(new_keys) == 1  # the old revision is kept, not overwritten
    (new_key,) = new_keys
    assert after[new_key] != next(iter(before.values()))
    assert served.active.revision_id != opened.active.revision_id
    assert ":bundle-" in _scene_key(served, repository)
    # #420: the old revision is still there under its own id, content unchanged.
    assert repository.revisions[original_id] == original

    _restart(monkeypatch, bundle)
    replayed = await _open(_service(repository, START), snapshot, START, hour=12)
    assert replayed.active.revision_id == served.active.revision_id
    assert replayed.active.sections == served.active.sections
    assert _stored(repository) == after


def _registry_bundles() -> list[tuple[str, str, dict[str, str]]]:
    """Every complete bundle in the checked-in registry, approved or pending."""

    grouped: dict[tuple[str, str], dict[str, str]] = {}
    for key, entry in load_registry().items():
        if key.startswith(copy_approval.BUNDLE_PREFIX):
            _, _, situation, number, part = key.split(".")
            grouped.setdefault((situation, number), {})[part] = entry.text
    return [
        (situation, number, parts)
        for (situation, number), parts in sorted(grouped.items())
        if set(parts) == set(BUNDLE_PARTS)
    ]


@pytest.mark.parametrize(
    ("situation", "number", "parts"),
    [pytest.param(*bundle, id=f"{bundle[0]}.{bundle[1]}") for bundle in _registry_bundles()],
)
def test_registry_bundle_passes_the_daily_gate_in_every_arena(
    situation: str, number: str, parts: dict[str, str]
) -> None:
    """A served bundle replaces the authored rotation, so it must clear the same Daily
    gate the authored combinations clear (test_daily_psychology). Otherwise approving it
    turns that day's note into ReadingContentRejected. Pending bundles are checked too,
    so a bad bundle is caught before anyone approves it."""

    assert _bundle_gate_failures(situation, parts) == [], (situation, number)


def test_bundle_gate_check_rejects_a_bundle_without_its_anchors() -> None:
    # The check above must bite: synthetic lines carry none of the issue's anchors.
    situation = ISSUES[0]
    parts = {part: _line(situation, "01", part)["text"] for part in BUNDLE_PARTS}
    assert _bundle_gate_failures(situation, parts)


def _bundle_gate_failures(situation: str, parts: dict[str, str]) -> list[tuple[str, Any]]:
    issue = next(issue for issue in DAILY_ISSUES if issue.key == situation)
    brief = DailyMeaningBrief(
        core_meaning=issue.meaning,
        reader_takeaway=issue.takeaway,
        scene_anchors=issue.scene_anchors,
        action_anchors=issue.action_anchors,
    )
    failures: list[tuple[str, Any]] = []
    for arena in (SemanticArena.GENERAL, *issue.arenas):
        lead = _ARENA_LEADS.get(arena)
        scene = lead_scene(lead, parts["scene"]) if lead else parts["scene"]
        report = evaluate_daily_rewrite(
            {
                "title": parts["headline"],
                "scene": scene,
                "action": parts["action"],
                "companion": COMPANION_ISSUE_LINES[issue.key].line.direct,
            },
            meaning_brief=brief,
        )
        if not report.passed:
            failures.append((arena.value, report.failure_codes))
    return failures
