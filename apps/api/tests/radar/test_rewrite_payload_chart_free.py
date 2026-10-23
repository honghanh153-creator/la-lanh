"""Luna sprint S2: the Hợp gu rewrite payload carries no chart facts.

Before, each evidence item sent technical labels (planet, other planet, aspect, house). The Radar
prompt only maps the supplied section meanings, so the labels add nothing for Luna and kept Radar
outside the chart-free rule (config CHART_FREE_REWRITE_SURFACES).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.radar.reading import build_radar_reading
from app.domains.radar.rewrite import compile_radar_rewrite_request
from app.domains.relationships.models import RelationshipVoice
from scripts.variety_baseline import RADAR_CONTEXTS, _radar_chart

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/variety/radar-pairs-v1.json"
CHART_TERMS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune",
    "pluto", "chiron", "true_node", "mean_node", "south_node", "ascendant", "midheaven",
    "mặt trời", "mặt trăng", "sao thủy", "sao thuỷ", "sao kim", "sao hỏa", "sao hoả",
    "sao mộc", "sao thổ", "thiên vương", "hải vương", "diêm vương", "nút bắc", "nút nam",
    "conjunction", "trine", "sextile", "square", "opposition",
    "tam hợp", "lục hợp", "đối đỉnh", "trùng tụ",
)  # fmt: skip


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for key, item in value.items() for s in (*_strings(key), *_strings(item))]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    return []


@pytest.fixture(scope="module")
def payloads() -> list[dict[str, object]]:
    engine = NatalChartEngine()
    pairs = json.loads(FIXTURES.read_text())["pairs"][:12]
    out: list[dict[str, object]] = []
    for pair in pairs:
        bundle = engine.calculate_relationship_bundle(
            _radar_chart(engine, pair["a"]), _radar_chart(engine, pair["b"])
        )
        for context in RADAR_CONTEXTS:
            reading = build_radar_reading(
                bundle, context=context, voice=RelationshipVoice.STRAIGHT_WARM
            )
            request = compile_radar_rewrite_request(
                uuid4(), uuid4(), "owner", reading, context=context,
                model_version="gpt-6-luna", prompt_version="test",
            )  # fmt: skip
            if request is not None:
                out.append(dict(request.safe_payload))
    assert len(out) >= 30
    return out


def test_evidence_items_carry_no_technical_labels(payloads: list[dict[str, object]]) -> None:
    for payload in payloads:
        evidence = payload["evidence"]
        assert isinstance(evidence, list) and evidence
        for item in evidence:
            assert isinstance(item, dict)
            assert not item.get("labels")
            assert item["confidence"] in {"limited", "medium", "high"}


def test_no_planet_aspect_or_house_name_anywhere_in_the_payload(
    payloads: list[dict[str, object]],
) -> None:
    for payload in payloads:
        for text in _strings(payload):
            low = text.casefold()
            for term in CHART_TERMS:
                assert not re.search(rf"(?<![\w]){re.escape(term)}(?![\w])", low), (term, text[:80])
