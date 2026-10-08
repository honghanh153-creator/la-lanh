import re
import unicodedata
from datetime import UTC, date, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.astro.models import EngineProvenance, TimePrecision, Tradition, TransitPhase

WESTERN_INTERPRETATION_KNOWLEDGE_VERSION = "western-interpretation-matrix-v7"
SUPPORTED_WESTERN_INTERPRETATION_KNOWLEDGE_VERSIONS = frozenset(
    {
        "western-interpretation-matrix-v4",
        "western-interpretation-matrix-v5",
        "western-interpretation-matrix-v6",
        WESTERN_INTERPRETATION_KNOWLEDGE_VERSION,
    }
)
JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION = "jyotish-structural-matrix-v1"
INTERPRETATION_KNOWLEDGE_VERSION = WESTERN_INTERPRETATION_KNOWLEDGE_VERSION


class ReadingDomain(StrEnum):
    CORE = "core"
    EMOTIONS = "emotions"
    MIND = "mind"
    RELATING = "relating"
    DRIVE = "drive"
    CURRENT_SKY = "current_sky"


class ReadingPurpose(StrEnum):
    DAILY_NOTE = "daily_note"
    AURA = "aura"
    READING_DETAIL = "reading_detail"
    PERSONALIZED_SKY = "personalized_sky"


class BackgroundLens(StrEnum):
    AUTO = "auto"
    RELATIONSHIPS = "relationships"
    COMMUNICATION = "communication"
    WORK = "work"
    ENERGY = "energy"
    SELF_CARE = "self_care"


class FactorSource(StrEnum):
    NATAL = "natal"
    TRANSIT = "transit"


class FactorKind(StrEnum):
    DATE_ONLY_VIBE = "date_only_vibe"
    PLANET_PLACEMENT = "planet_placement"
    HOUSE_PLACEMENT = "house_placement"
    ANGLE = "angle"
    NATAL_ASPECT = "natal_aspect"
    NAKSHATRA = "nakshatra"
    GRAHA_DRISHTI = "graha_drishti"
    TRANSIT_CONTACT = "transit_contact"


class FactorRole(StrEnum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    REINFORCEMENT = "reinforcement"
    TENSION = "tension"
    TRANSIT = "transit"
    FALLBACK = "fallback"


class FactorConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LIMITED = "limited"


class PlanMode(StrEnum):
    FULL_SYNTHESIS = "full_synthesis"
    VIBE_FALLBACK = "vibe_fallback"
    LIMITED = "limited"


class DerivedFactor(BaseModel):
    """An immutable, allowlisted interpretation input derived from engine facts."""

    model_config = ConfigDict(frozen=True)

    id: str
    tradition: Tradition
    source: FactorSource
    kind: FactorKind
    domain: ReadingDomain
    role: FactorRole
    subjects: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    child_refs: tuple[str, ...] = ()
    strength: float = Field(ge=0, le=1)
    salience: float = Field(ge=0)
    confidence: FactorConfidence
    phase: TransitPhase | None = None
    allowed_language: tuple[str, ...]
    forbidden_language: tuple[str, ...]

    @model_validator(mode="after")
    def validate_factor_shape(self) -> "DerivedFactor":
        if not self.id or not self.subjects or not self.evidence_refs:
            raise ValueError("factors require an id, subjects, and evidence")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("factor evidence must be unique")
        if len(set(self.child_refs)) != len(self.child_refs):
            raise ValueError("factor child references must be unique")
        if self.source is FactorSource.TRANSIT:
            if self.kind is not FactorKind.TRANSIT_CONTACT or self.phase is None:
                raise ValueError("transit factors require a contact and phase")
        elif self.phase is not None:
            raise ValueError("natal factors cannot carry a timing phase")
        if (
            self.kind in {FactorKind.NATAL_ASPECT, FactorKind.GRAHA_DRISHTI}
            and len(self.child_refs) < 2
        ):
            raise ValueError("higher-order factors require two child references")
        _validate_factor_identifier(self)
        return self


def _validate_factor_identifier(factor: DerivedFactor) -> None:
    """Fail closed before renderers decode the persisted canonical id grammar."""

    parts = factor.id.split(":")
    shape_ok = {
        FactorKind.DATE_ONLY_VIBE: len(parts) == 5 and parts[:3] == ["date_only", "sun", "vibe"],
        FactorKind.PLANET_PLACEMENT: len(parts) == 4 and parts[0] == "natal" and parts[2] == "sign",
        FactorKind.HOUSE_PLACEMENT: len(parts) == 4
        and parts[0] == "natal"
        and parts[2] == "house"
        and parts[3].isdigit()
        and 1 <= int(parts[3]) <= 12,
        FactorKind.ANGLE: len(parts) == 5
        and parts[:2] == ["natal", "angle"]
        and parts[3] == "longitude",
        FactorKind.NATAL_ASPECT: len(parts) == 7
        and parts[:2] == ["natal", "aspect"]
        and parts[5] == "orb",
        FactorKind.NAKSHATRA: len(parts) == 6
        and parts[0] == "jyotish"
        and parts[2] == "nakshatra"
        and parts[4] == "pada",
        FactorKind.GRAHA_DRISHTI: len(parts) == 7
        and parts[:2] == ["jyotish", "drishti"]
        and parts[4] == "houses",
        FactorKind.TRANSIT_CONTACT: len(parts) == 9
        and parts[0] == "transit"
        and parts[3] == "natal"
        and parts[5] == "orb"
        and parts[7] == "phase",
    }[factor.kind]
    if not shape_ok:
        raise ValueError(f"malformed canonical factor id for {factor.kind.value}")


class CompositionTarget(BaseModel):
    """Renderer budget for normalized Vietnamese user prose only."""

    model_config = ConfigDict(frozen=True)

    natal_percent: int = Field(ge=0, le=100)
    transit_percent: int = Field(ge=0, le=100)
    tolerance_percentage_points: int = Field(default=10, ge=0, le=50)
    count_scope: str = "user_prose_only"
    count_unit: str = "normalized_vietnamese_words"
    excluded_parts: tuple[str, ...] = ("headings", "evidence", "cta", "disclaimer")

    @model_validator(mode="after")
    def validate_total(self) -> "CompositionTarget":
        if self.natal_percent + self.transit_percent != 100:
            raise ValueError("composition percentages must total 100")
        return self

    def accepts(self, natal_user_prose: str, transit_user_prose: str) -> bool:
        """Check allocation without rejecting mathematically impossible short fallbacks."""

        natal_words = _normalized_vietnamese_word_count(natal_user_prose)
        transit_words = _normalized_vietnamese_word_count(transit_user_prose)
        total_words = natal_words + transit_words
        if total_words == 0 or natal_words == 0:
            return False
        if self.transit_percent == 0:
            return transit_words == 0
        actual_natal_percent = natal_words * 100 / total_words
        lower = self.natal_percent - self.tolerance_percentage_points
        upper = self.natal_percent + self.tolerance_percentage_points
        if lower <= actual_natal_percent <= upper:
            return transit_words > 0
        feasible = any(
            lower <= candidate_natal * 100 / total_words <= upper
            for candidate_natal in range(1, total_words)
        )
        return not feasible and transit_words == 0


class ReadingPlan(BaseModel):
    """Canonical factor selection passed to deterministic or optional renderers."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = "reading-plan/v1"
    rules_version: str = "factor-planner-v2"
    knowledge_version: str = Field(
        default=INTERPRETATION_KNOWLEDGE_VERSION,
        min_length=1,
        max_length=64,
    )
    plan_hash: str
    tradition: Tradition
    config_hash: str = Field(min_length=1, max_length=64)
    purpose: ReadingPurpose
    precision: TimePrecision
    mode: PlanMode
    factors: tuple[DerivedFactor, ...] = Field(max_length=24)
    hero_factor_refs: tuple[str, ...]
    composition: CompositionTarget
    background_lens: BackgroundLens | None = None
    editorial_seed: str | None = Field(default=None, min_length=1, max_length=64)
    allowed_language: tuple[str, ...]
    forbidden_language: tuple[str, ...]

    @model_validator(mode="after")
    def validate_plan(self) -> "ReadingPlan":
        factor_by_id = {factor.id: factor for factor in self.factors}
        if len(factor_by_id) != len(self.factors):
            raise ValueError("factor ids must be unique")
        if any(factor.tradition is not self.tradition for factor in self.factors):
            raise ValueError("a reading plan cannot mix traditions")
        if any(ref not in factor_by_id for ref in self.hero_factor_refs):
            raise ValueError("hero references must belong to the plan")
        if any(
            child_ref not in factor_by_id
            for factor in self.factors
            for child_ref in factor.child_refs
        ):
            raise ValueError("child references must belong to the plan")
        if self.tradition is Tradition.WESTERN and any(
            factor.kind in {FactorKind.NAKSHATRA, FactorKind.GRAHA_DRISHTI}
            for factor in self.factors
        ):
            raise ValueError("Western plans cannot contain Jyotish factors")
        if self.tradition is Tradition.JYOTISH and any(
            factor.kind in {FactorKind.NATAL_ASPECT, FactorKind.TRANSIT_CONTACT}
            for factor in self.factors
        ):
            raise ValueError("Jyotish plans cannot contain Western aspect semantics")
        supported_knowledge = (
            SUPPORTED_WESTERN_INTERPRETATION_KNOWLEDGE_VERSIONS
            if self.tradition is Tradition.WESTERN
            else frozenset({JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION})
        )
        if self.knowledge_version not in supported_knowledge:
            raise ValueError("knowledge version must match the reading tradition")
        has_transit = any(factor.source is FactorSource.TRANSIT for factor in self.factors)
        if has_transit != (self.composition.transit_percent > 0):
            raise ValueError("composition must match transit eligibility")
        if self.mode is PlanMode.VIBE_FALLBACK:
            if (
                len(self.factors) != 1
                or self.factors[0].kind is not FactorKind.DATE_ONLY_VIBE
                or self.hero_factor_refs != (self.factors[0].id,)
            ):
                raise ValueError("date-only Vibe must remain a one-factor fallback")
        if self.mode is PlanMode.FULL_SYNTHESIS:
            hero_factors = tuple(factor_by_id[ref] for ref in self.hero_factor_refs)
            independent_pair = any(
                not set(first.subjects).intersection(second.subjects)
                and not set(first.evidence_refs).intersection(second.evidence_refs)
                for index, first in enumerate(hero_factors)
                for second in hero_factors[index + 1 :]
            )
            higher_order = any(len(factor.child_refs) >= 2 for factor in hero_factors)
            if not independent_pair and not higher_order:
                raise ValueError("full synthesis requires independent factors or child evidence")
        return self


SHORT_DISCLAIMER = "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn."
FULL_FRAMEWORK_DISCLOSURE = (
    "Chiêm tinh là một khung diễn giải, không phải bằng chứng khoa học "
    "hay phán quyết thực tế về bạn."
)
EVIDENCE_DISCLOSURE_TITLE = "Căn cứ trong lá số"


class ClaimTemplateId(StrEnum):
    DATE_ONLY_VIBE = "date_only_vibe"
    PLANET_IN_SIGN = "planet_in_sign"
    PLANET_IN_HOUSE = "planet_in_house"
    ANGLE_LONGITUDE = "angle_longitude"
    NATAL_ASPECT = "natal_aspect"
    NAKSHATRA_POSITION = "nakshatra_position"
    GRAHA_DRISHTI = "graha_drishti"
    TRANSIT_CONTACT = "transit_contact"


class ClaimSlotName(StrEnum):
    BODY = "body"
    BODY_A = "body_a"
    BODY_B = "body_b"
    SIGN = "sign"
    DEGREE = "degree"
    MOTION = "motion"
    HOUSE = "house"
    ANGLE = "angle"
    LONGITUDE = "longitude"
    ASPECT = "aspect"
    ORB = "orb"
    PHASE = "phase"
    STATUS = "status"
    NAKSHATRA = "nakshatra"
    PADA = "pada"
    HOUSES_APART = "houses_apart"
    DRISHTI_KIND = "drishti_kind"


class ClaimSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: ClaimSlotName
    value: str = Field(min_length=1, max_length=64)


_CLAIM_SLOT_CONTRACT: dict[ClaimTemplateId, frozenset[ClaimSlotName]] = {
    ClaimTemplateId.DATE_ONLY_VIBE: frozenset(
        {ClaimSlotName.BODY, ClaimSlotName.STATUS, ClaimSlotName.SIGN}
    ),
    ClaimTemplateId.PLANET_IN_SIGN: frozenset(
        {
            ClaimSlotName.BODY,
            ClaimSlotName.SIGN,
            ClaimSlotName.DEGREE,
            ClaimSlotName.MOTION,
        }
    ),
    ClaimTemplateId.PLANET_IN_HOUSE: frozenset({ClaimSlotName.BODY, ClaimSlotName.HOUSE}),
    ClaimTemplateId.ANGLE_LONGITUDE: frozenset({ClaimSlotName.ANGLE, ClaimSlotName.LONGITUDE}),
    ClaimTemplateId.NATAL_ASPECT: frozenset(
        {
            ClaimSlotName.BODY_A,
            ClaimSlotName.BODY_B,
            ClaimSlotName.ASPECT,
            ClaimSlotName.ORB,
        }
    ),
    ClaimTemplateId.NAKSHATRA_POSITION: frozenset(
        {ClaimSlotName.BODY, ClaimSlotName.NAKSHATRA, ClaimSlotName.PADA}
    ),
    ClaimTemplateId.GRAHA_DRISHTI: frozenset(
        {
            ClaimSlotName.BODY_A,
            ClaimSlotName.BODY_B,
            ClaimSlotName.HOUSES_APART,
            ClaimSlotName.DRISHTI_KIND,
        }
    ),
    ClaimTemplateId.TRANSIT_CONTACT: frozenset(
        {
            ClaimSlotName.BODY_A,
            ClaimSlotName.BODY_B,
            ClaimSlotName.ASPECT,
            ClaimSlotName.ORB,
            ClaimSlotName.PHASE,
        }
    ),
}


class EvidenceClaim(BaseModel):
    """A server-owned factual template populated only from a ReadingPlan factor."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    factor_ref: str = Field(min_length=1, max_length=256)
    template_id: ClaimTemplateId
    slots: tuple[ClaimSlot, ...] = Field(max_length=6)
    display_text: str = Field(min_length=1, max_length=240)

    @model_validator(mode="after")
    def validate_bounded_slots(self) -> "EvidenceClaim":
        names = tuple(slot.name for slot in self.slots)
        if len(names) != len(set(names)):
            raise ValueError("claim slots must be unique")
        if len(names) > 6:
            raise ValueError("claims support at most six bounded slots")
        if not set(names).issubset(_CLAIM_SLOT_CONTRACT[self.template_id]):
            raise ValueError("claim contains a slot outside its closed template")
        return self


class EvidenceDisclosure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = EVIDENCE_DISCLOSURE_TITLE
    claims: tuple[EvidenceClaim, ...] = Field(max_length=16)
    framework_disclosure: str = FULL_FRAMEWORK_DISCLOSURE


class SemanticArena(StrEnum):
    GENERAL = "general"
    RELATIONSHIPS = "relationships"
    COMMUNICATION = "communication"
    WORK = "work"
    ENERGY = "energy"
    SELF_CARE = "self_care"
    STRUCTURAL = "structural"


class SemanticSection(StrEnum):
    ALL = "all"
    HOOK = "hook"
    THESIS = "thesis"
    MANIFESTATION = "manifestation"
    MICRO_ACTION = "micro_action"
    TRANSIT = "transit"


class SemanticRequirement(BaseModel):
    """One server-owned concept that rewritten prose must still express."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    section: SemanticSection = SemanticSection.ALL
    markers: tuple[str, ...] = Field(min_length=1, max_length=12)
    min_matches: int = Field(default=1, ge=1, le=4)

    @model_validator(mode="after")
    def validate_markers(self) -> "SemanticRequirement":
        normalized = tuple(marker.strip().casefold() for marker in self.markers)
        if any(len(marker) < 2 for marker in normalized):
            raise ValueError("semantic requirement markers must be meaningful")
        if len(normalized) != len(set(normalized)):
            raise ValueError("semantic requirement markers must be unique")
        if self.min_matches > len(normalized):
            raise ValueError("semantic requirement min_matches exceeds marker count")
        return self


class DailyMeaningBrief(BaseModel):
    """Editorial meaning, not an observed event or new personal-data context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    core_meaning: str = Field(min_length=1, max_length=300)
    reader_takeaway: str = Field(min_length=1, max_length=300)
    scene_status: Literal["illustrative"] = "illustrative"
    scene_anchors: tuple[str, ...] = Field(min_length=1, max_length=8)
    action_anchors: tuple[str, ...] = Field(min_length=1, max_length=8)
    observation_question: str | None = Field(default=None, min_length=1, max_length=200)


class SemanticBlueprint(BaseModel):
    """Internal contract joining one interpretation, one scene, and one action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = "semantic-blueprint/v1"
    arena: SemanticArena
    mechanism_key: str = Field(min_length=1, max_length=96)
    scene_key: str = Field(min_length=1, max_length=96)
    action_key: str = Field(min_length=1, max_length=96)
    hook: str = Field(max_length=280)
    thesis: str = Field(max_length=700)
    manifestation: str = Field(max_length=700)
    micro_action: str = Field(max_length=500)
    evidence_factor_refs: tuple[str, ...] = Field(max_length=12)
    requirements: tuple[SemanticRequirement, ...] = Field(min_length=1, max_length=8)
    daily_meaning: DailyMeaningBrief | None = None


class ReadingCandidate(BaseModel):
    """Typed renderer output evaluated locally before it may be published."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "reading-candidate/v1"
    renderer_version: str = Field(min_length=1, max_length=64)
    plan_hash: str = Field(min_length=1, max_length=64)
    hook: str = Field(max_length=280)
    thesis: str = Field(max_length=700)
    manifestation: str = Field(max_length=700)
    transit: str | None = Field(default=None, max_length=500)
    micro_action: str = Field(max_length=500)
    evidence: EvidenceDisclosure
    disclaimer: str = SHORT_DISCLAIMER
    semantic_blueprint: "SemanticBlueprint | None" = None

    @property
    def natal_user_prose(self) -> str:
        return " ".join(
            part.strip()
            for part in (self.hook, self.thesis, self.manifestation, self.micro_action)
            if part.strip()
        )

    @property
    def all_user_prose(self) -> tuple[str, ...]:
        sections = (self.hook, self.thesis, self.manifestation, self.micro_action)
        if self.transit is not None:
            return (*sections, self.transit)
        return sections


class GateName(StrEnum):
    EVIDENCE = "evidence"
    ANTI_INFLUENCE = "anti_influence"
    EDITORIAL = "editorial"
    MEANING = "meaning"
    PRIVACY = "privacy"


class GateFailureCode(StrEnum):
    EVIDENCE_REQUIRED_PROSE = "evidence_required_prose"
    EVIDENCE_PLAN_MISMATCH = "evidence_plan_mismatch"
    EVIDENCE_DISCLOSURE = "evidence_disclosure"
    EVIDENCE_UNSUPPORTED_CLAIM = "evidence_unsupported_claim"
    EVIDENCE_MISSING_HERO = "evidence_missing_hero"
    EVIDENCE_UNEXPECTED_TRANSIT = "evidence_unexpected_transit"
    EVIDENCE_ASTRO_LABEL = "evidence_astro_label"
    EVIDENCE_UNSUPPORTED_TIMING = "evidence_unsupported_timing"
    EVIDENCE_COMPOSITION = "evidence_composition"
    ANTI_ABSOLUTE_CERTAINTY = "anti_absolute_certainty"
    ANTI_FATE = "anti_fate"
    ANTI_DEPENDENCY = "anti_dependency"
    ANTI_URGENCY = "anti_urgency"
    ANTI_ISOLATION = "anti_isolation"
    ANTI_GUILT_FEAR = "anti_guilt_fear"
    ANTI_DIAGNOSIS = "anti_diagnosis"
    ANTI_MEDICAL_COMMAND = "anti_medical_command"
    ANTI_LEGAL_COMMAND = "anti_legal_command"
    ANTI_FINANCIAL_COMMAND = "anti_financial_command"
    ANTI_SAFETY_COMMAND = "anti_safety_command"
    EDITORIAL_BANNED_PHRASE = "editorial_banned_phrase"
    EDITORIAL_GENERIC_HEALING = "editorial_generic_healing"
    EDITORIAL_FORCED_SLANG = "editorial_forced_slang"
    EDITORIAL_REPETITION = "editorial_repetition"
    EDITORIAL_LENGTH = "editorial_length"
    MEANING_BLUEPRINT_REQUIRED = "meaning_blueprint_required"
    MEANING_BLUEPRINT_MISMATCH = "meaning_blueprint_mismatch"
    MEANING_REQUIRED_CONCEPT = "meaning_required_concept"
    MEANING_CONTEXT_MISMATCH = "meaning_context_mismatch"
    MEANING_UNSUPPORTED_FACTOR = "meaning_unsupported_factor"
    MEANING_UNOBSERVABLE_SCENE = "meaning_unobservable_scene"
    MEANING_ACTION_MISMATCH = "meaning_action_mismatch"
    MEANING_SCENE_CONTAINS_ADVICE = "meaning_scene_contains_advice"
    MEANING_DAILY_MATRIX_MISMATCH = "meaning_daily_matrix_mismatch"
    MEANING_DAILY_DIRECT_CONTRACT = "meaning_daily_direct_contract"
    PRIVACY_PERSONAL_DATA = "privacy_personal_data"


class GateReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: GateName
    version: str
    passed: bool
    failure_codes: tuple[GateFailureCode, ...] = ()

    @model_validator(mode="after")
    def validate_result(self) -> "GateReport":
        if self.passed == bool(self.failure_codes):
            raise ValueError("passed gates cannot have failures and failed gates require one")
        return self


class CandidateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted: bool
    reports: tuple[GateReport, ...]
    publishable_candidate: ReadingCandidate | None = None

    @model_validator(mode="after")
    def validate_publication_state(self) -> "CandidateEvaluation":
        passed = bool(self.reports) and all(report.passed for report in self.reports)
        if self.accepted != passed:
            raise ValueError("accepted must match the gate reports")
        if self.accepted != (self.publishable_candidate is not None):
            raise ValueError("publishable content exists exactly when evaluation is accepted")
        return self

    @property
    def failure_codes(self) -> tuple[GateFailureCode, ...]:
        return tuple(
            dict.fromkeys(code for report in self.reports for code in report.failure_codes)
        )


_VIETNAMESE_WORD = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)


def _normalized_vietnamese_word_count(text: str) -> int:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return len(_VIETNAMESE_WORD.findall(normalized))


class ReadingClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    domain: ReadingDomain
    title: str
    summary: str
    hook: str = ""
    meaning: str = ""
    manifestation: str = ""
    watch_for: str = ""
    micro_action: str = ""
    evidence: tuple[str, ...] = ()
    factor_refs: tuple[str, ...]
    confidence: str


class InsightReading(BaseModel):
    model_config = ConfigDict(frozen=True)

    tradition: Tradition
    config_hash: str
    observed_at: datetime
    claims: tuple[ReadingClaim, ...]
    provenance: EngineProvenance
    disclaimer: str = (
        "Nội dung mang tính diễn giải và tham khảo, không phải dự đoán chắc chắn "
        "hay lời khuyên chuyên môn."
    )


class ReadingRevisionSource(StrEnum):
    DETERMINISTIC = "deterministic"
    GENERATED = "generated"


class ProfileReadiness(StrEnum):
    VIBE = "vibe"
    LIMITED = "limited"
    AURA_READY = "aura_ready"


class AuraUnlockLayer(StrEnum):
    MULTI_FACTOR = "multi_factor"
    HOUSE_ARENA = "house_arena"
    RISING_ANGLES = "rising_angles"
    CURRENT_SKY = "current_sky"


class ExperimentProjection(BaseModel):
    """Server-owned action grammar; clients never split or author this prose."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action_key: str = Field(min_length=64, max_length=64)
    action: str = Field(min_length=1, max_length=500)
    observation: str = Field(min_length=1, max_length=240)
    permission: str = Field(min_length=1, max_length=240)


class AuraTransitionProjection(BaseModel):
    """Evidence-derived profile transition without shadow active/available depth fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_readiness: ProfileReadiness
    transition_id: str | None = Field(default=None, min_length=64, max_length=64)
    acknowledged: bool = False
    unlock_layers: tuple[AuraUnlockLayer, ...] = Field(max_length=4)


class ReadingSectionsProjection(BaseModel):
    """User-visible prose only; internal planning and gate state never crosses the API."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hook: str
    thesis: str
    manifestation: str
    transit: str | None = None
    micro_action: str


class ReadingEvidenceProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    claims: tuple[str, ...]
    framework_disclosure: str


class ReadingContentProjection(BaseModel):
    """The single private response contract shared by Daily and Insights."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    revision_id: UUID
    source: ReadingRevisionSource
    mode: PlanMode
    purpose: ReadingPurpose
    tradition: Tradition
    precision: TimePrecision
    sections: ReadingSectionsProjection
    evidence: ReadingEvidenceProjection
    disclaimer: str
    created_at: datetime
    experiment: ExperimentProjection | None = None


class AvailableReadingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    revision_id: UUID
    message: str = "Có một bản đọc mới đang chờ bạn"
    content: ReadingContentProjection


class ReadingProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_key: str = Field(min_length=64, max_length=64)
    active: ReadingContentProjection
    available_update: AvailableReadingUpdate | None = None
    aura_transition: AuraTransitionProjection


def canonical_experiment_action_key(revision_id: UUID, action: str) -> str:
    """Opaque identity for the accepted revision's bounded server-rendered action."""

    return sha256(f"action-experiment-v1\x1f{revision_id}\x1f{action}".encode()).hexdigest()


def experiment_projection_for(
    revision_id: UUID, action: str, *, blueprint: SemanticBlueprint | None = None
) -> ExperimentProjection:
    meaning = blueprint.daily_meaning if blueprint is not None else None
    observation_question = meaning.observation_question if meaning is not None else None
    return ExperimentProjection(
        action_key=canonical_experiment_action_key(revision_id, action),
        action=action,
        observation=observation_question
        or "Để ý xem việc này có tạo ra một khác biệt nhỏ, cụ thể nào không.",
        permission=(
            "Không hợp với tình huống của bạn thì bỏ qua."
            if observation_question
            else "Bạn có thể bỏ qua hoặc dừng bất cứ lúc nào; đây chỉ là một thử nghiệm."
        ),
    )


def canonical_reading_plan_key(plan: ReadingPlan) -> str:
    """Identity for the factual plan only; renderer/provider metadata is excluded."""

    return sha256(plan.model_dump_json(exclude_none=False).encode()).hexdigest()


def canonical_reading_revision_key(
    *,
    plan_key: str,
    source: ReadingRevisionSource,
    renderer_version: str,
    content_version: str,
    schema_version: str,
    rules_version: str,
    gate_policy_version: str,
) -> str:
    """Versioned content identity; provider/model execution details never participate."""

    parts = (
        plan_key,
        source.value,
        renderer_version,
        content_version,
        schema_version,
        rules_version,
        gate_policy_version,
    )
    return sha256("\x1f".join(parts).encode()).hexdigest()


def canonical_gate_policy_version(evaluation: CandidateEvaluation) -> str:
    return "+".join(f"{report.gate.value}:{report.version}" for report in evaluation.reports)


def canonical_projection_scope_key(
    *,
    purpose: ReadingPurpose,
    tradition: Tradition,
    config_hash: str,
    local_date: date,
    timezone_name: str,
    observed_at: datetime,
    lens_variant: str | None = None,
) -> str:
    """Stable projection identity for one user-visible reading surface."""

    timezone = _validate_timezone_name(timezone_name)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    if observed_at.astimezone(timezone).date() != local_date:
        raise ValueError("local_date must match observed_at in timezone_name")
    if not 1 <= len(config_hash) <= 64:
        raise ValueError("config_hash must contain between 1 and 64 characters")
    parts = (
        purpose.value,
        tradition.value,
        config_hash,
        local_date.isoformat(),
        timezone_name,
        observed_at.astimezone(UTC).isoformat(),
    )
    if lens_variant is None:
        return sha256("\x1f".join(parts).encode()).hexdigest()
    if len(lens_variant) != 64:
        raise ValueError("lens_variant must be an opaque 64-character identity")
    return sha256("\x1f".join((*parts, lens_variant)).encode()).hexdigest()


def canonical_lens_variant(background_lens: BackgroundLens | None) -> str | None:
    """Opaque context identity; automatic readings retain their legacy scope key."""

    if background_lens is None or background_lens is BackgroundLens.AUTO:
        return None
    return sha256(f"reading-projection-lens-v1\x1f{background_lens.value}".encode()).hexdigest()


class ReadingPlanRecord(BaseModel):
    """Immutable encrypted-at-rest plan owned by one guest birth profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    guest_id: UUID
    profile_id: UUID
    chart_snapshot_id: UUID | None = None
    plan_key: str = Field(min_length=64, max_length=64)
    plan: ReadingPlan
    created_at: datetime

    @model_validator(mode="after")
    def validate_identity(self) -> "ReadingPlanRecord":
        if self.plan_key != canonical_reading_plan_key(self.plan):
            raise ValueError("plan_key does not match the canonical plan payload")
        _validate_aware(self.created_at, "created_at")
        return self


class ReadingRevisionRecord(BaseModel):
    """Immutable accepted content; failed candidates are never persisted here."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    guest_id: UUID
    profile_id: UUID
    plan_id: UUID
    revision_key: str = Field(min_length=64, max_length=64)
    source: ReadingRevisionSource
    renderer_version: str = Field(min_length=1, max_length=64)
    content_version: str = Field(min_length=1, max_length=64)
    schema_version: str = Field(min_length=1, max_length=64)
    rules_version: str = Field(min_length=1, max_length=64)
    gate_policy_version: str = Field(min_length=1, max_length=255)
    evaluation: CandidateEvaluation
    created_at: datetime

    @model_validator(mode="after")
    def validate_publishable(self) -> "ReadingRevisionRecord":
        candidate = self.evaluation.publishable_candidate
        if not self.evaluation.accepted or candidate is None:
            raise ValueError("only accepted evaluations with publishable content may be stored")
        expected_gates = (
            GateName.EVIDENCE,
            GateName.ANTI_INFLUENCE,
            GateName.EDITORIAL,
            GateName.MEANING,
            GateName.PRIVACY,
        )
        if tuple(report.gate for report in self.evaluation.reports) != expected_gates or any(
            not report.passed for report in self.evaluation.reports
        ):
            raise ValueError("accepted content must pass all five ordered safety gates")
        expected_gate_policy = canonical_gate_policy_version(self.evaluation)
        if self.gate_policy_version != expected_gate_policy:
            raise ValueError("gate policy version must match the accepted evaluation")
        if candidate.renderer_version != self.renderer_version:
            raise ValueError("renderer version must match the accepted candidate")
        if candidate.schema_version != self.schema_version:
            raise ValueError("schema version must match the accepted candidate")
        _validate_aware(self.created_at, "created_at")
        return self


class ReadingProjectionRecord(BaseModel):
    """Mutable pointer state; activation is always an explicit user action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    guest_id: UUID
    profile_id: UUID
    scope_key: str = Field(min_length=64, max_length=64)
    purpose: ReadingPurpose
    tradition: Tradition
    config_hash: str = Field(min_length=1, max_length=64)
    lens_variant: str | None = Field(default=None, min_length=64, max_length=64)
    local_date: date
    timezone_name: str = Field(min_length=1, max_length=64)
    observed_at: datetime
    active_revision_id: UUID | None = None
    available_revision_id: UUID | None = None
    acknowledged_aura_transition_id: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    )
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_scope(self) -> "ReadingProjectionRecord":
        expected = canonical_projection_scope_key(
            purpose=self.purpose,
            tradition=self.tradition,
            config_hash=self.config_hash,
            local_date=self.local_date,
            timezone_name=self.timezone_name,
            observed_at=self.observed_at,
            lens_variant=self.lens_variant,
        )
        if self.scope_key != expected:
            raise ValueError("scope_key does not match the canonical projection scope")
        if self.active_revision_id is not None and (
            self.active_revision_id == self.available_revision_id
        ):
            raise ValueError("active and available revisions must be different")
        _validate_aware(self.created_at, "created_at")
        _validate_aware(self.updated_at, "updated_at")
        return self


class GenerationAttemptStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class GenerationAttemptResult(StrEnum):
    SUCCESS = "success"
    REFUSAL = "refusal"
    INCOMPLETE = "incomplete"
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    DISABLED = "disabled"
    GATE_REJECTED = "gate_rejected"
    AMBIGUOUS = "ambiguous"


def canonical_generation_key(
    *,
    plan_key: str,
    scope_key: str,
    provider: str,
    model: str,
    prompt_version: str,
) -> str:
    return sha256(
        "\x1f".join((plan_key, scope_key, provider, model, prompt_version)).encode()
    ).hexdigest()


class GenerationAttemptRecord(BaseModel):
    """Durable queue state; candidate and provider error text are never stored."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    guest_id: UUID
    profile_id: UUID
    plan_id: UUID
    scope_key: str = Field(min_length=64, max_length=64)
    generation_key: str = Field(min_length=64, max_length=64)
    provider: str = Field(min_length=1, max_length=32)
    model: str = Field(min_length=1, max_length=64)
    prompt_version: str = Field(min_length=1, max_length=64)
    deletion_epoch: UUID
    status: GenerationAttemptStatus = GenerationAttemptStatus.PENDING
    lease_token: UUID | None = None
    lease_expires_at: datetime | None = None
    request_started_at: datetime | None = None
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=2, ge=1, le=3)
    next_attempt_at: datetime
    accepted_revision_id: UUID | None = None
    last_result: GenerationAttemptResult | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_attempt(self) -> "GenerationAttemptRecord":
        for name in ("next_attempt_at", "created_at", "updated_at"):
            _validate_aware(getattr(self, name), name)
        for name in ("lease_expires_at", "request_started_at"):
            value = getattr(self, name)
            if value is not None:
                _validate_aware(value, name)
        leased = self.status is GenerationAttemptStatus.LEASED
        if leased != (self.lease_token is not None and self.lease_expires_at is not None):
            raise ValueError("leased attempts require a token and expiry only while leased")
        if self.request_started_at is not None and not leased:
            raise ValueError("request_started_at is valid only while leased")
        if (self.status is GenerationAttemptStatus.SUCCEEDED) != (
            self.accepted_revision_id is not None
        ):
            raise ValueError("only succeeded attempts reference an accepted revision")
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count cannot exceed max_attempts")
        return self


class LeasedGenerationAttempt(BaseModel):
    """Transaction-free work packet returned after a durable lease commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    plan_record: ReadingPlanRecord
    scope_key: str = Field(min_length=64, max_length=64)
    generation_key: str = Field(min_length=64, max_length=64)
    provider: str = Field(min_length=1, max_length=32)
    model: str = Field(min_length=1, max_length=64)
    prompt_version: str = Field(min_length=1, max_length=64)
    deletion_epoch: UUID
    lease_token: UUID
    lease_expires_at: datetime
    attempt_count: int = Field(ge=1)
    max_attempts: int = Field(ge=1, le=3)

    @model_validator(mode="after")
    def validate_lease(self) -> "LeasedGenerationAttempt":
        _validate_aware(self.lease_expires_at, "lease_expires_at")
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count cannot exceed max_attempts")
        return self


def _validate_timezone_name(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone_name must be a valid IANA timezone") from exc


def _validate_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
