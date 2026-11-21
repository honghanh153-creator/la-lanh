"""Daily pool widening (#841 follow-up): pair rules whose sentence waits in the copy registry."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput
from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import daily_personalization as personalization
from app.domains.readings import daily_psychology
from app.domains.readings.daily_personalization import PAIR_RULES, REGISTRY_PAIR_RULES
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.daily_rotation import VARIETY_KEY_VERSION, day_index
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import DailyVariety, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer

ENGINE = NatalChartEngine()
# Fictional birth moments; nothing real.
CHARTS = [
    ENGINE.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1994 + n % 9, 1 + n % 12, 3 + n, 2 + n % 20, tzinfo=UTC),
            latitude=10.82,
            longitude=106.63,
        )
    )
    for n in range(16)
]
START = datetime(2026, 11, 21, 5, tzinfo=UTC)
WORDS = re.compile(r"\b(?:sẽ|chắc chắn|định mệnh|số phận|vũ trụ|năng lượng)\b", re.IGNORECASE)


def _approve_all(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [
        {
            "id": entry.id,
            "category": entry.category,
            "text": entry.text,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-21",
            "digest": copy_digest(entry.text),
        }
        for entry in load_registry().values()
        if entry.id.startswith("situation.pair.")
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


def _pool_issues(chart: object, days: int) -> list[set[str]]:
    """Distinct eligible issues of each day's natal selection (as the app passes them)."""

    seen: list[set[str]] = []
    original = daily_psychology._situation_pool

    def spy(plan: object, situations: tuple[personalization.SupportedSituation, ...]) -> object:
        seen.append({situation.issue_key for situation in situations})
        return original(plan, situations)  # type: ignore[arg-type]

    planner = ReadingPlanner()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(daily_psychology, "_situation_pool", spy)
        for offset in range(days):
            moment = START + timedelta(days=offset)
            before = len(seen)
            plan = planner.plan(
                chart,  # type: ignore[arg-type]
                purpose=ReadingPurpose.DAILY_NOTE,
                transits=ENGINE.calculate_transit_to_natal(chart, moment),  # type: ignore[arg-type]
                editorial_seed=moment.date().isoformat(),
                daily_variety=DailyVariety(
                    key_version=VARIETY_KEY_VERSION,
                    catalog_version=daily_psychology.DAILY_PSYCHOLOGY_MATRIX_VERSION,
                    seed="0" * 32,
                    day_index=day_index(moment.date()),
                ),
            )
            card = DeterministicVietnameseRenderer().render(plan)
            assert evaluate_candidate(plan, card).accepted, (offset, card.hook)
            del seen[before + 1 :]
    return seen


def test_every_registry_rule_is_new_known_and_has_a_plain_pending_sentence() -> None:
    registry = load_registry()
    issues = {issue.key for issue in DAILY_ISSUES}
    existing = {rule.bodies for rule in PAIR_RULES}
    keys = set()
    for rule in REGISTRY_PAIR_RULES:
        assert rule.bodies not in existing, rule
        assert rule.kind in {"tense", "coop", "conj"} and rule.issue in issues, rule
        assert (rule.bodies, rule.kind) not in keys, rule
        keys.add((rule.bodies, rule.kind))
        entry = registry[rule.copy_id]
        assert entry.category == "reading"
        text = entry.text
        assert text.startswith("Bạn ") and text.endswith(".") and text.count(".") == 1, text
        assert len(text.split()) <= 16, text
        assert not WORDS.search(text), text
    texts = [registry[rule.copy_id].text for rule in REGISTRY_PAIR_RULES]
    assert len(set(texts)) == len(texts)


def test_a_pending_rule_never_reaches_a_daily_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    pending = {
        entry.text for key, entry in load_registry().items() if key.startswith("situation.pair.")
    }
    assert all(copy_approval.approved_copy(rule.copy_id) is None for rule in REGISTRY_PAIR_RULES)
    meanings: list[str] = []
    original = personalization.eligible_daily_situations

    def spy(plan: object) -> tuple[personalization.SupportedSituation, ...]:
        found = original(plan)  # type: ignore[arg-type]
        meanings.extend(situation.meaning for situation in found)
        return found

    monkeypatch.setattr(daily_psychology, "eligible_daily_situations", spy)
    for chart in CHARTS[:8]:
        _pool_issues(chart, 10)
    assert meanings and not pending & set(meanings)


def test_approved_rules_widen_the_needs_group_and_render_accepted_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    _approve_all(monkeypatch)
    after = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    assert all(b <= a for b, a in zip(before, after, strict=True))  # nothing is taken away
    need_before = sum("name-the-need" in issues for issues in before)
    need_after = sum("name-the-need" in issues for issues in after)
    assert need_after > need_before, (need_before, need_after)
    assert sum(map(len, after)) > sum(map(len, before))


def test_approved_rules_widen_the_self_judgment_group(monkeypatch: pytest.MonkeyPatch) -> None:
    group = {"comparison-loop", "perfect-before-start"}
    before = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    _approve_all(monkeypatch)
    after = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    assert sum(bool(group & issues) for issues in after) > sum(
        bool(group & issues) for issues in before
    )


def test_approved_rules_widen_the_thin_overload_situations(monkeypatch: pytest.MonkeyPatch) -> None:
    thin = {"decision-fatigue", "capacity-before-agreement"}
    before = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    _approve_all(monkeypatch)
    after = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    assert sum(bool(thin & issues) for issues in after) > sum(
        bool(thin & issues) for issues in before
    )


def test_approved_rules_widen_the_friction_group(monkeypatch: pytest.MonkeyPatch) -> None:
    group = {"changed-plan", "defend-old-choice", "avoid-small-conflict"}
    before = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    _approve_all(monkeypatch)
    after = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    assert sum(len(group & issues) for issues in after) > sum(
        len(group & issues) for issues in before
    )


def test_approved_cooperative_rules_add_situations(monkeypatch: pytest.MonkeyPatch) -> None:
    coop = [rule for rule in REGISTRY_PAIR_RULES if rule.kind == "coop"]
    assert coop
    before = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    _approve_all(monkeypatch)
    after = [issues for chart in CHARTS for issues in _pool_issues(chart, 14)]
    assert sum(map(len, after)) > sum(map(len, before))
