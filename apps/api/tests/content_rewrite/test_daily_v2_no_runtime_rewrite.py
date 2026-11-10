"""PV-28: Daily v2 calls no LLM at run time, and no rewrite payload carries house or angle.

Daily v2 (``docs/plans/2026-11-02-daily-v2-content-quality-plan.md`` section 6) writes its pieces
offline; the app itself calls no LLM. A house or an angle follows from the birth time, so neither
may reach a third-party provider on any surface.
"""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from app.domains.content_rewrite import registry as rewrite_registry
from app.domains.content_rewrite.models import RewriteSurface
from app.domains.content_rewrite.rollout import RewriteRolloutMode, SurfaceRolloutPolicy
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.rewrite import compile_reading_rewrite_request
from app.infrastructure.generation.openai import _safe_payload as _legacy_safe_payload
from app.infrastructure.generation.privacy import PrivacyMinimiser, UnsafeRewritePayload
from tests.content_rewrite.test_reading_rewrite import _records


def test_daily_v2_detail_surface_is_excluded_from_runtime_rewrite() -> None:
    excluded = rewrite_registry.RUNTIME_REWRITE_EXCLUDED_SURFACES
    assert excluded == frozenset({RewriteSurface.DAILY_DETAIL})
    # The surface stays registered so a queued job still resolves and is closed as disabled.
    assert RewriteSurface.DAILY_DETAIL in rewrite_registry.canonical_surface_registry().surfaces


@pytest.mark.parametrize("mode", list(RewriteRolloutMode))
def test_daily_v2_detail_never_generates_whatever_the_rollout(mode: RewriteRolloutMode) -> None:
    policy = SurfaceRolloutPolicy({RewriteSurface.DAILY_DETAIL: mode})

    assert policy.should_generate(RewriteSurface.DAILY_DETAIL) is False


def test_full_rollout_for_all_still_skips_daily_v2_detail() -> None:
    policy = SurfaceRolloutPolicy.full_for_all()

    assert policy.should_generate(RewriteSurface.DAILY_DETAIL) is False
    # Other surfaces keep their behaviour.
    assert policy.should_generate(RewriteSurface.DAILY_HOME) is True
    assert policy.should_generate(RewriteSurface.TAROT) is True


@pytest.mark.parametrize("name", ["house", "angle"])
@pytest.mark.parametrize(
    "surface",
    [
        RewriteSurface.DAILY_DETAIL,
        RewriteSurface.NATAL,
        RewriteSurface.REVEAL,
        RewriteSurface.TRANSIT_INSIGHT,
        RewriteSurface.HOUSE_INSIGHT,
        RewriteSurface.MATCHING,
    ],
)
def test_outbound_allowlist_refuses_house_and_angle_labels(
    surface: RewriteSurface, name: str
) -> None:
    evidence = {
        "label": "factor_1",
        "source": "natal",
        "kind": "planet_placement",
        "domain": "communication",
        "role": "primary",
        "confidence": "high",
        "labels": [{"name": name, "value": "7"}],
    }
    if surface is RewriteSurface.MATCHING:
        payload: dict[str, object] = {
            "context": "crush",
            "dimensions": [
                {
                    "dimension": "friction",
                    "band": "medium",
                    "direction": "mutual",
                    "meaning_keys": ["friction"],
                }
            ],
            "source_sections": [
                {"key": key, "meaning": "Hỏi rõ một câu thay vì đoán ý."}
                for key in ("overview", "strength", "friction", "asymmetry", "prompt")
            ],
            "evidence": [{**evidence, "source": "relationship"}],
        }
    else:
        payload = {
            "purpose": "reading_detail",
            "precision": "exact",
            "mode": "standard",
            "hero_labels": ["factor_1"],
            "source_sections": [
                {"section": section, "meaning": "Một ý đã duyệt.", "source": "natal"}
                for section in ("hook", "thesis", "manifestation", "micro_action")
            ],
            "requirements": [{"key": "reading.focus", "markers": ["ý"]}],
            "evidence": [evidence],
        }

    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(surface, payload)


@pytest.mark.parametrize(
    "purpose",
    [ReadingPurpose.AURA, ReadingPurpose.READING_DETAIL, ReadingPurpose.PERSONALIZED_SKY],
)
def test_reading_compiler_drops_house_and_angle_labels(purpose: ReadingPurpose) -> None:
    plan_record, projection, _revision = _records(purpose)
    baseline = DeterministicVietnameseRenderer().render(plan_record.plan)

    request = compile_reading_rewrite_request(
        plan_record,
        projection,
        baseline,
        model_version="gpt-6-luna",
        prompt_version="surface-rewrite-v1",
    )

    evidence = cast(list[dict[str, Any]], request.safe_payload["evidence"])
    names = {label["name"] for item in evidence for label in item["labels"]}
    assert names.isdisjoint({"house", "angle"})
    serialized = json.dumps(request.safe_payload, ensure_ascii=False)
    assert '"name": "house"' not in serialized
    assert '"name": "angle"' not in serialized
    # Still a valid, minimised payload for its own surface.
    assert PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)


def test_legacy_generation_payload_drops_house_and_angle_labels() -> None:
    """The legacy Reading provider is network-disabled, but its payload builder must agree."""

    plan_record, _projection, _revision = _records(ReadingPurpose.READING_DETAIL)
    names = {
        label["name"]
        for factor in _legacy_safe_payload(plan_record.plan)["factors"]
        for label in factor["labels"]
    }
    assert names
    assert names.isdisjoint({"house", "angle", "houses_apart"})
