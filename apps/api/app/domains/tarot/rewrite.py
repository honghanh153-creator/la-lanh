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

from app.db.rewrite_scope import rewrite_session
from app.domains.content_rewrite.authorization import content_rewrite_receipt_id
from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteArtifactKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.content_rewrite.service import RewriteProjectionDecision, RewriteProjector
from app.domains.tarot.engine import (
    TAROT_RENDERER_VERSION,
    TarotContentRejected,
    TarotReadingEngine,
)
from app.domains.tarot.meaning_brief import meaning_brief_for
from app.domains.tarot.models import (
    TarotContext,
    TarotReading,
    TarotReadingPosition,
    TarotSessionState,
    TarotSessionView,
)
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import EnvelopeCipher
from app.infrastructure.generation.privacy import reduce_tarot_question

TAROT_REWRITE_RENDERER_VERSION = "gpt-6-luna-tarot-v4"
TAROT_REWRITE_GATE_VERSION = canonical_surface_registry().require(RewriteSurface.TAROT).gate_version

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
    "thể",
}


def tarot_rewrite_owner(guest_id: UUID, session_id: UUID) -> ArtifactOwnerKey:
    return ArtifactOwnerKey(namespace="tarot", key=f"tarot|{guest_id}|{session_id}")


def _parse_owner(owner: ArtifactOwnerKey) -> tuple[UUID, UUID]:
    parts = owner.key.split("|")
    if owner.namespace != "tarot" or len(parts) != 3 or parts[0] != "tarot":
        raise ValueError("invalid Tarot rewrite owner")
    return UUID(parts[1]), UUID(parts[2])


def _category(context: TarotContext) -> Literal["relationship", "work", "self", "general"]:
    if context is TarotContext.RELATIONSHIPS:
        return "relationship"
    if context is TarotContext.WORK:
        return "work"
    if context in {TarotContext.ENERGY, TarotContext.SELF_CARE}:
        return "self"
    return "general"


def _blueprint_payload(reading: TarotReading) -> dict[str, JsonValue]:
    return {
        "context": reading.context.value,
        "intent": reading.question_intent.value,
        "spread": reading.spread.value,
        "spread_map": reading.spread_map.value,
        "voice": reading.voice.value,
        "meaning_brief": cast(JsonValue, meaning_brief_for(reading)),
        "positions": cast(
            JsonValue,
            [
                {
                    "position_key": position.key,
                    "position_label": position.label,
                    "card_key": position.card.id,
                    "card_title": position.card.title_vi,
                    "meaning_keys": list(position.card.source_concept_ids),
                    "meaning_here": position.meaning_here,
                    "everyday_scene": position.everyday_scene,
                    "reflection_question": position.reflection_question,
                    "small_action": position.small_action,
                }
                for position in reading.positions
            ],
        ),
        "provenance": reading.provenance.model_dump(mode="json"),
    }


def tarot_blueprint_hash(reading: TarotReading) -> str:
    canonical = json.dumps(
        _blueprint_payload(reading),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode()).hexdigest()


def compile_tarot_rewrite_request(
    guest_id: UUID,
    session: TarotSessionView,
    *,
    model_version: str,
    prompt_version: str,
) -> RewriteRequestEnvelope | None:
    reading = session.reading
    if session.state is not TarotSessionState.COMPLETE or reading is None:
        return None
    reduced = reduce_tarot_question(reading.question, category=_category(reading.context))
    if reduced is None:
        return None
    positions = [
        {
            "position_key": position.key,
            "position_label": position.label,
            "card_key": position.card.id,
            "card_title": position.card.title_vi,
            "orientation": "upright",
            "meaning_keys": list(position.card.source_concept_ids),
            "meaning_here": position.meaning_here,
            "everyday_scene": position.everyday_scene,
            "reflection_question": position.reflection_question,
            "small_action": position.small_action,
        }
        for position in reading.positions
    ]
    spec = canonical_surface_registry().require(RewriteSurface.TAROT)
    return RewriteRequestEnvelope(
        key=RewriteArtifactKey(
            surface=RewriteSurface.TAROT,
            owner=tarot_rewrite_owner(guest_id, session.id),
            blueprint_hash=tarot_blueprint_hash(reading),
            model_version=model_version,
            prompt_version=prompt_version,
            schema_version=spec.schema_version,
            gate_version=spec.gate_version,
        ),
        authorization_receipt_id=content_rewrite_receipt_id(guest_id),
        safe_payload={
            "category": reduced.category,
            "focus_key": reduced.focus_key.value,
            "focus_sentence": reduced.focus_sentence,
            "meaning_brief": cast(JsonValue, meaning_brief_for(reading)),
            "positions": cast(JsonValue, positions),
        },
    )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


_FOLDED_STOP_WORDS = frozenset(_fold(word) for word in _STOP_WORDS)


def _meaning_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[^\W_]+", _fold(value))
        if len(token) >= 4 and token not in _FOLDED_STOP_WORDS
    }


_NEGATION = re.compile(r"\b(?:khong can|khong nen|khong muon|chang can|dung|bo qua)\b")


def _negates_source_claim(source: str, rewritten: str) -> bool:
    """Conservative polarity tripwire, not a semantic-entailment proof.

    Reject a new negated clause sharing anchors with a source assertion. Preserve
    existing cautionary negations. Uncertain paraphrases fall back to the local reading.
    """
    source_clauses = [clause for clause in re.split(r"[.!?;:]", source) if clause.strip()]
    positive = [_meaning_tokens(c) for c in source_clauses if not _NEGATION.search(_fold(c))]
    negative = [_meaning_tokens(c) for c in source_clauses if _NEGATION.search(_fold(c))]
    for clause in re.split(r"[.!?;:]", rewritten):
        if not _NEGATION.search(_fold(clause)):
            continue
        tokens = _meaning_tokens(clause)
        if any(len(tokens & anchors) >= 2 for anchors in positive) and not any(
            len(tokens & anchors) >= 2 for anchors in negative
        ):
            return True
    return False


def rewrite_tarot_reading(
    baseline: TarotReading,
    output: dict[str, JsonValue],
) -> TarotReading | None:
    if set(output) != {"headline", "position_readings", "synthesis", "closing_question"}:
        return None
    headline = output.get("headline")
    synthesis = output.get("synthesis")
    closing = output.get("closing_question")
    raw_positions = output.get("position_readings")
    if (
        not isinstance(headline, str)
        or not headline.strip()
        or not isinstance(synthesis, str)
        or not synthesis.strip()
        or not isinstance(closing, str)
        or not closing.strip().endswith("?")
        or not isinstance(raw_positions, list)
        or len(raw_positions) != len(baseline.positions)
    ):
        return None

    expected = {position.key: position for position in baseline.positions}
    rewritten: list[TarotReadingPosition] = []
    fingerprints: set[str] = set()
    synthesis_terms = _meaning_tokens(synthesis)
    for raw in raw_positions:
        if not isinstance(raw, dict) or set(raw) != {"position_key", "reading"}:
            return None
        key = raw.get("position_key")
        prose = raw.get("reading")
        if not isinstance(key, str) or not isinstance(prose, str) or not prose.strip():
            return None
        source = expected.pop(key, None)
        if source is None or _fold(source.card.title_vi) not in _fold(prose):
            return None
        source_terms = _meaning_tokens(source.meaning_here)
        if len(source_terms & _meaning_tokens(prose)) < 2:
            return None
        if _negates_source_claim(source.meaning_here, prose):
            return None
        if len(source_terms & synthesis_terms) < 2:
            return None
        fingerprint = re.sub(r"\W+", " ", _fold(prose)).strip()
        if fingerprint in fingerprints:
            return None
        fingerprints.add(fingerprint)
        rewritten.append(source.model_copy(update={"meaning_here": prose.strip()}))
    if expected:
        return None

    word_count = len(
        re.findall(
            r"[^\W_]+",
            " ".join(
                (
                    headline,
                    synthesis,
                    closing,
                    *(position.meaning_here for position in rewritten),
                )
            ),
        )
    )
    if word_count > 800:
        return None
    source_prose = " ".join(
        (baseline.summary, *(position.meaning_here for position in baseline.positions))
    )
    if any(_negates_source_claim(source_prose, field) for field in (headline, synthesis, closing)):
        return None
    candidate = baseline.model_copy(
        update={
            "headline": headline.strip(),
            "summary": synthesis.strip(),
            "positions": tuple(rewritten),
            "closing_prompt": closing.strip(),
            "provenance": baseline.provenance.model_copy(
                update={
                    "renderer_version": TAROT_REWRITE_RENDERER_VERSION,
                    "gate_version": TAROT_REWRITE_GATE_VERSION,
                }
            ),
        }
    )
    try:
        TarotReadingEngine.validate(candidate)
    except TarotContentRejected:
        return None
    return candidate


class TarotRewriteProjector(RewriteProjector):
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        engine: TarotReadingEngine | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._engine = engine or TarotReadingEngine()

    async def validate_and_project(
        self,
        request: RewriteRequestEnvelope,
        output: dict[str, JsonValue],
        *,
        completed_at: datetime,
        publish: bool = True,
    ) -> RewriteProjectionDecision:
        if request.key.surface is not RewriteSurface.TAROT:
            return RewriteProjectionDecision(accepted=False, failure_code="unsupported_surface")
        try:
            guest_id, session_id = _parse_owner(request.key.owner)
        except ValueError:
            return RewriteProjectionDecision(accepted=False, failure_code="invalid_owner")

        async with rewrite_session(self._sessions, transaction=True) as database:
            row = await database.scalar(
                select(TarotSessionRow)
                .where(
                    TarotSessionRow.id == session_id,
                    TarotSessionRow.guest_id == guest_id,
                )
                .with_for_update()
            )
            if (
                row is None
                or row.state != TarotSessionState.COMPLETE.value
                or row.expires_at <= completed_at
            ):
                return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
            payload = self._decrypt(row)
            raw_reading = payload.get("reading")
            if raw_reading is None:
                return RewriteProjectionDecision(accepted=False, failure_code="stale_owner")
            baseline = TarotReading.model_validate(raw_reading)
            if baseline.provenance.renderer_version != TAROT_RENDERER_VERSION:
                return RewriteProjectionDecision(
                    accepted=False, failure_code="stale_domain_version"
                )
            if tarot_blueprint_hash(baseline) != request.key.blueprint_hash:
                return RewriteProjectionDecision(
                    accepted=False, failure_code="stale_domain_version"
                )
            candidate = rewrite_tarot_reading(baseline, output)
            if candidate is None:
                return RewriteProjectionDecision(accepted=False, failure_code="tarot_gate_rejected")
            try:
                self._engine.validate(candidate)
            except TarotContentRejected:
                return RewriteProjectionDecision(accepted=False, failure_code="tarot_gate_rejected")
            if publish:
                payload["reading"] = candidate.model_dump(mode="json")
                row.payload_ciphertext = self._encrypt(row.id, payload)
                row.updated_at = max(row.updated_at, completed_at)
                await database.flush([row])

        receipt = sha256(
            f"{request.key.cache_key}\x00{session_id}\x00{TAROT_REWRITE_GATE_VERSION}".encode()
        ).hexdigest()
        return RewriteProjectionDecision(accepted=True, gate_receipt_id=receipt)

    def _encrypt(self, session_id: UUID, payload: dict[str, object]) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return self._envelope.encrypt(encoded, context=f"tarot-session:{session_id}".encode())

    def _decrypt(self, row: TarotSessionRow) -> dict[str, object]:
        decoded = json.loads(
            self._envelope.decrypt(
                row.payload_ciphertext,
                context=f"tarot-session:{row.id}".encode(),
            )
        )
        if not isinstance(decoded, dict):
            raise ValueError("invalid encrypted Tarot payload")
        return cast(dict[str, object], decoded)
