from uuid import UUID, uuid4

from app.domains.astro.models import RelationshipDimension, RelationshipDimensionEvidence
from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    content_rewrite_receipt_id,
)
from app.domains.matching.models import (
    EnergySlot,
    MatchingCandidate,
    MatchingRelationshipEvidence,
    SlateCard,
)
from app.domains.matching.rewrite import (
    compile_matching_rewrite_request,
    rewrite_matching_card,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser


def _candidate() -> MatchingCandidate:
    return MatchingCandidate(
        candidate_id=UUID(int=12),
        active_verified=True,
        reciprocal_preference_eligible=True,
        safety_eligible=True,
        intent_overlap=True,
        relationship=MatchingRelationshipEvidence(
            dimensions=(
                RelationshipDimensionEvidence(
                    dimension=RelationshipDimension.COMMUNICATION,
                    contact_count=2,
                    evidence_ids=("synastry:communication:1",),
                    strongest_strength=0.81,
                ),
                RelationshipDimensionEvidence(
                    dimension=RelationshipDimension.FRICTION,
                    contact_count=1,
                    evidence_ids=("synastry:friction:1",),
                    strongest_strength=0.58,
                ),
            ),
            method_version="synastry-v2",
        ),
    )


def _card() -> SlateCard:
    return SlateCard(
        candidate_id=UUID(int=12),
        energy_slot=EnergySlot.EASY_TRUTH,
        evidence_ids=("synastry:communication:1", "synastry:friction:1"),
        relationship_method_version="synastry-v2",
    )


def test_matching_compiler_requires_hard_eligibility_and_sends_no_candidate_identity() -> None:
    guest_id = uuid4()
    request = compile_matching_rewrite_request(
        guest_id,
        pool_key="2026-W40:hcm:dating",
        card=_card(),
        candidate=_candidate(),
        model_version="gpt-6-luna",
        prompt_version="matching-rewrite-v1",
    )

    assert request is not None
    assert request.authorization_receipt_id == content_rewrite_receipt_id(
        guest_id,
        scope=RewriteConsentScope.MATCHING,
    )
    safe = PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    serialized = str(safe)
    assert str(guest_id) not in serialized
    assert str(_candidate().candidate_id) not in serialized
    assert "synastry:communication:1" not in serialized

    ineligible = _candidate().model_copy(update={"safety_eligible": False})
    assert (
        compile_matching_rewrite_request(
            guest_id,
            pool_key="2026-W40:hcm:dating",
            card=_card(),
            candidate=ineligible,
            model_version="gpt-6-luna",
            prompt_version="matching-rewrite-v1",
        )
        is None
    )


def test_matching_rewrite_preserves_candidate_and_evidence_without_score_claims() -> None:
    card = _card()
    copy = rewrite_matching_card(
        card,
        _candidate(),
        {
            "card_summary": "Hai người có tín hiệu hỗ trợ một cuộc trò chuyện dễ nói thật hơn.",
            "strengths": ["Cách nói chuyện có thể bắt nhịp khá nhanh."],
            "frictions": ["Khác biệt dễ lộ ra khi phản hồi hoặc đặt ranh giới."],
            "icebreaker": "Hỏi về một trải nghiệm gần đây mà cả hai đều dễ trả lời.",
        },
    )

    assert copy is not None
    assert copy.candidate_id == card.candidate_id
    assert copy.evidence_ids == card.evidence_ids

    rejected = rewrite_matching_card(
        card,
        _candidate(),
        {
            "card_summary": "Hai người chắc chắn hợp nhau 95%.",
            "strengths": ["Cách nói chuyện có thể bắt nhịp khá nhanh."],
            "frictions": ["Khác biệt dễ lộ ra khi phản hồi hoặc đặt ranh giới."],
            "icebreaker": "Hỏi về một trải nghiệm gần đây mà cả hai đều dễ trả lời.",
        },
    )
    assert rejected is None
