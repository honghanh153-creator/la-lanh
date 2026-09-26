from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

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
