from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    ZodiacSign,
)
from app.domains.content.catalog import compile_daily_catalog
from app.domains.content.models import ContentValidationFinding, ContentValidationReceipt
from app.domains.content.validation import validate_daily_catalog
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.knowledge import use_specific_runtime_catalog
from app.domains.readings.models import BackgroundLens, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.review_agent import ContentReviewAgent, ReviewSample

SYNTHETIC_PERSONA_COUNT = 10
CONTENT_RELEASE_VALIDATOR_VERSION = "content-studio-release-v2"
_LENSES = tuple(lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO)


def validate_daily_release(payload: dict[str, Any]) -> ContentValidationReceipt:
    static_receipt = validate_daily_catalog(payload)
    if not static_receipt.passed:
        return static_receipt

    catalog = compile_daily_catalog(payload, generation=0)
    with use_specific_runtime_catalog(catalog):
        samples = _synthetic_daily_samples()
    review = ContentReviewAgent().review(samples)
    findings = tuple(
        ContentValidationFinding(
            rule_id=finding.rule_id,
            severity=finding.severity,
            path=(f"synthetic.{finding.persona_id}.{finding.surface}.{finding.section}"),
            message="Bản đọc tổng hợp chưa qua gate trải nghiệm người mới.",
        )
        for finding in review.findings
    )
    return ContentValidationReceipt(
        validator_version=CONTENT_RELEASE_VALIDATOR_VERSION,
        payload_hash=static_receipt.payload_hash,
        passed=not any(item.severity in {"critical", "high"} for item in findings),
        findings=findings,
    )


def _synthetic_daily_samples() -> tuple[ReviewSample, ...]:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    samples: list[ReviewSample] = []
    for index, sign in enumerate(tuple(ZodiacSign)[:SYNTHETIC_PERSONA_COUNT]):
        chart = _date_only(sign) if index % 2 == 0 else _full_chart(index)
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            background_lens=_LENSES[index % len(_LENSES)],
            editorial_seed=(date(2026, 9, 29) + timedelta(days=index)).isoformat(),
        )
        candidate = renderer.render(plan)
        evaluation = evaluate_candidate(plan, candidate)
        samples.append(
            ReviewSample(
                persona_id=f"persona-{index + 1:02d}",
                surface="daily",
                sections=(
                    ("hook", candidate.hook),
                    ("scene", candidate.manifestation),
                    ("action", candidate.micro_action),
                ),
                disclaimer=candidate.disclaimer,
                provenance_ids=tuple(claim.factor_ref for claim in candidate.evidence.claims),
                evidence_validated=evaluation.accepted,
            )
        )
    return tuple(samples)


def _date_only(sign: ZodiacSign) -> DateOnlySunResult:
    return DateOnlySunResult(
        status="certain",
        sign=sign,
        candidates=(sign,),
        provenance=EngineProvenance(version="synthetic", profile="content-studio"),
    )


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
