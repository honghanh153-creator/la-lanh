import json
import logging
import re
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import load_only

from app.domains.astro import NatalChartEngine
from app.domains.astro.models import CalculationConfig, RelationshipBundle
from app.domains.birth.errors import BirthDomainError
from app.domains.birth.models import BirthTimeMode
from app.domains.birth.service import BirthChartService
from app.domains.birth.tables import BirthProfileRow
from app.domains.content_rewrite.send_fence import drain_sends, pending_sends
from app.domains.content_rewrite.service import ContentRewriteService
from app.domains.guest.tables import GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.radar.models import (
    RadarAcceptResult,
    RadarInviteView,
    RadarMode,
    RadarPublicInvite,
    RadarStatus,
)
from app.domains.radar.reading import build_radar_reading
from app.domains.radar.rewrite import (
    RadarPerspective,
    compile_radar_rewrite_request,
    radar_rewrite_owner,
)
from app.domains.radar.tables import RadarRequestRow
from app.domains.relationships.models import RelationshipVoice
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

CAPABILITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
CONTEXTS = {"crush", "friend", "partner", "someone"}
CONSENT_VERSION = "radar-pair-v1"
AUTHORIZED_INPUT_VERSION = "radar-authorized-input-v1"
INVITE_TTL = timedelta(days=7)
# Manual entry of the other person's birth data keeps the result briefly (owner decision
# 2026-10-19); a mutually consented pair result keeps the longer window.
PRIVATE_CHECK_TTL = timedelta(hours=24)
CONSENTED_RESULT_TTL = timedelta(days=30)
RECEIPT_TTL = timedelta(days=7)
MAX_RETAINED_REQUESTS = 100
PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
logger = logging.getLogger(__name__)


class RadarError(RuntimeError):
    pass


class RadarUnavailable(RadarError):
    pass


class RadarInvalid(RadarError):
    pass


class RadarChartRequired(RadarError):
    pass


class RadarLimitReached(RadarError):
    pass


class RadarConflict(RadarError):
    pass


class RadarService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        hasher: SecretHasher,
        envelope: EnvelopeCipher,
        birth: BirthChartService,
        engine: NatalChartEngine,
        *,
        generation_enabled: bool = False,
        generation_model: str = "disabled",
        generation_prompt_version: str = "surface-rewrite-v1",
        content_rewrite_service: ContentRewriteService | None = None,
    ) -> None:
        self._sessions = sessions
        self._hasher = hasher
        self._envelope = envelope
        self._birth = birth
        self._engine = engine
        self._generation_enabled = generation_enabled
        self._generation_model = generation_model
        self._generation_prompt_version = generation_prompt_version
        self._content_rewrite_service = content_rewrite_service

    async def create(
        self,
        *,
        principal_id: UUID,
        owner_guest_id: UUID,
        recipient_label: str,
        context: str,
        voice: RelationshipVoice,
        idempotency_key: str | None = None,
        now: datetime | None = None,
    ) -> tuple[RadarInviteView, str]:
        label = " ".join(recipient_label.split())
        if not 1 <= len(label) <= 40 or context not in CONTEXTS:
            raise RadarInvalid
        if await self._chart(owner_guest_id) is None:
            raise RadarChartRequired
        source = await self._birth.current(owner_guest_id)
        current = now or datetime.now(UTC)
        idem, request_hash = self._request_digests(
            principal_id,
            idempotency_key,
            RadarMode.CONSENTED_INVITE,
            [label, context, voice.value, str(source.snapshot_id), str(source.profile_revision)],
        )
        request_id = uuid4()
        token = secrets.token_urlsafe(32)
        row = RadarRequestRow(
            id=request_id,
            principal_id=principal_id,
            owner_guest_id=owner_guest_id,
            recipient_label_ciphertext=self._envelope.encrypt(
                label.encode(), context=f"radar-label:{request_id}".encode()
            ),
            context=context,
            voice=voice.value,
            mode=RadarMode.CONSENTED_INVITE.value,
            status=RadarStatus.PENDING.value,
            token_hash=self._hasher.digest("radar-capability", token),
            token_ciphertext=self._envelope.encrypt(
                token.encode(), context=f"radar-capability:{request_id}".encode()
            ),
            created_at=current,
            expires_at=current + INVITE_TTL,
            idempotency_hash=idem,
            request_hash=request_hash,
        )
        async with self._creation_transaction(principal_id, owner_guest_id, current) as session:
            existing = await self._replay(session, idem, request_hash, current)
            if existing is not None:
                return self._view(existing, current), self._invite_token(existing)
            await self._capacity(session, principal_id)
            await self._lock_chart_sources(
                session, {owner_guest_id: (source.snapshot_id, source.profile_revision)}
            )
            session.add(row)
            await session.flush()
        return self._view(row, current), token

    async def create_private_check(
        self,
        *,
        principal_id: UUID,
        owner_guest_id: UUID,
        recipient_label: str,
        context: str,
        voice: RelationshipVoice,
        birth_date: date,
        birth_time_mode: str,
        birth_time_local: str | None,
        place_id: str,
        consent_version: str,
        authorization_attested: bool,
        idempotency_key: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        label = " ".join(recipient_label.split())
        if (
            not 1 <= len(label) <= 40
            or context not in CONTEXTS
            or consent_version != AUTHORIZED_INPUT_VERSION
            or not authorization_attested
        ):
            raise RadarInvalid
        config = CalculationConfig.western_recommended()
        source = await self._birth.current(owner_guest_id)
        current = now or datetime.now(UTC)
        idem, request_hash = self._request_digests(
            principal_id,
            idempotency_key,
            RadarMode.PRIVATE_CHECK,
            [
                label,
                context,
                voice.value,
                birth_date.isoformat(),
                birth_time_mode,
                birth_time_local,
                place_id,
                consent_version,
                str(source.snapshot_id),
                str(source.profile_revision),
            ],
        )
        async with self._creation_transaction(principal_id, owner_guest_id, current) as session:
            existing = await self._replay(session, idem, request_hash, current)
            if existing is not None:
                return self._private_replay(existing)
            await self._capacity(session, principal_id)
        chart_a = await self._chart(owner_guest_id)
        if chart_a is None:
            raise RadarChartRequired
        try:
            chart_b = await self._birth.calculate_transient_chart(
                birth_date=birth_date,
                birth_time_mode=BirthTimeMode(birth_time_mode),
                birth_time_local=birth_time_local,
                place_id=place_id,
                config=config,
                now=now,
            )
        except BirthDomainError as error:
            raise RadarInvalid from error
        projection = _reading(
            self._engine.calculate_relationship_bundle(chart_a, chart_b),
            context=context,
            voice=voice,
        )
        metadata = cast(dict[str, Any], projection.setdefault("metadata", {}))
        metadata["time_precision"] = chart_b.time_precision.value
        if chart_b.time_precision.value == "unknown":
            metadata["precision_note"] = (
                "Không rõ giờ sinh của người kia: Radar đã bỏ Moon của họ, Rising, House "
                "và các lớp phụ thuộc giờ. Kết quả hiện tại ngắn hơn nhưng không giả vờ "
                "chính xác."
            )
            projection["disclaimer"] = (
                f"{projection['disclaimer']} Không rõ giờ sinh nên các tín hiệu phụ thuộc giờ "
                "đã được loại khỏi bản đọc."
            )
        request_id = uuid4()
        row = RadarRequestRow(
            id=request_id,
            principal_id=principal_id,
            owner_guest_id=owner_guest_id,
            recipient_label_ciphertext=self._envelope.encrypt(
                label.encode(), context=f"radar-label:{request_id}".encode()
            ),
            context=context,
            voice=voice.value,
            mode=RadarMode.PRIVATE_CHECK.value,
            status=RadarStatus.COMPLETED.value,
            consent_version=consent_version,
            authorization_attested_at=current,
            token_hash=None,
            token_ciphertext=None,
            result_ciphertext=self._envelope.encrypt(
                json.dumps(projection, ensure_ascii=False).encode(),
                context=f"radar-result:{request_id}".encode(),
            ),
            created_at=current,
            expires_at=current + PRIVATE_CHECK_TTL,
            completed_at=current,
            idempotency_hash=idem,
            request_hash=request_hash,
        )
        async with self._creation_transaction(principal_id, owner_guest_id, current) as session:
            existing = await self._replay(session, idem, request_hash, current)
            if existing is not None:
                return self._private_replay(existing)
            await self._capacity(session, principal_id)
            await self._lock_chart_sources(
                session, {owner_guest_id: (source.snapshot_id, source.profile_revision)}
            )
            session.add(row)
            await session.flush()
        await self._enqueue_rewrite(
            guest_id=owner_guest_id,
            request_id=request_id,
            perspective="owner",
            projection=projection,
            context=context,
        )
        return {
            "request_id": str(request_id),
            "recipient_label": label,
            "mode": RadarMode.PRIVATE_CHECK.value,
            **projection,
            "expires_at": row.expires_at,
        }

    async def list_owned(
        self,
        principal_id: UUID,
        *,
        before: UUID | None = None,
        mode: RadarMode | None = None,
        limit: int = PAGE_SIZE,
    ) -> tuple[RadarInviteView, ...]:
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise RadarInvalid
        current = datetime.now(UTC)
        async with self._sessions() as session:
            query = select(RadarRequestRow).where(RadarRequestRow.principal_id == principal_id)
            if mode is not None:
                query = query.where(RadarRequestRow.mode == mode.value)
            if before is not None:
                cursor = (
                    await session.execute(
                        select(RadarRequestRow.created_at, RadarRequestRow.id).where(
                            RadarRequestRow.id == before,
                            RadarRequestRow.principal_id == principal_id,
                            *([RadarRequestRow.mode == mode.value] if mode is not None else []),
                        )
                    )
                ).one_or_none()
                if cursor is None:
                    raise RadarUnavailable
                query = query.where(
                    or_(
                        RadarRequestRow.created_at < cursor.created_at,
                        and_(
                            RadarRequestRow.created_at == cursor.created_at,
                            RadarRequestRow.id < cursor.id,
                        ),
                    )
                )
            rows = tuple(
                await session.scalars(
                    query.options(
                        load_only(
                            RadarRequestRow.id,
                            RadarRequestRow.recipient_label_ciphertext,
                            RadarRequestRow.context,
                            RadarRequestRow.voice,
                            RadarRequestRow.mode,
                            RadarRequestRow.status,
                            RadarRequestRow.created_at,
                            RadarRequestRow.expires_at,
                        )
                    )
                    .order_by(RadarRequestRow.created_at.desc(), RadarRequestRow.id.desc())
                    .limit(limit)
                )
            )
        return tuple(self._view(row, current) for row in rows)

    async def share_invite(
        self, principal_id: UUID, request_id: UUID
    ) -> tuple[RadarInviteView, str]:
        current = datetime.now(UTC)
        async with self._sessions() as session:
            row = await session.scalar(
                select(RadarRequestRow).where(
                    RadarRequestRow.id == request_id,
                    RadarRequestRow.principal_id == principal_id,
                )
            )
            if row is None or self._effective_status(row, current) is not RadarStatus.PENDING:
                raise RadarUnavailable
            return self._view(row, current), self._invite_token(row)

    def _invite_token(self, row: RadarRequestRow) -> str:
        if row.token_ciphertext is None:
            raise RadarUnavailable
        return self._envelope.decrypt(
            row.token_ciphertext, context=f"radar-capability:{row.id}".encode()
        ).decode()

    def _request_digests(
        self,
        principal: UUID,
        key: str | None,
        mode: RadarMode,
        values: list[object],
    ) -> tuple[bytes | None, bytes | None]:
        if key is None:
            return None, None
        if IDEMPOTENCY_PATTERN.fullmatch(key) is None:
            raise RadarInvalid
        idem = self._hasher.digest("radar-create", f"{principal}:{mode.value}:{key}")
        fingerprint = self._hasher.digest(
            "radar-input",
            json.dumps([str(principal), key, mode.value, *values], ensure_ascii=False),
        )
        return idem, fingerprint

    @asynccontextmanager
    async def _creation_transaction(
        self,
        principal_id: UUID,
        guest_id: UUID,
        now: datetime,
    ) -> AsyncIterator[AsyncSession]:
        async with self._sessions() as session, session.begin():
            await session.connection(execution_options={"sqlite_write": True})
            guest = await session.scalar(
                select(GuestSessionRow)
                .where(
                    GuestSessionRow.id == guest_id,
                )
                .with_for_update()
            )
            principal = await session.scalar(
                select(PrincipalRow)
                .where(
                    PrincipalRow.id == principal_id,
                    PrincipalRow.source_guest_id == guest_id,
                )
                .with_for_update()
            )
            if (
                guest is None
                or principal is None
                or guest.state != "active"
                or guest.expires_at <= now
                or guest.expires_at <= datetime.now(UTC)
            ):
                raise RadarUnavailable
            yield session

    @staticmethod
    async def _capacity(session: AsyncSession, principal: UUID) -> None:
        retained = list(
            await session.scalars(
                select(RadarRequestRow.id)
                .where(
                    RadarRequestRow.principal_id == principal,
                )
                .limit(MAX_RETAINED_REQUESTS)
            )
        )
        if len(retained) >= MAX_RETAINED_REQUESTS:
            raise RadarLimitReached

    async def _replay(
        self,
        session: AsyncSession,
        idem: bytes | None,
        fingerprint: bytes | None,
        now: datetime,
    ) -> RadarRequestRow | None:
        if idem is None:
            return None
        row = await session.scalar(
            select(RadarRequestRow).where(
                RadarRequestRow.idempotency_hash == idem,
            )
        )
        if row is None:
            return None
        if row.request_hash != fingerprint:
            raise RadarConflict
        if self._effective_status(row, now) not in {RadarStatus.PENDING, RadarStatus.COMPLETED}:
            raise RadarUnavailable
        if row.mode == RadarMode.CONSENTED_INVITE.value and row.status != RadarStatus.PENDING.value:
            raise RadarUnavailable
        return row

    def _private_replay(self, row: RadarRequestRow) -> dict[str, Any]:
        if row.result_ciphertext is None:
            raise RadarUnavailable
        payload = json.loads(
            self._envelope.decrypt(
                row.result_ciphertext,
                context=f"radar-result:{row.id}".encode(),
            )
        )
        return {
            "request_id": str(row.id),
            "recipient_label": self._label(row),
            "mode": RadarMode.PRIVATE_CHECK.value,
            **payload,
            "expires_at": row.expires_at,
        }

    async def share_token(self, principal_id: UUID, request_id: UUID) -> str:
        async with self._sessions() as session:
            row = await session.get(RadarRequestRow, request_id)
            if (
                row is None
                or row.principal_id != principal_id
                or self._effective_status(row, datetime.now(UTC)) is not RadarStatus.PENDING
                or row.token_ciphertext is None
            ):
                raise RadarUnavailable
            return self._envelope.decrypt(
                row.token_ciphertext, context=f"radar-capability:{row.id}".encode()
            ).decode()

    async def revoke(self, principal_id: UUID, request_id: UUID) -> None:
        current = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            row = await session.get(RadarRequestRow, request_id, with_for_update=True)
            if row is None or row.principal_id != principal_id:
                raise RadarUnavailable
            if self._effective_status(row, current) is RadarStatus.PENDING:
                row.status = RadarStatus.REVOKED.value
                row.revoked_at = current
                row.token_ciphertext = None

    async def preview(self, token: str) -> RadarPublicInvite:
        row = await self._pending_by_token(token)
        return RadarPublicInvite(
            request_id=row.id,
            recipient_label=self._label(row),
            context=row.context,
            voice=row.voice,
            expires_at=row.expires_at,
        )

    async def accept(
        self,
        token: str,
        *,
        recipient_guest_id: UUID,
        consent_version: str,
        expected_request_id: UUID,
    ) -> RadarAcceptResult:
        if consent_version != CONSENT_VERSION:
            raise RadarInvalid
        pending = await self._pending_by_token(token)
        sources = {}
        for guest_id in (pending.owner_guest_id, recipient_guest_id):
            source = await self._birth.current(guest_id)
            sources[guest_id] = (source.snapshot_id, source.profile_revision)
        chart_b = await self._chart(recipient_guest_id)
        if chart_b is None:
            raise RadarChartRequired
        digest = self._hasher.digest("radar-capability", token)
        current = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            await self._lock_chart_sources(session, sources)
            row = await session.scalar(
                select(RadarRequestRow)
                .where(RadarRequestRow.token_hash == digest)
                .with_for_update()
            )
            if row is None or self._effective_status(row, current) is not RadarStatus.PENDING:
                raise RadarUnavailable
            if row.id != expected_request_id:
                raise RadarInvalid
            if row.owner_guest_id == recipient_guest_id:
                raise RadarInvalid
            chart_a = await self._chart(row.owner_guest_id)
            if chart_a is None:
                raise RadarChartRequired
            owner_projection = _reading(
                self._engine.calculate_relationship_bundle(chart_a, chart_b),
                context=row.context,
                voice=RelationshipVoice(row.voice),
            )
            recipient_projection = _reading(
                self._engine.calculate_relationship_bundle(chart_b, chart_a),
                context=row.context,
                voice=RelationshipVoice(row.voice),
            )
            receipt = secrets.token_urlsafe(32)
            row.recipient_guest_id = recipient_guest_id
            row.consent_version = consent_version
            row.result_ciphertext = self._envelope.encrypt(
                json.dumps(
                    {"owner": owner_projection, "recipient": recipient_projection},
                    ensure_ascii=False,
                ).encode(),
                context=f"radar-result:{row.id}".encode(),
            )
            row.receipt_hash = self._hasher.digest("radar-receipt", receipt)
            row.receipt_ciphertext = self._envelope.encrypt(
                receipt.encode(), context=f"radar-receipt:{row.id}".encode()
            )
            row.status = RadarStatus.COMPLETED.value
            row.completed_at = current
            row.expires_at = current + CONSENTED_RESULT_TTL
            row.token_ciphertext = None
            await session.flush()
            result = RadarAcceptResult(row.id, receipt, recipient_projection)
            owner_guest_id = row.owner_guest_id
            context = row.context
        await self._enqueue_rewrite(
            guest_id=owner_guest_id,
            request_id=result.request_id,
            perspective="owner",
            projection=owner_projection,
            context=context,
        )
        await self._enqueue_rewrite(
            guest_id=recipient_guest_id,
            request_id=result.request_id,
            perspective="recipient",
            projection=recipient_projection,
            context=context,
        )
        return result

    async def result(self, principal_id: UUID, request_id: UUID) -> dict[str, Any]:
        async with self._sessions() as session:
            row = await session.get(RadarRequestRow, request_id)
            if (
                row is None
                or row.principal_id != principal_id
                or RadarStatus(row.status) is not RadarStatus.COMPLETED
                or row.result_ciphertext is None
                or row.withdrawn_at is not None
                or row.expires_at <= datetime.now(UTC)
            ):
                raise RadarUnavailable
            stored = cast(
                dict[str, Any],
                json.loads(
                    self._envelope.decrypt(
                        row.result_ciphertext, context=f"radar-result:{row.id}".encode()
                    )
                ),
            )
            result = cast(dict[str, Any], stored.get("owner", stored))
            result["request_id"] = str(row.id)
            result["recipient_label"] = self._label(row)
            result["mode"] = row.mode
            result["expires_at"] = row.expires_at
            return result

    async def receipt_result(self, receipt: str) -> dict[str, Any]:
        current = datetime.now(UTC)
        digest = self._hasher.digest("radar-receipt", receipt)
        async with self._sessions() as session:
            row = await session.scalar(
                select(RadarRequestRow).where(RadarRequestRow.receipt_hash == digest)
            )
            if (
                row is None
                or row.completed_at is None
                or row.completed_at + RECEIPT_TTL <= current
                or row.withdrawn_at is not None
                or RadarStatus(row.status) is not RadarStatus.COMPLETED
                or row.result_ciphertext is None
            ):
                raise RadarUnavailable
            stored = cast(
                dict[str, Any],
                json.loads(
                    self._envelope.decrypt(
                        row.result_ciphertext, context=f"radar-result:{row.id}".encode()
                    )
                ),
            )
            recipient = stored.get("recipient")
            if not isinstance(recipient, dict):
                raise RadarUnavailable
            result = cast(dict[str, Any], recipient)
            result["request_id"] = str(row.id)
            result["mode"] = RadarMode.CONSENTED_INVITE.value
            return result

    async def delete(self, principal_id: UUID, request_id: UUID) -> None:
        owner_guest_id: UUID
        recipient_guest_id: UUID | None
        async with self._sessions() as session, session.begin():
            row = await session.get(RadarRequestRow, request_id, with_for_update=True)
            if row is None or row.principal_id != principal_id:
                raise RadarUnavailable
            owner_guest_id = row.owner_guest_id
            recipient_guest_id = row.recipient_guest_id
            sends = await pending_sends(
                session, (owner_guest_id,) + ((recipient_guest_id,) if recipient_guest_id else ())
            )
            await session.delete(row)
        await self._cancel_rewrites(request_id, owner_guest_id, recipient_guest_id)
        await drain_sends(self._sessions, sends)

    async def withdraw(self, receipt: str, *, expected_request_id: UUID) -> None:
        current = datetime.now(UTC)
        digest = self._hasher.digest("radar-receipt", receipt)
        owner_guest_id: UUID
        recipient_guest_id: UUID | None
        async with self._sessions() as session, session.begin():
            row = await session.scalar(
                select(RadarRequestRow)
                .where(RadarRequestRow.receipt_hash == digest)
                .with_for_update()
            )
            if (
                row is None
                or row.completed_at is None
                or row.completed_at + RECEIPT_TTL <= current
                or row.withdrawn_at is not None
                or row.id != expected_request_id
            ):
                raise RadarUnavailable
            owner_guest_id = row.owner_guest_id
            recipient_guest_id = row.recipient_guest_id
            sends = await pending_sends(
                session, (owner_guest_id,) + ((recipient_guest_id,) if recipient_guest_id else ())
            )
            row.status = RadarStatus.WITHDRAWN.value
            row.withdrawn_at = current
            row.result_ciphertext = None
            row.receipt_ciphertext = None
        await self._cancel_rewrites(expected_request_id, owner_guest_id, recipient_guest_id)
        await drain_sends(self._sessions, sends)

    async def _enqueue_rewrite(
        self,
        *,
        guest_id: UUID,
        request_id: UUID,
        perspective: RadarPerspective,
        projection: dict[str, Any],
        context: str,
    ) -> None:
        if not self._generation_enabled or self._content_rewrite_service is None:
            return
        request = compile_radar_rewrite_request(
            guest_id,
            request_id,
            perspective,
            cast(dict[str, object], projection),
            context=context,
            model_version=self._generation_model,
            prompt_version=self._generation_prompt_version,
        )
        if request is None:
            return
        try:
            await self._content_rewrite_service.enqueue(request)
        except (PermissionError, ValueError):
            logger.info(
                "Radar rewrite skipped because scoped authorization or safe evidence is unavailable"
            )
        except Exception as error:
            logger.warning("optional Radar rewrite enqueue failed: %s", type(error).__name__)

    async def _cancel_rewrites(
        self,
        request_id: UUID,
        owner_guest_id: UUID,
        recipient_guest_id: UUID | None,
    ) -> None:
        if self._content_rewrite_service is None:
            return
        await self._content_rewrite_service.cancel_owner(
            radar_rewrite_owner(owner_guest_id, request_id, "owner")
        )
        if recipient_guest_id is not None:
            await self._content_rewrite_service.cancel_owner(
                radar_rewrite_owner(recipient_guest_id, request_id, "recipient")
            )

    async def _pending_by_token(self, token: str) -> RadarRequestRow:
        if CAPABILITY_PATTERN.fullmatch(token) is None:
            raise RadarUnavailable
        digest = self._hasher.digest("radar-capability", token)
        current = datetime.now(UTC)
        async with self._sessions() as session:
            row = await session.scalar(
                select(RadarRequestRow).where(RadarRequestRow.token_hash == digest)
            )
            if row is None or self._effective_status(row, current) is not RadarStatus.PENDING:
                raise RadarUnavailable
            return row

    async def _chart(self, guest_id: UUID):  # type: ignore[no-untyped-def]
        return await self._birth.chart_for_config(guest_id, CalculationConfig.western_recommended())

    @staticmethod
    async def _lock_chart_sources(
        session: AsyncSession, sources: dict[UUID, tuple[UUID, datetime | None]]
    ) -> None:
        guests = []
        for guest_id in sorted(sources, key=lambda id: id.int):
            guests.append(
                await session.scalar(
                    select(GuestSessionRow).where(GuestSessionRow.id == guest_id).with_for_update()
                )
            )
        now = datetime.now(UTC)
        if any(
            guest is None or guest.state != "active" or guest.expires_at <= now for guest in guests
        ):
            raise RadarUnavailable
        for guest_id, (snapshot_id, revision) in sources.items():
            profile = await session.scalar(
                select(BirthProfileRow).where(
                    BirthProfileRow.guest_id == guest_id,
                    BirthProfileRow.current_snapshot_id == snapshot_id,
                    BirthProfileRow.updated_at == revision,
                    BirthProfileRow.profile_level == 3,
                )
            )
            if profile is None:
                raise RadarChartRequired

    def _label(self, row: RadarRequestRow) -> str:
        return self._envelope.decrypt(
            row.recipient_label_ciphertext, context=f"radar-label:{row.id}".encode()
        ).decode()

    def _view(self, row: RadarRequestRow, now: datetime) -> RadarInviteView:
        return RadarInviteView(
            id=row.id,
            recipient_label=self._label(row),
            context=row.context,
            voice=row.voice,
            mode=RadarMode(row.mode),
            status=self._effective_status(row, now),
            created_at=row.created_at,
            expires_at=row.expires_at,
        )

    @staticmethod
    def _effective_status(row: RadarRequestRow, now: datetime) -> RadarStatus:
        status = RadarStatus(row.status)
        if status in {RadarStatus.PENDING, RadarStatus.COMPLETED} and row.expires_at <= now:
            return RadarStatus.EXPIRED
        return status


def _reading(
    bundle: RelationshipBundle,
    *,
    context: str,
    voice: RelationshipVoice,
) -> dict[str, Any]:
    try:
        return build_radar_reading(bundle, context=context, voice=voice)
    except ValueError as error:
        raise RadarInvalid from error
