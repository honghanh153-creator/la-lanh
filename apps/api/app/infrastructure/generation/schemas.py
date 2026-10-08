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
    RewriteSurface.DAILY_HOME: (
        "Map title from title_meaning, scene from scene_meaning, and action from "
        "action_meaning. Scene must describe one ordinary observable moment. Action must "
        "start with a familiar Vietnamese action verb and stay connected to that moment. "
        "Honor the supplied requirement markers without mentioning astrology. Keep the title "
        "between 3 and 11 Vietnamese words, scene 8-40 words, action 4-24 words, total at most 70. "
        "Use meaning_brief.core_meaning to understand the situation and reader_takeaway to "
        "preserve its point. The scene is illustrative, NOT an observed fact about this user. "
        "Use conditional wording in the scene; do not claim it happened or will happen. "
        "Keep title, scene, action on the SAME situation. Do not add a new role, conflict, motive, "
        "or advice absent from the brief. Never turn reader_takeaway into another paragraph of "
        "abstract explanation. No advice in title or scene. No filler after action. "
        "Write direct everyday Vietnamese with a subject and a visible action. "
        "Never use a paradox, abstract comparison, or poetic metaphor. "
        "Example meaning: agreeing with the group while still having an unanswered question. "
        "title: 'Bạn gật đầu, nhưng vẫn chưa hiểu hết.' "
        "scene: 'Khi cả nhóm chốt rất nhanh, bạn có thể đồng ý theo dù vẫn còn một chỗ "
        "muốn hỏi lại.' "
        "action: 'Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?' "
        "Different meaning: editing an adequate draft instead of sending it for feedback. "
        "title: 'Bạn định gửi rồi, nhưng lại sửa thêm.' "
        "scene: 'Khi bản nháp đã đủ ý, bạn có thể vẫn sửa vài chữ vì lo người khác đánh giá.' "
        "action: 'Gửi bản nháp và nói rõ phần nào còn cần góp ý.' "
        "Examples teach style, not facts or sentences to copy into unrelated situations."
    ),
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
        "Use plain everyday Vietnamese that a Vietnamese student can understand on the first "
        "read. Sound like a smart close friend in their twenties: warm, direct, lightly playful, "
        "and serious when the subject is vulnerable. At most one lightly playful phrase per "
        "response; never force memes, slang, catchphrases, poetic metaphors, pseudo-profound "
        "paradoxes, or therapy jargon. Prefer a clear subject, verb, and observable situation. "
        "Preserve every supplied meaning and distinction. "
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
