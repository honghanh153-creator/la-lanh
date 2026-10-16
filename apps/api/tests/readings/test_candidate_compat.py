"""Rollback floor for Lá's line: stored revisions vs the reader from before the field.

``LegacyReadingCandidate`` / ``LegacyCandidateEvaluation`` copy the models of
`collab/integration` @ 3d3107a (the last reader without ``companion``) field for field,
including ``extra="forbid"``. Nested models (evidence, blueprint, reports) did not change.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.domains.readings.companion import companion_issue_entry
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    SHORT_DISCLAIMER,
    CandidateEvaluation,
    EvidenceDisclosure,
    GateReport,
    ReadingPurpose,
    SemanticBlueprint,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.rewrite import GENERATED_COMPANION_SCHEMA_VERSION
from tests.readings.test_daily_psychology import _date_only


class LegacyReadingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "reading-candidate/v1"
    renderer_version: str = Field(min_length=1, max_length=64)
    plan_hash: str = Field(min_length=1, max_length=64)
    hook: str = Field(max_length=280)
    thesis: str = Field(max_length=700)
    manifestation: str = Field(max_length=700)
    transit: str | None = Field(default=None, max_length=500)
    micro_action: str = Field(max_length=500)
    evidence: EvidenceDisclosure
    disclaimer: str = SHORT_DISCLAIMER
    semantic_blueprint: SemanticBlueprint | None = None


class LegacyCandidateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted: bool
    reports: tuple[GateReport, ...]
    publishable_candidate: LegacyReadingCandidate | None = None

    @model_validator(mode="after")
    def validate_publication_state(self) -> LegacyCandidateEvaluation:
        if self.accepted != (self.publishable_candidate is not None):
            raise ValueError("publishable content exists exactly when evaluation is accepted")
        return self


def _evaluation(*, luna_line: bool = False) -> CandidateEvaluation:
    plan = ReadingPlanner().plan(
        _date_only(),
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=datetime(2026, 10, 14, tzinfo=UTC).date().isoformat(),
    )
    candidate = DeterministicVietnameseRenderer().render(plan)
    if luna_line:
        blueprint = candidate.semantic_blueprint
        assert blueprint is not None
        authored = companion_issue_entry(blueprint.mechanism_key).line.direct
        candidate = candidate.model_copy(
            update={
                "companion": f"Nè, {authored[:1].lower()}{authored[1:]}",
                "schema_version": GENERATED_COMPANION_SCHEMA_VERSION,
            }
        )
    evaluation = evaluate_candidate(plan, candidate)
    assert evaluation.accepted, evaluation.failure_codes
    return evaluation


def test_deterministic_revision_still_opens_in_the_pre_companion_reader() -> None:
    stored = _evaluation().model_dump_json(exclude_none=False)  # exactly as postgres stores it
    assert '"companion"' not in stored
    legacy = LegacyCandidateEvaluation.model_validate_json(stored)
    assert legacy.publishable_candidate is not None
    assert legacy.publishable_candidate.schema_version == "reading-candidate/v1"
    # And a revision written by the old reader opens in the new one.
    assert CandidateEvaluation.model_validate_json(legacy.model_dump_json()).publishable_candidate


def test_luna_revision_with_a_line_is_v2_and_needs_a_companion_reader() -> None:
    stored = _evaluation(luna_line=True).model_dump_json(exclude_none=False)
    current = CandidateEvaluation.model_validate_json(stored)
    assert current.publishable_candidate is not None
    assert current.publishable_candidate.schema_version == "reading-candidate/v2"
    assert current.publishable_candidate.companion
    # Documented rollback floor: a pre-companion reader cannot open v2 revisions, so an
    # environment that ever generated one keeps the companion reader on rollback.
    with pytest.raises(ValidationError):
        LegacyCandidateEvaluation.model_validate_json(stored)
