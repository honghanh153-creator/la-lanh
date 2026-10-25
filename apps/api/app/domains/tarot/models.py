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
    ROAST = "roast"


class TarotQuestionIntent(StrEnum):
    CLARITY = "clarity"
    BOUNDARY = "boundary"
    NEXT_STEP = "next_step"
    COMMUNICATION = "communication"
    SELF_CHECK = "self_check"


QUESTION_RULES_VERSION = "tarot-question-rules-v2"
# v2 (2026-10-22, audit T01): topic, action and goals read the asked clause, not background
# clauses ("sau lần nói chuyện…"). Stored v1 frames keep whole-question semantics.
QUESTION_FRAME_VERSION = "tarot-question-frame-v2"


class TarotQuestionForm(StrEnum):
    YES_NO = "yes_no"
    CHOICE = "choice"
    HOW = "how"
    WHY = "why"
    TIMING = "timing"  # answered as "what to have ready first" (AC05)
    OPEN = "open"


class TarotAction(StrEnum):
    """Closed action labels (US-20, owner decision A6)."""

    NHAN_LOI = "nhan_loi"
    TU_CHOI = "tu_choi"
    NOI_RA = "noi_ra"
    NHAN_LAI = "nhan_lai"
    HOI_LAI = "hoi_lai"
    CHO_THEM = "cho_them"
    BAT_DAU = "bat_dau"
    DUNG_LAI = "dung_lai"
    DOI_VIEC = "doi_viec"
    XIN_GOP_Y = "xin_gop_y"
    NGHI_NGOI = "nghi_ngoi"
    GUI_DI = "gui_di"
    XIN_LOI = "xin_loi"
    HEN_GAP = "hen_gap"
    CHIA_SE = "chia_se"
    DAT_RANH_GIOI = "dat_ranh_gioi"
    KET_THUC = "ket_thuc"
    THU_LAI = "thu_lai"
    HOC_THEM = "hoc_them"
    TAP_TRUNG = "tap_trung"
    SAP_XEP_LAI = "sap_xep_lai"
    NHO_GIUP = "nho_giup"
    GOP_Y = "gop_y"
    DE_XUAT = "de_xuat"
    DON_DEP = "don_dep"
    RA_NGOAI = "ra_ngoai"
    O_NHA = "o_nha"
    DOI_THOI_QUEN = "doi_thoi_quen"
    TU_THUONG = "tu_thuong"
    VIET_RA = "viet_ra"


class QuestionFrame(BaseModel):
    """Closed labels only; never a span of the user's text (US-20 AC06)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = QUESTION_FRAME_VERSION
    form: TarotQuestionForm
    topic: TarotContext
    action: TarotAction | None = None


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
    frame: QuestionFrame | None = None  # accepted questions only; never part of an API body
    rules_version: str = QUESTION_RULES_VERSION
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
    # Only step roles carry an action since B2-2 (US-20 AC07); legacy readings always have one.
    small_action: str | None = None


class TarotStanceKind(StrEnum):
    YES_NO = "yes_no"
    CHOICE = "choice"


class TarotStanceLevel(StrEnum):
    """Three levels of lean (no "lean to not doing it"), plus the choice fallback (US-20 AC08)."""

    LEAN_TRY = "lean_try"
    CONSIDER = "consider"
    UNCLEAR = "unclear"
    CLARIFY_CHOICE = "clarify_choice"


class TarotStanceReason(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    position_key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    card_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=400)


class TarotStance(BaseModel):
    """Lean computed from card labels and role weights (US-20 AC08/AC09, B2-3)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = "tarot-stance-v1"
    kind: TarotStanceKind
    level: TarotStanceLevel
    topic: TarotContext = TarotContext.GENERAL
    action: TarotAction | None = None
    options: tuple[TarotAction, TarotAction] | None = None
    conclusion: str = Field(min_length=1, max_length=300)
    reasons: tuple[TarotStanceReason, ...] = Field(default=(), max_length=2)


class TarotReadingProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "tarot-reading/v1"
    # US-20 AC18: no stale defaults. The engine writes these four on every reading (v4/v6/v4 and
    # rules v1 for sessions without a frame, v5/v7/v5 and rules v2 for framed ones), and every
    # stored reading since Tarot shipped (b391e66) carries them through model_dump.
    knowledge_version: str
    renderer_version: str
    gate_version: str
    deck_version: str = "tarot-78-v1"
    spread_version: str = "tarot-spreads-v1"
    question_rules_version: str
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
    # B2-3: lean for yes/no and choice questions of framed sessions. Readings without one
    # omit the key, so they serialize exactly as before B2-3 (stored and API bytes, AC17).
    stance: TarotStance | None = Field(default=None, exclude_if=lambda value: value is None)
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
