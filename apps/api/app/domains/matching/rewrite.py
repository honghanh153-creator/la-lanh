from __future__ import annotations

import json
import re
import unicodedata
from hashlib import sha256
from typing import cast
from uuid import UUID

from pydantic import JsonValue

from app.domains.astro.models import RelationshipDimension, RelationshipDimensionEvidence
from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    content_rewrite_receipt_id,
)
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.matching.models import (
    EnergySlot,
    MatchingCandidate,
    MatchingCardCopy,
    SlateCard,
)

MATCHING_REWRITE_RENDERER_VERSION = "gpt-6-luna-matching-v1"

_SLOT_MEANING = {
    EnergySlot.EASY_TRUTH: "Hai người có tín hiệu hỗ trợ một cuộc trò chuyện dễ nói thật hơn.",
    EnergySlot.DIFFERENT_RHYTHM: "Hai người có nhịp khác nhau đáng để hỏi rõ thay vì đoán.",
    EnergySlot.SLOW_STEADY: "Kết nối này hợp với cách làm quen chậm, đều và có phản hồi rõ.",
    EnergySlot.IDEA_SPARK: "Hai người có thể dễ bật ra ý tưởng hoặc góc nhìn mới khi nói chuyện.",
    EnergySlot.NEW_ANGLE: "Kết nối này có thể mở một góc khác với kiểu người bạn thường chú ý.",
}
_DIMENSION_MEANING = {
    RelationshipDimension.COMMUNICATION: "cách nói chuyện và hiểu ý có tín hiệu để bắt nhịp",
    RelationshipDimension.EMOTIONAL: "cách nhận ra cảm xúc có tín hiệu hỗ trợ sự an tâm",
    RelationshipDimension.RELATING: "cách cho và nhận sự quan tâm có điểm để kết nối",
    RelationshipDimension.DRIVE: "nhịp chủ động và phản ứng có lực kéo nhưng cần quan sát tốc độ",
    RelationshipDimension.GROWTH: "cách khích lệ và mở rộng góc nhìn có điểm để cùng thử",
    RelationshipDimension.FRICTION: (
        "khác biệt có thể lộ ra khi phản hồi, chủ động hoặc đặt ranh giới"
    ),
}
_STOP_WORDS = {
    "bạn",
    "một",
    "những",
    "điều",
    "này",
    "đang",
    "được",
    "trong",
    "và",
    "của",
    "cho",
    "với",
    "người",
}
_FORBIDDEN = (
    "định mệnh",
    "soulmate",
    "chắc chắn hợp",
    "tỉ lệ thành công",
    "tỷ lệ thành công",
    "thử lòng",
    "theo dõi họ",
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[^\W_]+", _fold(value))
        if len(token) >= 4 and token not in _STOP_WORDS
    }


def _band(value: float) -> str:
    if value < 0.34:
        return "low"
    if value < 0.67:
        return "medium"
    return "high"


def _card_token(pool_key: str, candidate_id: UUID) -> str:
    return sha256(f"{pool_key}\x00{candidate_id}".encode()).hexdigest()[:24]


def matching_rewrite_owner(
    guest_id: UUID,
    *,
    pool_key: str,
    candidate_id: UUID,
) -> ArtifactOwnerKey:
    pool_token = sha256(pool_key.encode()).hexdigest()[:20]
    return ArtifactOwnerKey(
        namespace="matching",
        key=f"matching|{guest_id}|{pool_token}|{_card_token(pool_key, candidate_id)}",
    )


def _ranked_dimensions(
    candidate: MatchingCandidate,
) -> list[RelationshipDimensionEvidence]:
    return sorted(
        (
            dimension
            for dimension in candidate.relationship.dimensions
            if dimension.contact_count > 0 and dimension.evidence_ids
        ),
        key=lambda item: (item.strongest_strength, item.dimension.value),
        reverse=True,
    )


def _source_meanings(
    card: SlateCard,
    candidate: MatchingCandidate,
) -> dict[str, str] | None:
    ranked = _ranked_dimensions(candidate)
    if not ranked:
        return None
    strengths = [item for item in ranked if item.dimension is not RelationshipDimension.FRICTION]
    friction = next(
        (item for item in ranked if item.dimension is RelationshipDimension.FRICTION),
        ranked[-1],
    )
    strongest = strengths[0] if strengths else ranked[0]
    return {
        "overview": _SLOT_MEANING[card.energy_slot],
        "strength": _DIMENSION_MEANING[strongest.dimension],
        "friction": _DIMENSION_MEANING[friction.dimension],
        "asymmetry": (
            "Dữ liệu matching hiện chưa có chiều cảm nhận riêng của từng người; "
            "không được đoán ai thích nhiều hơn."
        ),
        "prompt": (
            "Câu mở đầu nên hỏi về một trải nghiệm gần đây, dễ trả lời và không dò xét đời tư."
        ),
    }


def compile_matching_rewrite_request(
    guest_id: UUID,
    *,
    pool_key: str,
    card: SlateCard,
    candidate: MatchingCandidate,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope | None:
    if (
        card.candidate_id != candidate.candidate_id
        or not candidate.active_verified
        or not candidate.reciprocal_preference_eligible
        or not candidate.safety_eligible
        or not candidate.intent_overlap
    ):
        return None
    meanings = _source_meanings(card, candidate)
    ranked = _ranked_dimensions(candidate)
    if meanings is None or not ranked:
        return None
    dimensions = [
        {
            "dimension": (
                "friction" if item.dimension is RelationshipDimension.FRICTION else "coordination"
            ),
            "band": _band(item.strongest_strength),
            "direction": "mutual",
            "meaning_keys": [item.dimension.value],
        }
        for item in ranked[:8]
    ]
    evidence: list[dict[str, JsonValue]] = [
        {
            "label": f"signal_{index}",
            "source": "relationship",
            "kind": "dimension_evidence",
            "domain": item.dimension.value,
            "role": "supporting",
            "confidence": (
                "high"
                if item.strongest_strength >= 0.75
                else "medium"
                if item.strongest_strength >= 0.45
                else "limited"
            ),
            "labels": [],
        }
        for index, item in enumerate(ranked[:16], start=1)
    ]
    source_sections = [{"key": key, "meaning": meaning} for key, meaning in meanings.items()]
    blueprint = {
        "energy_slot": card.energy_slot.value,
        "evidence_ids": list(card.evidence_ids),
        "method_version": card.relationship_method_version,
        "meanings": meanings,
    }
    blueprint_hash = sha256(
        json.dumps(blueprint, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    spec = canonical_surface_registry().require(RewriteSurface.MATCHING)
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.MATCHING,
            owner=matching_rewrite_owner(
                guest_id,
                pool_key=pool_key,
                candidate_id=candidate.candidate_id,
            ),
            blueprint_hash=blueprint_hash,
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=spec.schema_version,
            gate_version=spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(
            guest_id,
            scope=RewriteConsentScope.MATCHING,
        ),
        safe_payload={
            "context": "matching",
            "low_signal": False,
            "dimensions": cast(JsonValue, dimensions),
            "source_sections": cast(JsonValue, source_sections),
            "evidence": cast(JsonValue, evidence),
        },
    )


def rewrite_matching_card(
    card: SlateCard,
    candidate: MatchingCandidate,
    output: dict[str, JsonValue],
) -> MatchingCardCopy | None:
    if set(output) != {"card_summary", "strengths", "frictions", "icebreaker"}:
        return None
    summary = output.get("card_summary")
    strengths = output.get("strengths")
    frictions = output.get("frictions")
    icebreaker = output.get("icebreaker")
    if (
        not isinstance(summary, str)
        or not summary.strip()
        or not isinstance(strengths, list)
        or not 1 <= len(strengths) <= 3
        or not all(isinstance(item, str) and item.strip() for item in strengths)
        or not isinstance(frictions, list)
        or not 1 <= len(frictions) <= 3
        or not all(isinstance(item, str) and item.strip() for item in frictions)
        or not isinstance(icebreaker, str)
        or not icebreaker.strip()
    ):
        return None
    meanings = _source_meanings(card, candidate)
    if meanings is None:
        return None
    strength_texts = cast(list[str], strengths)
    friction_texts = cast(list[str], frictions)
    texts = [summary, *strength_texts, *friction_texts, icebreaker]
    folded = " ".join(_fold(item) for item in texts)
    if any(_fold(term) in folded for term in _FORBIDDEN):
        return None
    if re.search(r"\b\d{1,3}\s*(?:%|/\s*100)\b", folded):
        return None
    if len(re.findall(r"[^\W_]+", " ".join(texts))) > 420:
        return None
    if len(_tokens(summary) & _tokens(meanings["overview"])) < 2:
        return None
    if not all(len(_tokens(item) & _tokens(meanings["strength"])) >= 1 for item in strength_texts):
        return None
    if not all(len(_tokens(item) & _tokens(meanings["friction"])) >= 1 for item in friction_texts):
        return None
    if len(_tokens(icebreaker) & _tokens(meanings["prompt"])) < 1:
        return None
    return MatchingCardCopy(
        candidate_id=card.candidate_id,
        energy_slot=card.energy_slot,
        card_summary=summary.strip(),
        strengths=tuple(item.strip() for item in strength_texts),
        frictions=tuple(item.strip() for item in friction_texts),
        icebreaker=icebreaker.strip(),
        evidence_ids=card.evidence_ids,
        relationship_method_version=card.relationship_method_version,
        renderer_version=MATCHING_REWRITE_RENDERER_VERSION,
    )
