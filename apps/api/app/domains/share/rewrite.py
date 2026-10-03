from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from pydantic import JsonValue

from app.domains.content_rewrite.authorization import content_rewrite_receipt_id
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.share.models import SafeShareSnapshot

SHARE_REWRITE_RENDERER_VERSION = "gpt-6-luna-share-v1"
RECAP_REWRITE_RENDERER_VERSION = "gpt-6-luna-recap-v1"

_STOP_WORDS = {
    "bạn",
    "mình",
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
}
_FORBIDDEN = (
    "chắc chắn sẽ",
    "định mệnh",
    "chẩn đoán",
    "ngày sinh",
    "giờ sinh",
    "nơi sinh",
)
_RECAP_CLAIM_MARKERS = (
    "match",
    "cuộc hẹn",
    "gặp người mới",
    "gặp một người mới",
    "chuỗi ngày",
    "streak",
    "chia sẻ",
    "đã lưu",
)


@dataclass(frozen=True, slots=True)
class RecordedRecapActivity:
    key: str
    summary: str


@dataclass(frozen=True, slots=True)
class RecapCopy:
    headline: str
    summary: str
    activity_keys: tuple[str, ...]
    renderer_version: str = RECAP_REWRITE_RENDERER_VERSION


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


def _safe_copy(output: dict[str, JsonValue], *, word_budget: int) -> tuple[str, str] | None:
    if set(output) != {"headline", "summary"}:
        return None
    headline = output.get("headline")
    summary = output.get("summary")
    if (
        not isinstance(headline, str)
        or not headline.strip()
        or not isinstance(summary, str)
        or not summary.strip()
    ):
        return None
    folded = _fold(f"{headline} {summary}")
    if any(_fold(term) in folded for term in _FORBIDDEN):
        return None
    if len(re.findall(r"[^\W_]+", f"{headline} {summary}")) > word_budget:
        return None
    return headline.strip(), summary.strip()


def share_rewrite_owner(guest_id: UUID, artifact_id: UUID) -> ArtifactOwnerKey:
    return ArtifactOwnerKey(namespace="share", key=f"share|{guest_id}|{artifact_id}|public")


def recap_rewrite_owner(guest_id: UUID, recap_key: str) -> ArtifactOwnerKey:
    token = sha256(recap_key.encode()).hexdigest()[:32]
    return ArtifactOwnerKey(namespace="share", key=f"recap|{guest_id}|{token}|private")


def compile_share_rewrite_request(
    guest_id: UUID,
    artifact_id: UUID,
    snapshot: SafeShareSnapshot,
    *,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope:
    summary = snapshot.body.strip() or snapshot.title.strip()
    approved_claim_keys = (
        f"content:{snapshot.content_version}",
        f"persona:{snapshot.persona_version}",
    )
    blueprint = {
        "title": snapshot.title,
        "body": summary,
        "context_label": snapshot.context_label,
        "content_version": snapshot.content_version,
        "persona_mode": snapshot.persona_mode,
        "persona_version": snapshot.persona_version,
    }
    spec = canonical_surface_registry().require(RewriteSurface.SHARE_CARD)
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.SHARE_CARD,
            owner=share_rewrite_owner(guest_id, artifact_id),
            blueprint_hash=sha256(
                json.dumps(blueprint, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest(),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=spec.schema_version,
            gate_version=spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(guest_id),
        safe_payload={
            "source_headline": snapshot.title,
            "source_summary": summary,
            "approved_claim_keys": list(approved_claim_keys),
            "activity_keys": [],
            "activity_summaries": [],
        },
    )


def rewrite_share_snapshot(
    baseline: SafeShareSnapshot,
    output: dict[str, JsonValue],
) -> SafeShareSnapshot | None:
    copy = _safe_copy(output, word_budget=90)
    if copy is None:
        return None
    headline, summary = copy
    source_summary = baseline.body.strip() or baseline.title
    if not _tokens(headline) & _tokens(baseline.title):
        return None
    if len(_tokens(summary) & _tokens(source_summary)) < 2:
        return None
    return SafeShareSnapshot(
        title=headline,
        body=summary,
        context_label=baseline.context_label,
        content_version=baseline.content_version,
        persona_mode=baseline.persona_mode,
        persona_label=baseline.persona_label,
        persona_version=baseline.persona_version,
        watermark=baseline.watermark,
    )


def compile_recap_rewrite_request(
    guest_id: UUID,
    recap_key: str,
    activities: tuple[RecordedRecapActivity, ...],
    *,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope | None:
    if not activities or len(activities) > 12:
        return None
    if any(
        re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", item.key) is None
        or not item.summary.strip()
        or len(item.summary) > 280
        for item in activities
    ):
        return None
    source_summary = " ".join(item.summary.strip() for item in activities)
    spec = canonical_surface_registry().require(RewriteSurface.RECAP)
    blueprint = [(item.key, item.summary) for item in activities]
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.RECAP,
            owner=recap_rewrite_owner(guest_id, recap_key),
            blueprint_hash=sha256(
                json.dumps(blueprint, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest(),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=spec.schema_version,
            gate_version=spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(guest_id),
        safe_payload={
            "source_headline": "Những điều bạn đã thật sự làm tuần này",
            "source_summary": source_summary,
            "approved_claim_keys": [item.key for item in activities],
            "activity_keys": [item.key for item in activities],
            "activity_summaries": [item.summary for item in activities],
        },
    )


def rewrite_recap(
    activities: tuple[RecordedRecapActivity, ...],
    output: dict[str, JsonValue],
) -> RecapCopy | None:
    copy = _safe_copy(output, word_budget=180)
    if copy is None or not activities:
        return None
    headline, summary = copy
    source = " ".join(item.summary for item in activities)
    candidate_text = f"{headline} {summary}"
    if len(_tokens(candidate_text) & _tokens(source)) < 2:
        return None
    folded_source = _fold(source)
    folded_candidate = _fold(candidate_text)
    if any(
        _fold(marker) in folded_candidate and _fold(marker) not in folded_source
        for marker in _RECAP_CLAIM_MARKERS
    ):
        return None
    return RecapCopy(
        headline=headline,
        summary=summary,
        activity_keys=tuple(item.key for item in activities),
    )
