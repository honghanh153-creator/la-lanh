from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class RewriteSurface(StrEnum):
    DAILY_HOME = "daily_home"
    DAILY_DETAIL = "daily_detail"
    REVEAL = "reveal"
    NATAL = "natal"
    PLANET_INSIGHT = "planet_insight"
    HOUSE_INSIGHT = "house_insight"
    ASPECT_INSIGHT = "aspect_insight"
    TRANSIT_INSIGHT = "transit_insight"
    RADAR = "radar"
    MATCHING = "matching"
    TAROT = "tarot"
    SHARE_CARD = "share_card"
    RECAP = "recap"


class ContentClassification(StrEnum):
    PERSONALISED_INTERPRETIVE = "personalised_interpretive"
    STATIC = "static"
    LEGAL = "legal"
    TRANSACTIONAL = "transactional"
    SECURITY = "security"


class RewriteResultStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RewriteJobStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RewriteJobResult(StrEnum):
    ACCEPTED = "accepted"
    GATE_REJECTED = "gate_rejected"
    AUTHORIZATION_REVOKED = "authorization_revoked"
    REFUSAL = "refusal"
    INCOMPLETE = "incomplete"
    TRANSIENT = "transient"
    AMBIGUOUS = "ambiguous"
    PERMANENT = "permanent"
    DISABLED = "disabled"


class ArtifactOwnerKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    key: str = Field(min_length=1, max_length=240)


class RewriteArtifactKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: RewriteSurface
    owner: ArtifactOwnerKey
    blueprint_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_version: str = Field(min_length=1, max_length=80)
    prompt_version: str = Field(min_length=1, max_length=80)
    schema_version: str = Field(min_length=1, max_length=80)
    gate_version: str = Field(min_length=1, max_length=80)
    locale: str = Field(default="vi-VN", pattern=r"^[a-z]{2}-[A-Z]{2}$")
    tone_preference: str = Field(default="plain_warm", min_length=1, max_length=40)
    candidate_variant: str = Field(
        default="runtime",
        pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$",
    )

    @property
    def cache_key(self) -> str:
        payload = self.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return sha256(canonical).hexdigest()


class RewriteRequestEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: RewriteArtifactKey
    authorization_receipt_id: str = Field(min_length=1, max_length=240)
    safe_payload: dict[str, JsonValue]


class RewriteResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: RewriteArtifactKey
    status: RewriteResultStatus
    output: dict[str, JsonValue] | None = None
    gate_receipt_id: str | None = Field(default=None, max_length=240)
    failure_code: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_result_shape(self) -> RewriteResultEnvelope:
        if self.status is RewriteResultStatus.ACCEPTED:
            if self.output is None or self.gate_receipt_id is None or self.failure_code is not None:
                raise ValueError("accepted rewrite results require output and a gate receipt")
        elif self.output is not None:
            raise ValueError("non-accepted rewrite results cannot carry publishable output")
        return self


class RewriteJobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    request: RewriteRequestEnvelope
    status: RewriteJobStatus = RewriteJobStatus.PENDING
    deletion_epoch: UUID
    attempt_count: int = Field(default=0, ge=0, le=3)
    max_attempts: int = Field(default=2, ge=1, le=3)
    next_attempt_at: datetime
    last_result: RewriteJobResult | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_attempt_bounds(self) -> RewriteJobRecord:
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt count cannot exceed max attempts")
        return self


class LeasedRewriteJob(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    request: RewriteRequestEnvelope
    deletion_epoch: UUID
    lease_token: UUID
    lease_expires_at: datetime
    attempt_count: int = Field(ge=1, le=3)
    max_attempts: int = Field(ge=1, le=3)


class RewriteFieldSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    classification: ContentClassification = ContentClassification.PERSONALISED_INTERPRETIVE


class RewriteSurfaceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: RewriteSurface
    fallback_owner: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    schema_version: str = Field(min_length=1, max_length=80)
    gate_version: str = Field(min_length=1, max_length=80)
    fields: tuple[RewriteFieldSpec, ...] = Field(min_length=1)
    word_budget: int = Field(ge=12, le=1_200)
    forbidden_claims: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_field_ownership(self) -> RewriteSurfaceSpec:
        names = tuple(field.name for field in self.fields)
        if len(names) != len(set(names)):
            raise ValueError("field ownership must be unique within a rewrite surface")
        if any(
            field.classification is not ContentClassification.PERSONALISED_INTERPRETIVE
            for field in self.fields
        ):
            raise ValueError("only personalised interpretive content can be rewritten")
        return self

    @property
    def rewritable_fields(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields)
