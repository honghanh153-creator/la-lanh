"""Daily bundles (owner decision 10.11.2026): one matched headline/scene/action per day.

Synthetic sentences only; no personal data.
"""

from __future__ import annotations

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
from app.domains.readings.daily_psychology import DAILY_ISSUES, apply_daily_psychology
from app.domains.readings.knowledge import full_frame
from tests.readings.test_daily_rotation import OWNER_A, OWNER_B, START, _date_only_plan, _variety

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
