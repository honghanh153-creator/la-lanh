"""Luna sprint S2: the Hợp gu rewrite payload carries no chart facts.

Before, each evidence item sent technical labels (planet, other planet, aspect, house). The Radar
prompt only maps the supplied section meanings, so the labels add nothing for Luna and kept Radar
outside the chart-free rule (config CHART_FREE_REWRITE_SURFACES).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.content_rewrite.models import RewriteRequestEnvelope, RewriteSurface
from app.domains.radar.reading import build_radar_reading
from app.domains.radar.rewrite import compile_radar_rewrite_request, radar_blueprint_hash
from app.domains.relationships.models import RelationshipVoice
from app.infrastructure.generation.privacy import PrivacyMinimiser
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


@dataclass(frozen=True)
class Compiled:
    pair: dict[str, Any]
    guest_id: UUID
    request_id: UUID
    stored: dict[str, object]  # the reading as the Radar row keeps it
    before: str  # canonical JSON of the reading before compiling
    request: RewriteRequestEnvelope


@pytest.fixture(scope="module")
def compiled() -> list[Compiled]:
    engine = NatalChartEngine()
    pairs = json.loads(FIXTURES.read_text())["pairs"][:12]
    out: list[Compiled] = []
    for pair in pairs:
        bundle = engine.calculate_relationship_bundle(
            _radar_chart(engine, pair["a"]), _radar_chart(engine, pair["b"])
        )
        for context in RADAR_CONTEXTS:
            reading = build_radar_reading(
                bundle, context=context, voice=RelationshipVoice.STRAIGHT_WARM
            )
            before = json.dumps(reading, ensure_ascii=False, sort_keys=True)
            guest_id, request_id = uuid4(), uuid4()
            request = compile_radar_rewrite_request(
                guest_id, request_id, "owner", reading, context=context,
                model_version="gpt-6-luna", prompt_version="test",
            )  # fmt: skip
            if request is not None:
                out.append(Compiled(pair, guest_id, request_id, reading, before, request))
    assert len(out) >= 30
    return out


@pytest.fixture(scope="module")
def payloads(compiled: list[Compiled]) -> list[dict[str, object]]:
    return [dict(item.request.safe_payload) for item in compiled]


def test_evidence_items_carry_no_technical_labels(payloads: list[dict[str, object]]) -> None:
    for payload in payloads:
        evidence = payload["evidence"]
        assert isinstance(evidence, list) and evidence
        for item in evidence:
            assert isinstance(item, dict)
            assert not item.get("labels")
            assert item["kind"] == "relationship_signal"
            assert item["confidence"] in {"limited", "medium", "high"}


def test_no_planet_aspect_or_house_name_anywhere_in_the_payload(
    payloads: list[dict[str, object]],
) -> None:
    for payload in payloads:
        for text in _strings(payload):
            low = text.casefold()
            for term in CHART_TERMS:
                assert not re.search(rf"(?<![\w]){re.escape(term)}(?![\w])", low), (term, text[:80])


def test_payload_is_only_approved_meanings_and_levels(payloads: list[dict[str, object]]) -> None:
    """Section meanings come from the engine's approved reading; the rest is closed levels."""

    for payload in payloads:
        assert set(payload) == {
            "context",
            "low_signal",
            "dimensions",
            "source_sections",
            "evidence",
        }
        for dimension in payload["dimensions"]:  # type: ignore[attr-defined]
            assert set(dimension) == {"dimension", "band", "direction", "meaning_keys"}
            assert dimension["band"] in {"low", "medium", "high"}
        keys = [section["key"] for section in payload["source_sections"]]  # type: ignore[attr-defined]
        assert keys == ["overview", "strength", "friction", "asymmetry", "prompt"]


def test_minimiser_accepts_every_payload_unchanged(payloads: list[dict[str, object]]) -> None:
    for payload in payloads:
        safe = PrivacyMinimiser().minimise(RewriteSurface.RADAR, payload)
        evidence = safe.pop("evidence")
        assert isinstance(evidence, list)
        # The contract adds an empty default; nothing else is added, dropped or rewritten.
        assert all(isinstance(item, dict) and item.pop("labels") == [] for item in evidence)
        assert {**safe, "evidence": evidence} == payload


def test_privacy_canary_no_birth_data_or_identifier_reaches_the_payload(
    compiled: list[Compiled],
) -> None:
    for item in compiled:
        text = json.dumps(item.request.safe_payload, ensure_ascii=False).casefold()
        canaries = [str(item.guest_id), str(item.request_id), "recipient", "birth"]
        for person in (item.pair["a"], item.pair["b"]):
            canaries += [
                person["id"], person["birth_date"], person["birth_time_local"], person["place"],
                str(person["latitude"]), str(person["longitude"]),
            ]  # fmt: skip
        for canary in filter(None, canaries):
            assert canary.casefold() not in text, canary


def test_stored_reading_and_provenance_are_untouched(compiled: list[Compiled]) -> None:
    """Readings already given to people stay frozen: compiling never edits the stored reading,
    which still keeps its local technical receipts, and the job key still matches its hash, so
    the projector's stale-version check accepts it."""

    for item in compiled:
        assert json.dumps(item.stored, ensure_ascii=False, sort_keys=True) == item.before
        assert item.request.key.blueprint_hash == radar_blueprint_hash(item.stored)
        assert item.stored["metadata"]["renderer_version"] == "radar-living-dossier-v1"  # type: ignore[index]
    receipts = [
        receipt
        for item in compiled
        for section in item.stored["sections"]  # type: ignore[attr-defined]
        for receipt in section.get("evidence", [])
    ]
    assert any(
        isinstance(receipt.get("technical"), dict) and receipt["technical"].get("body_a")
        for receipt in receipts
    )
