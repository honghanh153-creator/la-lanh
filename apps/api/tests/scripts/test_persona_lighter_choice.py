"""The persona run reads the day's small action the way the web shows it (#627, PR C).

Synthetic personas only (qa/personas/personas-100.json); local SQLite; no provider call.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, parse_registry
from app.domains.readings import lighter_action
from app.domains.readings.lighter_action import LIGHTER_ACTION_PREFIX
from scripts import persona_sim
from scripts.persona_metrics import LOW_MOOD, is_light
from scripts.persona_sim import shown_action

ROOT = Path(__file__).resolve().parents[4]
WEB_RULE = ROOT / "apps" / "web" / "src" / "shared" / "hooks" / "useDailyActionView.ts"

OWN = {"action_key": "a" * 64, "action": "Hỏi lại một câu trước khi nhận việc."}
LIGHTER = {
    "action": "Uống một cốc nước rồi ngồi yên hai phút.",
    "weight": "light",
    "experiment": {"action_key": "b" * 64, "action": "Uống một cốc nước rồi ngồi yên hai phút."},
}


def _active(**extra: Any) -> dict[str, Any]:
    return {"sections": {"micro_action": OWN["action"]}, "experiment": OWN, **extra}


def test_low_mood_shows_the_lighter_action_and_keeps_that_one() -> None:
    view = shown_action(_active(lighter_action=LIGHTER), LOW_MOOD)
    assert view["action"] == LIGHTER["action"]
    assert view["experiment"] == LIGHTER["experiment"]  # the kept action is the one on screen
    assert view["lighter_shown"] is True
    assert is_light(view["action"], {}, view["weight"]) == (True, "api")


@pytest.mark.parametrize("mood", ["Rực", "Chill", "Căng", "Lạc trôi"])
def test_other_moods_keep_the_cards_own_action(mood: str) -> None:
    view = shown_action(_active(lighter_action=LIGHTER), mood)
    assert (view["action"], view["experiment"]) == (OWN["action"], OWN)
    assert (view["lighter_offered"], view["lighter_shown"]) == (True, False)
    assert view["weight"] is None


def test_a_mood_that_was_not_saved_never_changes_the_action() -> None:
    view = shown_action(_active(lighter_action=LIGHTER), None)
    assert (view["action"], view["lighter_shown"]) == (OWN["action"], False)


def test_no_lighter_action_offered_means_the_cards_own_action() -> None:
    view = shown_action(_active(), LOW_MOOD)
    assert (view["action"], view["experiment"]) == (OWN["action"], OWN)
    assert (view["lighter_offered"], view["lighter_shown"]) == (False, False)


def test_a_lighter_action_without_an_experiment_cannot_be_kept() -> None:
    view = shown_action(_active(lighter_action={**LIGHTER, "experiment": None}), LOW_MOOD)
    assert view["action"] == LIGHTER["action"]
    assert view["experiment"] is None


def test_the_run_uses_the_mood_and_the_rule_the_web_uses() -> None:
    source = WEB_RULE.read_text(encoding="utf-8")
    mood = re.search(r'export const LIGHTER_MOOD: MoodValue = "([^"]+)";', source)
    assert mood is not None and mood.group(1) == LOW_MOOD
    # The web shows the lighter action when one is offered and the saved mood is that mood.
    assert "reading?.lighter_action) && confirmedMood === LIGHTER_MOOD" in source
    assert 'lighterShown = canSwitch && view.choice !== "original"' in source


def _approve_lighter_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    """The checked-in registry with every lighter sentence approved (in memory only)."""

    data = json.loads(copy_approval.REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        if entry["id"].startswith(LIGHTER_ACTION_PREFIX):
            entry.update(
                status="approved",
                approver="codex",
                date="2026-11-17",
                digest=copy_digest(entry["text"]),
            )
    registry = parse_registry(data)
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _persona_with_most_low_days(precision: str) -> dict[str, Any]:
    personas = json.loads(persona_sim.PERSONAS.read_text(encoding="utf-8"))["personas"]
    group = [p for p in personas if p["birth"]["precision"] == precision]
    persona: dict[str, Any] = max(group, key=lambda p: p["mood_29"].count(LOW_MOOD))
    return persona


def test_simulated_low_days_get_a_light_action_once_the_copy_is_approved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#627 AC2 through the real API: 29 days of one synthetic persona."""

    _approve_lighter_pool(monkeypatch)
    # An exact-time persona: the only kind the API offers a keepable action to today.
    persona = _persona_with_most_low_days("exact")
    rows = persona_sim.run_persona(persona, f"sqlite+aiosqlite:///{tmp_path}/personas.db", {})
    served = [row for row in rows if row.get("status") == 200]
    low = [row for row in served if row["mood"] == LOW_MOOD]
    assert len(low) >= 3
    light = [row for row in low if row["light"] and row["light_source"] == "api"]
    assert len(light) / len(low) >= 0.9
    for row in low:
        # The note itself is untouched (US-04 AC14): its own action is still the one from
        # before the mood, and only what is on screen differs.
        assert row["lighter_shown"] is True
        assert row["card_action"] == row["before_mood"]["action"] != row["action"]
    # Other moods are not pulled to the lighter action (AC3).
    others = [row for row in served if row["mood"] != LOW_MOOD]
    assert others and all(row.get("lighter_shown") is False for row in others)
    assert all(row["action"] == row["before_mood"]["action"] for row in others)
    # A persona who wants the action keeps the one on screen: the server accepts the lighter
    # action's own key.
    wanted = [row for row in low if row["wants_keep"]]
    assert wanted and all(row["experiment_offered"] for row in low)
    assert all(row["kept"] and row["keep_status"] == 200 for row in wanted)


def test_no_lighter_offer_leaves_the_run_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """While no lighter sentence is served the rows keep the shape of the committed baselines."""

    monkeypatch.setattr(lighter_action, "LIGHTER_CATALOG", ())
    persona = _persona_with_most_low_days("date_only")
    rows = persona_sim.run_persona(persona, f"sqlite+aiosqlite:///{tmp_path}/personas.db", {})
    served = [row for row in rows if row.get("status") == 200]
    assert served
    assert all("lighter_shown" not in row and "card_action" not in row for row in served)
    assert all(row["action"] == row["before_mood"]["action"] for row in served)
