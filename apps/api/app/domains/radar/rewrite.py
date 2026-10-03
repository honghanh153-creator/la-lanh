from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from hashlib import sha256
from typing import Literal, cast
from uuid import UUID

from pydantic import JsonValue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.authorization import (
    RewriteConsentScope,
    content_rewrite_receipt_id,
)
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.content_rewrite.service import RewriteProjectionDecision, RewriteProjector
from app.domains.radar.tables import RadarRequestRow
from app.infrastructure.crypto import EnvelopeCipher

RADAR_REWRITE_RENDERER_VERSION = "gpt-6-luna-radar-v1"
RADAR_REWRITE_GATE_VERSION = "relationship-rewrite-gates/v1"

RadarPerspective = Literal["owner", "recipient"]

_SECTION_OUTPUT = {
    "fit": "strengths",
    "friction": "frictions",
    "perspective": "asymmetry",
    "check": "prompt",
}
_STOP_WORDS = {
    "bạn",
    "mình",
    "người",
    "kia",
    "một",
    "những",
    "điều",
    "này",
    "đang",
    "được",
    "trong",
    "và",
    "của",
    "cho",
    "với",
    "thể",
    "hai",
}
_FORBIDDEN = (
    "định mệnh",
    "soulmate",
    "chắc chắn yêu",
    "chắc chắn thành công",
    "tỉ lệ thành công",
    "tỷ lệ thành công",
    "thử lòng",
    "theo dõi họ",
    "kiểm tra điện thoại",
)


def radar_rewrite_owner(
    guest_id: UUID,
    request_id: UUID,
    perspective: RadarPerspective,
) -> ArtifactOwnerKey:
    return ArtifactOwnerKey(
        namespace="radar",
        key=f"radar|{guest_id}|{request_id}|{perspective}",
    )


def _parse_owner(owner: ArtifactOwnerKey) -> tuple[UUID, UUID, RadarPerspective]:
    parts = owner.key.split("|")
    if (
        owner.namespace != "radar"
        or len(parts) != 4
        or parts[0] != "radar"
        or parts[3] not in {"owner", "recipient"}
    ):
        raise ValueError("invalid Radar rewrite owner")
    return UUID(parts[1]), UUID(parts[2]), cast(RadarPerspective, parts[3])


def radar_blueprint_hash(projection: dict[str, object]) -> str:
    canonical = json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode()).hexdigest()


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[^\W_]+", _fold(value))
        if len(token) >= 4 and token not in _STOP_WORDS
    }


def _section(projection: dict[str, object], key: str) -> dict[str, object] | None:
    sections = projection.get("sections")
    if not isinstance(sections, list):
        return None
    for raw in sections:
        if isinstance(raw, dict) and raw.get("key") == key:
            return cast(dict[str, object], raw)
    return None


def _section_meaning(section: dict[str, object]) -> str:
    parts: list[str] = []
    for key in ("title", "body"):
        value = section.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    scene = section.get("scene")
    if isinstance(scene, dict):
        parts.extend(
            str(scene[key]).strip()
            for key in ("title", "body")
            if isinstance(scene.get(key), str) and str(scene[key]).strip()
        )
    perspectives = section.get("perspectives")
    if isinstance(perspectives, list):
        for item in perspectives:
            if isinstance(item, dict):
                parts.extend(
                    str(value).strip()
                    for value in item.values()
                    if isinstance(value, str) and value.strip()
                )
    highlights = section.get("highlights")
    if isinstance(highlights, list):
        for item in highlights[:2]:
            if isinstance(item, dict):
                for key in ("title", "body"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        parts.append(value.strip())
    return " ".join(parts)


def _bounded_meaning(value: str, *, limit: int = 1_150) -> str:
    if len(value) <= limit:
        return value
    shortened = value[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{shortened}."


def _band(value: object) -> Literal["low", "medium", "high"]:
    if not isinstance(value, int | float) or value < 34:
        return "low"
    if value < 67:
        return "medium"
    return "high"


def _safe_dimensions(projection: dict[str, object]) -> list[dict[str, JsonValue]]:
    mapping = {
        "resonance": "attraction",
        "coordination": "coordination",
        "friction": "friction",
    }
    dimensions: list[dict[str, JsonValue]] = []
    raw_map = projection.get("compatibility_map")
    if isinstance(raw_map, list):
        for raw in raw_map:
            if not isinstance(raw, dict) or raw.get("key") not in mapping:
                continue
            dimensions.append(
                {
                    "dimension": mapping[cast(str, raw["key"])],
                    "band": _band(raw.get("value")),
                    "direction": "mutual",
                    "meaning_keys": [cast(str, raw["key"])],
                }
            )
    perspective = _section(projection, "perspective")
    if perspective is not None and perspective.get("evidence"):
        dimensions.append(
            {
                "dimension": "asymmetry",
                "band": "medium",
                "direction": "mixed",
                "meaning_keys": ["two_way_experience"],
            }
        )
    return dimensions


def _safe_evidence(projection: dict[str, object]) -> list[dict[str, JsonValue]]:
    evidence: list[dict[str, JsonValue]] = []
    seen: set[str] = set()
    sections = projection.get("sections")
    if not isinstance(sections, list):
        return evidence
    for section in sections:
        if not isinstance(section, dict):
            continue
        domain = str(section.get("key", "relationship"))
        receipts = section.get("evidence")
        if not isinstance(receipts, list):
            continue
        for receipt in receipts:
            if not isinstance(receipt, dict):
                continue
            source_id = str(receipt.get("evidence_id", ""))
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)
            technical = receipt.get("technical")
            labels: list[dict[str, str]] = []
            strength = 0.5
            if isinstance(technical, dict):
                for source_key, label_name in (
                    ("body_a", "body"),
                    ("body_b", "other_body"),
                    ("aspect", "aspect"),
                    ("house", "house"),
                ):
                    value = technical.get(source_key)
                    if isinstance(value, str | int) and str(value).strip():
                        labels.append({"name": label_name, "value": str(value)[:64]})
                if isinstance(technical.get("strength"), int | float):
                    strength = float(technical["strength"])
            source = str(receipt.get("source", "relationship"))
            kind = {
                "synastry": "synastry_aspect",
                "composite_midpoint": "composite_aspect",
                "house_overlay": "house_overlay",
            }.get(source, "relationship_signal")
            evidence.append(
                {
                    "label": f"signal_{len(evidence) + 1}",
                    "source": "relationship",
                    "kind": kind,
                    "domain": re.sub(r"[^a-z0-9_]", "_", domain.casefold())[:40],
                    "role": "supporting",
                    "confidence": (
                        "high" if strength >= 0.75 else "medium" if strength >= 0.45 else "limited"
                    ),
                    "labels": cast(JsonValue, labels[:8]),
                }
            )
            if len(evidence) == 16:
                return evidence
    return evidence


def compile_radar_rewrite_request(
    guest_id: UUID,
    request_id: UUID,
    perspective: RadarPerspective,
    projection: dict[str, object],
    *,
    context: str,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope | None:
    dimensions = _safe_dimensions(projection)
    evidence = _safe_evidence(projection)
    if not dimensions or not evidence:
        return None
    source_sections: list[dict[str, str]] = []
    headline = projection.get("headline")
    summary = projection.get("summary")
    if not isinstance(headline, str) or not isinstance(summary, str):
        return None
    source_sections.append(
        {"key": "overview", "meaning": _bounded_meaning(f"{headline} {summary}")}
    )
    for section_key, safe_key in (
        ("fit", "strength"),
        ("friction", "friction"),
        ("perspective", "asymmetry"),
        ("check", "prompt"),
    ):
        section = _section(projection, section_key)
        if section is None:
            return None
        meaning = _section_meaning(section)
        if not meaning:
            return None
        source_sections.append({"key": safe_key, "meaning": _bounded_meaning(meaning)})
    spec = canonical_surface_registry().require(RewriteSurface.RADAR)
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.RADAR,
            owner=radar_rewrite_owner(guest_id, request_id, perspective),
            blueprint_hash=radar_blueprint_hash(projection),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=spec.schema_version,
            gate_version=spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(
            guest_id,
            scope=RewriteConsentScope.RADAR,
        ),
        safe_payload={
            "context": context
            if context in {"crush", "friend", "partner", "someone"}
            else "someone",
            "low_signal": False,
            "dimensions": cast(JsonValue, dimensions),
            "source_sections": cast(JsonValue, source_sections),
            "evidence": cast(JsonValue, evidence),
        },
    )


def _has_meaning(candidate: str, source: str) -> bool:
    return len(_tokens(candidate) & _tokens(source)) >= 2


def rewrite_radar_projection(
    baseline: dict[str, object],
    output: dict[str, JsonValue],
) -> dict[str, object] | None:
    if set(output) != {"overview", "strengths", "frictions", "asymmetry", "prompt"}:
        return None
    overview = output.get("overview")
    strengths = output.get("strengths")
    frictions = output.get("frictions")
    asymmetry = output.get("asymmetry")
    prompt = output.get("prompt")
    if (
        not isinstance(overview, str)
        or not overview.strip()
        or not isinstance(strengths, list)
        or not 1 <= len(strengths) <= 3
        or not all(isinstance(item, str) and item.strip() for item in strengths)
        or not isinstance(frictions, list)
        or not 1 <= len(frictions) <= 3
        or not all(isinstance(item, str) and item.strip() for item in frictions)
        or not isinstance(asymmetry, str)
        or not asymmetry.strip()
        or not isinstance(prompt, str)
        or not prompt.strip()
    ):
        return None
    strength_texts = cast(list[str], strengths)
    friction_texts = cast(list[str], frictions)
    texts = [overview, *strength_texts, *friction_texts, asymmetry, prompt]
    folded = " ".join(_fold(text) for text in texts)
    if any(term in folded for term in (_fold(term) for term in _FORBIDDEN)):
        return None
    if re.search(r"\b\d{1,3}\s*(?:%|/\s*100)\b", folded):
        return None
    if len(re.findall(r"[^\W_]+", " ".join(texts))) > 900:
        return None

    fit = _section(baseline, "fit")
    friction = _section(baseline, "friction")
    perspective = _section(baseline, "perspective")
    check = _section(baseline, "check")
    headline = baseline.get("headline")
    summary = baseline.get("summary")
    if not all(section is not None for section in (fit, friction, perspective, check)):
        return None
    if not isinstance(headline, str) or not isinstance(summary, str):
        return None
    if not _has_meaning(overview, f"{headline} {summary}"):
        return None
    if not all(
        _has_meaning(item, _section_meaning(cast(dict[str, object], fit)))
        for item in strength_texts
    ):
        return None
    if not all(
        _has_meaning(item, _section_meaning(cast(dict[str, object], friction)))
        for item in friction_texts
    ):
        return None
    if not _has_meaning(asymmetry, _section_meaning(cast(dict[str, object], perspective))):
        return None
    if not _has_meaning(prompt, _section_meaning(cast(dict[str, object], check))):
        return None

    candidate = json.loads(json.dumps(baseline, ensure_ascii=False))
    if not isinstance(candidate, dict):
        return None
    candidate["summary"] = overview.strip()
    signature = candidate.get("pair_signature")
    if isinstance(signature, dict):
        signature["summary"] = overview.strip()
    replacements = {
        "fit": "\n\n".join(item.strip() for item in strength_texts),
        "friction": "\n\n".join(item.strip() for item in friction_texts),
        "perspective": asymmetry.strip(),
        "check": prompt.strip(),
    }
    for key, body in replacements.items():
        section = _section(cast(dict[str, object], candidate), key)
        if section is None:
            return None
        section["body"] = body
    metadata = candidate.get("metadata")
    if not isinstance(metadata, dict):
        return None
    metadata["renderer_version"] = RADAR_REWRITE_RENDERER_VERSION
    metadata["gate_version"] = RADAR_REWRITE_GATE_VERSION
    return cast(dict[str, object], candidate)


class RadarRewriteProjector(RewriteProjector):
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope

    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
    ) -> RewriteProjectionDecision:
        if request.key.surface is not RewriteSurface.RADAR:
            return RewriteProjectionDecision(accepted=False, failure_code="unsupported_surface")
        try:
            guest_id, request_id, perspective = _parse_owner(request.key.owner)
        except ValueError:
            return RewriteProjectionDecision(accepted=False, failure_code="invalid_owner")

        async with self._sessions() as database, database.begin():
            row = await database.scalar(
                select(RadarRequestRow).where(RadarRequestRow.id == request_id).with_for_update()
            )
            if (
                row is None
                or row.status != "completed"
                or row.result_ciphertext is None
                or row.withdrawn_at is not None
                or row.expires_at <= completed_at
            ):
                return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
            expected_guest = (
                row.owner_guest_id if perspective == "owner" else row.recipient_guest_id
            )
            if expected_guest != guest_id:
                return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
            stored = self._decrypt(row)
            raw_projection = stored.get(perspective) if "owner" in stored else stored
            if not isinstance(raw_projection, dict):
                return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
            baseline = cast(dict[str, object], raw_projection)
            metadata = baseline.get("metadata")
            if (
                not isinstance(metadata, dict)
                or metadata.get("renderer_version") != "radar-living-dossier-v1"
                or radar_blueprint_hash(baseline) != request.key.blueprint_hash
            ):
                return RewriteProjectionDecision(
                    accepted=False,
                    failure_code="stale_domain_version",
                )
            candidate = rewrite_radar_projection(baseline, output)
            if candidate is None:
                return RewriteProjectionDecision(accepted=False, failure_code="radar_gate_rejected")
            if "owner" in stored:
                stored[perspective] = candidate
            else:
                stored = candidate
            row.result_ciphertext = self._encrypt(row.id, stored)
            await database.flush([row])

        receipt = sha256(
            f"{request.key.cache_key}\x00{request_id}\x00{perspective}\x00{RADAR_REWRITE_GATE_VERSION}".encode()
        ).hexdigest()
        return RewriteProjectionDecision(accepted=True, gate_receipt_id=receipt)

    def _encrypt(self, request_id: UUID, payload: dict[str, object]) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return self._envelope.encrypt(encoded, context=f"radar-result:{request_id}".encode())

    def _decrypt(self, row: RadarRequestRow) -> dict[str, object]:
        decoded = json.loads(
            self._envelope.decrypt(
                cast(str, row.result_ciphertext),
                context=f"radar-result:{row.id}".encode(),
            )
        )
        if not isinstance(decoded, dict):
            raise ValueError("invalid encrypted Radar result")
        return cast(dict[str, object], decoded)
