from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import JsonValue

from app.domains.content_rewrite.models import RewriteRequestEnvelope
from app.infrastructure.generation.base import (
    GenerationPermanent,
    RewriteGenerationResult,
    RewriteGenerationSuccess,
)
from scripts.run_paid_rewrite_probe import (
    HARD_DAILY_LIMIT_USD,
    _estimated_max_cost_usd,
    _parse_confirmed_limit,
    _read_api_key,
    _requirements_pass,
    _reserve_daily_probe,
    _run,
    _synthetic_request,
)


def test_paid_probe_requires_exact_confirmed_daily_limit() -> None:
    assert _parse_confirmed_limit("1.00") == HARD_DAILY_LIMIT_USD
    with pytest.raises(ValueError, match="explicit"):
        _parse_confirmed_limit("0.99")
    with pytest.raises(ValueError, match="explicit"):
        _parse_confirmed_limit("2.00")


def test_paid_probe_rejects_key_file_with_group_or_other_access(tmp_path: Path) -> None:
    path = tmp_path / "openai_api_key"
    path.write_text("test-key", encoding="utf-8")
    path.chmod(0o640)

    with pytest.raises(ValueError, match="group or other"):
        _read_api_key(path)

    path.chmod(0o600)
    assert _read_api_key(path) == "test-key"


def test_paid_probe_uses_only_synthetic_safe_payload_below_one_dollar() -> None:
    request = _synthetic_request()
    serialized = request.model_dump_json().casefold()

    assert request.authorization_receipt_id == "synthetic-probe-no-user-data"
    assert "birth" not in serialized
    assert "latitude" not in serialized
    assert '"question":' not in serialized
    assert _estimated_max_cost_usd(request) < Decimal("1.00")


def test_paid_probe_can_be_reserved_only_once_per_utc_day(tmp_path: Path) -> None:
    now = datetime(2026, 10, 4, 12, tzinfo=UTC)

    receipt = _reserve_daily_probe(tmp_path, now=now)

    assert receipt.stat().st_mode & 0o077 == 0
    with pytest.raises(ValueError, match="already reserved"):
        _reserve_daily_probe(tmp_path, now=now)


def test_paid_probe_requires_semantic_markers_in_generated_output() -> None:
    request = _synthetic_request()

    assert _requirements_pass(
        request,
        {
            "title": "Chưa rõ thì chưa cần kết luận.",
            "scene": "Khi một tin nhắn ngắn khiến ý của người kia chưa rõ.",
            "action": "Hỏi lại một câu rõ ràng trước khi kết luận.",
        },
    )
    assert not _requirements_pass(
        request,
        {
            "title": "Chậm lại một chút.",
            "scene": "Khi lịch làm việc thay đổi, bạn thấy mình mất nhịp.",
            "action": "Chọn một việc cần làm trước.",
        },
    )


class FakeProvider:
    def __init__(self, result: RewriteGenerationResult) -> None:
        self.result = result

    async def generate_rewrite(self, request: RewriteRequestEnvelope) -> RewriteGenerationResult:
        del request
        return self.result


async def test_paid_probe_reports_only_gate_usage_cost_and_retention_metadata() -> None:
    request = _synthetic_request()
    generated: dict[str, JsonValue] = {
        "title": "Chưa rõ thì chưa cần kết luận.",
        "scene": "Khi một tin nhắn ngắn khiến ý của người kia chưa rõ.",
        "action": "Hỏi lại một câu rõ ràng trước khi kết luận.",
    }

    report = await _run(
        request,
        FakeProvider(
            RewriteGenerationSuccess(
                key=request.key,
                output=generated,
                input_tokens=500,
                output_tokens=100,
            )
        ),
    )

    assert report["status"] == "completed"
    assert report["gate_passed"] is True
    assert report["responses_application_state_stored"] is False
    assert report["provider_abuse_monitoring_may_retain_up_to_days"] == 30
    assert not set(generated).intersection(report)


async def test_paid_probe_reports_provider_failure_without_generated_content() -> None:
    report = await _run(
        _synthetic_request(),
        FakeProvider(GenerationPermanent(code="provider_request_rejected")),
    )

    assert report == {"status": "permanent", "code": "provider_request_rejected"}
