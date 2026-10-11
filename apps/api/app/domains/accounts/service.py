import secrets
from datetime import UTC, datetime, timedelta
from typing import TypeGuard
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.domains.accounts.models import (
    ACCOUNT_DAYS,
    CHALLENGE_SECONDS,
    DEVICE_DAYS,
    STORAGE_CONSENT,
    AccountDevice,
    AccountError,
    Challenge,
    LoginResult,
    ProviderIdentity,
)
from app.domains.accounts.postgres import (
    account_transaction,
    admit,
    lock_owner,
    lock_owners,
    lock_subject,
    owned_credential,
)
from app.domains.accounts.provider import SupabaseOtpProvider
from app.domains.accounts.tables import AccountDeviceRow, AccountRow, LoginChallengeRow
from app.domains.guest.models import GuestSessionRecord, GuestState, OnboardingStatus
from app.domains.guest.tables import ConsentRow, GuestCreationRow, GuestSessionRow
from app.domains.identity.tables import OwnerSessionRow, PrincipalRow
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

LOGIN_COOKIE = "la_lanh_login"
RESTORE_COOKIE = "la_lanh_login_restore"


class AccountService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        hasher: SecretHasher,
        envelope: EnvelopeCipher,
        provider: SupabaseOtpProvider,
        settings: Settings,
    ) -> None:
        self._sessions = sessions
        self._hasher = hasher
        self._envelope = envelope
        self._provider = provider
        self._settings = settings

    def _enabled(self) -> None:
        if not self._settings.auth_enabled or not (
            self._settings.auth_delivery_approved or self._settings.auth_google_enabled
        ):
            raise AccountError("LOGIN_UNAVAILABLE", 503)

    def _credential_digest(self, token: str | None) -> bytes | None:
        return self._hasher.digest("guest-credential", token) if token else None

    async def request_code(
        self,
        email: str,
        *,
        token: str | None,
        csrf: str | None,
        consent: str | None,
        peer: str,
        now: datetime | None = None,
    ) -> Challenge:
        self._enabled()
        current = now or datetime.now(UTC)
        cookie, login_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        email_digest = self._hasher.digest("account-email", email)
        credential_digest = self._credential_digest(token)
        error = None
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, credential_digest, current)
            if owned is not None:
                guest, device = owned
                expected = device.csrf_digest if device is not None else guest.csrf_hash
                if not csrf or not self._hasher.verify("guest-csrf", csrf, expected):
                    raise AccountError("LOGIN_CSRF_REJECTED", 403)
            # Expired credentials can request account recovery but cannot link a
            # profile. Bind even an expired cookie so a guest switch invalidates
            # the challenge. No renewal or mutation of the initiating guest here.
            error = await admit(session, self._hasher, "send", peer, email_digest, current)
            if error is None:
                challenge = LoginChallengeRow(
                    cookie_digest=self._hasher.digest("account-login-cookie", cookie),
                    csrf_digest=self._hasher.digest("account-login-csrf", login_csrf),
                    initiating_guest_id=owned[0].id if owned is not None else None,
                    initiating_credential_digest=credential_digest,
                    email_digest=email_digest,
                    email_envelope=self._envelope.encrypt(
                        email.encode(), context=b"account-login-email-v1"
                    ),
                    storage_consent=consent,
                    state="sending",
                    attempts=0,
                    created_at=current,
                    expires_at=current + timedelta(seconds=CHALLENGE_SECONDS),
                )
                session.add(challenge)
                await session.flush()
        if error is not None:
            raise error
        try:
            await self._provider.request_code(email)
        except AccountError:
            await self._finish_send(cookie, success=False)
            raise AccountError("LOGIN_CODE_UNAVAILABLE", 503) from None
        await self._finish_send(cookie, success=True)
        return Challenge(cookie, login_csrf, current + timedelta(seconds=CHALLENGE_SECONDS))

    async def _finish_send(self, cookie: str, *, success: bool) -> None:
        async with account_transaction(self._sessions) as session:
            row = await session.scalar(
                select(LoginChallengeRow)
                .where(
                    LoginChallengeRow.cookie_digest
                    == self._hasher.digest("account-login-cookie", cookie)
                )
                .with_for_update()
            )
            if row is not None and row.state == "sending":
                row.state = "pending" if success else "failed"
                if not success:
                    row.email_envelope = None

    async def _challenge(
        self,
        session: AsyncSession,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        now: datetime,
        *,
        lock: bool = True,
        allow_expired: bool = False,
    ) -> LoginChallengeRow:
        if not cookie or not csrf:
            raise AccountError("LOGIN_CHALLENGE_REJECTED", 403)
        query = (
            select(LoginChallengeRow)
            .execution_options(populate_existing=True)
            .where(
                LoginChallengeRow.cookie_digest
                == self._hasher.digest("account-login-cookie", cookie)
            )
        )
        row = await session.scalar(query.with_for_update() if lock else query)
        if row is None or not self._hasher.verify("account-login-csrf", csrf, row.csrf_digest):
            raise AccountError("LOGIN_CHALLENGE_REJECTED", 403)
        if row.initiating_credential_digest != self._credential_digest(token):
            raise AccountError("LOGIN_CHALLENGE_REJECTED", 403)
        if not allow_expired and row.expires_at <= now:
            raise AccountError("LOGIN_CHALLENGE_EXPIRED")
        return row

    async def verify(
        self,
        code: str,
        *,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        peer: str,
        now: datetime | None = None,
    ) -> LoginResult:
        self._enabled()
        current = now or datetime.now(UTC)
        error = None
        async with account_transaction(self._sessions) as session:
            row = await self._challenge(session, cookie, csrf, token, current)
            if (
                row.login_provider != "email"
                or row.state != "pending"
                or row.attempts >= 5
                or row.email_envelope is None
            ):
                raise AccountError("LOGIN_CHALLENGE_USED")
            error = await admit(session, self._hasher, "verify", peer, row.email_digest, current)
            if error is None:
                # Commit the single verifier claim and attempt BEFORE sending.
                # A crash or cancelled request fails closed until challenge expiry.
                row.state = "verifying"
                row.attempts += 1
                email = self._envelope.decrypt(
                    row.email_envelope, context=b"account-login-email-v1"
                ).decode()
        if error is not None:
            raise error
        try:
            identity = await self._provider.verify_code(email, code)
        except AccountError:
            async with account_transaction(self._sessions) as session:
                row = await self._challenge(session, cookie, csrf, token, current)
                if row.state == "verifying":
                    row.state = "failed" if row.attempts >= 5 else "pending"
                    if row.state == "failed":
                        row.email_envelope = None
            raise AccountError("LOGIN_VERIFICATION_FAILED") from None
        # Time is checked again after the external request, unless a deterministic
        # clock was explicitly supplied by a caller such as a maintenance test.
        completed = current if now is not None else datetime.now(UTC)
        return await self._complete_verified(
            identity, cookie=cookie, csrf=csrf, token=token, completed=completed
        )

    async def start_google(
        self,
        *,
        token: str | None,
        csrf: str | None,
        consent: str | None,
        peer: str,
        now: datetime | None = None,
    ) -> tuple[Challenge, str]:
        self._enabled()
        if not self._settings.auth_google_enabled:
            raise AccountError("LOGIN_UNAVAILABLE", 503)
        if consent != STORAGE_CONSENT:
            raise AccountError("ACCOUNT_CONSENT_REQUIRED", 403)
        current = now or datetime.now(UTC)
        cookie, state, verifier = (secrets.token_urlsafe(32) for _ in range(3))
        url = self._provider.google_authorize_url(verifier, state)
        digest = self._credential_digest(token)
        error = None
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, digest, current)
            if owned:
                owner, device = owned
                expected = device.csrf_digest if device else owner.csrf_hash
                if not csrf or not self._hasher.verify("guest-csrf", csrf, expected):
                    raise AccountError("LOGIN_CSRF_REJECTED", 403)
            error = await admit(
                session,
                self._hasher,
                "send",
                peer,
                self._hasher.digest("account-oauth-quota", state),
                current,
            )
            if error is None:
                session.add(
                    LoginChallengeRow(
                        cookie_digest=self._hasher.digest("account-login-cookie", cookie),
                        csrf_digest=self._hasher.digest("account-login-csrf", state),
                        initiating_guest_id=owned[0].id if owned else None,
                        initiating_credential_digest=digest,
                        email_digest=self._hasher.digest("account-oauth-quota", state),
                        oauth_verifier_envelope=self._envelope.encrypt(
                            verifier.encode(), context=b"account-google-pkce-v1"
                        ),
                        login_provider="google",
                        storage_consent=consent,
                        state="oauth_pending",
                        attempts=0,
                        created_at=current,
                        expires_at=current + timedelta(seconds=CHALLENGE_SECONDS),
                    )
                )
        if error:
            raise error
        return Challenge(cookie, state, current + timedelta(seconds=CHALLENGE_SECONDS)), url

    async def verify_google(
        self,
        code: str,
        *,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        peer: str,
        now: datetime | None = None,
    ) -> LoginResult:
        self._enabled()
        if not self._settings.auth_google_enabled:
            raise AccountError("LOGIN_UNAVAILABLE", 503)
        current = now or datetime.now(UTC)
        error = None
        async with account_transaction(self._sessions) as session:
            row = await self._challenge(session, cookie, csrf, token, current)
            if (
                row.login_provider != "google"
                or row.state != "oauth_pending"
                or row.oauth_verifier_envelope is None
            ):
                raise AccountError("LOGIN_CHALLENGE_USED")
            error = await admit(session, self._hasher, "verify", peer, row.email_digest, current)
            if error is None:
                row.state = "verifying"
                row.attempts += 1
                verifier = self._envelope.decrypt(
                    row.oauth_verifier_envelope, context=b"account-google-pkce-v1"
                ).decode()
                row.oauth_verifier_envelope = None
        if error:
            raise error
        try:
            identity = await self._provider.exchange_google(code, verifier)
        except AccountError:
            async with account_transaction(self._sessions) as session:
                row = await self._challenge(session, cookie, csrf, token, current)
                if row.state == "verifying":
                    self._consume(row)
            raise AccountError("LOGIN_VERIFICATION_FAILED") from None
        completed = current if now is not None else datetime.now(UTC)
        return await self._complete_verified(
            identity, cookie=cookie, csrf=csrf, token=token, completed=completed
        )

    async def _complete_verified(
        self,
        identity: ProviderIdentity,
        *,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        completed: datetime,
    ) -> LoginResult:
        async with account_transaction(self._sessions) as session:
            row = await self._challenge(session, cookie, csrf, token, completed, lock=False)
            await lock_subject(session, identity.subject)
            account = await session.get(AccountRow, identity.subject)
            # Discover first, then acquire owner-before-challenge locks. Erasure
            # cascades challenge rows while holding the owner lock in this order.
            await lock_owners(
                session, [row.initiating_guest_id, account.guest_id if account else None]
            )
            guest = await lock_owner(session, account.guest_id) if account else None
            owned = (
                None
                if account
                else await owned_credential(session, row.initiating_credential_digest, completed)
            )
            row = await self._challenge(session, cookie, csrf, token, completed)
            if row.state != "verifying":
                raise AccountError("LOGIN_CHALLENGE_USED")
            if account is not None:
                if not _active(guest, completed):
                    self._consume(row)
                    return LoginResult("onboarding_required")
                proof = secrets.token_urlsafe(32)
                row.state = "restore_required"
                row.subject_id = identity.subject
                row.target_guest_id = account.guest_id
                row.proof_digest = self._hasher.digest("account-restore-proof", proof)
                row.email_envelope = None
                row.oauth_verifier_envelope = None
                row.expires_at = min(row.expires_at, completed + timedelta(minutes=5))
                return LoginResult(
                    "restore_required",
                    restore_token=proof,
                    masked_email=account.masked_email,
                    profile_expires_at=guest.expires_at,
                )
            if owned is None or owned[1] is not None or owned[0].id != row.initiating_guest_id:
                self._consume(row)
                return LoginResult("onboarding_required")
            guest = owned[0]
            # A guest can be linked to only one subject, even when two independently
            # verified challenges race for that guest under different subject locks.
            linked = await session.scalar(select(AccountRow).where(AccountRow.guest_id == guest.id))
            if linked is not None:
                self._consume(row)
                return LoginResult("onboarding_required")
            if row.storage_consent != STORAGE_CONSENT:
                self._consume(row)
                return LoginResult("consent_required")
            session.add(
                AccountRow(
                    subject_id=identity.subject,
                    guest_id=guest.id,
                    masked_email=identity.masked_email,
                    created_at=completed,
                )
            )
            await session.flush()
            consent = await session.scalar(
                select(ConsentRow).where(
                    ConsentRow.guest_id == guest.id, ConsentRow.purpose == "account_storage"
                )
            )
            if consent is None:
                session.add(
                    ConsentRow(
                        guest_id=guest.id,
                        purpose="account_storage",
                        version=STORAGE_CONSENT,
                        accepted_at=completed,
                    )
                )
            else:
                consent.version, consent.accepted_at, consent.revoked_at = (
                    STORAGE_CONSENT,
                    completed,
                    None,
                )
            # Invalidate the shared anonymous secret ONCE. Later devices never
            # rotate it. No pre-link idempotency envelope may re-advertise it.
            guest.token_hash = self._hasher.digest("guest-credential", secrets.token_urlsafe(32))
            guest.csrf_hash = self._hasher.digest("guest-csrf", secrets.token_urlsafe(32))
            await session.execute(
                update(GuestCreationRow)
                .where(GuestCreationRow.guest_id == guest.id)
                .values(credential_envelope=None)
            )
            # A legacy owner bearer must not survive initial ownership takeover.
            await session.execute(
                update(OwnerSessionRow)
                .where(
                    OwnerSessionRow.principal_id.in_(
                        select(PrincipalRow.id).where(PrincipalRow.source_guest_id == guest.id)
                    )
                )
                .values(revoked_at=completed)
            )
            self._consume(row)
            return await self._issue_device(session, guest, identity, completed)

    async def restore(
        self,
        *,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        proof: str | None,
        now: datetime | None = None,
    ) -> LoginResult:
        self._enabled()
        current = now or datetime.now(UTC)
        async with account_transaction(self._sessions) as session:
            row = await self._challenge(session, cookie, csrf, token, current, lock=False)
            if (
                row.state != "restore_required"
                or row.subject_id is None
                or row.proof_digest is None
                or not proof
                or not self._hasher.verify("account-restore-proof", proof, row.proof_digest)
            ):
                raise AccountError("LOGIN_CHALLENGE_USED")
            await lock_subject(session, row.subject_id)
            account = await session.get(AccountRow, row.subject_id)
            if account is None or account.guest_id != row.target_guest_id:
                raise AccountError("LOGIN_CHALLENGE_USED")
            await lock_owners(session, [row.initiating_guest_id, account.guest_id])
            guest = await lock_owner(session, account.guest_id)
            row = await self._challenge(session, cookie, csrf, token, current)
            if (
                row.state != "restore_required"
                or row.proof_digest is None
                or not self._hasher.verify("account-restore-proof", proof, row.proof_digest)
            ):
                raise AccountError("LOGIN_CHALLENGE_USED")
            if not _active(guest, current):
                raise AccountError("LOGIN_CHALLENGE_EXPIRED")
            self._consume(row)
            # Do not read, copy or grant ANY initiating guest's consent/history.
            return await self._issue_device(
                session, guest, ProviderIdentity(account.subject_id, account.masked_email), current
            )

    @staticmethod
    def _consume(row: LoginChallengeRow) -> None:
        row.state = "consumed"
        row.email_envelope = None
        row.oauth_verifier_envelope = None
        row.proof_digest = None
        row.subject_id = None

    async def _issue_device(
        self,
        session: AsyncSession,
        guest: GuestSessionRow,
        identity: ProviderIdentity,
        now: datetime,
    ) -> LoginResult:
        from app.domains.history.postgres import activate_policy

        # First-link consent includes the disclosed history policy. Restoring a legacy
        # account is not new consent; it must use the explicit history opt-in endpoint.
        new_consent = await session.scalar(
            select(ConsentRow.id).where(
                ConsentRow.guest_id == guest.id,
                ConsentRow.purpose == "account_storage",
                ConsentRow.version == STORAGE_CONSENT,
                ConsentRow.accepted_at == now,
                ConsentRow.revoked_at.is_(None),
            )
        )
        if new_consent is not None:
            await activate_policy(session, guest.id, now)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        guest.last_active_at = max(guest.last_active_at, now)
        guest.expires_at = max(guest.expires_at, now + timedelta(days=ACCOUNT_DAYS))
        device = AccountDeviceRow(
            guest_id=guest.id,
            credential_digest=self._hasher.digest("guest-credential", token),
            csrf_digest=self._hasher.digest("guest-csrf", csrf),
            created_at=now,
            last_active_at=now,
            expires_at=now + timedelta(days=DEVICE_DAYS),
        )
        session.add(device)
        await session.flush()
        record = GuestSessionRecord(
            id=guest.id,
            token_hash=device.credential_digest,
            csrf_hash=device.csrf_digest,
            state=GuestState(guest.state),
            onboarding_status=OnboardingStatus(guest.onboarding_status),
            created_at=guest.created_at,
            last_active_at=guest.last_active_at,
            expires_at=min(guest.expires_at, device.expires_at),
        )
        return LoginResult(
            "signed_in",
            record,
            token,
            csrf,
            masked_email=identity.masked_email,
            profile_expires_at=guest.expires_at,
        )

    async def cancel(
        self,
        *,
        cookie: str | None,
        csrf: str | None,
        token: str | None,
        now: datetime | None = None,
    ) -> None:
        # Cancelling and logging out work even after the provider is disabled.
        if cookie is None:
            return
        async with account_transaction(self._sessions) as session:
            row = await self._challenge(
                session, cookie, csrf, token, now or datetime.now(UTC), allow_expired=True
            )
            await session.delete(row)

    async def status(
        self,
        token: str | None,
        *,
        now: datetime | None = None,
    ) -> tuple[bool, str | None, datetime | None]:
        current = now or datetime.now(UTC)
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, self._credential_digest(token), current)
            if owned is None:
                return False, None, None
            guest, device = owned
            if device is None:
                return False, None, None
            account = await session.scalar(
                select(AccountRow).where(AccountRow.guest_id == guest.id)
            )
            if account is None:
                return False, None, None
            guest.expires_at = max(guest.expires_at, current + timedelta(days=ACCOUNT_DAYS))
            guest.last_active_at = max(guest.last_active_at, current)
            device.expires_at = max(device.expires_at, current + timedelta(days=DEVICE_DAYS))
            device.last_active_at = max(device.last_active_at, current)
            return True, account.masked_email, guest.expires_at

    async def logout(
        self,
        token: str | None,
        csrf: str | None,
        *,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(UTC)
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, self._credential_digest(token), current)
            if owned is None or owned[1] is None:
                raise AccountError("ACCOUNT_SESSION_UNAVAILABLE", 401)
            device = owned[1]
            if not csrf or not self._hasher.verify("guest-csrf", csrf, device.csrf_digest):
                raise AccountError("LOGIN_CSRF_REJECTED", 403)
            device.revoked_at = current
            # Revocation is device-only. The account data clock and other devices
            # are unchanged. The route clears the legacy owner cookie separately.
            await session.execute(
                delete(LoginChallengeRow).where(
                    LoginChallengeRow.initiating_credential_digest == device.credential_digest
                )
            )

    async def devices(
        self, token: str | None, *, now: datetime | None = None
    ) -> list[AccountDevice]:
        current = now or datetime.now(UTC)
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, self._credential_digest(token), current)
            if owned is None or owned[1] is None:
                raise AccountError("ACCOUNT_SESSION_UNAVAILABLE", 401)
            guest, device = owned
            rows = await session.scalars(
                select(AccountDeviceRow)
                .where(
                    AccountDeviceRow.guest_id == guest.id,
                    AccountDeviceRow.revoked_at.is_(None),
                    AccountDeviceRow.expires_at > current,
                )
                .order_by(AccountDeviceRow.created_at, AccountDeviceRow.id)
            )
            if device is None:
                raise AccountError("ACCOUNT_SESSION_UNAVAILABLE", 401)
            return [
                AccountDevice(
                    row.id, row.id == device.id, row.created_at, row.last_active_at, row.expires_at
                )
                for row in rows
            ]

    async def revoke_devices(
        self,
        token: str | None,
        csrf: str | None,
        *,
        device_id: UUID | None = None,
        others: bool = False,
        now: datetime | None = None,
    ) -> bool:
        """Revoke only a cookie-derived account's devices; return current-device revocation."""
        if (device_id is None) == (not others):
            raise ValueError("select one device or all other devices")
        current = now or datetime.now(UTC)
        async with account_transaction(self._sessions) as session:
            owned = await owned_credential(session, self._credential_digest(token), current)
            if owned is None or owned[1] is None:
                raise AccountError("ACCOUNT_SESSION_UNAVAILABLE", 401)
            guest, device = owned
            if device is None:
                raise AccountError("ACCOUNT_SESSION_UNAVAILABLE", 401)
            if not csrf or not self._hasher.verify("guest-csrf", csrf, device.csrf_digest):
                raise AccountError("LOGIN_CSRF_REJECTED", 403)
            # owned_credential locks the data owner before the device. This also
            # serializes revoke-others against issuance, erasure and logout.
            query = select(AccountDeviceRow).where(AccountDeviceRow.guest_id == guest.id)
            query = query.where(
                AccountDeviceRow.id != device.id if others else AccountDeviceRow.id == device_id
            )
            rows = list(await session.scalars(query.with_for_update()))
            if not others and not rows:
                raise AccountError("ACCOUNT_DEVICE_UNAVAILABLE", 404)
            for row in rows:
                if row.revoked_at is None:
                    row.revoked_at = current
            if rows:
                await session.execute(
                    delete(LoginChallengeRow).where(
                        LoginChallengeRow.initiating_credential_digest.in_(
                            select(AccountDeviceRow.credential_digest).where(
                                AccountDeviceRow.guest_id == guest.id,
                                AccountDeviceRow.id != device.id
                                if others
                                else AccountDeviceRow.id == device_id,
                            )
                        )
                    )
                )
            return any(row.id == device.id for row in rows)


def _active(guest: GuestSessionRow | None, now: datetime) -> TypeGuard[GuestSessionRow]:
    return guest is not None and guest.state == GuestState.ACTIVE.value and guest.expires_at > now
