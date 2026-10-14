"""Roast voice never half-roasts a generated (Luna) Daily revision."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import JsonValue

from app.domains.astro.engine import NatalChartEngine
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.companion import companion_issue_entry
from app.domains.readings.models import (
    ReadingCandidate,
    ReadingProjection,
    ReadingPurpose,
    ReadingRevisionSource,
)
from app.domains.readings.rewrite import DailyRewriteProjector, compile_daily_rewrite_request
from app.domains.readings.voice import (
    DailySections,
    ReadingVoice,
    apply_content_voice,
    roast_daily_sections,
    voice_from_baseline,
)
from tests.readings.test_application import NOW, MemoryReadingRepository, _exact_snapshot

GUEST_ID = UUID("20000000-0000-4000-8000-000000000501")
PROFILE_ID = UUID("30000000-0000-4000-8000-000000000501")


def luna_companion(baseline: ReadingCandidate) -> str:
    """A Luna-style paraphrase that keeps the card's nudge (differs from the authored line)."""

    blueprint = baseline.semantic_blueprint
    authored = companion_issue_entry(blueprint.mechanism_key if blueprint else None).line.direct
    return f"Nè, {authored[:1].lower()}{authored[1:]}"


def _rewrite_output(baseline: ReadingCandidate) -> dict[str, JsonValue]:
    """A gate-passing Luna-style rewrite whose title/scene/action differ from the baseline."""

    scene = baseline.manifestation.rstrip(".")
    action = baseline.micro_action
    return {
        "title": "Bạn nhận lời trước, rồi mới thấy khó.",
        "scene": f"{scene} trước đã.",
        "action": f"Ghi lại điều này: {action[:1].lower()}{action[1:]}",
        "companion": luna_companion(baseline),
    }


def _sections(projection: ReadingProjection) -> DailySections:
    sections = projection.active.sections
    return DailySections(
        sections.hook, sections.thesis, sections.manifestation, sections.micro_action
    )


async def _generated_active() -> tuple[
    MemoryReadingRepository, ReadingApplicationService, ReadingProjection, ReadingProjection
]:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    snapshot = _exact_snapshot(GUEST_ID, PROFILE_ID, engine)
    deterministic = await service.project(
        guest_id=GUEST_ID,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    baseline_record = repository.revisions[(GUEST_ID, PROFILE_ID, deterministic.active.revision_id)]
    baseline = baseline_record.evaluation.publishable_candidate
    assert baseline is not None
    plan_record = await repository.get_plan(GUEST_ID, PROFILE_ID, baseline_record.plan_id)
    projection_record = await repository.get_projection(
        GUEST_ID, PROFILE_ID, deterministic.scope_key
    )
    assert plan_record is not None and projection_record is not None
    request = compile_daily_rewrite_request(
        plan_record,
        projection_record,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v3",
    )
    decision = await DailyRewriteProjector(repository).validate_and_project(
        request, _rewrite_output(baseline), completed_at=NOW
    )
    assert decision.accepted, decision.failure_code
    available = await service.project(
        guest_id=GUEST_ID,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    assert available.available_update is not None
    assert available.available_update.content.source is ReadingRevisionSource.GENERATED
    activated = await service.activate(
        guest_id=GUEST_ID,
        profile_id=PROFILE_ID,
        scope_key=available.scope_key,
        expected_revision_id=available.available_update.revision_id,
        updated_at=NOW,
    )
    assert activated.active.source is ReadingRevisionSource.GENERATED
    return repository, service, deterministic, activated


@pytest.mark.asyncio
async def test_roast_over_generated_serves_the_whole_roasted_baseline_not_a_mix() -> None:
    repository, service, deterministic, generated = await _generated_active()
    roast = await service.project(
        guest_id=GUEST_ID,
        snapshot=_exact_snapshot(GUEST_ID, PROFILE_ID, NatalChartEngine()),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        voice=ReadingVoice.ROAST,
    )

    expected = roast_daily_sections(_sections(deterministic))
    assert expected != _sections(deterministic)
    assert _sections(roast) == expected
    # No generated sentence leaks into the roast card.
    generated_sections = generated.active.sections
    for value in (
        generated_sections.hook,
        generated_sections.manifestation,
        generated_sections.micro_action,
    ):
        assert value not in " ".join(
            (
                roast.active.sections.hook,
                roast.active.sections.manifestation,
                roast.active.sections.micro_action,
            )
        )
    assert roast.active.sections.transit == deterministic.active.sections.transit
    assert roast.active.source is ReadingRevisionSource.DETERMINISTIC
    # Identity stays bound to the active generated revision: activation, experiments,
    # saves and resonance keep their existing semantics.
    assert roast.scope_key == generated.scope_key
    assert roast.active.revision_id == generated.active.revision_id
    assert roast.active.evidence == generated.active.evidence
    assert roast.active.disclaimer == generated.active.disclaimer
    assert roast.available_update is None
    assert generated.active.experiment is not None and roast.active.experiment is not None
    assert roast.active.experiment.action_key == generated.active.experiment.action_key
    assert roast.active.experiment.action == roast.active.sections.micro_action
    # Nothing was persisted for the voice.
    stored = repository.revisions[(GUEST_ID, PROFILE_ID, generated.active.revision_id)]
    candidate = stored.evaluation.publishable_candidate
    assert candidate is not None
    assert candidate.hook == generated_sections.hook


@pytest.mark.asyncio
async def test_direct_over_generated_is_the_unchanged_generated_text() -> None:
    _, service, _, generated = await _generated_active()
    direct = await service.project(
        guest_id=GUEST_ID,
        snapshot=_exact_snapshot(GUEST_ID, PROFILE_ID, NatalChartEngine()),
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        voice=ReadingVoice.DIRECT,
    )

    assert direct == generated
    assert direct.active.source is ReadingRevisionSource.GENERATED
    assert direct.active.sections.hook == "Bạn nhận lời trước, rồi mới thấy khó."


@pytest.mark.asyncio
async def test_roast_over_deterministic_is_unchanged_roast_behaviour() -> None:
    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    service = ReadingApplicationService(repository, engine)
    snapshot = _exact_snapshot(GUEST_ID, PROFILE_ID, engine)
    direct = await service.project(
        guest_id=GUEST_ID, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE, requested_at=NOW
    )
    roast = await service.project(
        guest_id=GUEST_ID,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
        voice=ReadingVoice.ROAST,
    )

    assert roast.active == apply_content_voice(direct.active, ReadingVoice.ROAST)
    assert _sections(roast) == roast_daily_sections(_sections(direct))
    assert roast.active.source is ReadingRevisionSource.DETERMINISTIC
    assert roast.active.revision_id == direct.active.revision_id


@pytest.mark.asyncio
async def test_roast_without_a_usable_baseline_keeps_the_generated_text_whole() -> None:
    _, _, deterministic, generated = await _generated_active()
    content = generated.active

    # Direct voicing helpers never touch generated wording on their own.
    assert apply_content_voice(content, ReadingVoice.ROAST) is content
    assert voice_from_baseline(content, None, ReadingVoice.ROAST) is content
    # A generated "baseline" is not a baseline.
    assert voice_from_baseline(content, content, ReadingVoice.ROAST) is content
    # A deterministic baseline with no authored roast wording is not substituted.
    unvoiced = deterministic.active.model_copy(
        update={
            "sections": deterministic.active.sections.model_copy(
                update={
                    "hook": "Một câu chưa có giọng Cà khịa.",
                    "thesis": "Một luận điểm chưa có trong ma trận.",
                    "micro_action": "Ghi một điều nhỏ.",
                }
            )
        }
    )
    assert voice_from_baseline(content, unvoiced, ReadingVoice.ROAST) is content
