from uuid import UUID

from app.domains.astro.models import (
    RelationshipDimension,
    RelationshipDimensionEvidence,
)
from app.domains.matching.models import (
    EnergySlot,
    MatchingCandidate,
    MatchingRelationshipEvidence,
    WeeklyIntent,
)
from app.domains.matching.slate import select_weekly_slate


def _relationship_evidence(seed: int) -> MatchingRelationshipEvidence:
    strengths = {
        RelationshipDimension.COMMUNICATION: 0.55 + (seed % 4) * 0.1,
        RelationshipDimension.EMOTIONAL: 0.45 + (seed % 3) * 0.1,
        RelationshipDimension.RELATING: 0.50 + (seed % 2) * 0.1,
        RelationshipDimension.DRIVE: 0.40 + (seed % 5) * 0.08,
        RelationshipDimension.GROWTH: 0.48 + (seed % 4) * 0.08,
        RelationshipDimension.FRICTION: 0.35 + (seed % 3) * 0.12,
    }
    return MatchingRelationshipEvidence(
        dimensions=tuple(
            RelationshipDimensionEvidence(
                dimension=dimension,
                contact_count=1,
                evidence_ids=(f"synastry:{dimension.value}:{seed}",),
                strongest_strength=strength,
            )
            for dimension, strength in strengths.items()
        ),
        method_version="synastry-v2",
    )


def _candidate(seed: int, **overrides: bool | int) -> MatchingCandidate:
    values: dict[str, object] = {
        "candidate_id": UUID(int=seed),
        "active_verified": True,
        "reciprocal_preference_eligible": True,
        "safety_eligible": True,
        "intent_overlap": True,
        "prior_exposure_count": seed % 3,
        "relationship": _relationship_evidence(seed),
    }
    values.update(overrides)
    return MatchingCandidate.model_validate(values)


def test_slate_has_five_unique_people_and_five_distinct_energy_slots() -> None:
    result = select_weekly_slate(
        tuple(_candidate(seed) for seed in range(1, 9)),
        pool_key="2026-W38:hcm:dating",
    )

    assert result.low_pool is False
    assert len(result.cards) == 5
    assert len({card.candidate_id for card in result.cards}) == 5
    assert {card.energy_slot for card in result.cards} == set(EnergySlot)
    assert all(1 <= len(card.evidence_ids) <= 3 for card in result.cards)
    assert all(card.display_score_eligible is False for card in result.cards)


def test_hard_filters_run_before_any_slate_selection() -> None:
    candidates = (
        _candidate(1, safety_eligible=False),
        _candidate(2, reciprocal_preference_eligible=False),
        _candidate(3, active_verified=False),
        _candidate(4, intent_overlap=False),
        _candidate(5),
    )
    result = select_weekly_slate(candidates, pool_key="week-1")

    assert result.excluded_by_hard_filter == 4
    assert {card.candidate_id for card in result.cards} <= {UUID(int=5)}
    assert result.low_pool is True


def test_same_pool_version_is_deterministic() -> None:
    candidates = tuple(_candidate(seed) for seed in range(1, 12))
    first = select_weekly_slate(candidates, pool_key="stable-week")
    second = select_weekly_slate(tuple(reversed(candidates)), pool_key="stable-week")

    assert first == second


def test_weekly_intent_changes_slot_priority_not_hard_eligibility() -> None:
    candidates = (
        *(_candidate(seed) for seed in range(1, 12)),
        _candidate(99, safety_eligible=False),
    )
    result = select_weekly_slate(
        candidates,
        pool_key="intent-week",
        weekly_intent=WeeklyIntent.SLOW_PACE,
        requested_size=1,
    )

    assert result.cards[0].energy_slot is EnergySlot.SLOW_STEADY
    assert result.cards[0].candidate_id != UUID(int=99)


def test_low_evidence_returns_fewer_cards_instead_of_inventing_slots() -> None:
    relationship = MatchingRelationshipEvidence(
        dimensions=tuple(
            RelationshipDimensionEvidence(
                dimension=dimension,
                contact_count=0,
                evidence_ids=(),
            )
            for dimension in RelationshipDimension
        ),
        method_version="synastry-v2",
    )
    candidate = _candidate(1).model_copy(update={"relationship": relationship})

    result = select_weekly_slate((candidate,), pool_key="thin-week")

    assert result.cards == ()
    assert result.low_pool is True
    assert result.model_dump()["cards"] == ()
    assert result.model_dump().get("total_score") is None
    assert result.model_dump().get("compatibility_score") is None
