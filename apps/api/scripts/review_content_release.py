"""Release content review: the core reviewer on ten personas, then the clarity ratchet.

``python -m scripts.review_content_release`` fails when the core ``ContentReviewAgent`` finds a
critical/high problem, or when any plain-language rule count (``clarity_lint``, spec layer A)
rises above ``content_clarity_baseline.json`` on Daily, Tarot, Radar or Khám phá, or sample
coverage drops. After an intended change, rewrite the baseline with ``--update-baseline`` and
explain the new numbers in the PR. Only rule ids, counts and surface names are printed.
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    NatalChart,
    ZodiacSign,
)
from app.domains.readings.clarity_lint import (
    RULES,
    TODO_RULES,
    SurfaceReport,
    baseline_document,
    lint_surface,
    ratchet_regressions,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import BackgroundLens, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.review_agent import ContentReviewAgent, ReviewSample
from app.domains.readings.voice import DailySections, roast_daily_sections
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.knowledge import BOOK_SOURCES, all_cards
from app.domains.tarot.models import TarotContext, TarotSpread, TarotVoice
from scripts.content_clarity_corpus import (
    MINIMUM_SAMPLES,
    build_clarity_corpus,
    date_only_chart,
)
from scripts.content_clarity_corpus import daily_review_plan as _daily_review_plan

BASELINE_PATH = Path(__file__).with_name("content_clarity_baseline.json")
PERSONA_COUNT = 10
_QUESTIONS = (
    "Mình cần nhìn rõ điều gì trước khi nhắn lại?",
    "Mình nên nói gì để cuộc trao đổi ở công việc rõ hơn?",
    "Mình cần bỏ bớt việc gì để cơ thể có chỗ nghỉ?",
    "Mình đang né gọi tên nhu cầu nào của bản thân?",
    "Bước nhỏ nào giúp mình kiểm tra chuyện đang phân vân?",
    "Mình cần đặt ranh giới nào trong kết nối này?",
    "Điều gì đã rõ mà mình vẫn đang trì hoãn?",
    "Mình nên quan sát gì trước khi nhận thêm việc?",
    "Câu nào cần được nói thẳng thay vì giải thích vòng?",
    "Mình có thể chăm phần đang quá tải bằng cách nào?",
)
_CONTEXTS = (
    TarotContext.RELATIONSHIPS,
    TarotContext.WORK,
    TarotContext.ENERGY,
    TarotContext.SELF_CARE,
    TarotContext.GENERAL,
    TarotContext.RELATIONSHIPS,
    TarotContext.GENERAL,
    TarotContext.WORK,
    TarotContext.COMMUNICATION,
    TarotContext.SELF_CARE,
)
_LENSES = tuple(lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO)
_SPREADS = (TarotSpread.ONE_CARD, TarotSpread.THREE_CARD, TarotSpread.FIVE_CARD)
_SPREAD_CARD_COUNTS = {
    TarotSpread.ONE_CARD: 1,
    TarotSpread.THREE_CARD: 3,
    TarotSpread.FIVE_CARD: 5,
}


# tests/readings/test_voice.py imports this helper from here.
_date_only = date_only_chart


def _full_chart(index: int) -> NatalChart:
    return NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(
                1990 + index,
                (index % 12) + 1,
                8 + index,
                1 + index,
                15,
                tzinfo=UTC,
            ),
            latitude=10.8231 + (index * 0.21),
            longitude=106.6297 - (index * 0.17),
        ),
        CalculationConfig.western_recommended(),
    )


def build_synthetic_samples(*, roast: bool = False) -> tuple[ReviewSample, ...]:
    """Production default voices (Daily direct, Tarot ``playful_grounded``) by default;
    ``roast`` reviews the approved read-time roast voice on both."""
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    engine = NatalChartEngine()
    tarot = TarotReadingEngine()
    cards = all_cards()
    samples: list[ReviewSample] = []

    for index, sign in enumerate(tuple(ZodiacSign)[:PERSONA_COUNT]):
        persona_id = f"persona-{index + 1:02d}"
        chart = _date_only(sign) if index % 2 == 0 else _full_chart(index)
        plan = _daily_review_plan(
            planner, engine, chart, _LENSES[index % len(_LENSES)], date(2026, 9, 29), index
        )
        candidate = renderer.render(plan)
        evaluation = evaluate_candidate(plan, candidate)
        daily = DailySections(
            candidate.hook, candidate.thesis, candidate.manifestation, candidate.micro_action
        )
        if roast:
            daily = roast_daily_sections(daily)
        samples.append(
            ReviewSample(
                persona_id=persona_id,
                surface="daily",
                sections=(
                    ("hook", daily.hook),
                    ("thesis", daily.thesis),
                    ("scene", daily.manifestation),
                    ("action", daily.micro_action),
                    *((("why_today", candidate.transit),) if candidate.transit else ()),
                ),
                disclaimer=candidate.disclaimer,
                provenance_ids=tuple(claim.factor_ref for claim in candidate.evidence.claims),
                evidence_validated=evaluation.accepted,
            )
        )

        natal_plan = planner.plan(
            _full_chart(index),
            purpose=ReadingPurpose.READING_DETAIL,
            background_lens=_LENSES[index % len(_LENSES)],
            editorial_seed=(date(2026, 9, 29) + timedelta(days=index)).isoformat(),
        )
        natal_candidate = renderer.render(natal_plan)
        natal_evaluation = evaluate_candidate(natal_plan, natal_candidate)
        samples.append(
            ReviewSample(
                persona_id=persona_id,
                surface="natal",
                sections=(
                    ("hook", natal_candidate.hook),
                    ("thesis", natal_candidate.thesis),
                    ("scene", natal_candidate.manifestation),
                    ("action", natal_candidate.micro_action),
                ),
                disclaimer=natal_candidate.disclaimer,
                provenance_ids=tuple(claim.factor_ref for claim in natal_candidate.evidence.claims),
                evidence_validated=natal_evaluation.accepted,
            )
        )

        spread = _SPREADS[index % len(_SPREADS)]
        card_count = _SPREAD_CARD_COUNTS[spread]
        card_ids = tuple(
            cards[(index * 7 + offset) % len(cards)].id for offset in range(card_count)
        )
        tarot_reading = tarot.render(
            card_ids=card_ids,
            spread=spread,
            context=_CONTEXTS[index],
            question=_QUESTIONS[index],
            voice=TarotVoice.ROAST if roast else TarotVoice.PLAYFUL_GROUNDED,
        )
        source_ids = set(tarot_reading.provenance.source_ids)
        registered_source_ids = {source.source_id for source in BOOK_SOURCES}
        provenance_is_valid = bool(source_ids) and source_ids <= registered_source_ids
        samples.append(
            ReviewSample(
                persona_id=persona_id,
                surface="tarot",
                sections=(
                    ("hook", tarot_reading.headline),
                    ("summary", tarot_reading.summary),
                    *tuple(
                        (f"meaning_{position.key}", position.meaning_here)
                        for position in tarot_reading.positions
                    ),
                    *tuple(
                        (f"scene_{position.key}", position.everyday_scene)
                        for position in tarot_reading.positions
                    ),
                    *tuple(
                        (f"reflection_{position.key}", position.reflection_question)
                        for position in tarot_reading.positions
                    ),
                    *tuple(
                        (f"action_{position.key}", position.small_action)
                        for position in tarot_reading.positions
                        if position.small_action
                    ),
                    ("closing", tarot_reading.closing_prompt),
                ),
                disclaimer=tarot_reading.disclaimer,
                provenance_ids=tarot_reading.provenance.source_ids,
                evidence_validated=provenance_is_valid,
            )
        )
    return tuple(samples)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="rewrite the clarity baseline with the current counts (intended changes only)",
    )
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    _review(build_synthetic_samples(), label="Content review")
    _review(build_synthetic_samples(roast=True), label="Roast voice review")
    _clarity_ratchet(args.baseline, update=args.update_baseline)


def clarity_reports() -> dict[str, SurfaceReport]:
    return {
        surface: lint_surface(surface, documents)
        for surface, documents in build_clarity_corpus().items()
    }


def format_clarity_table(reports: Mapping[str, SurfaceReport], baseline: Mapping[str, Any]) -> str:
    """Rule counts per surface; ``(+n)``/``(-n)`` is the change against the baseline."""

    surfaces = list(reports)
    expected: Mapping[str, Any] = baseline.get("surfaces", {})
    width = 18
    lines = [
        f"{'rule':<34}" + "".join(f"{surface:>{width}}" for surface in surfaces),
        f"{'samples':<34}"
        + "".join(f"{reports[surface].samples:>{width}}" for surface in surfaces),
    ]
    for rule, name in RULES.items():
        cells = []
        for surface in surfaces:
            value = reports[surface].rules[rule]
            delta = value - int(expected.get(surface, {}).get("rules", {}).get(rule, 0))
            cell = f"{value}" + (f" ({delta:+d})" if delta else "")
            cells.append(f"{cell:>{width}}")
        lines.append(f"{rule + ' ' + name:<34}" + "".join(cells))
    return "\n".join(lines)


def _clarity_ratchet(path: Path, *, update: bool) -> None:
    started = time.perf_counter()
    reports = clarity_reports()
    elapsed = time.perf_counter() - started
    baseline: dict[str, Any] = json.loads(path.read_text("utf-8")) if path.exists() else {}
    print(f"Clarity lint (spec layer A) on rendered output, {elapsed:.1f}s:")
    print(format_clarity_table(reports, baseline))
    print("Not measured yet: " + "; ".join(f"{key} {name}" for key, name in TODO_RULES.items()))
    if update:
        path.write_text(
            json.dumps(baseline_document(reports), ensure_ascii=False, indent=2) + "\n", "utf-8"
        )
        print(f"Clarity baseline rewritten: {path.name}")
        return
    problems = ratchet_regressions(reports, baseline, minimum_samples=MINIMUM_SAMPLES)
    if problems:
        print("Clarity ratchet failed (counts may only go down):")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    expected = baseline.get("surfaces", {})
    improved = any(
        report.rules[rule] < int(expected.get(surface, {}).get("rules", {}).get(rule, 0))
        for surface, report in reports.items()
        for rule in RULES
    )
    print(
        "Clarity ratchet passed: no rule count rose and coverage held."
        + (" Some counts fell; lock them in with --update-baseline." if improved else "")
    )


def _review(samples: tuple[ReviewSample, ...], *, label: str) -> None:
    result = ContentReviewAgent().review(samples)
    if result.persona_count != PERSONA_COUNT:
        raise SystemExit(f"Content review needs {PERSONA_COUNT} synthetic personas")
    if result.sample_count != PERSONA_COUNT * 3:
        raise SystemExit("Content review needs Daily, Natal and Tarot for every synthetic persona")
    surfaces_by_persona = {
        persona_id: {sample.surface for sample in samples if sample.persona_id == persona_id}
        for persona_id in {sample.persona_id for sample in samples}
    }
    if any(surfaces != {"daily", "natal", "tarot"} for surfaces in surfaces_by_persona.values()):
        raise SystemExit("Every synthetic persona must be reviewed on Daily, Natal and Tarot")
    if not result.passed:
        print(f"{label} failed (source prose is intentionally omitted):")
        for finding in result.findings:
            print(
                f"- {finding.severity}: {finding.rule_id} "
                f"[{finding.persona_id}/{finding.surface}/{finding.section}]"
            )
        raise SystemExit(1)
    medium_count = sum(finding.severity == "medium" for finding in result.findings)
    print(
        f"{label} passed: {result.persona_count} synthetic personas, "
        f"{result.sample_count} generated readings, no critical/high findings, "
        f"{medium_count} medium follow-ups."
    )


if __name__ == "__main__":
    main()
