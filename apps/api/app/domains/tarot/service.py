from __future__ import annotations

import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.errors import (
    TarotQuestionRejected,
    TarotSelectionInvalid,
    TarotSessionConflict,
    TarotSessionNotFound,
)
from app.domains.tarot.knowledge import all_cards, card_by_id
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotQuestionIntent,
    TarotReading,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.tables import TarotSessionRow
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22,200}$")


class TarotSessionService:
    RETENTION_WINDOW = timedelta(days=29, hours=18)

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        hasher: SecretHasher,
        engine: TarotReadingEngine | None = None,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._hasher = hasher
        self._engine = engine or TarotReadingEngine()

    async def start(
        self,
        *,
        guest_id: UUID,
        context: TarotContext,
        question: str,
        spread: TarotSpread,
        voice: TarotVoice,
        origin: TarotOrigin,
        idempotency_key: str,
        prompt_id: str | None = None,
        now: datetime | None = None,
    ) -> TarotSessionView:
        assessment = self._engine.assess_question(question, context)
        if not assessment.accepted:
            raise TarotQuestionRejected(assessment)
        if not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
            raise TarotSelectionInvalid
        current = now or datetime.now(UTC)
        if assessment.intent is None:
            raise TarotSelectionInvalid
        spread_map = self._engine.choose_spread_map(
            spread,
            assessment.intent,
            assessment.normalized_question,
        )
        idempotency_hash = self._hasher.digest("tarot-create", idempotency_key)
        request_hash = sha256(
            "\x00".join(
                (
                    context.value,
                    assessment.normalized_question,
                    spread.value,
                    spread_map.value,
                    origin.value,
                    prompt_id or "",
                )
            ).encode()
        ).hexdigest()
        async with self._sessions() as database:
            existing = await database.scalar(
                select(TarotSessionRow).where(
                    TarotSessionRow.guest_id == guest_id,
                    TarotSessionRow.idempotency_hash == idempotency_hash,
                )
            )
            if existing is not None:
                payload = self._decrypt(existing)
                if payload.get("request_hash") != request_hash:
                    raise TarotSessionConflict
                return self._view(existing, payload)
        session_id = uuid4()
        deck_order = [card.id for card in all_cards()]
        secrets.SystemRandom().shuffle(deck_order)
        payload = {
            "question": assessment.normalized_question,
            "question_intent": assessment.intent.value if assessment.intent else None,
            "spread_map": spread_map.value,
            "question_rules_version": assessment.rules_version,
            "request_hash": request_hash,
            "prompt_id": prompt_id,
            "deck_order": deck_order,
            "selected_indices": [],
            "reading": None,
        }
        row = TarotSessionRow(
            id=session_id,
            guest_id=guest_id,
            version=1,
            state=TarotSessionState.CHOOSING.value,
            context=context.value,
            spread=spread.value,
            voice=voice.value,
            origin=origin.value,
            idempotency_hash=idempotency_hash,
            payload_ciphertext=self._encrypt(session_id, payload),
            created_at=current,
            updated_at=current,
            expires_at=current + self.RETENTION_WINDOW,
        )
        async with self._sessions() as database, database.begin():
            database.add(row)
            await database.flush([row])
        return self._view(row, payload)

    async def get(
        self, guest_id: UUID, session_id: UUID, *, now: datetime | None = None
    ) -> TarotSessionView:
        current = now or datetime.now(UTC)
        async with self._sessions() as database:
            row = await database.scalar(
                select(TarotSessionRow).where(
                    TarotSessionRow.id == session_id,
                    TarotSessionRow.guest_id == guest_id,
                    TarotSessionRow.expires_at > current,
                )
            )
            if row is None:
                raise TarotSessionNotFound
            return self._view(row, self._decrypt(row))

    async def select_card(
        self,
        *,
        guest_id: UUID,
        session_id: UUID,
        fan_index: int,
        expected_version: int,
        now: datetime | None = None,
    ) -> TarotSessionView:
        if not 0 <= fan_index < 78:
            raise TarotSelectionInvalid
        current = now or datetime.now(UTC)
        async with self._sessions() as database, database.begin():
            row = await database.scalar(
                select(TarotSessionRow)
                .where(
                    TarotSessionRow.id == session_id,
                    TarotSessionRow.guest_id == guest_id,
                    TarotSessionRow.expires_at > current,
                )
                .with_for_update()
            )
            if row is None:
                raise TarotSessionNotFound
            payload = self._decrypt(row)
            selected_indices = self._selected_indices(payload)
            if fan_index in selected_indices:
                return self._view(row, payload)
            if row.state == TarotSessionState.COMPLETE.value or row.version != expected_version:
                raise TarotSessionConflict
            selected_indices.append(fan_index)
            spread = TarotSpread(row.spread)
            spread_map = self._spread_map(payload, spread)
            required = _required_cards(spread_map)
            if len(selected_indices) > required:
                raise TarotSessionConflict
            payload["selected_indices"] = selected_indices
            row.version += 1
            row.updated_at = current
            if len(selected_indices) == required:
                card_ids = tuple(self._deck(payload)[index] for index in selected_indices)
                reading = self._engine.render(
                    card_ids=card_ids,
                    spread=spread,
                    spread_map=spread_map,
                    context=TarotContext(row.context),
                    question=self._question(payload),
                    voice=TarotVoice(row.voice),
                    question_intent=self._question_intent(payload),
                )
                payload["reading"] = reading.model_dump(mode="json")
                row.state = TarotSessionState.COMPLETE.value
            row.payload_ciphertext = self._encrypt(row.id, payload)
            await database.flush([row])
            return self._view(row, payload)

    async def delete(self, guest_id: UUID, session_id: UUID) -> None:
        async with self._sessions() as database, database.begin():
            result = await database.execute(
                delete(TarotSessionRow).where(
                    TarotSessionRow.id == session_id,
                    TarotSessionRow.guest_id == guest_id,
                )
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                raise TarotSessionNotFound

    async def cleanup(self, *, batch_size: int = 500, now: datetime | None = None) -> int:
        if not 1 <= batch_size <= 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        current = now or datetime.now(UTC)
        async with self._sessions() as database, database.begin():
            ids = tuple(
                await database.scalars(
                    select(TarotSessionRow.id)
                    .where(TarotSessionRow.expires_at <= current)
                    .order_by(TarotSessionRow.expires_at, TarotSessionRow.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            if not ids:
                return 0
            result = await database.execute(
                delete(TarotSessionRow).where(TarotSessionRow.id.in_(ids))
            )
            return int(cast(CursorResult[Any], result).rowcount or 0)

    def _view(self, row: TarotSessionRow, payload: dict[str, Any]) -> TarotSessionView:
        spread = TarotSpread(row.spread)
        spread_map = self._spread_map(payload, spread)
        positions = self._engine.positions_for(spread_map)
        deck = self._deck(payload)
        selected = tuple(
            TarotSelectedCard(
                fan_index=fan_index,
                position_key=positions[index][0],
                position_label=positions[index][1],
                card=card_by_id(deck[fan_index]),
            )
            for index, fan_index in enumerate(self._selected_indices(payload))
        )
        raw_reading = payload.get("reading")
        reading = TarotReading.model_validate(raw_reading) if raw_reading is not None else None
        return TarotSessionView(
            id=row.id,
            version=row.version,
            state=TarotSessionState(row.state),
            context=TarotContext(row.context),
            spread=spread,
            spread_map=spread_map,
            voice=TarotVoice(row.voice),
            origin=TarotOrigin(row.origin),
            prompt_id=_optional_text(payload.get("prompt_id")),
            question=self._question(payload),
            required_cards=_required_cards(spread_map),
            selected_cards=selected,
            reading=reading,
            created_at=row.created_at,
            updated_at=row.updated_at,
            expires_at=row.expires_at,
        )

    def _encrypt(self, session_id: UUID, payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
        return self._envelope.encrypt(encoded, context=_payload_context(session_id))

    def _decrypt(self, row: TarotSessionRow) -> dict[str, Any]:
        payload = json.loads(
            self._envelope.decrypt(row.payload_ciphertext, context=_payload_context(row.id))
        )
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted Tarot payload")
        return cast(dict[str, Any], payload)

    @staticmethod
    def _deck(payload: dict[str, Any]) -> list[str]:
        deck = payload.get("deck_order")
        if (
            not isinstance(deck, list)
            or len(deck) != 78
            or not all(isinstance(item, str) for item in deck)
        ):
            raise ValueError("invalid encrypted Tarot deck")
        return cast(list[str], deck)

    @staticmethod
    def _selected_indices(payload: dict[str, Any]) -> list[int]:
        selected = payload.get("selected_indices")
        if not isinstance(selected, list) or not all(isinstance(item, int) for item in selected):
            raise ValueError("invalid encrypted Tarot selection")
        return cast(list[int], selected)

    @staticmethod
    def _question(payload: dict[str, Any]) -> str:
        question = payload.get("question")
        if not isinstance(question, str) or not question:
            raise ValueError("invalid encrypted Tarot question")
        return question

    @staticmethod
    def _question_intent(payload: dict[str, Any]) -> TarotQuestionIntent:
        intent = payload.get("question_intent")
        if not isinstance(intent, str):
            raise ValueError("invalid encrypted Tarot question intent")
        return TarotQuestionIntent(intent)

    @staticmethod
    def _spread_map(payload: dict[str, Any], spread: TarotSpread) -> TarotSpreadMap:
        raw = payload.get("spread_map")
        if isinstance(raw, str):
            return TarotSpreadMap(raw)
        return {
            TarotSpread.ONE_CARD: TarotSpreadMap.ONE_FOCUS,
            TarotSpread.THREE_CARD: TarotSpreadMap.THREE_UNBLOCK,
            TarotSpread.FIVE_CARD: TarotSpreadMap.FIVE_CLARITY,
        }[spread]


def _payload_context(session_id: UUID) -> bytes:
    return f"tarot-session:{session_id}".encode()


def _required_cards(spread_map: TarotSpreadMap) -> int:
    return {
        TarotSpreadMap.ONE_FOCUS: 1,
        TarotSpreadMap.THREE_UNBLOCK: 3,
        TarotSpreadMap.FIVE_CLARITY: 5,
        TarotSpreadMap.FIVE_LOOP: 5,
        TarotSpreadMap.FIVE_CHOICE: 5,
        TarotSpreadMap.FIVE_CONVERSATION: 5,
    }[spread_map]


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
