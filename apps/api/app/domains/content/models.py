from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTENT_CONTRACT_VERSION = "daily-content-matrix/v1"
CONTENT_BUNDLE_KEY = "daily-astrology"


class ContentRevisionStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"


class ContentAuditAction(StrEnum):
    DRAFT_CREATED = "draft_created"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ROLLED_BACK = "rolled_back"


class ContentValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1, max_length=80)
    severity: str = Field(pattern=r"^(critical|high|medium)$")
    path: str = Field(min_length=1, max_length=240)
    message: str = Field(min_length=1, max_length=300)


class ContentValidationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    validator_version: str = Field(min_length=1, max_length=64)
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    passed: bool
    findings: tuple[ContentValidationFinding, ...] = ()

    @model_validator(mode="after")
    def validate_result(self) -> ContentValidationReceipt:
        blocking = any(item.severity in {"critical", "high"} for item in self.findings)
        if self.passed == blocking:
            raise ValueError("validation pass state must match blocking findings")
        return self


class ContentRevision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    bundle_key: str = CONTENT_BUNDLE_KEY
    contract_version: str = CONTENT_CONTRACT_VERSION
    parent_revision_id: UUID | None = None
    status: ContentRevisionStatus
    payload: dict[str, Any]
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation: ContentValidationReceipt | None = None
    created_at: datetime

    @model_validator(mode="after")
    def validate_integrity(self) -> ContentRevision:
        if canonical_payload_hash(self.payload) != self.payload_hash:
            raise ValueError("content payload hash mismatch")
        if self.validation is not None and self.validation.payload_hash != self.payload_hash:
            raise ValueError("validation receipt must bind to the revision payload")
        if self.status is not ContentRevisionStatus.DRAFT and self.validation is None:
            raise ValueError("validated and published revisions require validation")
        return self


class ContentChannel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_key: str = CONTENT_BUNDLE_KEY
    active_revision_id: UUID | None = None
    generation: int = Field(default=0, ge=0)
    updated_at: datetime


class ContentAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    request_key_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    action: ContentAuditAction
    revision_id: UUID
    previous_revision_id: UUID | None = None
    channel_generation: int = Field(ge=0)
    reason: str = Field(min_length=3, max_length=240)
    created_at: datetime


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()
