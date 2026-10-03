from __future__ import annotations

import json
from typing import Any, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domains.astro.models import Tradition
from app.domains.content_rewrite.models import RewriteRequestEnvelope
from app.domains.readings.models import (
    ClaimSlotName,
    ReadingCandidate,
    ReadingPlan,
)
from app.domains.readings.renderers import DeterministicVietnameseRenderer, canonical_evidence_claim
from app.infrastructure.generation.base import (
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationRefusal,
    GenerationResult,
    GenerationSuccess,
    GenerationTransient,
    RewriteGenerationResult,
    RewriteGenerationSuccess,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser, UnsafeRewritePayload
from app.infrastructure.generation.schemas import (
    surface_output_contract,
    validate_surface_output,
)

OPENAI_RENDERER_VERSION = "openai-responses-v1"
OPENAI_PROMPT_VERSION = "chart-synthesis-v1"
OPENAI_REWRITE_PROMPT_VERSION = "surface-rewrite-v1"

_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["hook", "thesis", "manifestation", "transit", "micro_action"],
    "properties": {
        "hook": {"type": "string", "maxLength": 280},
        "thesis": {"type": "string", "maxLength": 700},
        "manifestation": {"type": "string", "maxLength": 700},
        "transit": {"anyOf": [{"type": "string", "maxLength": 500}, {"type": "null"}]},
        "micro_action": {"type": "string", "maxLength": 500},
    },
}

_DEVELOPER_INSTRUCTIONS = (
    "Write one reflective Vietnamese chart synthesis using only the supplied closed facts. "
    "Do not add astrology facts, dates, identities, diagnoses, predictions, professional advice, "
    "or urgent/decisive instructions. Keep transit null unless one supplied fact is transit."
)


class ResponseTransport(Protocol):
    async def create_response(
        self, request: dict[str, Any], *, timeout_seconds: float
    ) -> dict[str, Any]: ...


class RequestNotSentError(RuntimeError):
    """A transport failure proven to occur before request delivery."""


class RetryableTransportError(RuntimeError):
    """A retryable provider response that did not accept generation work."""


class AmbiguousTransportTimeout(RuntimeError):
    """Delivery may have occurred, so repeating the request is unsafe."""


class PermanentTransportError(RuntimeError):
    """A non-retryable provider or request failure."""


class _ProviderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    hook: str = Field(max_length=280)
    thesis: str = Field(max_length=700)
    manifestation: str = Field(max_length=700)
    transit: str | None = Field(max_length=500)
    micro_action: str = Field(max_length=500)


class OpenAIResponsesProvider:
    """One-shot Responses adapter with no provider state exposed to the domain."""

    def __init__(
        self,
        transport: ResponseTransport,
        *,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._transport = transport
        self._model = model
        self._timeout_seconds = timeout_seconds

    async def generate(self, plan: ReadingPlan) -> GenerationResult:
        if plan.tradition is not Tradition.WESTERN:
            return GenerationDisabled(code="generated_jyotish_disabled")
        try:
            request = _request(self._model, plan)
        except (IndexError, KeyError, ValueError):
            return GenerationPermanent(code="invalid_plan_allowlist")

        try:
            response = await self._transport.create_response(
                request,
                timeout_seconds=self._timeout_seconds,
            )
        except (RequestNotSentError, RetryableTransportError):
            return GenerationTransient(code="provider_unavailable", retry_safe=True)
        except AmbiguousTransportTimeout:
            return GenerationTransient(code="provider_timeout", retry_safe=False)
        except PermanentTransportError:
            return GenerationPermanent(code="provider_request_rejected")
        except Exception:
            return GenerationPermanent(code="provider_transport_failure")

        return _parse_response(response, plan)


class OpenAIRewriteProvider:
    """Stateless provider adapter for every registered rewrite surface."""

    def __init__(
        self,
        transport: ResponseTransport,
        *,
        model: str,
        timeout_seconds: float,
        minimiser: PrivacyMinimiser | None = None,
    ) -> None:
        self._transport = transport
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._minimiser = minimiser or PrivacyMinimiser()

    async def generate_rewrite(self, envelope: RewriteRequestEnvelope) -> RewriteGenerationResult:
        try:
            safe_payload = self._minimiser.minimise(
                envelope.key.surface,
                envelope.safe_payload,
            )
            request = _rewrite_request(self._model, envelope, safe_payload)
        except (LookupError, UnsafeRewritePayload, ValueError):
            return GenerationPermanent(code="unsafe_or_invalid_payload")

        try:
            response = await self._transport.create_response(
                request,
                timeout_seconds=self._timeout_seconds,
            )
        except (RequestNotSentError, RetryableTransportError):
            return GenerationTransient(code="provider_unavailable", retry_safe=True)
        except AmbiguousTransportTimeout:
            return GenerationTransient(code="provider_timeout", retry_safe=False)
        except PermanentTransportError:
            return GenerationPermanent(code="provider_request_rejected")
        except Exception:
            return GenerationPermanent(code="provider_transport_failure")

        return _parse_rewrite_response(response, envelope)


class OpenAISDKResponseTransport:
    """Narrow SDK boundary; SDK retries are disabled so the DB worker is sole retry owner."""

    def __init__(self, *, api_key: str) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, max_retries=0)

    async def create_response(
        self, request: dict[str, Any], *, timeout_seconds: float
    ) -> dict[str, Any]:
        from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

        try:
            response = await self._client.responses.create(
                **cast(Any, request),
                timeout=timeout_seconds,
            )
        except APITimeoutError as exc:
            raise AmbiguousTransportTimeout from exc
        except RateLimitError as exc:
            raise RetryableTransportError from exc
        except APIConnectionError as exc:
            cause_name = type(exc.__cause__).__name__
            if cause_name in {"ConnectError", "ConnectTimeout"}:
                raise RequestNotSentError from exc
            raise AmbiguousTransportTimeout from exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise RetryableTransportError from exc
            if exc.status_code in {408, 409} or exc.status_code >= 500:
                raise AmbiguousTransportTimeout from exc
            raise PermanentTransportError from exc
        return cast(dict[str, Any], response.model_dump(mode="json"))


def _request(model: str, plan: ReadingPlan) -> dict[str, Any]:
    safe_payload = _safe_payload(plan)
    return {
        "model": model,
        "store": False,
        "stream": False,
        "reasoning": {"effort": "none"},
        "max_output_tokens": 1200,
        "input": [
            {"role": "developer", "content": _DEVELOPER_INSTRUCTIONS},
            {
                "role": "user",
                "content": json.dumps(safe_payload, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "reading_candidate_v1",
                "strict": True,
                "schema": _OUTPUT_SCHEMA,
            }
        },
    }


def _rewrite_request(
    model: str,
    envelope: RewriteRequestEnvelope,
    safe_payload: dict[str, Any],
) -> dict[str, Any]:
    contract = surface_output_contract(envelope.key.surface)
    return {
        "model": model,
        "store": False,
        "stream": False,
        "reasoning": {"effort": "none"},
        "max_output_tokens": contract.max_output_tokens,
        "input": [
            {"role": "developer", "content": contract.developer_instruction},
            {
                "role": "user",
                "content": json.dumps(safe_payload, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": f"{envelope.key.surface.value}_rewrite_v1",
                "strict": True,
                "schema": contract.schema,
            }
        },
    }


def _safe_payload(plan: ReadingPlan) -> dict[str, Any]:
    factors: list[dict[str, Any]] = []
    for index, factor in enumerate(plan.factors, start=1):
        claim = canonical_evidence_claim(factor)
        labels = [
            {"name": slot.name.value, "value": slot.value}
            for slot in claim.slots
            if slot.name not in {ClaimSlotName.LONGITUDE, ClaimSlotName.ORB}
        ]
        factors.append(
            {
                "label": f"factor_{index}",
                "source": factor.source.value,
                "kind": factor.kind.value,
                "domain": factor.domain.value,
                "role": factor.role.value,
                "confidence": factor.confidence.value,
                "phase": factor.phase.value if factor.phase is not None else None,
                "labels": labels,
            }
        )
    hero_indexes = {
        factor.id: f"factor_{index}" for index, factor in enumerate(plan.factors, start=1)
    }
    return {
        "purpose": plan.purpose.value,
        "precision": plan.precision.value,
        "mode": plan.mode.value,
        "background_lens": plan.background_lens.value if plan.background_lens else None,
        "hero_factors": [hero_indexes[ref] for ref in plan.hero_factor_refs],
        "composition": {
            "natal_percent": plan.composition.natal_percent,
            "transit_percent": plan.composition.transit_percent,
        },
        "factors": factors,
    }


def _parse_response(response: dict[str, Any], plan: ReadingPlan) -> GenerationResult:
    status = response.get("status")
    if status == "incomplete":
        return GenerationIncomplete()
    if status != "completed":
        return GenerationPermanent(code="provider_failed")
    text_items: list[str] = []
    for output in response.get("output", []):
        if not isinstance(output, dict) or output.get("type") != "message":
            return GenerationPermanent(code="provider_invalid_response")
        for content in output.get("content", []):
            if not isinstance(content, dict):
                return GenerationPermanent(code="provider_invalid_response")
            if content.get("type") == "refusal":
                return GenerationRefusal()
            if content.get("type") != "output_text" or not isinstance(content.get("text"), str):
                return GenerationPermanent(code="provider_invalid_response")
            text_items.append(content["text"])
    if len(text_items) != 1:
        return GenerationIncomplete(code="provider_missing_output")
    try:
        output = _ProviderOutput.model_validate_json(text_items[0])
    except ValidationError:
        return GenerationPermanent(code="provider_invalid_output")

    baseline = DeterministicVietnameseRenderer().render(plan)
    candidate = ReadingCandidate(
        renderer_version=OPENAI_RENDERER_VERSION,
        plan_hash=plan.plan_hash,
        hook=output.hook,
        thesis=output.thesis,
        manifestation=output.manifestation,
        transit=output.transit,
        micro_action=output.micro_action,
        evidence=baseline.evidence,
        semantic_blueprint=baseline.semantic_blueprint,
    )
    return GenerationSuccess(candidate=candidate)


def _parse_rewrite_response(
    response: dict[str, Any], envelope: RewriteRequestEnvelope
) -> RewriteGenerationResult:
    status = response.get("status")
    if status == "incomplete":
        return GenerationIncomplete()
    if status != "completed":
        return GenerationPermanent(code="provider_failed")

    text_items: list[str] = []
    for output in response.get("output", []):
        if not isinstance(output, dict) or output.get("type") != "message":
            return GenerationPermanent(code="provider_invalid_response")
        for content in output.get("content", []):
            if not isinstance(content, dict):
                return GenerationPermanent(code="provider_invalid_response")
            if content.get("type") == "refusal":
                return GenerationRefusal()
            if content.get("type") != "output_text" or not isinstance(content.get("text"), str):
                return GenerationPermanent(code="provider_invalid_response")
            text_items.append(content["text"])
    if len(text_items) != 1:
        return GenerationIncomplete(code="provider_missing_output")
    try:
        raw_output = json.loads(text_items[0])
    except (TypeError, json.JSONDecodeError):
        return GenerationPermanent(code="provider_invalid_output")
    output = validate_surface_output(envelope.key.surface, raw_output)
    if output is None:
        return GenerationPermanent(code="provider_invalid_output")
    return RewriteGenerationSuccess(key=envelope.key, output=output)
