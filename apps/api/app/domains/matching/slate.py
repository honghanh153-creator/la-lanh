"""Deterministic five-energy slate selection.

The selector never sees birth data, profile text, mood, chat, popularity or a
compatibility total. It consumes already-authorized relationship evidence only
after reciprocal preference and safety eligibility have passed.
"""

from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from app.domains.astro.engine import summarize_synastry_dimensions
from app.domains.astro.models import (
    RelationshipDimension,
    RelationshipDimensionEvidence,
    SynastryFacts,
)
from app.domains.matching.models import (
    EnergySlot,
    MatchingCandidate,
    MatchingRelationshipEvidence,
    SlateCard,
    SlateResult,
    WeeklyIntent,
)

SLATE_ALGORITHM_VERSION = "vong-la-slate-v1"


@dataclass(frozen=True)
class _SlotPolicy:
    weights: tuple[tuple[RelationshipDimension, float], ...]
    required: tuple[RelationshipDimension, ...]


_SLOT_POLICIES: dict[EnergySlot, _SlotPolicy] = {
    EnergySlot.EASY_TRUTH: _SlotPolicy(
        weights=(
            (RelationshipDimension.COMMUNICATION, 0.65),
            (RelationshipDimension.EMOTIONAL, 0.35),
        ),
        required=(RelationshipDimension.COMMUNICATION,),
    ),
    EnergySlot.DIFFERENT_RHYTHM: _SlotPolicy(
        weights=(
            (RelationshipDimension.DRIVE, 0.45),
            (RelationshipDimension.FRICTION, 0.35),
            (RelationshipDimension.RELATING, 0.20),
        ),
        required=(RelationshipDimension.FRICTION, RelationshipDimension.DRIVE),
    ),
    EnergySlot.SLOW_STEADY: _SlotPolicy(
        weights=(
            (RelationshipDimension.GROWTH, 0.55),
            (RelationshipDimension.EMOTIONAL, 0.45),
        ),
        required=(RelationshipDimension.GROWTH,),
    ),
    EnergySlot.IDEA_SPARK: _SlotPolicy(
        weights=(
            (RelationshipDimension.COMMUNICATION, 0.45),
            (RelationshipDimension.GROWTH, 0.35),
            (RelationshipDimension.DRIVE, 0.20),
        ),
        required=(RelationshipDimension.COMMUNICATION, RelationshipDimension.GROWTH),
    ),
    EnergySlot.NEW_ANGLE: _SlotPolicy(
        weights=(
            (RelationshipDimension.FRICTION, 0.35),
            (RelationshipDimension.GROWTH, 0.35),
            (RelationshipDimension.RELATING, 0.30),
        ),
        required=(RelationshipDimension.GROWTH, RelationshipDimension.RELATING),
    ),
}

_INTENT_SLOT_ORDER: dict[WeeklyIntent, tuple[EnergySlot, ...]] = {
    WeeklyIntent.EASY_TALK: (
        EnergySlot.EASY_TRUTH,
        EnergySlot.IDEA_SPARK,
        EnergySlot.SLOW_STEADY,
        EnergySlot.DIFFERENT_RHYTHM,
        EnergySlot.NEW_ANGLE,
    ),
    WeeklyIntent.SLOW_PACE: (
        EnergySlot.SLOW_STEADY,
        EnergySlot.EASY_TRUTH,
        EnergySlot.IDEA_SPARK,
        EnergySlot.NEW_ANGLE,
        EnergySlot.DIFFERENT_RHYTHM,
    ),
    WeeklyIntent.NEW_ANGLE: (
        EnergySlot.NEW_ANGLE,
        EnergySlot.DIFFERENT_RHYTHM,
        EnergySlot.IDEA_SPARK,
        EnergySlot.EASY_TRUTH,
        EnergySlot.SLOW_STEADY,
    ),
    WeeklyIntent.LET_LA_BALANCE: tuple(EnergySlot),
}


def matching_evidence_from_synastry(synastry: SynastryFacts) -> MatchingRelationshipEvidence:
    """Project strict Synastry into pre-mutual evidence without deeper pair charts."""
    return MatchingRelationshipEvidence(
        dimensions=summarize_synastry_dimensions(synastry),
        method_version=synastry.method_version,
    )


def select_weekly_slate(
    candidates: tuple[MatchingCandidate, ...],
    *,
    pool_key: str,
    weekly_intent: WeeklyIntent = WeeklyIntent.LET_LA_BALANCE,
    requested_size: int = 5,
) -> SlateResult:
    if not pool_key.strip():
        raise ValueError("pool_key is required for stable weekly rotation")
    if requested_size < 1 or requested_size > 5:
        raise ValueError("requested_size must be between 1 and 5")

    eligible = tuple(candidate for candidate in candidates if _passes_hard_filters(candidate))
    selected: list[SlateCard] = []
    used_candidates: set[UUID] = set()
    slot_order = _INTENT_SLOT_ORDER[weekly_intent]

    for slot in slot_order:
        if len(selected) >= requested_size:
            break
        ranked: list[tuple[float, int, MatchingCandidate, tuple[str, ...]]] = []
        for candidate in eligible:
            if candidate.candidate_id in used_candidates:
                continue
            score, evidence_ids = _slot_fit(candidate.relationship, slot)
            if score is None or not evidence_ids:
                continue
            fairness_adjusted = score - min(candidate.prior_exposure_count, 10) * 0.03
            ranked.append(
                (
                    fairness_adjusted,
                    _stable_rotation(pool_key, slot, str(candidate.candidate_id)),
                    candidate,
                    evidence_ids,
                )
            )
        if not ranked:
            continue
        _, _, winner, evidence_ids = max(ranked, key=lambda item: (item[0], item[1]))
        selected.append(
            SlateCard(
                candidate_id=winner.candidate_id,
                energy_slot=slot,
                evidence_ids=evidence_ids,
                relationship_method_version=winner.relationship.method_version,
            )
        )
        used_candidates.add(winner.candidate_id)

    return SlateResult(
        cards=tuple(selected),
        requested_size=requested_size,
        low_pool=len(selected) < requested_size,
        weekly_intent=weekly_intent,
        algorithm_version=SLATE_ALGORITHM_VERSION,
        excluded_by_hard_filter=len(candidates) - len(eligible),
    )


def _passes_hard_filters(candidate: MatchingCandidate) -> bool:
    return all(
        (
            candidate.active_verified,
            candidate.reciprocal_preference_eligible,
            candidate.safety_eligible,
            candidate.intent_overlap,
        )
    )


def _slot_fit(
    relationship: MatchingRelationshipEvidence,
    slot: EnergySlot,
) -> tuple[float | None, tuple[str, ...]]:
    policy = _SLOT_POLICIES[slot]
    by_dimension = {item.dimension: item for item in relationship.dimensions}
    if not all(_has_evidence(by_dimension.get(dimension)) for dimension in policy.required):
        return None, ()

    fit = 0.0
    evidence: list[str] = []
    for dimension, weight in policy.weights:
        dimension_evidence = by_dimension.get(dimension)
        if dimension_evidence is None:
            continue
        fit += dimension_evidence.strongest_strength * weight
        for evidence_id in dimension_evidence.evidence_ids:
            if evidence_id not in evidence:
                evidence.append(evidence_id)
            if len(evidence) == 3:
                break
    return fit, tuple(evidence[:3])


def _has_evidence(value: RelationshipDimensionEvidence | None) -> bool:
    return bool(value and value.contact_count > 0 and value.evidence_ids)


def _stable_rotation(pool_key: str, slot: EnergySlot, candidate_id: str) -> int:
    payload = f"{SLATE_ALGORITHM_VERSION}:{pool_key}:{slot.value}:{candidate_id}"
    return int.from_bytes(sha256(payload.encode()).digest()[:8], "big")
