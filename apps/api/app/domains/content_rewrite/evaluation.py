from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.content_rewrite.models import RewriteSurface


class CorpusSegment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: RewriteSurface
    count: int = Field(ge=1, le=1_000)


class FixedCorpusManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1, max_length=80)
    synthetic_only: bool
    total_cases: int = Field(ge=1, le=10_000)
    segments: tuple[CorpusSegment, ...]

    @model_validator(mode="after")
    def validate_counts(self) -> FixedCorpusManifest:
        surfaces = tuple(segment.surface for segment in self.segments)
        if len(surfaces) != len(set(surfaces)):
            raise ValueError("corpus surfaces must be unique")
        if sum(segment.count for segment in self.segments) != self.total_cases:
            raise ValueError("corpus segment counts must equal total_cases")
        if not self.synthetic_only:
            raise ValueError("rewrite evaluation corpus must contain synthetic data only")
        return self

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(
            f"{segment.surface.value}-{index:04d}"
            for segment in self.segments
            for index in range(1, segment.count + 1)
        )


class HumanScores(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    comprehension: int = Field(ge=1, le=5)
    natural_vietnamese: int = Field(ge=1, le=5)
    recognisable_situation: int = Field(ge=1, le=5)
    action_linkage: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    return_value: int = Field(ge=1, le=5)

    @property
    def mean(self) -> float:
        return (
            sum(
                (
                    self.comprehension,
                    self.natural_vietnamese,
                    self.recognisable_situation,
                    self.action_linkage,
                    self.specificity,
                    self.return_value,
                )
            )
            / 6
        )


class EvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(pattern=r"^[a-z_]+-[0-9]{4}$")
    surface: RewriteSurface
    baseline: HumanScores
    candidate: HumanScores
    gate_passed: bool
    failure_codes: tuple[str, ...] = ()
    frame_fingerprint: str = Field(min_length=8, max_length=64)

    @model_validator(mode="after")
    def validate_gate_shape(self) -> EvaluationRecord:
        if self.gate_passed and self.failure_codes:
            raise ValueError("passing evaluations cannot contain failure codes")
        if not self.gate_passed and not self.failure_codes:
            raise ValueError("failed evaluations require a failure code")
        if not self.case_id.startswith(f"{self.surface.value}-"):
            raise ValueError("case_id must belong to its surface")
        return self


class SurfaceEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: RewriteSurface
    case_count: int
    comprehension_rate: float
    relevance_rate: float
    duplicate_frame_rate: float
    baseline_mean: float
    candidate_mean: float
    gate_failures: int
    passed: bool


class ReleaseEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    corpus_version: str
    passed: bool
    findings: tuple[str, ...]
    surfaces: tuple[SurfaceEvaluation, ...]


def load_manifest(path: Path) -> FixedCorpusManifest:
    return FixedCorpusManifest.model_validate_json(path.read_text(encoding="utf-8"))


def load_records(path: Path) -> tuple[EvaluationRecord, ...]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("evaluation results must be a JSON array")
    return tuple(EvaluationRecord.model_validate(row) for row in rows)


def evaluate_release(
    manifest: FixedCorpusManifest,
    records: tuple[EvaluationRecord, ...],
) -> ReleaseEvaluation:
    expected = set(manifest.case_ids)
    actual = {record.case_id for record in records}
    findings: list[str] = []
    if len(actual) != len(records):
        findings.append("duplicate_case_id")
    if actual != expected:
        findings.append("corpus_coverage_mismatch")

    surface_results: list[SurfaceEvaluation] = []
    for segment in manifest.segments:
        items = tuple(record for record in records if record.surface is segment.surface)
        denominator = max(len(items), 1)
        comprehension_rate = sum(item.candidate.comprehension >= 4 for item in items) / denominator
        relevance_rate = (
            sum(
                item.candidate.recognisable_situation >= 4 and item.candidate.action_linkage >= 4
                for item in items
            )
            / denominator
        )
        duplicate_rate = (
            len(items) - len({item.frame_fingerprint for item in items})
        ) / denominator
        baseline_mean = sum(item.baseline.mean for item in items) / denominator
        candidate_mean = sum(item.candidate.mean for item in items) / denominator
        gate_failures = sum(not item.gate_passed for item in items)
        duplicate_limit = (
            0.05
            if segment.surface
            in {
                RewriteSurface.DAILY_HOME,
                RewriteSurface.DAILY_DETAIL,
            }
            else 0.10
        )
        passed = (
            len(items) == segment.count
            and comprehension_rate >= 0.90
            and relevance_rate >= 0.85
            and duplicate_rate < duplicate_limit
            and gate_failures == 0
            and candidate_mean > baseline_mean
        )
        if not passed:
            findings.append(f"surface_threshold_failed:{segment.surface.value}")
        surface_results.append(
            SurfaceEvaluation(
                surface=segment.surface,
                case_count=len(items),
                comprehension_rate=comprehension_rate,
                relevance_rate=relevance_rate,
                duplicate_frame_rate=duplicate_rate,
                baseline_mean=baseline_mean,
                candidate_mean=candidate_mean,
                gate_failures=gate_failures,
                passed=passed,
            )
        )
    return ReleaseEvaluation(
        corpus_version=manifest.version,
        passed=not findings,
        findings=tuple(dict.fromkeys(findings)),
        surfaces=tuple(surface_results),
    )
