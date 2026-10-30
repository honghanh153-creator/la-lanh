"""Codex r55 on #118: honest fit selection and the readable contract on assembled rewrites.

1. A theme that is not "good" never gets the unqualified positive headline, reason or
   "Điều trôi chảy" paragraph (a sole strong Mercury-Moon square; a pair with no good theme).
2. A rewrite of a tiered (readable) result is checked as the page will show it: at most 400
   visible words, no astrology jargon in the default view, no sentence repeated across fields or
   layers. A rejected rewrite leaves the deterministic result (``None`` here).
"""

from __future__ import annotations

import re
from typing import Any, cast

import pytest

from app.domains.astro.models import BodyName, RelationshipDimension
from app.domains.radar import reading as radar
from app.domains.radar.rewrite import rewrite_radar_projection
from tests.content_rewrite.test_radar_rewrite import _projection, _valid_output
from tests.radar.test_reading import _contact, _default_view, _with_contacts

CONTEXTS = ("crush", "friend", "partner", "someone")
POSITIVE_HEADLINES = {
    text for by_context in radar.HEADLINES.values() for text in by_context.values()
}
POSITIVE_FIT = {text for by_context in radar.FIT_COPY.values() for text in by_context.values()}


def _sole_square() -> Any:
    return _with_contacts(
        _contact(
            BodyName.MERCURY, BodyName.MOON, "square", 0.90, RelationshipDimension.COMMUNICATION
        )
    )


def _no_good_theme() -> Any:
    return _with_contacts(
        _contact(
            BodyName.MERCURY, BodyName.MOON, "sextile", 0.30, RelationshipDimension.COMMUNICATION
        ),
        _contact(BodyName.VENUS, BodyName.MARS, "sextile", 0.30, RelationshipDimension.EMOTIONAL),
    )


def _fit_section(result: dict[str, Any]) -> dict[str, Any]:
    return next(section for section in result["sections"] if section["key"] == "fit")


@pytest.mark.parametrize("context", CONTEXTS)
def test_a_watch_theme_is_never_presented_as_easy_fit(context: str) -> None:
    bundle = _sole_square()
    signals = radar.pair_signals(bundle)
    assert signals is not None
    assert signals.fit is None or signals.levels[signals.fit.key] == "good"
    result = radar.build_radar_reading(bundle, context=context)
    assert result["pair_signature"]["headline"] not in POSITIVE_HEADLINES
    fit = _fit_section(result)
    assert fit["body"] not in POSITIVE_FIT and fit["label"] != "Điều trôi chảy"
    assert "dễ nói cho nhau hiểu" not in " ".join(_default_view(result))
    # The tension stays classified and shown.
    assert any(section["key"] == "friction" for section in result["sections"])


@pytest.mark.parametrize("context", CONTEXTS)
def test_a_pair_without_any_good_theme_gets_no_positive_claim(context: str) -> None:
    bundle = _no_good_theme()
    signals = radar.pair_signals(bundle)
    assert signals is not None
    assert all(level != "good" for level in signals.levels.values())
    result = radar.build_radar_reading(bundle, context=context)
    assert result["pair_signature"]["headline"] not in POSITIVE_HEADLINES
    assert _fit_section(result)["body"] not in POSITIVE_FIT
    positive_reasons = {
        reason.format(fit=plain)
        for reason in radar.TIER_REASONS.values()
        for plain in radar.THEME_PLAIN.values()
    }
    assert result["pair_signature"]["summary"] not in positive_reasons


def test_a_good_theme_keeps_its_positive_copy() -> None:
    bundle = _with_contacts(
        _contact(
            BodyName.MERCURY, BodyName.MOON, "trine", 0.95, RelationshipDimension.COMMUNICATION
        )
    )
    signals = radar.pair_signals(bundle)
    assert signals is not None and signals.fit is not None
    assert signals.levels[signals.fit.key] == "good"
    result = radar.build_radar_reading(bundle, context="partner")
    assert result["pair_signature"]["headline"] in POSITIVE_HEADLINES
    assert _fit_section(result)["label"] == "Điều trôi chảy"


def test_a_rewrite_cannot_repeat_the_visible_headline() -> None:
    baseline = _projection()
    output: Any = _valid_output(baseline)
    signature = baseline["pair_signature"]
    assert isinstance(signature, dict)
    output["overview"] = f"{signature['headline']} {baseline['summary']}"
    assert rewrite_radar_projection(baseline, output, context="crush") is None


def test_a_rewrite_cannot_push_the_default_view_past_400_words() -> None:
    baseline = _projection()
    output: Any = _valid_output(baseline)
    output["strengths"] = [
        f"{output['strengths'][0]} "
        + " ".join(f"Một điều nhỏ thứ {n} hai bạn có thể thử." for n in range(60))
    ]
    candidate = rewrite_radar_projection(baseline, output, context="crush")
    assert candidate is None or (
        len(re.findall(r"[^\W_]+", " ".join(_default_view(candidate)))) <= 400
    )
    assert candidate is None


def test_a_rewrite_cannot_bring_astrology_jargon_into_the_default_view() -> None:
    baseline = _projection()
    output: Any = _valid_output(baseline)
    output["prompt"] = f"{output['prompt']} Góc vuông giữa sao Thủy và Mặt Trăng nói vậy."
    assert rewrite_radar_projection(baseline, output, context="crush") is None


def test_a_clean_rewrite_of_the_same_result_is_still_accepted() -> None:
    baseline = _projection()
    assert (
        rewrite_radar_projection(baseline, cast(Any, _valid_output(baseline)), context="crush")
        is not None
    )
