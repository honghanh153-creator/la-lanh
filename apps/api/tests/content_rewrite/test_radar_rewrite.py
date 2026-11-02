from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from pydantic import JsonValue

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput
from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    content_rewrite_receipt_id,
)
from app.domains.content_rewrite.polarity import negates_source_claim
from app.domains.radar.reading import build_radar_reading
from app.domains.radar.rewrite import (
    NO_FRICTION_MEANING,
    RADAR_REWRITE_RENDERER_VERSION,
    _section_meaning,
    _tokens,
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


# The S3 polarity regressions (Codex #72) were written against a fit chapter that named its theme
# and carried a caution. The gate is text-generic, so they keep running on that exact wording,
# placed in the current projection's fit body.
GATE_FIT = (
    "Điểm dễ đi cùng nhất nằm ở sức hút và cách thể hiện sự thích. Phần dưới chỉ ra lúc nó giúp "
    "hai người vào nhịp và đi cùng nhau trong đời thường. Hai nhịp có sẵn đường để đi cùng mà "
    "không cần cố quá nhiều."
)


def _gate_projection() -> dict[str, object]:
    projection = _projection()
    _section(projection, "fit")["body"] = GATE_FIT
    return projection


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
    tier = json.loads(json.dumps(baseline["pair_signature"]["tier"], ensure_ascii=False))  # type: ignore[index]
    areas = json.loads(json.dumps(baseline["pair_signature"]["areas"], ensure_ascii=False))  # type: ignore[index]
    evidence_ids = list(baseline["metadata"]["evidence_ids"])  # type: ignore[index]

    candidate = rewrite_radar_projection(
        baseline,
        cast(dict[str, JsonValue], _valid_output(baseline)),
    )

    assert candidate is not None
    assert candidate["compatibility_map"] == compatibility
    assert candidate["pair_signature"]["tier"] == tier  # type: ignore[index]
    assert candidate["pair_signature"]["areas"] == areas  # type: ignore[index]
    assert candidate["disclaimer"] == baseline["disclaimer"]
    assert candidate["metadata"]["evidence_ids"] == evidence_ids  # type: ignore[index]
    assert candidate["metadata"]["renderer_version"] == RADAR_REWRITE_RENDERER_VERSION  # type: ignore[index]


def test_radar_rewrite_rejects_fate_probability_and_manipulation_copy() -> None:
    baseline = _projection()
    output = _valid_output(baseline)
    output["overview"] = "Hai người chắc chắn yêu nhau với tỷ lệ thành công 90%."

    assert rewrite_radar_projection(baseline, cast(dict[str, JsonValue], output)) is None

    output = _valid_output(baseline)
    output["prompt"] = "Hãy thử lòng bằng cách theo dõi họ trong vài ngày."
    assert rewrite_radar_projection(baseline, cast(dict[str, JsonValue], output)) is None


# --- Luna sprint S3: Radar merge gates on par with Tarot -------------------------------------


def _rewrite(baseline: dict[str, object], output: dict[str, object], context: str = "crush"):  # type: ignore[no-untyped-def]
    return rewrite_radar_projection(baseline, cast(dict[str, JsonValue], output), context=context)


def test_radar_rewrite_rejects_a_negated_source_claim() -> None:
    baseline = _gate_projection()
    output = _valid_output(baseline)
    output["strengths"] = [
        "Không nên tin vào sức hút và cách thể hiện sự thích; điểm dễ đi cùng nhất không nằm ở đó."
    ]
    assert _rewrite(baseline, output) is None


def test_an_unrelated_caution_does_not_exempt_a_reversed_fit_claim() -> None:
    """Codex #72 P2-1: the source caution "Hai nhịp có sẵn đường để đi cùng mà không cần cố quá
    nhiều" shares only "cùng"/"không" with this reversal, which is not the same claim."""

    baseline = _gate_projection()
    output = _valid_output(baseline)
    output["strengths"] = [
        "Không nên cho rằng điểm dễ đi cùng nhất nằm ở sức hút và cách thể hiện sự thích."
    ]
    assert _rewrite(baseline, output) is None


def test_an_introduction_cannot_lend_a_caution_to_a_reversed_fit_claim() -> None:
    """Codex #72 P2 @ 86971f6: words before the comma ("đường", "nhịp") matched the source
    caution and exempted the reversal after it. The plain reversal was already refused."""

    baseline = _gate_projection()
    for text in (
        "Đừng xem sức hút và cách thể hiện sự thích là điểm dễ đi cùng nhất.",
        "Trên đường tìm nhịp chung, đừng xem sức hút và cách thể hiện sự thích là điểm dễ đi "
        "cùng nhất.",
        "Trên đường tìm nhịp chung đừng xem sức hút và cách thể hiện sự thích là điểm dễ đi "
        "cùng nhất.",
        "Trên đường tìm nhịp chung, hai nhịp có sẵn đường, đừng xem sức hút là điểm dễ đi cùng "
        "nhất.",
        "Sức hút và cách thể hiện sự thích, đừng xem là điểm dễ đi cùng nhất.",
    ):
        output = _valid_output(baseline)
        output["strengths"] = [text]
        assert _rewrite(baseline, output) is None, text


def test_restating_a_source_caution_is_still_accepted() -> None:
    """Genuine restatements of the source caution "Hai nhịp có sẵn đường để đi cùng mà không
    cần cố quá nhiều", with and without a comma, keep the exemption."""

    baseline = _gate_projection()
    fit = _section_meaning(_section(baseline, "fit"))
    for control in (
        "Hai nhịp có sẵn đường để đi cùng mà không cần cố quá nhiều.",
        "Không cần cố quá nhiều, hai nhịp vẫn có sẵn đường để đi cùng.",
    ):
        # Each control reaches the exemption: without the caution it would be refused.
        assert negates_source_claim(fit, control, _tokens, caution_tokens=lambda _: set())
        output = _valid_output(baseline)
        output["strengths"] = [control]
        assert _rewrite(baseline, output) is not None, control


def test_radar_rewrite_rejects_mind_reading_and_judgement_labels() -> None:
    baseline = _gate_projection()
    for text in (
        "Người kia chắc chắn đang để ý bạn qua sức hút và cách thể hiện sự thích.",
        "Họ đang nghĩ về bạn nhiều hơn bạn tưởng, sức hút và cách thể hiện sự thích rất rõ.",
        "Đây là một red flag về sức hút và cách thể hiện sự thích giữa hai người.",
    ):
        output = _valid_output(baseline)
        output["strengths"] = [text]
        assert _rewrite(baseline, output) is None, text


def test_radar_rewrite_keeps_the_chosen_relationship_context() -> None:
    baseline = _projection()  # rendered for context "crush"
    output = _valid_output(baseline)
    output["overview"] = f"Với người yêu của bạn, {baseline['summary']}"
    assert _rewrite(baseline, output, context="crush") is None
    assert _rewrite(baseline, _valid_output(baseline), context="crush") is not None


def test_self_reference_is_not_a_friendship_context() -> None:
    """Codex #72 P2-2: "bản thân" (oneself) is not "bạn thân" (close friend)."""

    baseline = _projection()  # rendered for context "crush"
    for extra in (
        " Bạn có thể bắt đầu từ điều bản thân cần.",
        " BẢN THÂN bạn cũng cần được nghe.",
        " Nếu bạn là người yêu cầu gặp, hãy hỏi một câu rõ.",
    ):
        output = _valid_output(baseline)
        output["prompt"] = f"{output['prompt']}{extra}"
        assert _rewrite(baseline, output, context="crush") is not None, extra


def test_another_relationship_context_is_still_refused() -> None:
    baseline = _projection()
    for extra in (
        " Hỏi bạn thân của bạn trước khi nhắn.",
        " Bạn Thân của bạn có thể góp ý.",
        unicodedata.normalize("NFD", " Hỏi bạn thân trước."),
        " Hãy nói với nửa kia điều bạn cần.",
    ):
        output = _valid_output(baseline)
        output["prompt"] = f"{output['prompt']}{extra}"
        assert _rewrite(baseline, output, context="crush") is None, extra


def test_radar_rewrite_rejects_duplicate_items() -> None:
    baseline = _projection()
    output = _valid_output(baseline)
    fit = _section(baseline, "fit")["body"]
    output["strengths"] = [fit, fit]
    assert _rewrite(baseline, output) is None


def test_radar_rewrite_leaves_highlights_and_contact_lines_untouched() -> None:
    """Contact-specific sentences (R03) live in highlights; Luna rewrites section bodies only."""

    baseline = _projection()
    fit = _section(baseline, "fit")
    fit["highlights"] = [
        {
            "key": "fit:synthetic",
            "label": "x",
            "title": "x",
            "body": "x",
            "evidence_ids": ["syn:x"],
            "contact_lines": [{"text": "synthetic contact line", "evidence_id": "syn:x"}],
        }
    ]
    before = json.loads(json.dumps(fit["highlights"], ensure_ascii=False))
    candidate = _rewrite(baseline, _valid_output(baseline))
    assert candidate is not None
    assert _section(candidate, "fit")["highlights"] == before


# --- radar-readable-v2: the "cần để ý" paragraph is optional -----------------------------------


def _calm_projection() -> dict[str, object]:
    projection = _projection()
    sections = projection["sections"]
    assert isinstance(sections, list)
    projection["sections"] = [item for item in sections if item.get("key") != "friction"]
    return projection


def test_a_reading_without_friction_still_compiles_with_a_fixed_no_friction_meaning() -> None:
    request = compile_radar_rewrite_request(
        uuid4(),
        uuid4(),
        "owner",
        _calm_projection(),
        context="crush",
        model_version="gpt-6-luna",
        prompt_version="relationship-rewrite-v1",
    )
    assert request is not None
    source = cast(list[dict[str, str]], request.safe_payload["source_sections"])
    sections = {item["key"]: item["meaning"] for item in source}
    assert sections["friction"] == NO_FRICTION_MEANING


def test_rewritten_frictions_are_never_added_to_a_reading_without_one() -> None:
    baseline = _calm_projection()
    output = {
        "overview": baseline["summary"],
        "strengths": [_section(baseline, "fit")["body"]],
        "frictions": ["Không có điểm cần để ý nào nổi bật giữa hai bạn."],
        "asymmetry": _section(baseline, "perspective")["body"],
        "prompt": _section(baseline, "check")["body"],
    }
    candidate = _rewrite(baseline, output)
    assert candidate is not None
    sections = cast(list[dict[str, object]], candidate["sections"])
    metadata = cast(dict[str, object], candidate["metadata"])
    assert "friction" not in {item["key"] for item in sections}
    assert metadata["renderer_version"] == RADAR_REWRITE_RENDERER_VERSION

    output["frictions"] = ["Người kia chắc chắn đang giận bạn."]
    assert _rewrite(baseline, output) is None  # still gated, even though it is dropped


def test_a_previous_renderer_reading_without_tier_still_needs_its_friction() -> None:
    baseline = _calm_projection()
    del baseline["pair_signature"]["tier"]  # type: ignore[attr-defined]
    output = _valid_output(_projection())
    assert _rewrite(baseline, output) is None
