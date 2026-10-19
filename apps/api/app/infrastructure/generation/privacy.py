from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError, model_validator

from app.domains.content_rewrite.models import RewriteSurface
from app.domains.readings.models import DailyMeaningBrief
from app.domains.tarot.models import TarotAction, TarotStanceKind, TarotStanceLevel


class UnsafeRewritePayload(ValueError):
    """The payload could not be proven safe for an external rewrite provider."""


class SafeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SafeLabel(SafeModel):
    name: Literal[
        "body",
        "sign",
        "house",
        "aspect",
        "other_body",
        "angle",
        "phase",
        "motion",
    ]
    value: str = Field(min_length=1, max_length=64)


class SafeEvidence(SafeModel):
    label: str = Field(pattern=r"^(?:factor|signal)_[1-9][0-9]{0,2}$")
    source: Literal["natal", "transit", "relationship", "tarot", "activity"]
    kind: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    domain: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    role: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    confidence: Literal["limited", "medium", "high"]
    phase: Literal["approaching", "exact", "separating"] | None = None
    labels: tuple[SafeLabel, ...] = Field(default=(), max_length=8)


class SafeRequirement(SafeModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9._-]{1,95}$")
    section: Literal["all", "hook", "thesis", "manifestation", "transit", "micro_action"] = "all"
    markers: tuple[str, ...] = Field(min_length=1, max_length=12)
    min_matches: int = Field(default=1, ge=1, le=4)


class DailySafePayload(SafeModel):
    context: Literal["general", "relationships", "communication", "work", "energy"]
    scene_key: str = Field(pattern=r"^[a-z][a-z0-9:._-]{1,95}$")
    action_key: str = Field(pattern=r"^[a-z][a-z0-9:._-]{1,95}$")
    title_meaning: str = Field(min_length=1, max_length=280)
    scene_meaning: str = Field(min_length=1, max_length=700)
    action_meaning: str = Field(min_length=1, max_length=500)
    # Editorial brief for Lá's line (companion catalog), never the authored sentence.
    companion_meaning: str = Field(min_length=1, max_length=200)
    meaning_brief: DailyMeaningBrief | None = None
    requirements: tuple[SafeRequirement, ...] = Field(min_length=1, max_length=8)
    evidence: tuple[SafeEvidence, ...] = Field(min_length=1, max_length=12)


class ReadingSourceSection(SafeModel):
    section: Literal["hook", "thesis", "manifestation", "transit", "micro_action"]
    meaning: str = Field(min_length=1, max_length=900)
    source: Literal["natal", "transit", "mixed"]


class ReadingSafePayload(SafeModel):
    purpose: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    precision: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    mode: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    background_lens: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]{1,39}$")
    hero_labels: tuple[str, ...] = Field(min_length=1, max_length=8)
    source_sections: tuple[ReadingSourceSection, ...] = Field(min_length=4, max_length=5)
    requirements: tuple[SafeRequirement, ...] = Field(min_length=1, max_length=8)
    evidence: tuple[SafeEvidence, ...] = Field(min_length=1, max_length=16)


class TarotFocusKey(StrEnum):
    CLARITY = "clarity"
    COMMUNICATION = "communication"
    BOUNDARY = "boundary"
    CHOICE = "choice"
    NEXT_STEP = "next_step"
    REPEATING_PATTERN = "repeating_pattern"


class TarotPositionSource(SafeModel):
    """Catalog codes of a framed position's texts (tarot/provenance.py resolves them)."""

    frame: str = Field(pattern=r"^[a-z_]{2,20}\.[0-2]$")
    lead: str | None = Field(
        default=None, pattern=r"^(?:yes_no|choice|how|why|timing|open)\.[0-4]$"
    )
    gentle: bool
    reflection: str = Field(pattern=r"^(?:role|goal\.[a-z_]{2,20})$")
    action: str | None = Field(default=None, pattern=r"^(?:card|goal\.[a-z_]{2,20})$")


class TarotPosition(SafeModel):
    position_key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    position_label: str = Field(min_length=1, max_length=100)
    card_key: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    card_title: str = Field(min_length=1, max_length=100)
    orientation: Literal["upright", "reversed"]
    meaning_keys: tuple[str, ...] = Field(min_length=1, max_length=8)
    meaning_here: str = Field(min_length=1, max_length=900)
    everyday_scene: str = Field(min_length=1, max_length=900)
    reflection_question: str = Field(min_length=1, max_length=500)
    # Only step roles carry an action since B2-2; other positions send null.
    small_action: str | None = Field(default=None, min_length=1, max_length=500)
    # Brief v3 (framed readings, US-20 AC06): the catalog codes every text above resolves from.
    source: TarotPositionSource | None = None


class TarotGoal(SafeModel):
    key: Literal[
        "general",
        "apology",
        "meeting",
        "shared_care",
        "task_handoff",
        "recognition",
        "workload",
        "rest",
        "disagreement",
    ]
    meaning: str = Field(min_length=1, max_length=280)


class TarotLink(SafeModel):
    key: Literal["express_then_ask", "hope_and_disappointment", "care_and_reciprocity"]
    kind: Literal["ordered_interpretation"]
    source_positions: tuple[str, ...] = Field(min_length=2, max_length=2)
    meaning: str = Field(min_length=1, max_length=400)


class TarotStanceLabels(SafeModel):
    """Closed lean labels only; the conclusion and reasons stay local."""

    kind: TarotStanceKind
    level: TarotStanceLevel
    action: TarotAction | None = None
    options: tuple[TarotAction, TarotAction] | None = None


class TarotSummarySource(SafeModel):
    readiness: bool


class TarotMeaningBrief(SafeModel):
    version: Literal["tarot-meaning-brief-v1", "tarot-meaning-brief-v2", "tarot-meaning-brief-v3"]
    topic: Literal["general", "relationships", "work", "communication", "energy", "self_care"]
    intent: Literal["clarity", "boundary", "next_step", "communication", "self_check"]
    goals: tuple[TarotGoal, ...] = Field(min_length=1, max_length=8)
    local_summary: str = Field(min_length=1, max_length=2400)
    links: tuple[TarotLink, ...] = Field(max_length=3)
    limits: tuple[
        Literal[
            "Examples are hypothetical, not observed events.",
            "Cards cannot establish another person's thoughts or predict events.",
            "No facts beyond the supplied card meanings and locally recognised goals.",
        ],
        ...,
    ] = Field(min_length=3, max_length=3)
    # v3 only (framed readings, US-20 AC06): closed labels and the summary's resolution input.
    spread_map: (
        Literal[
            "one_focus",
            "three_unblock",
            "five_clarity",
            "five_loop",
            "five_choice",
            "five_conversation",
        ]
        | None
    ) = None
    summary_source: TarotSummarySource | None = None
    stance: TarotStanceLabels | None = None

    @model_validator(mode="after")
    def _v3_fields_belong_to_v3(self) -> TarotMeaningBrief:
        v3 = self.version == "tarot-meaning-brief-v3"
        if v3 and (self.spread_map is None or self.summary_source is None):
            raise ValueError("brief v3 needs spread_map and summary_source")
        if not v3 and (
            self.spread_map is not None
            or self.summary_source is not None
            or self.stance is not None
        ):
            raise ValueError("only brief v3 carries spread_map, summary_source or stance")
        return self


class TarotSafePayload(SafeModel):
    category: Literal["relationship", "work", "self", "general"]
    focus_key: TarotFocusKey
    focus_sentence: str = Field(min_length=1, max_length=160)
    positions: tuple[TarotPosition, ...] = Field(min_length=1, max_length=5)
    meaning_brief: TarotMeaningBrief | None = None

    @model_validator(mode="after")
    def _sources_follow_the_brief(self) -> TarotSafePayload:
        v3 = self.meaning_brief is not None and self.meaning_brief.version.endswith("-v3")
        if any((position.source is not None) != v3 for position in self.positions):
            raise ValueError("every v3 position carries its catalog source, and only v3 ones")
        return self


class RelationshipDimension(SafeModel):
    dimension: Literal["attraction", "coordination", "friction", "asymmetry"]
    band: Literal["low", "medium", "high"]
    direction: Literal["mutual", "a_to_b", "b_to_a", "mixed"]
    meaning_keys: tuple[str, ...] = Field(min_length=1, max_length=8)


class RelationshipSourceSection(SafeModel):
    key: Literal["overview", "strength", "friction", "asymmetry", "prompt"]
    meaning: str = Field(min_length=1, max_length=1_200)


class RelationshipSafePayload(SafeModel):
    context: Literal["crush", "friend", "partner", "someone", "matching"]
    low_signal: bool = False
    dimensions: tuple[RelationshipDimension, ...] = Field(min_length=1, max_length=8)
    source_sections: tuple[RelationshipSourceSection, ...] = Field(min_length=5, max_length=5)
    evidence: tuple[SafeEvidence, ...] = Field(min_length=1, max_length=16)


class ShareSafePayload(SafeModel):
    source_headline: str = Field(min_length=1, max_length=280)
    source_summary: str = Field(min_length=1, max_length=900)
    approved_claim_keys: tuple[str, ...] = Field(min_length=1, max_length=12)
    activity_keys: tuple[str, ...] = Field(default=(), max_length=12)
    activity_summaries: tuple[str, ...] = Field(default=(), max_length=12)


_PAYLOAD_MODELS: dict[RewriteSurface, type[SafeModel]] = {
    RewriteSurface.DAILY_HOME: DailySafePayload,
    RewriteSurface.DAILY_DETAIL: ReadingSafePayload,
    RewriteSurface.REVEAL: ReadingSafePayload,
    RewriteSurface.NATAL: ReadingSafePayload,
    RewriteSurface.PLANET_INSIGHT: ReadingSafePayload,
    RewriteSurface.HOUSE_INSIGHT: ReadingSafePayload,
    RewriteSurface.ASPECT_INSIGHT: ReadingSafePayload,
    RewriteSurface.TRANSIT_INSIGHT: ReadingSafePayload,
    RewriteSurface.RADAR: RelationshipSafePayload,
    RewriteSurface.MATCHING: RelationshipSafePayload,
    RewriteSurface.TAROT: TarotSafePayload,
    RewriteSurface.SHARE_CARD: ShareSafePayload,
    RewriteSurface.RECAP: ShareSafePayload,
}

_SENSITIVE_KEY = re.compile(
    r"^(?:name|.*_name|email|.*_email|phone|.*_phone|dob|birth(?:_.*)?|date|time|place|"
    r"city|province|latitude|longitude|guest_id|profile_id|chart_id|user_id|question|"
    r"message|diary)$",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"),
    re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I
    ),
)

_FOCUS_SENTENCES: dict[TarotFocusKey, str] = {
    TarotFocusKey.CLARITY: "Điều gì trong tình huống này cần được nhìn rõ hơn?",
    TarotFocusKey.COMMUNICATION: "Cuộc trao đổi này đang bỏ sót điều gì?",
    TarotFocusKey.BOUNDARY: "Ranh giới nào cần được nhận ra trong tình huống này?",
    TarotFocusKey.CHOICE: "Điều gì đáng cân nhắc trước khi chọn?",
    TarotFocusKey.NEXT_STEP: "Bước nhỏ nào có thể làm rõ tình hình?",
    TarotFocusKey.REPEATING_PATTERN: "Điều gì đang lặp lại trong tình huống này?",
}

# Public read-only view for the Tarot provenance tracer.
TAROT_FOCUS_SENTENCES: Mapping[str, str] = {
    key.value: text for key, text in _FOCUS_SENTENCES.items()
}

_FOCUS_KEYWORDS: tuple[tuple[TarotFocusKey, tuple[str, ...]], ...] = (
    (TarotFocusKey.COMMUNICATION, ("nhắn", "nói", "trả lời", "im lặng", "giao tiếp")),
    (TarotFocusKey.BOUNDARY, ("ranh giới", "quá giới hạn", "khó từ chối", "áp lực")),
    (TarotFocusKey.CHOICE, ("chọn", "quyết định", "phân vân", "hay là")),
    (TarotFocusKey.NEXT_STEP, ("tiếp theo", "nên làm gì", "bước nào", "bắt đầu")),
    (TarotFocusKey.REPEATING_PATTERN, ("lặp lại", "lần nào", "luôn luôn", "vì sao cứ")),
)


def reduce_tarot_question(
    question: str, *, category: Literal["relationship", "work", "self", "general"]
) -> TarotSafePayload | None:
    """Map free text to a fixed local focus; never forward the original question."""

    normalized = unicodedata.normalize("NFC", " ".join(question.split())).casefold()
    if not normalized or any(pattern.search(normalized) for pattern in _SENSITIVE_VALUE_PATTERNS):
        return None
    focus_key = TarotFocusKey.CLARITY
    for candidate, keywords in _FOCUS_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            focus_key = candidate
            break
    return TarotSafePayload(
        category=category,
        focus_key=focus_key,
        focus_sentence=_FOCUS_SENTENCES[focus_key],
        positions=(
            TarotPosition(
                position_key="placeholder",
                position_label="Vị trí đang chờ bốc",
                card_key="pending_draw",
                card_title="Lá đang chờ bốc",
                orientation="upright",
                meaning_keys=("pending_draw",),
                meaning_here="Nội dung được tạo sau khi người dùng tự chọn lá.",
                everyday_scene="Tình huống cụ thể được giữ ở máy chủ.",
                reflection_question="Điều gì cần được nhìn rõ hơn?",
                small_action="Chọn lá trước khi đọc.",
            ),
        ),
    )


class PrivacyMinimiser:
    def minimise(
        self, surface: RewriteSurface, payload: Mapping[str, object]
    ) -> dict[str, JsonValue]:
        self._reject_sensitive_keys(payload)
        model_type = _PAYLOAD_MODELS[surface]
        try:
            safe = model_type.model_validate(payload)
        except ValidationError as error:
            raise UnsafeRewritePayload(
                "payload does not match the surface privacy contract"
            ) from error
        dumped = safe.model_dump(mode="json", exclude_none=True)
        self._reject_sensitive_values(dumped)
        return dumped

    @classmethod
    def _reject_sensitive_keys(cls, value: object) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                is_safe_label_name = key == "name" and set(value) == {"name", "value"}
                if not is_safe_label_name and _SENSITIVE_KEY.search(str(key)):
                    raise UnsafeRewritePayload("sensitive field is not allowed")
                cls._reject_sensitive_keys(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                cls._reject_sensitive_keys(nested)

    @classmethod
    def _reject_sensitive_values(cls, value: object) -> None:
        if isinstance(value, Mapping):
            for nested in value.values():
                cls._reject_sensitive_values(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                cls._reject_sensitive_values(nested)
        elif isinstance(value, str) and any(
            pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS
        ):
            raise UnsafeRewritePayload("sensitive value is not allowed")
