from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TarotContext(StrEnum):
    GENERAL = "general"
    RELATIONSHIPS = "relationships"
    WORK = "work"
    COMMUNICATION = "communication"
    ENERGY = "energy"
    SELF_CARE = "self_care"


class TarotSpread(StrEnum):
    ONE_CARD = "one_card"
    THREE_CARD = "three_card"
    FIVE_CARD = "five_card"


class TarotSpreadMap(StrEnum):
    ONE_FOCUS = "one_focus"
    THREE_UNBLOCK = "three_unblock"
    FIVE_CLARITY = "five_clarity"
    FIVE_LOOP = "five_loop"
    FIVE_CHOICE = "five_choice"
    FIVE_CONVERSATION = "five_conversation"


class TarotVoice(StrEnum):
    STRAIGHT_WARM = "straight_warm"
    GENTLE_SPECIFIC = "gentle_specific"
    PLAYFUL_GROUNDED = "playful_grounded"


class TarotQuestionIntent(StrEnum):
    CLARITY = "clarity"
    BOUNDARY = "boundary"
    NEXT_STEP = "next_step"
    COMMUNICATION = "communication"
    SELF_CHECK = "self_check"


class TarotSessionState(StrEnum):
    CHOOSING = "choosing"
    COMPLETE = "complete"


class TarotOrigin(StrEnum):
    DIRECT = "direct"
    DAILY = "daily"
    RADAR = "radar"


class TarotCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(
        pattern=r"^(?:major-[a-z-]+|(?:wands|cups|swords|pentacles)-(?:ace|[2-9]|10|page|knight|queen|king))$"
    )
    title_vi: str
    title_en: str
    arcana: str
    suit: str | None = None
    rank: str | None = None
    core: str
    tension: str
    resource: str
    source_concept_ids: tuple[str, ...]


class TarotBookSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    title: str
    authors: tuple[str, ...]
    official_url: str
    concept_ids: tuple[str, ...]
    allowed_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]


class TarotQuestionAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    accepted: bool
    normalized_question: str
    intent: TarotQuestionIntent | None = None
    rules_version: str = "tarot-question-rules-v1"
    explanation: str | None = None
    suggested_reframe: str | None = None


class TarotReadingPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    card: TarotCard
    meaning_here: str
    everyday_scene: str
    reflection_question: str
    small_action: str


class TarotReadingProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "tarot-reading/v1"
    knowledge_version: str = "tarot-knowledge-v2"
    renderer_version: str = "tarot-renderer-v1"
    gate_version: str = "tarot-gates-v1"
    deck_version: str = "tarot-78-v1"
    spread_version: str = "tarot-spreads-v1"
    question_rules_version: str = "tarot-question-rules-v1"
    methodology_version: str = "tarot-methodology-v1"
    source_ids: tuple[str, ...]
    draw_actor: str = "self"
    draw_purpose: str = "first_reading"


class TarotReading(BaseModel):
    model_config = ConfigDict(frozen=True)

    headline: str
    summary: str
    question: str
    question_intent: TarotQuestionIntent
    context: TarotContext
    spread: TarotSpread
    spread_map: TarotSpreadMap
    voice: TarotVoice
    positions: tuple[TarotReadingPosition, ...]
    closing_prompt: str
    disclaimer: str
    provenance: TarotReadingProvenance


class TarotSelectedCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    fan_index: int = Field(ge=0, lt=78)
    position_key: str
    position_label: str
    card: TarotCard


class TarotSessionView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    version: int = Field(ge=1)
    state: TarotSessionState
    context: TarotContext
    spread: TarotSpread
    spread_map: TarotSpreadMap
    voice: TarotVoice
    origin: TarotOrigin
    prompt_id: str | None = None
    question: str
    fan_size: int = 78
    required_cards: int = Field(ge=1, le=5)
    selected_cards: tuple[TarotSelectedCard, ...]
    reading: TarotReading | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
