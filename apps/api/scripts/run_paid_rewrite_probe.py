from __future__ import annotations

import argparse
import asyncio
import json
import os
import stat
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.infrastructure.generation.base import (
    RewriteGenerationProvider,
    RewriteGenerationSuccess,
)
from app.infrastructure.generation.openai import (
    OPENAI_REWRITE_PROMPT_VERSION,
    OpenAIRewriteProvider,
    OpenAISDKResponseTransport,
)
from app.infrastructure.generation.pricing import (
    GPT_6_LUNA_STANDARD_2026_10_04,
    USD_NANOS_PER_DOLLAR,
)
from app.infrastructure.generation.schemas import surface_output_contract

MODEL = "gpt-6-luna"
HARD_DAILY_LIMIT_USD = Decimal("1.00")


def _read_api_key(path: Path) -> str:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError("API key file must not be readable by group or other users")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("API key file is empty")
    return value


def _synthetic_request() -> RewriteRequestEnvelope:
    payload = {
        "context": "communication",
        "scene_key": "psychology:missing-context:communication",
        "action_key": "psychology:ask-one-clear-question",
        "title_meaning": "Chưa rõ thì chưa cần kết luận.",
        "scene_meaning": "Khi một tin nhắn ngắn khiến ý của người kia chưa rõ.",
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
                "labels": [{"name": "sign", "value": "Song Ngư"}],
            }
        ],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.DAILY_HOME,
            owner=ArtifactOwnerKey(namespace="readings", key="synthetic-paid-probe"),
            blueprint_hash=sha256(canonical.encode()).hexdigest(),
            model_version=MODEL,
            prompt_version=OPENAI_REWRITE_PROMPT_VERSION,
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v2",
            candidate_variant="paid-probe",
        ),
        authorization_receipt_id="synthetic-probe-no-user-data",
        safe_payload=payload,
    )


def _estimated_max_cost_usd(request: RewriteRequestEnvelope) -> Decimal:
    contract = surface_output_contract(request.key.surface)
    # UTF-8 bytes are a deliberately conservative upper bound for prompt token count here.
    input_upper_bound = (
        len(json.dumps(request.safe_payload, ensure_ascii=False).encode())
        + len(contract.developer_instruction.encode())
        + len(json.dumps(contract.schema).encode())
        + 512
    )
    nanos = GPT_6_LUNA_STANDARD_2026_10_04.cost_nanos(
        input_tokens=input_upper_bound,
        output_tokens=contract.max_output_tokens,
    )
    return Decimal(nanos) / Decimal(USD_NANOS_PER_DOLLAR)


def _requirements_pass(request: RewriteRequestEnvelope, output: Mapping[str, object]) -> bool:
    section_fields = {
        "hook": ("title",),
        "manifestation": ("scene",),
        "micro_action": ("action",),
        "all": ("title", "scene", "action"),
    }
    requirements = request.safe_payload.get("requirements")
    if not isinstance(requirements, list):
        return False
    for requirement in requirements:
        if not isinstance(requirement, dict):
            return False
        fields = section_fields.get(str(requirement.get("section")))
        markers = requirement.get("markers")
        min_matches = requirement.get("min_matches")
        if fields is None or not isinstance(markers, list) or not isinstance(min_matches, int):
            return False
        text = " ".join(str(output.get(field, "")) for field in fields).casefold()
        if sum(str(marker).casefold() in text for marker in markers) < min_matches:
            return False
    return True


async def _run(
    request: RewriteRequestEnvelope,
    provider: RewriteGenerationProvider,
) -> dict[str, object]:
    result = await provider.generate_rewrite(request)
    if not isinstance(result, RewriteGenerationSuccess):
        return {"status": result.kind, "code": getattr(result, "code", "unknown")}
    if result.input_tokens is None or result.output_tokens is None:
        return {"status": "failed", "code": "provider_usage_missing"}
    gate = evaluate_daily_rewrite(
        result.output,
        source_scene=str(request.safe_payload["scene_meaning"]),
        source_action=str(request.safe_payload["action_meaning"]),
    )
    requirements_passed = _requirements_pass(request, result.output)
    actual_nanos = GPT_6_LUNA_STANDARD_2026_10_04.cost_nanos(
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    return {
        "status": "completed",
        "gate_passed": gate.passed and requirements_passed,
        "gate_failure_codes": gate.failure_codes
        + (() if requirements_passed else ("daily_requirement_marker_missing",)),
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cost_usd": f"{Decimal(actual_nanos) / Decimal(USD_NANOS_PER_DOLLAR):.8f}",
        "pricing_version": GPT_6_LUNA_STANDARD_2026_10_04.version,
        "responses_application_state_stored": False,
        "local_generated_output_retained": False,
        "provider_abuse_monitoring_may_retain_up_to_days": 30,
    }


def _parse_confirmed_limit(raw: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError("confirmed USD limit must be a decimal amount") from error
    if value != HARD_DAILY_LIMIT_USD:
        raise ValueError("paid probe requires an explicit --confirm-max-usd 1.00")
    return value


def _reserve_daily_probe(state_dir: Path, *, now: datetime | None = None) -> Path:
    current = now or datetime.now(UTC)
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_dir.chmod(0o700)
    receipt = state_dir / f"paid-probe-{current.date().isoformat()}.json"
    try:
        descriptor = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise ValueError("paid probe already reserved for this UTC day") from error
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(
            {
                "reserved_at": current.isoformat(),
                "limit_usd": str(HARD_DAILY_LIMIT_USD),
                "payload": "synthetic-only",
            },
            stream,
            sort_keys=True,
        )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one privacy-safe paid rewrite probe")
    parser.add_argument("--api-key-file", type=Path, required=True)
    parser.add_argument("--confirm-max-usd", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    args = parser.parse_args()

    confirmed_limit = _parse_confirmed_limit(args.confirm_max_usd)
    request = _synthetic_request()
    estimated_max = _estimated_max_cost_usd(request)
    if estimated_max >= confirmed_limit:
        raise SystemExit("Probe blocked: estimated maximum cost reaches the confirmed limit")
    api_key = _read_api_key(args.api_key_file)
    _reserve_daily_probe(Path.home() / ".local" / "state" / "la-lanh")
    provider = OpenAIRewriteProvider(
        OpenAISDKResponseTransport(api_key=api_key),
        model=MODEL,
        timeout_seconds=args.timeout_seconds,
    )
    result = asyncio.run(_run(request, provider))
    result["estimated_max_usd"] = f"{estimated_max:.8f}"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result.get("status") != "completed" or result.get("gate_passed") is not True:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
