"""Audit that every Daily "Vì sao hôm nay?" reason is real (B1b).

Synthetic charts only (no user data, no provider calls). Relevance is graded by
an oracle written from PAIR_RULES and the transit factor id, independent of the
selector it audits. Fails on any shown transit the oracle rejects, any gate
rejection, or any reason sentence with technical jargon.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput
from app.domains.readings.daily_personalization import PAIR_RULES
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import DailyTransitRole, FactorSource, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer

CHARTS = 20
DAYS = 60
_JARGON = re.compile(r"orb|°|\bpha\b|Nhà \d|tam hợp|lục hợp|vuông|đối đỉnh|đồng cung")


def oracle_issue(transit_id: str) -> str | None:
    parts = transit_id.split(":")
    body_a, aspect, body_b, phase = parts[1], parts[2], parts[4], parts[8]
    rule = next((rule for rule in PAIR_RULES if rule.bodies == {body_a, body_b}), None)
    if rule is None:
        return None
    if aspect in {"square", "opposition"}:
        issue = rule.tension_issue
        return "repair-reply" if issue == "quick-reply" and phase == "separating" else issue
    if aspect in {"trine", "sextile"}:
        return rule.cooperative_issue
    return rule.conjunction_issue


def main() -> None:
    engine = NatalChartEngine()
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    totals: Counter[str] = Counter()
    bodies: Counter[str] = Counter()
    longest_streaks: list[int] = []
    problems: list[str] = []
    for index in range(CHARTS):
        chart = engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(
                    1985 + index, (index % 12) + 1, 3 + index, (index * 5) % 24, 10, tzinfo=UTC
                ),
                latitude=10.8 + index * 0.3,
                longitude=106.6 - index * 0.2,
            ),
            CalculationConfig.western_recommended(),
        )
        previous, streak, longest = None, 0, 0
        for offset in range(DAYS):
            day = datetime(2026, 10, 1, 5, tzinfo=UTC) + timedelta(days=offset)
            plan = planner.plan(
                chart,
                purpose=ReadingPurpose.DAILY_NOTE,
                transits=engine.calculate_transit_to_natal(chart, day),
                editorial_seed=day.date().isoformat(),
            )
            candidate = renderer.render(plan)
            totals["days"] += 1
            if not evaluate_candidate(plan, candidate).accepted:
                problems.append(f"chart {index} day {offset}: gate rejected")
            selection = plan.daily_selection
            if selection is None:
                problems.append(f"chart {index} day {offset}: no frozen selection")
                continue
            totals[f"role:{selection.transit_role.value}"] += 1
            transits = [f for f in plan.factors if f.source is FactorSource.TRANSIT]
            key = None
            if selection.transit_role is not DailyTransitRole.NONE:
                (transit,) = transits
                key = transit.id.split(":orb:")[0]
                bodies[transit.subjects[0]] += 1
                totals["reason_shown"] += 1
                touches = (
                    transit.id in selection.support_refs
                    if selection.transit_role is DailyTransitRole.DRIVES
                    else bool(set(transit.child_refs) & set(selection.support_refs))
                )
                if oracle_issue(transit.id) != selection.issue_key or not touches:
                    problems.append(f"chart {index} day {offset}: oracle rejects {transit.id}")
                if candidate.transit is None or _JARGON.search(candidate.transit):
                    problems.append(f"chart {index} day {offset}: reason missing or jargon")
            elif transits or candidate.transit is not None:
                problems.append(f"chart {index} day {offset}: transit without a reason role")
            streak = streak + 1 if key is not None and key == previous else (1 if key else 0)
            longest = max(longest, streak)
            previous = key
        longest_streaks.append(longest)
    shown = totals["reason_shown"]
    print(
        f"Daily why-today audit: {CHARTS} synthetic charts x {DAYS} days = {totals['days']} notes; "
        f"reason shown {shown} ({shown * 100 / totals['days']:.1f}%), "
        f"drives {totals['role:drives']}, supports {totals['role:supports']}; "
        f"oracle-relevant {shown - sum('oracle' in p for p in problems)}/{shown}."
    )
    print(f"Transit bodies shown: {dict(bodies.most_common())}")
    print(f"Longest same-transit streak per chart (days): {longest_streaks}")
    if problems:
        print("\n".join(problems[:20]), file=sys.stderr)
        raise SystemExit(f"Daily why-today audit failed: {len(problems)} problem(s)")
    print("Not a human comprehension study.")


if __name__ == "__main__":
    main()
