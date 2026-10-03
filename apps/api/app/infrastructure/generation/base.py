from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import JsonValue

from app.domains.content_rewrite.models import RewriteArtifactKey, RewriteRequestEnvelope
from app.domains.readings.models import ReadingCandidate, ReadingPlan


@dataclass(frozen=True, slots=True)
class GenerationSuccess:
    candidate: ReadingCandidate
    kind: Literal["success"] = "success"


@dataclass(frozen=True, slots=True)
class GenerationRefusal:
    kind: Literal["refusal"] = "refusal"
    code: str = "provider_refusal"


@dataclass(frozen=True, slots=True)
class GenerationIncomplete:
    kind: Literal["incomplete"] = "incomplete"
    code: str = "provider_incomplete"


@dataclass(frozen=True, slots=True)
class GenerationTransient:
    kind: Literal["transient"] = "transient"
    code: str = "provider_unavailable"
    retry_safe: bool = False


@dataclass(frozen=True, slots=True)
class GenerationPermanent:
    kind: Literal["permanent"] = "permanent"
    code: str = "provider_invalid_response"


@dataclass(frozen=True, slots=True)
class GenerationDisabled:
    kind: Literal["disabled"] = "disabled"
    code: str = "provider_disabled"


type GenerationResult = (
    GenerationSuccess
    | GenerationRefusal
    | GenerationIncomplete
    | GenerationTransient
    | GenerationPermanent
    | GenerationDisabled
)


class GenerationProvider(Protocol):
    async def generate(self, plan: ReadingPlan) -> GenerationResult: ...


class DisabledGenerationProvider:
    async def generate(self, plan: ReadingPlan) -> GenerationResult:
        del plan
        return GenerationDisabled()


@dataclass(frozen=True, slots=True)
class RewriteGenerationSuccess:
    """Provider prose bound to the immutable server-owned artifact key."""

    key: RewriteArtifactKey
    output: dict[str, JsonValue]
    kind: Literal["success"] = "success"


type RewriteGenerationResult = (
    RewriteGenerationSuccess
    | GenerationRefusal
    | GenerationIncomplete
    | GenerationTransient
    | GenerationPermanent
    | GenerationDisabled
)


class RewriteGenerationProvider(Protocol):
    async def generate_rewrite(
        self, request: RewriteRequestEnvelope
    ) -> RewriteGenerationResult: ...


class DisabledRewriteGenerationProvider:
    async def generate_rewrite(self, request: RewriteRequestEnvelope) -> RewriteGenerationResult:
        del request
        return GenerationDisabled()
