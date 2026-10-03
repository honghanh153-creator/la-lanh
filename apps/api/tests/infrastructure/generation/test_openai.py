import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.config import PINNED_OPENAI_MODEL, Settings
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, Tradition
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.infrastructure.generation import build_generation_provider
from app.infrastructure.generation.base import (
    DisabledGenerationProvider,
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationRefusal,
    GenerationSuccess,
    GenerationTransient,
    RewriteGenerationSuccess,
)
from app.infrastructure.generation.openai import (
    AmbiguousTransportTimeout,
    OpenAIResponsesProvider,
    OpenAIRewriteProvider,
    OpenAISDKResponseTransport,
)

MODEL = "gpt-6-luna"


class FakeTransport:
    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response
        self.requests: list[tuple[dict[str, Any], float]] = []

    async def create_response(
        self, request: dict[str, Any], *, timeout_seconds: float
    ) -> dict[str, Any]:
        self.requests.append((request, timeout_seconds))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeSDKResponse:
    def model_dump(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        return {}


def _plan(*, tradition: Tradition = Tradition.WESTERN):  # type: ignore[no-untyped-def]
    engine = NatalChartEngine()
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 12, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        ),
        (
            CalculationConfig.western_recommended()
            if tradition is Tradition.WESTERN
            else CalculationConfig.jyotish_recommended()
        ),
    )
    return ReadingPlanner().plan(chart, purpose=ReadingPurpose.READING_DETAIL)


def _output(**overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {
        "hook": "Hai nhịp khác nhau có thể cùng xuất hiện.",
        "thesis": "Một phần muốn tiến tới, phần khác muốn kiểm tra thêm.",
        "manifestation": "Điều này có thể lộ ra khi bạn nhận việc rồi mới cân lại sức.",
        "transit": None,
        "micro_action": "Thử dừng một nhịp trước khi nhận thêm việc.",
    }
    payload.update(overrides)
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(payload)}],
            }
        ],
    }


def _assert_closed_schema(node: object) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False
        for value in node.values():
            _assert_closed_schema(value)
    elif isinstance(node, list):
        for value in node:
            _assert_closed_schema(value)


@pytest.mark.asyncio
async def test_one_shot_request_is_stateless_strict_minimized_and_allowlisted() -> None:
    transport = FakeTransport(_output())
    provider = OpenAIResponsesProvider(transport, model=MODEL, timeout_seconds=17.0)
    plan = _plan()

    result = await provider.generate(plan)

    assert isinstance(result, GenerationSuccess)
    assert len(transport.requests) == 1
    request, timeout = transport.requests[0]
    assert timeout == 17.0
    assert request["model"] == MODEL
    assert request["store"] is False
    assert request["stream"] is False
    assert request["reasoning"] == {"effort": "none"}
    assert {"tools", "conversation", "previous_response_id", "background", "include"}.isdisjoint(
        request
    )
    output_format = request["text"]["format"]
    assert output_format["type"] == "json_schema"
    assert output_format["strict"] is True
    _assert_closed_schema(output_format["schema"])

    serialized = json.dumps(request, ensure_ascii=False).lower()
    assert plan.plan_hash.lower() not in serialized
    assert plan.config_hash.lower() not in serialized
    assert "1990-01-01" not in serialized
    assert "10.8231" not in serialized
    assert "106.6297" not in serialized
    assert "guest_id" not in serialized
    assert "profile_id" not in serialized
    assert "chart_id" not in serialized
    assert '"longitude"' not in serialized
    assert '"orb"' not in serialized
    assert "factor_1" in serialized
    assert "mặt trời" in serialized
    assert result.candidate.semantic_blueprint is not None


def _rewrite_envelope() -> RewriteRequestEnvelope:
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.DAILY_HOME,
            owner=ArtifactOwnerKey(namespace="readings", key="daily:anonymous"),
            blueprint_hash="a" * 64,
            model_version=MODEL,
            prompt_version="surface-rewrite-v1",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
        ),
        authorization_receipt_id="consent-receipt",
        safe_payload={
            "context": "relationships",
            "scene_key": "psychology:missing-context:relationships",
            "action_key": "psychology:ask-one-clear-question",
            "title_meaning": "Chưa rõ thì chưa cần kết luận.",
            "scene_meaning": "Một tin nhắn ngắn khiến ý của người kia chưa rõ.",
            "action_meaning": "Hỏi lại một câu rõ ràng trước khi kết luận.",
            "requirements": [
                {
                    "key": "daily.missing-context",
                    "section": "manifestation",
                    "markers": ["tin nhắn", "chưa rõ"],
                    "min_matches": 1,
                }
            ],
            "evidence": [
                {
                    "label": "factor_1",
                    "source": "natal",
                    "kind": "planet_placement",
                    "domain": "communication",
                    "role": "primary",
                    "confidence": "high",
                    "labels": [{"name": "body", "value": "Mặt Trời"}],
                }
            ],
        },
    )


@pytest.mark.asyncio
async def test_surface_rewrite_request_uses_luna_stateless_schema_and_returns_only_prose() -> None:
    response = {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            {
                                "title": "Đừng tự điền vào chỗ trống.",
                                "scene": "Một tin nhắn ngắn làm bạn chưa rõ ý người kia.",
                                "action": "Hỏi lại một câu rõ ràng trước khi kết luận.",
                            }
                        ),
                    }
                ],
            }
        ],
    }
    transport = FakeTransport(response)
    provider = OpenAIRewriteProvider(transport, model=MODEL, timeout_seconds=8)
    envelope = _rewrite_envelope()

    result = await provider.generate_rewrite(envelope)

    assert isinstance(result, RewriteGenerationSuccess)
    assert result.key == envelope.key
    assert set(result.output) == {"title", "scene", "action"}
    request, timeout = transport.requests[0]
    assert timeout == 8
    assert request["model"] == PINNED_OPENAI_MODEL
    assert request["store"] is False
    assert request["reasoning"] == {"effort": "none"}
    assert request["max_output_tokens"] <= 300
    assert request["text"]["format"]["strict"] is True
    assert request["text"]["format"]["schema"]["additionalProperties"] is False
    serialized = json.dumps(request, ensure_ascii=False).lower()
    assert envelope.authorization_receipt_id not in serialized
    assert envelope.key.owner.key not in serialized
    assert envelope.key.blueprint_hash not in serialized


@pytest.mark.asyncio
async def test_surface_rewrite_rejects_extra_output_and_unsafe_input_without_sending() -> None:
    transport = FakeTransport(
        {
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {"title": "a", "scene": "b", "action": "c", "score": 99}
                            ),
                        }
                    ],
                }
            ],
        }
    )
    provider = OpenAIRewriteProvider(transport, model=MODEL, timeout_seconds=8)

    invalid_output = await provider.generate_rewrite(_rewrite_envelope())
    assert isinstance(invalid_output, GenerationPermanent)

    unsafe = _rewrite_envelope().model_copy(
        update={
            "safe_payload": {
                **_rewrite_envelope().safe_payload,
                "birth_date": "1990-03-15",
            }
        }
    )
    before = len(transport.requests)
    unsafe_result = await provider.generate_rewrite(unsafe)
    assert isinstance(unsafe_result, GenerationPermanent)
    assert unsafe_result.code == "unsafe_or_invalid_payload"
    assert len(transport.requests) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "expected_type"),
    [
        (
            {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "refusal", "refusal": "private refusal detail"}],
                    }
                ],
            },
            GenerationRefusal,
        ),
        (
            {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}},
            GenerationIncomplete,
        ),
        (
            {"status": "failed", "error": {"message": "private provider failure"}},
            GenerationPermanent,
        ),
        (_output(unknown="not allowed"), GenerationPermanent),
        (
            {
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "{"}]}],
            },
            GenerationPermanent,
        ),
    ],
)
async def test_terminal_response_shapes_are_typed_and_redacted(
    response: dict[str, Any], expected_type: type[object]
) -> None:
    provider = OpenAIResponsesProvider(FakeTransport(response), model=MODEL, timeout_seconds=10)

    result = await provider.generate(_plan())

    assert isinstance(result, expected_type)
    assert "private refusal detail" not in repr(result)
    assert "private provider failure" not in repr(result)
    assert "not allowed" not in repr(result)


@pytest.mark.asyncio
async def test_timeout_after_send_is_transient_but_never_retry_safe_or_leaky() -> None:
    provider = OpenAIResponsesProvider(
        FakeTransport(AmbiguousTransportTimeout("secret prompt and transport internals")),
        model=MODEL,
        timeout_seconds=3,
    )

    result = await provider.generate(_plan())

    assert isinstance(result, GenerationTransient)
    assert result.retry_safe is False
    assert "secret" not in repr(result)


@pytest.mark.asyncio
async def test_generated_jyotish_fails_closed_without_transport_call() -> None:
    transport = FakeTransport(_output())
    provider = OpenAIResponsesProvider(transport, model=MODEL, timeout_seconds=10)

    result = await provider.generate(_plan(tradition=Tradition.JYOTISH))

    assert isinstance(result, GenerationDisabled)
    assert transport.requests == []


@pytest.mark.asyncio
async def test_pinned_sdk_transport_disables_sdk_retries_and_forwards_timeout() -> None:
    transport = OpenAISDKResponseTransport(api_key="test-key")
    fake_create = AsyncMock(return_value=FakeSDKResponse())
    transport._client.responses.create = fake_create  # type: ignore[method-assign]

    await transport.create_response(
        {"model": MODEL, "store": False, "stream": False, "input": "safe"},
        timeout_seconds=4.5,
    )

    assert transport._client.max_retries == 0
    call = fake_create.await_args
    assert call is not None
    assert call.kwargs["timeout"] == 4.5
    assert call.kwargs["store"] is False


def test_provider_is_off_by_default_and_enabled_settings_fail_closed() -> None:
    settings = Settings(environment="test")

    assert isinstance(build_generation_provider(settings), DisabledGenerationProvider)
    killed = Settings(
        environment="test",
        generation_provider="openai",
        generation_governance_approved=True,
        generation_openai_api_key="secret",
    )
    assert isinstance(build_generation_provider(killed), DisabledGenerationProvider)

    with pytest.raises(ValidationError, match="governance"):
        Settings(
            environment="test",
            generation_enabled=True,
            generation_provider="openai",
            generation_openai_api_key="secret",
        )

    with pytest.raises(ValidationError, match="lease"):
        Settings(
            environment="test",
            generation_timeout_seconds=60,
            generation_lease_seconds=30,
        )
