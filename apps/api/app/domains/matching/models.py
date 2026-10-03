from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.astro.models import RelationshipDimensionEvidence


class WeeklyIntent(StrEnum):
    EASY_TALK = "de_noi_chuyen"
    SLOW_PACE = "di_cham"
    NEW_ANGLE = "goc_moi"
    LET_LA_BALANCE = "de_la_can"


class MatchingIntent(StrEnum):
    DATING = "dating"
    FRIENDSHIP = "friendship"
    OPEN = "open"


class MatchingGender(StrEnum):
    WOMAN = "woman"
    MAN = "man"
    NONBINARY = "nonbinary"


class GenderPreference(StrEnum):
    WOMEN = "women"
    MEN = "men"
    NONBINARY = "nonbinary"
    EVERYONE = "everyone"


class VerificationStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    APPROVED = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class MatchingProfile:
    principal_id: UUID
    display_name: str
    gender_identity: MatchingGender
    intent: MatchingIntent
    gender_preference: GenderPreference
    min_age: int
    max_age: int
    region_code: str
    weekly_intent: WeeklyIntent
    active: bool
    joined_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MatchingConsent:
    principal_id: UUID
    version: str
    purpose: str
    accepted_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class MatchingVerification:
    principal_id: UUID
    status: VerificationStatus
    reason_code: str | None
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MatchingReadiness:
    profile: MatchingProfile | None
    consent: MatchingConsent | None
    verification: MatchingVerification
    age_eligible: bool
    birth_profile_level: int

    @property
    def ready(self) -> bool:
        return all(
            (
                self.profile is not None,
                self.consent is not None and self.consent.revoked_at is None,
                self.verification.status is VerificationStatus.APPROVED,
                self.age_eligible,
                self.birth_profile_level >= 3,
            )
        )


class EnergySlot(StrEnum):
    EASY_TRUTH = "de_noi_that"
    DIFFERENT_RHYTHM = "khac_nhip_dang_hoi"
    SLOW_STEADY = "di_cham"
    IDEA_SPARK = "bat_y_tuong"
    NEW_ANGLE = "goc_moi"


class MatchingRelationshipEvidence(BaseModel):
    """Purpose-minimized projection; excludes Composite, Davison and raw chart facts."""

    model_config = ConfigDict(frozen=True)

    dimensions: tuple[RelationshipDimensionEvidence, ...]
    method_version: str
    scalar_score_eligible: bool = False


class MatchingCandidate(BaseModel):
    """Privacy-minimized input after coarse pool discovery."""

    model_config = ConfigDict(frozen=True)

    candidate_id: UUID
    active_verified: bool
    reciprocal_preference_eligible: bool
    safety_eligible: bool
    intent_overlap: bool
    prior_exposure_count: int = Field(default=0, ge=0)
    relationship: MatchingRelationshipEvidence


class SlateCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_id: UUID
    energy_slot: EnergySlot
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=3)
    relationship_method_version: str
    display_score_eligible: bool = False


class SlateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    cards: tuple[SlateCard, ...]
    requested_size: int = 5
    low_pool: bool
    weekly_intent: WeeklyIntent
    algorithm_version: str = "vong-la-slate-v1"
    excluded_by_hard_filter: int = Field(ge=0)


class MatchingCardCopy(BaseModel):
    """Generated prose layered over one deterministic, privacy-filtered slate card."""

    model_config = ConfigDict(frozen=True)

    candidate_id: UUID
    energy_slot: EnergySlot
    card_summary: str
    strengths: tuple[str, ...] = Field(min_length=1, max_length=3)
    frictions: tuple[str, ...] = Field(min_length=1, max_length=3)
    icebreaker: str
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=3)
    relationship_method_version: str
    renderer_version: str = "gpt-6-luna-matching-v1"
