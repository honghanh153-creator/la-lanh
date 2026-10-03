from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from pydantic import JsonValue

from app.domains.content_rewrite.models import RewriteSurface
from app.domains.content_rewrite.registry import canonical_surface_registry


@dataclass(frozen=True, slots=True)
class SurfaceOutputContract:
    schema: dict[str, Any]
    max_output_tokens: int
    developer_instruction: str


_ARRAY_FIELDS = {
    "section_intros",
    "examples",
    "strengths",
    "frictions",
}

_SURFACE_MAPPING_INSTRUCTIONS = {
    RewriteSurface.REVEAL: (
        "Map headline from source hook, synthesis from source thesis, section_intros from "
        "source manifestation, and examples from source micro_action."
    ),
    RewriteSurface.NATAL: (
        "Map headline from source hook, synthesis from source thesis, section_intros from "
        "source manifestation, and examples from source micro_action. Keep the supplied "
        "multi-factor meaning; never reduce it to one placement."
    ),
    RewriteSurface.TRANSIT_INSIGHT: (
        "Map hook from source hook, explanation from source thesis, everyday_example from "
        "source manifestation, and bounded_action from source micro_action. Keep natal and "
        "current-transit meanings distinct."
    ),
    RewriteSurface.TAROT: (
        "Write exactly one position_reading for each supplied position_key, in the same order. "
        "Each reading must name its supplied card_title and explain what that card means in that "
        "specific position. Use synthesis to answer the fixed focus_sentence without predicting."
    ),
    RewriteSurface.RADAR: (
        "Map overview from source overview, strengths from source strength, frictions from source "
        "friction, asymmetry from source asymmetry, and prompt from source prompt. Keep every "
        "score, direction, uncertainty and evidence boundary unchanged. Do not add compatibility "
        "percentages, fate claims, surveillance, manipulation, or tests of another person."
    ),
    RewriteSurface.MATCHING: (
        "Use only the supplied anonymous relationship dimensions. Do not identify the candidate, "
        "change ranking, invent compatibility percentages, or imply that a match will succeed."
    ),
    RewriteSurface.SHARE_CARD: (
        "Rewrite only the supplied approved public headline and summary. Do not reveal hidden "
        "evidence, private context, birth data, names, identifiers, or unpublished source prose."
    ),
    RewriteSurface.RECAP: (
        "Summarize only the supplied recorded activity summaries. Do not invent an action, mood, "
        "relationship event, result, or streak that is absent from the brief."
    ),
}


def surface_output_contract(surface: RewriteSurface) -> SurfaceOutputContract:
    spec = canonical_surface_registry().require(surface)
    properties: dict[str, Any] = {}
    for field in spec.rewritable_fields:
        if field == "position_readings":
            properties[field] = {
                "type": "array",
                "minItems": 1,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["position_key", "reading"],
                    "properties": {
                        "position_key": {"type": "string", "maxLength": 40},
                        "reading": {"type": "string", "maxLength": 900},
                    },
                },
            }
        elif field in _ARRAY_FIELDS:
            properties[field] = {
                "type": "array",
                "minItems": 1,
                "maxItems": 8,
                "items": {"type": "string", "maxLength": 700},
            }
        else:
            properties[field] = {"type": "string", "maxLength": 900}
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": list(spec.rewritable_fields),
        "properties": properties,
    }
    tokens = min(1_800, max(220, spec.word_budget * 3))
    instruction = (
        "Rewrite only the requested Vietnamese prose fields from the closed safe brief. "
        "Use plain everyday Vietnamese. Preserve every supplied meaning and distinction. "
        "Do not infer identity, private facts, diagnoses, predictions, urgency, or decisions. "
        f"{_SURFACE_MAPPING_INSTRUCTIONS.get(surface, '')} "
        "Return only JSON matching the schema."
    )
    return SurfaceOutputContract(
        schema=schema,
        max_output_tokens=tokens,
        developer_instruction=instruction,
    )


def validate_surface_output(surface: RewriteSurface, output: object) -> dict[str, JsonValue] | None:
    if not isinstance(output, dict):
        return None
    spec = canonical_surface_registry().require(surface)
    if set(output) != set(spec.rewritable_fields):
        return None
    for field, value in output.items():
        if field == "position_readings":
            if not isinstance(value, list) or not 1 <= len(value) <= 5:
                return None
            for item in value:
                if not isinstance(item, dict) or set(item) != {"position_key", "reading"}:
                    return None
                if not all(isinstance(item[key], str) and item[key].strip() for key in item):
                    return None
        elif field in _ARRAY_FIELDS:
            if not isinstance(value, list) or not 1 <= len(value) <= 8:
                return None
            if not all(isinstance(item, str) and item.strip() for item in value):
                return None
        elif not isinstance(value, str) or not value.strip():
            return None
    return cast(dict[str, JsonValue], output)
