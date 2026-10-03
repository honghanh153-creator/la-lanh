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
