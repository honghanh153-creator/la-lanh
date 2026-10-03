from pathlib import Path

from app.domains.content_rewrite.evaluation import (
    EvaluationRecord,
    HumanScores,
    evaluate_release,
    load_manifest,
)
from app.domains.content_rewrite.models import RewriteSurface
from app.domains.content_rewrite.registry import canonical_surface_registry

MANIFEST = Path(__file__).parents[1] / "fixtures" / "content_rewrite" / "corpus_manifest.json"


def _scores(value: int) -> HumanScores:
    return HumanScores(
        comprehension=value,
        natural_vietnamese=value,
        recognisable_situation=value,
        action_linkage=value,
        specificity=value,
        return_value=value,
    )


def test_fixed_corpus_has_670_synthetic_cases_and_every_registered_surface() -> None:
    manifest = load_manifest(MANIFEST)

    assert manifest.synthetic_only is True
    assert len(manifest.case_ids) == 670
    assert len(set(manifest.case_ids)) == 670
    assert {segment.surface for segment in manifest.segments} == set(
        canonical_surface_registry().surfaces
    )


def test_release_gate_requires_complete_better_safe_and_diverse_results() -> None:
    manifest = load_manifest(MANIFEST)
    records = tuple(
        EvaluationRecord(
            case_id=case_id,
            surface=RewriteSurface(case_id.rsplit("-", 1)[0]),
            baseline=_scores(3),
            candidate=_scores(5),
            gate_passed=True,
            frame_fingerprint=f"frame-{index:04d}",
        )
        for index, case_id in enumerate(manifest.case_ids, start=1)
    )

    result = evaluate_release(manifest, records)

    assert result.passed is True
    assert result.findings == ()
    assert all(surface.passed for surface in result.surfaces)


def test_release_gate_fails_closed_for_missing_or_unsafe_results() -> None:
    manifest = load_manifest(MANIFEST)
    first_id = manifest.case_ids[0]
    result = evaluate_release(
        manifest,
        (
            EvaluationRecord(
                case_id=first_id,
                surface=RewriteSurface.DAILY_HOME,
                baseline=_scores(4),
                candidate=_scores(2),
                gate_passed=False,
                failure_codes=("unsupported_claim",),
                frame_fingerprint="repeated-frame",
            ),
        ),
    )

    assert result.passed is False
    assert "corpus_coverage_mismatch" in result.findings
    assert "surface_threshold_failed:daily_home" in result.findings
