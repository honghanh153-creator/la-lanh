from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput
from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    content_rewrite_receipt_id,
)
from app.domains.radar.reading import build_radar_reading
from app.domains.radar.rewrite import (
    RADAR_REWRITE_RENDERER_VERSION,
    compile_radar_rewrite_request,
    rewrite_radar_projection,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser


def _projection() -> dict[str, object]:
    engine = NatalChartEngine()
    first = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 5, 15, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        )
    )
    second = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1992, 7, 21, 12, 40, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    return build_radar_reading(
        engine.calculate_relationship_bundle(first, second),
        context="crush",
    )


def _section(projection: dict[str, object], key: str) -> dict[str, object]:
    sections = projection["sections"]
    assert isinstance(sections, list)
    return next(item for item in sections if isinstance(item, dict) and item.get("key") == key)


def _valid_output(projection: dict[str, object]) -> dict[str, object]:
    return {
        "overview": projection["summary"],
        "strengths": [_section(projection, "fit")["body"]],
        "frictions": [_section(projection, "friction")["body"]],
        "asymmetry": _section(projection, "perspective")["body"],
        "prompt": _section(projection, "check")["body"],
    }


def test_radar_compiler_forwards_only_anonymous_derived_relationship_meaning() -> None:
    guest_id = uuid4()
    request = compile_radar_rewrite_request(
        guest_id,
        uuid4(),
        "owner",
        _projection(),
        context="crush",
        model_version="gpt-6-luna",
        prompt_version="relationship-rewrite-v1",
    )

    assert request is not None
    assert request.authorization_receipt_id == content_rewrite_receipt_id(
        guest_id,
        scope=RewriteConsentScope.RADAR,
    )
    safe = PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    serialized = json.dumps(safe, ensure_ascii=False).casefold()
    assert str(guest_id) not in serialized
    assert "birth" not in serialized
    assert "recipient" not in serialized
    assert "1990-" not in serialized
    assert set(safe) == {
        "context",
        "low_signal",
        "dimensions",
        "source_sections",
        "evidence",
    }


def test_radar_rewrite_preserves_scores_evidence_and_domain_structure() -> None:
    baseline = _projection()
    compatibility = json.loads(json.dumps(baseline["compatibility_map"], ensure_ascii=False))
    evidence_ids = list(baseline["metadata"]["evidence_ids"])  # type: ignore[index]

    candidate = rewrite_radar_projection(baseline, _valid_output(baseline))

    assert candidate is not None
    assert candidate["compatibility_map"] == compatibility
    assert candidate["metadata"]["evidence_ids"] == evidence_ids  # type: ignore[index]
    assert candidate["metadata"]["renderer_version"] == RADAR_REWRITE_RENDERER_VERSION  # type: ignore[index]


def test_radar_rewrite_rejects_fate_probability_and_manipulation_copy() -> None:
    baseline = _projection()
    output = _valid_output(baseline)
    output["overview"] = "Hai người chắc chắn yêu nhau với tỷ lệ thành công 90%."

    assert rewrite_radar_projection(baseline, output) is None

    output = _valid_output(baseline)
    output["prompt"] = "Hãy thử lòng bằng cách theo dõi họ trong vài ngày."
    assert rewrite_radar_projection(baseline, output) is None
