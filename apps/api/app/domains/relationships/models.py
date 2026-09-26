from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.domains.astro.models import RelationshipDimension


class EvidenceClass(StrEnum):
    RELATIONSHIP_PSYCHOLOGY = "relationship_psychology"
    DATING_DECISION_SCIENCE = "dating_decision_science"
    COMMUNICATION_PRACTICE = "communication_practice"
    ASTROLOGY_TRADITION = "astrology_tradition"


class RelationshipVoice(StrEnum):
    """Explicit delivery preference; never inferred from chart or behaviour."""

    STRAIGHT_WARM = "straight_warm"
    GENTLE_SPECIFIC = "gentle_specific"
    PLAYFUL_GROUNDED = "playful_grounded"
    DEEP_DIVE = "deep_dive"


class BookSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    title: str
    authors: tuple[str, ...]
    evidence_class: EvidenceClass
    official_url: str
    concept_ids: tuple[str, ...]
    allowed_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]


class EditorialConcept(BaseModel):
    model_config = ConfigDict(frozen=True)

    concept_id: str
    label: str
    source_ids: tuple[str, ...]
    dimensions: tuple[RelationshipDimension, ...]
    prompt_pattern: str
    safety_boundary: str


class VoiceProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice: RelationshipVoice
    label: str
    description: str
    sentence_budget: tuple[int, int]
    slang_budget: int
    required_moves: tuple[str, ...]
    prohibited_moves: tuple[str, ...]


class RelationshipPrompt(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: RelationshipDimension
    concept_id: str
    source_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    label: str
    prompt_pattern: str
    safety_boundary: str


class RelationshipEditorialPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    knowledge_version: str
    voice_profile: VoiceProfile
    prompts: tuple[RelationshipPrompt, ...]
    disclaimer: str
