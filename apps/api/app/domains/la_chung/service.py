import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.la_chung.models import (
    IdentityMode,
    InviteView,
    OwnerResult,
    PublicInvite,
    RequestStatus,
    Statement,
    SubmitResult,
)
from app.domains.la_chung.tables import LaChungReportRow, LaChungRequestRow, LaChungResponseRow
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

BANK_VERSION = "la-chung-v1"
STATEMENTS = (
    Statement("warm-presence", "Bạn khiến người khác thấy dễ được là chính mình.", "connection"),
    Statement("quiet-courage", "Bạn thường can đảm hơn vẻ ngoài.", "drive"),
    Statement("sharp-observer", "Bạn nhận ra những điều nhỏ mà người khác bỏ qua.", "mind"),
    Statement("soft-boundary", "Bạn dịu dàng nhưng có ranh giới riêng.", "boundary"),
    Statement("steady-care", "Bạn quan tâm bằng những hành động rất cụ thể.", "care"),
    Statement("bright-chaos", "Bạn mang tới một chút hỗn loạn đầy sức sống.", "energy"),
    Statement("deep-loyalty", "Khi đã tin ai, bạn ở lại rất thật lòng.", "trust"),
    Statement("fresh-angle", "Bạn hay mở ra một góc nhìn không ai ngờ tới.", "mind"),
)
STATEMENT_IDS = {item.id for item in STATEMENTS}
CONTEXTS = {"bff", "crush", "couple", "friend", "workmate"}
ALIAS_CONTACT = re.compile(r"(?:\+?\d[\d .-]{7,}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})")
REPORT_REASONS = {"not_for_me", "unsafe", "spam", "other"}
RECEIPT_TTL = timedelta(days=7)
CAPABILITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


class LaChungError(RuntimeError):
    pass


class LaChungUnavailable(LaChungError):
    pass


class LaChungInvalid(LaChungError):
    pass


class LaChungService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        hasher: SecretHasher,
        envelope: EnvelopeCipher,
    ) -> None:
        self._sessions = sessions
        self._hasher = hasher
        self._envelope = envelope

    async def create(
        self,
        *,
        principal_id: UUID,
        recipient_label: str,
        context: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[InviteView, str]:
        label = " ".join(recipient_label.split())
        if (
            not 1 <= len(label) <= 40
            or context not in CONTEXTS
            or IDEMPOTENCY_PATTERN.fullmatch(idempotency_key) is None
        ):
            raise LaChungInvalid
        current = now or datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        request_id = uuid4()
        idempotency_hash = self._hasher.digest(
            "la-chung-invite-idempotency", f"{principal_id}:{idempotency_key}"
        )
        draft_hash = self._hasher.digest("la-chung-invite-draft", f"{label}\x00{context}")
        row = LaChungRequestRow(
            id=request_id,
            principal_id=principal_id,
            recipient_label=None,
            recipient_label_ciphertext=self._envelope.encrypt(
                label.encode(), context=f"la-chung-recipient-label:{request_id}".encode()
            ),
            context=context,
            status=RequestStatus.PENDING.value,
            bank_version=BANK_VERSION,
            token_hash=self._hasher.digest("la-chung-capability", token),
            token_ciphertext=self._envelope.encrypt(
                token.encode(), context=f"la-chung-capability:{request_id}".encode()
            ),
            idempotency_hash=idempotency_hash,
            draft_hash=draft_hash,
            created_at=current,
            expires_at=current + timedelta(days=7),
        )
        async with self._sessions() as session, session.begin():
            try:
                async with session.begin_nested():
                    session.add(row)
                    await session.flush()
            except IntegrityError:
                pass
            stored = await session.scalar(
                select(LaChungRequestRow).where(
                    LaChungRequestRow.idempotency_hash == idempotency_hash
                )
            )
            if stored is None:
                raise RuntimeError("idempotent invite creation could not be resolved")
            if stored.draft_hash is None or not secrets.compare_digest(
                stored.draft_hash, draft_hash
            ):
                raise LaChungInvalid
            if (
                stored.principal_id != principal_id
                or _effective_status(stored, current) is not RequestStatus.PENDING
                or stored.token_ciphertext is None
            ):
                raise LaChungUnavailable
            replay_token = self._envelope.decrypt(
                stored.token_ciphertext,
                context=f"la-chung-capability:{stored.id}".encode(),
            ).decode()
            view = self._view(stored, current)
        return view, replay_token

    async def list_owned(self, principal_id: UUID) -> tuple[InviteView, ...]:
        current = datetime.now(UTC)
        async with self._sessions() as session:
            rows = tuple(
                await session.scalars(
                    select(LaChungRequestRow)
                    .where(LaChungRequestRow.principal_id == principal_id)
                    .order_by(LaChungRequestRow.created_at.desc())
                )
            )
        return tuple(self._view(row, current) for row in rows)

    async def resend(self, principal_id: UUID, request_id: UUID) -> str:
        current = datetime.now(UTC)
        async with self._sessions() as session:
            row = await session.get(LaChungRequestRow, request_id)
            if (
                row is None
                or row.principal_id != principal_id
                or _effective_status(row, current) is not RequestStatus.PENDING
                or row.token_ciphertext is None
            ):
                raise LaChungUnavailable
            return self._envelope.decrypt(
                row.token_ciphertext,
                context=f"la-chung-capability:{row.id}".encode(),
            ).decode()

    async def replace(self, principal_id: UUID, request_id: UUID) -> tuple[InviteView, str]:
        current = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        async with self._sessions() as session, session.begin():
            row = await session.get(LaChungRequestRow, request_id, with_for_update=True)
            if row is None or row.principal_id != principal_id:
                raise LaChungUnavailable
            if _effective_status(row, current) in {
                RequestStatus.COMPLETED,
                RequestStatus.WITHDRAWN,
                RequestStatus.DELETED,
            }:
                raise LaChungUnavailable
            row.token_hash = self._hasher.digest("la-chung-capability", token)
            row.token_ciphertext = self._envelope.encrypt(
                token.encode(), context=f"la-chung-capability:{row.id}".encode()
            )
            row.status = RequestStatus.PENDING.value
            row.revoked_at = None
            row.expires_at = current + timedelta(days=7)
            await session.flush()
            view = self._view(row, current)
        return view, token

    async def revoke(self, principal_id: UUID, request_id: UUID) -> None:
        current = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            row = await session.get(LaChungRequestRow, request_id, with_for_update=True)
            if row is None or row.principal_id != principal_id:
                raise LaChungUnavailable
            if _effective_status(row, current) is RequestStatus.PENDING:
                row.status = RequestStatus.REVOKED.value
                row.revoked_at = current
                row.token_ciphertext = None

    async def preview(self, token: str) -> PublicInvite:
        if CAPABILITY_PATTERN.fullmatch(token) is None:
            raise LaChungUnavailable
        current = datetime.now(UTC)
        digest = self._hasher.digest("la-chung-capability", token)
        async with self._sessions() as session:
            row = await session.scalar(
                select(LaChungRequestRow).where(LaChungRequestRow.token_hash == digest)
            )
            if row is None:
                raise LaChungUnavailable
            status = _effective_status(row, current)
            if status is not RequestStatus.PENDING:
                raise LaChungUnavailable
            return PublicInvite(
                recipient_label=self._recipient_label(row),
                context=row.context,
                status=status,
                expires_at=row.expires_at,
                statements=STATEMENTS,
            )

    async def submit(
        self,
        *,
        token: str,
        selections: tuple[str, ...],
        identity_mode: IdentityMode,
        display_alias: str | None,
        idempotency_key: str,
    ) -> SubmitResult:
        if CAPABILITY_PATTERN.fullmatch(token) is None:
            raise LaChungUnavailable
        if not 3 <= len(selections) <= 5 or len(set(selections)) != len(selections):
            raise LaChungInvalid
        if not set(selections) <= STATEMENT_IDS:
            raise LaChungInvalid
        alias = " ".join((display_alias or "").split()) or None
        if identity_mode is IdentityMode.ANONYMOUS:
            alias = None
        elif alias is None or len(alias) > 24 or ALIAS_CONTACT.search(alias):
            raise LaChungInvalid
        current = datetime.now(UTC)
        capability_hash = self._hasher.digest("la-chung-capability", token)
        idem_hash = self._hasher.digest(
            "la-chung-response-idempotency", f"{token}:{idempotency_key}"
        )
        async with self._sessions() as session, session.begin():
            replay = await session.scalar(
                select(LaChungResponseRow).where(LaChungResponseRow.idempotency_hash == idem_hash)
            )
            if replay is not None:
                replay_request = await session.get(LaChungRequestRow, replay.request_id)
                if (
                    replay_request is None
                    or replay_request.token_hash != capability_hash
                    or RequestStatus(replay_request.status) is not RequestStatus.COMPLETED
                    or replay_request.expires_at <= current
                    or replay.receipt_ciphertext is None
                    or replay.withdrawn_at is not None
                    or replay.submitted_at + RECEIPT_TTL <= current
                ):
                    raise LaChungUnavailable
                receipt = self._envelope.decrypt(
                    replay.receipt_ciphertext,
                    context=f"la-chung-receipt:{replay.id}".encode(),
                ).decode()
                return SubmitResult(replay.request_id, receipt, replay.submitted_at, True)
            request = await session.scalar(
                select(LaChungRequestRow)
                .where(LaChungRequestRow.token_hash == capability_hash)
                .with_for_update()
            )
            if request is None or _effective_status(request, current) is not RequestStatus.PENDING:
                raise LaChungUnavailable
            receipt = secrets.token_urlsafe(32)
            response_id = uuid4()
            response = LaChungResponseRow(
                id=response_id,
                request_id=request.id,
                selections=list(selections),
                identity_mode=identity_mode.value,
                display_alias=alias,
                idempotency_hash=idem_hash,
                receipt_hash=self._hasher.digest("la-chung-receipt", receipt),
                receipt_ciphertext=self._envelope.encrypt(
                    receipt.encode(), context=f"la-chung-receipt:{response_id}".encode()
                ),
                submitted_at=current,
            )
            session.add(response)
            request.status = RequestStatus.COMPLETED.value
            request.completed_at = current
            request.token_ciphertext = None
            await session.flush()
            return SubmitResult(request.id, receipt, current, False)

    async def withdraw(self, receipt: str) -> None:
        current = datetime.now(UTC)
        digest = self._hasher.digest("la-chung-receipt", receipt)
        async with self._sessions() as session, session.begin():
            response = await session.scalar(
                select(LaChungResponseRow)
                .where(LaChungResponseRow.receipt_hash == digest)
                .with_for_update()
            )
            if (
                response is None
                or response.withdrawn_at is not None
                or response.receipt_ciphertext is None
                or response.submitted_at + RECEIPT_TTL <= current
            ):
                raise LaChungUnavailable
            request = await session.get(
                LaChungRequestRow, response.request_id, with_for_update=True
            )
            if request is None or RequestStatus(request.status) is not RequestStatus.COMPLETED:
                raise LaChungUnavailable
            response.withdrawn_at = current
            response.receipt_ciphertext = None
            request.status = RequestStatus.WITHDRAWN.value

    async def result(self, principal_id: UUID, request_id: UUID) -> OwnerResult:
        async with self._sessions() as session:
            request = await session.get(LaChungRequestRow, request_id)
            if request is None or request.principal_id != principal_id:
                raise LaChungUnavailable
            response = await session.scalar(
                select(LaChungResponseRow).where(
                    LaChungResponseRow.request_id == request_id,
                    LaChungResponseRow.deleted_at.is_(None),
                    LaChungResponseRow.withdrawn_at.is_(None),
                    LaChungResponseRow.hidden_at.is_(None),
                )
            )
            if response is None:
                raise LaChungUnavailable
            text_by_id = {item.id: item.text for item in STATEMENTS}
            return OwnerResult(
                request_id=request.id,
                recipient_label=self._recipient_label(request),
                identity_mode=IdentityMode(response.identity_mode),
                display_alias=response.display_alias,
                statements=tuple(text_by_id[item] for item in response.selections),
                submitted_at=response.submitted_at,
            )

    async def report(self, token: str, reason: str) -> None:
        if reason not in REPORT_REASONS:
            raise LaChungInvalid
        if CAPABILITY_PATTERN.fullmatch(token) is None:
            return
        current = datetime.now(UTC)
        digest = self._hasher.digest("la-chung-capability", token)
        async with self._sessions() as session, session.begin():
            request = await session.scalar(
                select(LaChungRequestRow).where(LaChungRequestRow.token_hash == digest)
            )
            if request is None or _effective_status(request, current) is not RequestStatus.PENDING:
                return
            existing = await session.scalar(
                select(LaChungReportRow.id).where(
                    LaChungReportRow.request_id == request.id,
                    LaChungReportRow.reason == reason,
                )
            )
            if existing is not None:
                return
            try:
                async with session.begin_nested():
                    session.add(
                        LaChungReportRow(
                            request_id=request.id,
                            reason=reason,
                            created_at=datetime.now(UTC),
                        )
                    )
                    await session.flush()
            except IntegrityError:
                # Concurrent duplicate reports collapse to one row by the DB constraint.
                return

    async def hide_result(self, principal_id: UUID, request_id: UUID) -> None:
        async with self._sessions() as session, session.begin():
            request = await session.get(LaChungRequestRow, request_id)
            if request is None or request.principal_id != principal_id:
                raise LaChungUnavailable
            response = await session.scalar(
                select(LaChungResponseRow).where(
                    LaChungResponseRow.request_id == request_id,
                    LaChungResponseRow.withdrawn_at.is_(None),
                    LaChungResponseRow.deleted_at.is_(None),
                )
            )
            if response is None:
                raise LaChungUnavailable
            response.hidden_at = datetime.now(UTC)

    async def delete_result(self, principal_id: UUID, request_id: UUID) -> None:
        async with self._sessions() as session, session.begin():
            request = await session.get(LaChungRequestRow, request_id, with_for_update=True)
            if request is None or request.principal_id != principal_id:
                raise LaChungUnavailable
            await session.delete(request)

    def _recipient_label(self, row: LaChungRequestRow) -> str:
        if row.recipient_label_ciphertext is not None:
            return self._envelope.decrypt(
                row.recipient_label_ciphertext,
                context=f"la-chung-recipient-label:{row.id}".encode(),
            ).decode()
        if row.recipient_label is not None:
            return row.recipient_label
        raise LaChungUnavailable

    def _view(self, row: LaChungRequestRow, now: datetime) -> InviteView:
        return InviteView(
            id=row.id,
            recipient_label=self._recipient_label(row),
            context=row.context,
            status=_effective_status(row, now),
            created_at=row.created_at,
            expires_at=row.expires_at,
        )


def _effective_status(row: LaChungRequestRow, now: datetime) -> RequestStatus:
    status = RequestStatus(row.status)
    if status is RequestStatus.PENDING and row.expires_at <= now:
        return RequestStatus.EXPIRED
    return status
