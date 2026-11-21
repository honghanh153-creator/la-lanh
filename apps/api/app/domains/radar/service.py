import json
import logging
import re
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import ColumnElement, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import load_only

from app.domains.astro import NatalChartEngine
from app.domains.astro.models import CalculationConfig, NatalChart, RelationshipBundle
from app.domains.birth.errors import BirthDomainError, BirthProfileNotFound
from app.domains.birth.models import BirthTimeMode
from app.domains.birth.service import BirthChartService
from app.domains.birth.tables import BirthProfileRow
from app.domains.content_rewrite.send_fence import drain_sends, pending_sends
from app.domains.content_rewrite.service import ContentRewriteService
from app.domains.erasure_journal.journal import ErasureJournal, ErasureKind
from app.domains.guest.tables import GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.radar import ask as radar_ask
from app.domains.radar import weekly as radar_weekly
from app.domains.radar.cards import (
    MAX_CARDS_PER_RESULT,
    RadarCardView,
    card_snapshot,
    card_view,
    initial_of,
)
from app.domains.radar.consent_drafts import invite_first_sentences
from app.domains.radar.models import (
    RadarAcceptResult,
    RadarInviteView,
    RadarMode,
    RadarPublicInvite,
    RadarReceivedView,
    RadarStatus,
)
from app.domains.radar.reading import BASIS_DATE_ONLY, BASIS_FULL, build_radar_reading
from app.domains.radar.rewrite import (
    RadarPerspective,
    compile_radar_rewrite_request,
    radar_rewrite_owner,
)
from app.domains.radar.tables import RadarRequestRow, RadarShareCardRow, RadarWeeklyPairRow
from app.domains.radar.weekly import weekly_sentences
from app.domains.relationships.models import RelationshipVoice
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

CAPABILITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
CONTEXTS = {"crush", "friend", "partner", "someone", "coworker", "family"}
CONSENT_VERSION = "radar-pair-v1"
AUTHORIZED_INPUT_VERSION = "radar-authorized-input-v1"
# Hợp gu AL1 (owner, 20.11.2026), both behind ``radar_invite_first_consent`` and the owner's
# approval of their sentences (``consent_drafts``): entering only the other person's birth date
# under the "tick only after asking" attestation, and the one-field invite where the other person
# types their own birth date.
AUTHORIZED_DATE_INPUT_VERSION = "radar-authorized-input-v2"
DATE_CONSENT_VERSION = "radar-pair-date-v1"
DATE_ONLY_MODE = "date_only"
INVITE_TTL = timedelta(days=7)
# Manual entry of the other person's birth data keeps the result briefly (owner decision
# 2026-10-19); a mutually consented pair result keeps the longer window.
PRIVATE_CHECK_TTL = timedelta(hours=24)
CONSENTED_RESULT_TTL = timedelta(days=30)
# B's receipt lives as long as the consented result, so B can view or withdraw it for the
# whole time A can (owner decision P09 D1, 22/10/2026; was 7 days).
RECEIPT_TTL = CONSENTED_RESULT_TTL
MAX_RETAINED_REQUESTS = 100
# AL1 direction C: a kept pair lives 90 days unless deleted sooner (owner AQ1, 21.11.2026); at
# most five kept pairs per sender. Only the invited person's own box keeps one (owner AR1).
WEEKLY_CONSENT_VERSION = "radar-weekly-recipient-v1"
WEEKLY_PAIR_TTL = timedelta(days=90)
MAX_WEEKLY_PAIRS = 5
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


class RadarRetired(RadarError):
    """Self-attested private checks are retired (owner AP2, 21.11.2026)."""


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
        invite_first_consent: bool = False,
        share_card_links: bool = False,
        weekly_pairs: bool = False,
        self_attested_checks: bool = False,
        erasure_journal: ErasureJournal | None = None,
    ) -> None:
        self._sessions = sessions
        self._hasher = hasher
        self._erasure_journal = erasure_journal
        self._envelope = envelope
        self._birth = birth
        self._engine = engine
        self._generation_enabled = generation_enabled
        self._generation_model = generation_model
        self._generation_prompt_version = generation_prompt_version
        self._content_rewrite_service = content_rewrite_service
        self._invite_first_consent = invite_first_consent
        self._share_card_links = share_card_links
        self._weekly_pairs = weekly_pairs
        self._self_attested_checks = self_attested_checks

    @property
    def weekly_enabled(self) -> bool:
        """AL1 direction C: keeping a pair for "Hai bạn tuần này". Needs the switch and the
        owner's approval of the opt-in sentences; off by default."""

        return self._weekly_pairs and weekly_sentences() is not None

    @property
    def share_card_links_enabled(self) -> bool:
        """AL1 direction C: revocable links to a frozen card. Off until the owner turns it on."""

        return self._share_card_links

    @property
    def invite_first_enabled(self) -> bool:
        """The AL1 consent paths: the switch is on and every sentence they show is approved."""

        return self._invite_first_consent and invite_first_sentences() is not None

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
        # AL1: a date-only owner may invite; the pair is then read from both birth dates.
        source = await self._source(owner_guest_id)
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
                session,
                {owner_guest_id: (source.snapshot_id, source.profile_revision)},
                require_full=False,
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
        place_id: str | None,
        consent_version: str,
        authorization_attested: bool,
        idempotency_key: str | None = None,
        now: datetime | None = None,
        keep_weekly: bool = False,
    ) -> dict[str, Any]:
        if not self._self_attested_checks:
            # Owner AP2 (21.11.2026): no "this person agreed" tick on any path. A pair is read only
            # when the other person types their own birth date through the link.
            raise RadarRetired
        label = " ".join(recipient_label.split())
        if keep_weekly:
            # Owner AR1 (21.11.2026): a pair is kept only when the invited person ticks their own
            # box on the link page; the sender cannot keep anyone's birth date.
            raise RadarInvalid
        date_only_input = birth_time_mode == DATE_ONLY_MODE
        accepted_versions = {AUTHORIZED_INPUT_VERSION}
        if self.invite_first_enabled:
            accepted_versions.add(AUTHORIZED_DATE_INPUT_VERSION)
        if (
            not 1 <= len(label) <= 40
            or context not in CONTEXTS
            or consent_version not in accepted_versions
            or not authorization_attested
            # AL1: the other person's date alone only under the new attestation (owner copy).
            or (date_only_input and consent_version != AUTHORIZED_DATE_INPUT_VERSION)
            or (date_only_input and (birth_time_local is not None or place_id is not None))
            or (not date_only_input and place_id is None)
        ):
            raise RadarInvalid
        config = CalculationConfig.western_recommended()
        source = await self._source(owner_guest_id)
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
                keep_weekly,
            ],
        )
        async with self._creation_transaction(principal_id, owner_guest_id, current) as session:
            existing = await self._replay(session, idem, request_hash, current)
            if existing is not None:
                return self._private_replay(existing)
            await self._capacity(session, principal_id)
        exact_a = await self._chart(owner_guest_id)
        if exact_a is None and consent_version != AUTHORIZED_DATE_INPUT_VERSION:
            # A date-only owner reads the pair from both dates, so the other person's time and
            # place would be collected only to be dropped. Under the old attestation that owner
            # uses the invite instead (no third-party data at all); the date-only form opens
            # with the AL1 attestation.
            raise RadarChartRequired
        # AL1: a pair is read at the lower basis of the two people. If either side has only a
        # birth date, both are read from their dates; the other person's time and place, when
        # given, are then not used at all.
        try:
            if exact_a is None or place_id is None:
                basis = BASIS_DATE_ONLY
                chart_a = await self._birth.date_only_chart_for(owner_guest_id, config)
                chart_b = await self._birth.calculate_date_only_chart(
                    birth_date=birth_date, config=config, now=now
                )
            else:
                basis, chart_a = BASIS_FULL, exact_a
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
            basis=basis,
        )
        metadata = cast(dict[str, Any], projection.setdefault("metadata", {}))
        metadata["time_precision"] = chart_b.time_precision.value
        if basis == BASIS_DATE_ONLY:
            pass  # the reading carries ``basis_note`` ("Dựa vào: ngày sinh của hai bạn.")
        elif chart_b.time_precision.value == "unknown":
            # Plain words (radar-readable-v2): the closing line stays one fixed sentence, so the
            # time caveat lives only in this note next to the headline.
            metadata["precision_note"] = (
                "Không rõ giờ sinh của người kia, nên Lá bỏ qua những dữ kiện cần giờ sinh. "
                "Bài đọc ngắn hơn một chút nhưng không đoán bừa."
            )
        elif chart_b.time_precision.value == "approximate":
            # An exact clock time whose historical UTC offset is unresolved (vn-offset-uncertain-v1)
            # is read as approximate: no Ascendant or houses. Reuses the shipped approximate-time
            # label from the birth form until owner-approved wording names the offset itself.
            metadata["precision_note"] = (
                "Giờ gần đúng: không dùng để khẳng định cung Mọc hay nhà chính xác."
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
                session,
                {owner_guest_id: (source.snapshot_id, source.profile_revision)},
                require_full=basis == BASIS_FULL,
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
                if self._erasure_journal is not None:
                    self._erasure_journal.record(
                        session, ErasureKind.RADAR_INVITE_REVOKED, row.id, current
                    )

    async def preview(self, token: str) -> RadarPublicInvite:
        row = await self._pending_by_token(token)
        return RadarPublicInvite(
            request_id=row.id,
            context=row.context,
            voice=row.voice,
            expires_at=row.expires_at,
            weekly_offer=await self._weekly_room(row.principal_id),
        )

    async def _weekly_room(self, principal_id: UUID) -> bool:
        """AR1: whether the link page may offer B the weekly box (on, approved, room left)."""

        if not self.weekly_enabled:
            return False
        async with self._sessions() as session:
            kept = await self._weekly_count(session, principal_id, datetime.now(UTC))
        return kept < MAX_WEEKLY_PAIRS

    @staticmethod
    async def _weekly_count(session: AsyncSession, principal_id: UUID, now: datetime) -> int:
        kept = await session.scalar(
            select(func.count())
            .select_from(RadarWeeklyPairRow)
            .where(
                RadarWeeklyPairRow.principal_id == principal_id,
                RadarWeeklyPairRow.expires_at > now,
            )
        )
        return int(kept or 0)

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
            source = await self._source(guest_id)
            sources[guest_id] = (source.snapshot_id, source.profile_revision)
        config = CalculationConfig.western_recommended()
        exact_b = await self._chart(recipient_guest_id)
        exact_a = await self._chart(pending.owner_guest_id)
        # AL1: if either side has only a birth date, both are read from their dates.
        if exact_a is not None and exact_b is not None:
            basis, chart_a, chart_b = BASIS_FULL, exact_a, exact_b
        else:
            basis = BASIS_DATE_ONLY
            chart_a = await self._birth.date_only_chart_for(pending.owner_guest_id, config)
            chart_b = await self._birth.date_only_chart_for(recipient_guest_id, config)
        return await self._complete_invite(
            token,
            chart_a=chart_a,
            chart_b=chart_b,
            basis=basis,
            sources=sources,
            recipient_guest_id=recipient_guest_id,
            consent_version=consent_version,
            expected_request_id=expected_request_id,
        )

    async def accept_with_date(
        self,
        token: str,
        *,
        birth_date: date,
        consent_version: str,
        expected_request_id: UUID,
        now: datetime | None = None,
        keep_weekly: bool = False,
    ) -> RadarAcceptResult:
        """The one-field invite (AL1): B types only B's own birth date and consents.

        Off unless ``invite_first_enabled``. B needs no profile or session: B's date is read
        once into a date-only chart in memory and is not stored unless B ticks the separate
        "Hai bạn tuần này" box (owner AR1, 21.11.2026; ``keep_weekly``, unticked by default). B
        keeps the result through the HttpOnly receipt and can withdraw it like any consented
        result; withdrawing, or using the invite link later, also deletes the kept pair.
        """

        if not self.invite_first_enabled or consent_version != DATE_CONSENT_VERSION:
            raise RadarInvalid
        if keep_weekly and not self.weekly_enabled:
            raise RadarInvalid
        pending = await self._pending_by_token(token)
        source = await self._source(pending.owner_guest_id)
        config = CalculationConfig.western_recommended()
        try:
            chart_b = await self._birth.calculate_date_only_chart(
                birth_date=birth_date, config=config, now=now
            )
        except BirthDomainError as error:
            raise RadarInvalid from error
        chart_a = await self._birth.date_only_chart_for(pending.owner_guest_id, config)
        return await self._complete_invite(
            token,
            chart_a=chart_a,
            chart_b=chart_b,
            basis=BASIS_DATE_ONLY,
            sources={pending.owner_guest_id: (source.snapshot_id, source.profile_revision)},
            recipient_guest_id=None,
            consent_version=consent_version,
            expected_request_id=expected_request_id,
            weekly_date=birth_date if keep_weekly else None,
        )

    async def _complete_invite(
        self,
        token: str,
        *,
        chart_a: NatalChart,
        chart_b: NatalChart,
        basis: str,
        sources: dict[UUID, tuple[UUID, datetime | None]],
        recipient_guest_id: UUID | None,
        consent_version: str,
        expected_request_id: UUID,
        weekly_date: date | None = None,
    ) -> RadarAcceptResult:
        digest = self._hasher.digest("radar-capability", token)
        current = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            await self._lock_chart_sources(session, sources, require_full=basis == BASIS_FULL)
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
            owner_projection = _reading(
                self._engine.calculate_relationship_bundle(chart_a, chart_b),
                context=row.context,
                voice=RelationshipVoice(row.voice),
                basis=basis,
            )
            recipient_projection = _reading(
                self._engine.calculate_relationship_bundle(chart_b, chart_a),
                context=row.context,
                voice=RelationshipVoice(row.voice),
                basis=basis,
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
            if weekly_date is not None:
                await self._keep_weekly(
                    session,
                    principal_id=row.principal_id,
                    owner_guest_id=row.owner_guest_id,
                    context=row.context,
                    label=self._envelope.decrypt(
                        row.recipient_label_ciphertext, context=f"radar-label:{row.id}".encode()
                    ).decode(),
                    birth_date=weekly_date,
                    now=current,
                    request_id=row.id,
                    invite_token_hash=digest,
                )
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
        if recipient_guest_id is not None:
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
            result["context"] = row.context
            return result

    async def ask_questions(self, principal_id: UUID, request_id: UUID) -> list[dict[str, str]]:
        """ "Hỏi về hai bạn": the approved questions the owner's stored reading can answer."""

        return radar_ask.questions_for(await self.result(principal_id, request_id))

    async def ask(self, principal_id: UUID, request_id: UUID, question_id: str) -> dict[str, Any]:
        """One answer, built only from the owner's stored reading (no new data, no AI)."""

        reading = await self.result(principal_id, request_id)
        try:
            return radar_ask.answer(reading, question_id).as_dict()
        except KeyError as error:
            raise RadarUnavailable from error

    async def create_card(
        self, principal_id: UUID, request_id: UUID, *, show_initial: bool
    ) -> tuple[RadarCardView, str]:
        """A revocable link to a frozen card of the owner's live result (no birth data, no name;
        at most an initial). It expires with the result and is removed with it."""

        if not self._share_card_links:
            raise RadarUnavailable
        reading = await self.result(principal_id, request_id)
        current = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        card_id = uuid4()
        snapshot = card_snapshot(
            reading, label=str(reading.get("recipient_label") or ""), show_initial=show_initial
        )
        async with self._sessions() as session, session.begin():
            row = await session.get(RadarRequestRow, request_id, with_for_update=True)
            if (
                row is None
                or row.principal_id != principal_id
                or self._effective_status(row, current) is not RadarStatus.COMPLETED
                or row.withdrawn_at is not None
            ):
                raise RadarUnavailable
            active = await session.scalar(
                select(func.count())
                .select_from(RadarShareCardRow)
                .where(
                    RadarShareCardRow.request_id == request_id,
                    RadarShareCardRow.revoked_at.is_(None),
                )
            )
            if (active or 0) >= MAX_CARDS_PER_RESULT:
                raise RadarLimitReached
            card = RadarShareCardRow(
                id=card_id,
                request_id=request_id,
                principal_id=principal_id,
                token_hash=self._hasher.digest("radar-card", token),
                snapshot_ciphertext=self._envelope.encrypt(
                    json.dumps(snapshot, ensure_ascii=False).encode(),
                    context=f"radar-card:{card_id}".encode(),
                ),
                created_at=current,
                expires_at=row.expires_at,
            )
            session.add(card)
            await session.flush()
            return card_view(card, current), token

    async def list_cards(self, principal_id: UUID, request_id: UUID) -> list[RadarCardView]:
        current = datetime.now(UTC)
        async with self._sessions() as session:
            rows = await session.scalars(
                select(RadarShareCardRow)
                .where(
                    RadarShareCardRow.request_id == request_id,
                    RadarShareCardRow.principal_id == principal_id,
                )
                .order_by(RadarShareCardRow.created_at.desc())
            )
            return [card_view(card, current) for card in rows]

    async def revoke_card(self, principal_id: UUID, card_id: UUID) -> None:
        async with self._sessions() as session, session.begin():
            card = await session.get(RadarShareCardRow, card_id, with_for_update=True)
            if card is None or card.principal_id != principal_id:
                raise RadarUnavailable
            if card.revoked_at is None:
                card.revoked_at = datetime.now(UTC)

    async def card(self, token: str) -> dict[str, Any]:
        """The public view of a card link; the same not-found for every refusal."""

        if not self._share_card_links or CAPABILITY_PATTERN.fullmatch(token) is None:
            raise RadarUnavailable
        current = datetime.now(UTC)
        async with self._sessions() as session:
            card = await session.scalar(
                select(RadarShareCardRow).where(
                    RadarShareCardRow.token_hash == self._hasher.digest("radar-card", token)
                )
            )
            if card is None or card.revoked_at is not None or card.expires_at <= current:
                raise RadarUnavailable
            row = await session.get(RadarRequestRow, card.request_id)
            if (
                row is None
                or self._effective_status(row, current) is not RadarStatus.COMPLETED
                or row.withdrawn_at is not None
            ):
                raise RadarUnavailable
            return cast(
                dict[str, Any],
                json.loads(
                    self._envelope.decrypt(
                        card.snapshot_ciphertext, context=f"radar-card:{card.id}".encode()
                    )
                ),
            )

    async def _keep_weekly(
        self,
        session: AsyncSession,
        *,
        principal_id: UUID,
        owner_guest_id: UUID,
        context: str,
        label: str,
        birth_date: date,
        now: datetime,
        request_id: UUID,
        invite_token_hash: bytes,
    ) -> None:
        """Keep the pair B opted into. When the sender already has the most pairs (a race with
        the preview's ``weekly_offer``), nothing is kept: storing less than B allowed is safe."""

        if await self._weekly_count(session, principal_id, now) >= MAX_WEEKLY_PAIRS:
            return
        pair_id = uuid4()
        session.add(
            RadarWeeklyPairRow(
                id=pair_id,
                principal_id=principal_id,
                owner_guest_id=owner_guest_id,
                context=context,
                label_ciphertext=self._envelope.encrypt(
                    label.encode(), context=f"radar-weekly-label:{pair_id}".encode()
                ),
                birth_date_ciphertext=self._envelope.encrypt(
                    birth_date.isoformat().encode(),
                    context=f"radar-weekly-date:{pair_id}".encode(),
                ),
                consent_version=WEEKLY_CONSENT_VERSION,
                created_at=now,
                expires_at=now + WEEKLY_PAIR_TTL,
                request_id=request_id,
                invite_token_hash=invite_token_hash,
            )
        )

    async def weekly(
        self, principal_id: UUID, *, today: date | None = None
    ) -> list[dict[str, Any]]:
        """This week's card for each kept pair (initial only, never the nickname or date)."""

        if not self.weekly_enabled:
            raise RadarUnavailable
        current = datetime.now(UTC)
        monday = radar_weekly.week_start(today or current.astimezone(radar_weekly.VIETNAM).date())
        config = CalculationConfig.western_recommended()
        async with self._sessions() as session:
            rows = list(
                await session.scalars(
                    select(RadarWeeklyPairRow)
                    .where(
                        RadarWeeklyPairRow.principal_id == principal_id,
                        RadarWeeklyPairRow.expires_at > current,
                    )
                    .order_by(RadarWeeklyPairRow.created_at)
                )
            )
        items: list[dict[str, Any]] = []
        for pair in rows:
            other = date.fromisoformat(
                self._envelope.decrypt(
                    pair.birth_date_ciphertext, context=f"radar-weekly-date:{pair.id}".encode()
                ).decode()
            )
            try:
                chart_a = await self._birth.date_only_chart_for(pair.owner_guest_id, config)
            except BirthDomainError:
                continue  # the owner's profile is gone; the pair goes with the guest data
            chart_b = await self._birth.calculate_date_only_chart(
                birth_date=other, config=config, require_adult=False
            )
            card = radar_weekly.card_for(
                radar_weekly.weekly_hits(self._engine, (chart_a, chart_b), monday), monday
            )
            if card is None:
                continue
            label = self._envelope.decrypt(
                pair.label_ciphertext, context=f"radar-weekly-label:{pair.id}".encode()
            ).decode()
            items.append(
                {
                    "id": str(pair.id),
                    "context": pair.context,
                    "initial": initial_of(label),
                    "week_of": card.week_of.isoformat(),
                    "easy": card.easy,
                    "watch": card.watch,
                    "try_line": card.try_line,
                    "quiet": card.quiet,
                    "expires_at": pair.expires_at,
                }
            )
        return items

    async def delete_weekly(self, principal_id: UUID, pair_id: UUID) -> None:
        async with self._sessions() as session, session.begin():
            pair = await session.get(RadarWeeklyPairRow, pair_id, with_for_update=True)
            if pair is None or pair.principal_id != principal_id:
                raise RadarUnavailable
            await session.delete(pair)

    async def receipt_result(self, receipt: str) -> dict[str, Any]:
        current = datetime.now(UTC)
        digest = self._hasher.digest("radar-receipt", receipt)
        async with self._sessions() as session:
            row = await session.scalar(
                select(RadarRequestRow).where(RadarRequestRow.receipt_hash == digest)
            )
            if row is None or not self._shared_with_recipient(row, current):
                raise RadarUnavailable
            return self._recipient_result(row)

    async def received(
        self,
        recipient_guest_id: UUID,
        *,
        before: UUID | None = None,
        limit: int = PAGE_SIZE,
    ) -> tuple[RadarReceivedView, ...]:
        """Consented results B can still see, found by B's own session (P09 D2).

        B needs no receipt: the session that accepted the invite is the proof, so a lost
        receipt cookie does not end B's view, export or withdrawal. Eligibility is filtered in
        SQL before the page limit, so withdrawn or expired rows never hide a readable one, and
        ``before`` continues from the last id of the previous page across every sender.
        """

        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise RadarInvalid
        current = datetime.now(UTC)
        async with self._sessions() as session:
            query = select(RadarRequestRow).where(
                RadarRequestRow.recipient_guest_id == recipient_guest_id,
                RadarRequestRow.status == RadarStatus.COMPLETED.value,
                RadarRequestRow.withdrawn_at.is_(None),
                RadarRequestRow.result_ciphertext.is_not(None),
                RadarRequestRow.completed_at.is_not(None),
                RadarRequestRow.completed_at > current - RECEIPT_TTL,
            )
            if before is not None:
                cursor = (
                    await session.execute(
                        select(RadarRequestRow.completed_at, RadarRequestRow.id).where(
                            RadarRequestRow.id == before,
                            RadarRequestRow.recipient_guest_id == recipient_guest_id,
                            RadarRequestRow.completed_at.is_not(None),
                        )
                    )
                ).one_or_none()
                if cursor is None:
                    raise RadarUnavailable
                query = query.where(
                    or_(
                        RadarRequestRow.completed_at < cursor.completed_at,
                        and_(
                            RadarRequestRow.completed_at == cursor.completed_at,
                            RadarRequestRow.id < cursor.id,
                        ),
                    )
                )
            rows = tuple(
                await session.scalars(
                    query.options(
                        load_only(
                            RadarRequestRow.id,
                            RadarRequestRow.context,
                            RadarRequestRow.voice,
                            RadarRequestRow.completed_at,
                            RadarRequestRow.expires_at,
                        )
                    )
                    .order_by(RadarRequestRow.completed_at.desc(), RadarRequestRow.id.desc())
                    .limit(limit)
                )
            )
        return tuple(
            RadarReceivedView(
                request_id=row.id,
                context=row.context,
                voice=row.voice,
                completed_at=cast(datetime, row.completed_at),
                expires_at=row.expires_at,
            )
            for row in rows
        )

    async def received_result(self, recipient_guest_id: UUID, request_id: UUID) -> dict[str, Any]:
        current = datetime.now(UTC)
        async with self._sessions() as session:
            row = await session.get(RadarRequestRow, request_id)
            if (
                row is None
                or row.recipient_guest_id != recipient_guest_id
                or not self._shared_with_recipient(row, current)
            ):
                raise RadarUnavailable
            return self._recipient_result(row)

    @staticmethod
    def _shared_with_recipient(row: RadarRequestRow, now: datetime) -> bool:
        return (
            row.completed_at is not None
            and row.completed_at + RECEIPT_TTL > now
            and row.withdrawn_at is None
            and RadarStatus(row.status) is RadarStatus.COMPLETED
            and row.result_ciphertext is not None
        )

    def _recipient_result(self, row: RadarRequestRow) -> dict[str, Any]:
        stored = cast(
            dict[str, Any],
            json.loads(
                self._envelope.decrypt(
                    cast(str, row.result_ciphertext), context=f"radar-result:{row.id}".encode()
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
            if self._erasure_journal is not None:
                self._erasure_journal.record(
                    session, ErasureKind.RADAR_DELETED, request_id, datetime.now(UTC)
                )
            await session.execute(
                delete(RadarShareCardRow).where(RadarShareCardRow.request_id == request_id)
            )
            await session.delete(row)
        await self._cancel_rewrites(request_id, owner_guest_id, recipient_guest_id)
        await drain_sends(self._sessions, sends)

    async def withdraw(self, receipt: str, *, expected_request_id: UUID) -> None:
        digest = self._hasher.digest("radar-receipt", receipt)
        await self._withdraw(RadarRequestRow.receipt_hash == digest, expected_request_id)

    async def withdraw_received(self, recipient_guest_id: UUID, request_id: UUID) -> None:
        """B withdraws from B's own session, without the receipt (P09 D2)."""

        await self._withdraw(
            and_(
                RadarRequestRow.id == request_id,
                RadarRequestRow.recipient_guest_id == recipient_guest_id,
            ),
            request_id,
        )

    async def withdraw_by_invite(self, token: str) -> None:
        """Withdraw a consented result by proving possession of its invite link (P09 D2).

        For B without the receipt or the session. Withdraw only, never view: A holds the same
        link, and A can already delete the result. The token names the row; no request id is
        bound because B on a new device cannot learn it (the completed invite no longer previews).
        """

        if CAPABILITY_PATTERN.fullmatch(token) is None:
            raise RadarUnavailable
        digest = self._hasher.digest("radar-capability", token)
        try:
            await self._withdraw(RadarRequestRow.token_hash == digest, None)
        except RadarUnavailable:
            # AR1: B's kept weekly pair outlives the 30-day result; the invite link still
            # deletes it for its whole 90 days.
            if not await self._delete_weekly_by_invite(digest):
                raise

    async def _delete_weekly_by_invite(self, digest: bytes) -> bool:
        async with self._sessions() as session, session.begin():
            deleted = await session.execute(
                delete(RadarWeeklyPairRow).where(RadarWeeklyPairRow.invite_token_hash == digest)
            )
        return bool(getattr(deleted, "rowcount", 0))

    async def _withdraw(
        self, condition: ColumnElement[bool], expected_request_id: UUID | None
    ) -> None:
        current = datetime.now(UTC)
        request_id: UUID
        owner_guest_id: UUID
        recipient_guest_id: UUID | None
        async with self._sessions() as session, session.begin():
            row = await session.scalar(select(RadarRequestRow).where(condition).with_for_update())
            if (
                row is None
                or row.completed_at is None
                or row.completed_at + RECEIPT_TTL <= current
                or row.withdrawn_at is not None
                or (expected_request_id is not None and row.id != expected_request_id)
            ):
                raise RadarUnavailable
            request_id = row.id
            owner_guest_id = row.owner_guest_id
            recipient_guest_id = row.recipient_guest_id
            sends = await pending_sends(
                session, (owner_guest_id,) + ((recipient_guest_id,) if recipient_guest_id else ())
            )
            row.status = RadarStatus.WITHDRAWN.value
            row.withdrawn_at = current
            await session.execute(
                delete(RadarShareCardRow).where(RadarShareCardRow.request_id == row.id)
            )
            await session.execute(
                delete(RadarWeeklyPairRow).where(RadarWeeklyPairRow.request_id == row.id)
            )
            if self._erasure_journal is not None:
                self._erasure_journal.record(session, ErasureKind.RADAR_WITHDRAWN, row.id, current)
            row.result_ciphertext = None
            row.receipt_ciphertext = None
        await self._cancel_rewrites(request_id, owner_guest_id, recipient_guest_id)
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

    async def _chart(self, guest_id: UUID) -> NatalChart | None:
        """The exact chart, or None when the profile has only a birth date (or no exact time)."""

        try:
            return await self._birth.chart_for_config(
                guest_id, CalculationConfig.western_recommended()
            )
        except BirthProfileNotFound as error:
            raise RadarChartRequired from error

    async def _source(self, guest_id: UUID):  # type: ignore[no-untyped-def]
        try:
            return await self._birth.current(guest_id)
        except BirthProfileNotFound as error:
            raise RadarChartRequired from error

    @staticmethod
    async def _lock_chart_sources(
        session: AsyncSession,
        sources: dict[UUID, tuple[UUID, datetime | None]],
        *,
        require_full: bool = True,
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
                    *((BirthProfileRow.profile_level == 3,) if require_full else ()),
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
    basis: str = BASIS_FULL,
) -> dict[str, Any]:
    try:
        return build_radar_reading(bundle, context=context, voice=voice, basis=basis)
    except ValueError as error:
        raise RadarInvalid from error
