import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import httpx
import pytest
from sqlalchemy import delete, event, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.session import Database
from app.domains.accounts.erasure import SupabaseIdentityEraser
from app.domains.accounts.models import AccountError, Challenge, LoginResult
from app.domains.accounts.provider import SupabaseOtpProvider
from app.domains.accounts.service import AccountService
from app.domains.accounts.tables import (
    AccountDeviceRow,
    AccountRow,
    LoginChallengeRow,
    LoginQuotaRow,
)
from app.domains.guest.errors import AccountErasurePending, GuestDomainError, GuestExpired
from app.domains.guest.models import CreationResult
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.service import GuestSessionService
from app.domains.guest.tables import ConsentRow, GuestCreationRow, GuestSessionRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider
from tests.accounts.support import EMAIL, FakeTransport, settings

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


@dataclass
class Runtime:
    database: Database
    config: Settings
    fake: FakeTransport
    accounts: AccountService
    guests: GuestSessionService
    hasher: SecretHasher
    envelope: AesGcmEnvelopeCipher

    async def create_guest(self, suffix: str = "default") -> CreationResult:
        return await self.guests.create(
            consent_version="birth-profile-v1",
            purpose="birth_profile_basic",
            idempotency_key=f"synthetic-service-guest-{suffix}-123456",
            now=NOW,
        )

    async def challenge(
        self,
        guest: CreationResult | None = None,
        *,
        email: str = EMAIL,
        consent: str | None = "account-storage-v1",
        now: datetime = NOW,
        peer: str = "synthetic-peer",
    ) -> Challenge:
        return await self.accounts.request_code(
            email,
            token=guest.token if guest else None,
            csrf=guest.csrf_token if guest else None,
            consent=consent,
            peer=peer,
            now=now,
        )

    async def verify(
        self,
        challenge: Challenge,
        guest: CreationResult | None = None,
        *,
        code: str = "123456",
        now: datetime = NOW,
    ) -> LoginResult:
        return await self.accounts.verify(
            code,
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=guest.token if guest else None,
            peer="synthetic-peer",
            now=now,
        )

    async def link(self, suffix: str = "default") -> tuple[CreationResult, LoginResult]:
        guest = await self.create_guest(suffix)
        result = await self.verify(await self.challenge(guest), guest)
        assert result.status == "signed_in"
        return guest, result


async def test_consent_write_rechecks_owner_lifetime_after_preflight(runtime: Runtime) -> None:
    expired = await runtime.create_guest("consent-expired")
    erased = await runtime.create_guest("consent-erased")
    async with runtime.database.sessions() as session, session.begin():
        await session.execute(
            update(GuestSessionRow)
            .where(GuestSessionRow.id == expired.guest.id)
            .values(
                created_at=datetime.now(UTC) - timedelta(days=31),
                last_active_at=datetime.now(UTC) - timedelta(days=31),
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == erased.guest.id))
    for guest in (expired, erased):
        with pytest.raises(GuestExpired):
            await runtime.guests.accept_deep_birth_consent(
                guest.guest.id, version="birth-profile-deep-v1"
            )
    async with runtime.database.sessions() as session:
        assert (
            await session.scalar(
                select(ConsentRow.id).where(ConsentRow.purpose == "birth_profile_deep")
            )
            is None
        )


@pytest.fixture
async def runtime(tmp_path: Path) -> AsyncIterator[Runtime]:
    config = settings(tmp_path / "accounts.db")
    database = Database(config.database_url)
    await database.initialize()
    fake = FakeTransport()
    hasher = SecretHasher(b"h" * 32)
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))
    yield Runtime(
        database,
        config,
        fake,
        AccountService(
            database.sessions,
            hasher,
            envelope,
            SupabaseOtpProvider(config, transport=httpx.MockTransport(fake.handle)),
            config,
        ),
        GuestSessionService(
            PostgresGuestRepository(
                database.sessions,
                identity_eraser=SupabaseIdentityEraser(
                    config, transport=httpx.MockTransport(fake.handle)
                ),
            ),
            hasher,
            envelope,
            consent_version="birth-profile-v1",
            consent_purpose="birth_profile_basic",
        ),
        hasher,
        envelope,
    )
    await database.dispose()


async def count(
    runtime: Runtime, table: type[AccountRow | AccountDeviceRow | GuestSessionRow]
) -> int:
    async with runtime.database.sessions() as session:
        return len(list(await session.scalars(select(table))))


async def second_device(runtime: Runtime) -> LoginResult:
    challenge = await runtime.challenge(now=NOW + timedelta(seconds=61))
    pending = await runtime.verify(challenge, now=NOW + timedelta(seconds=61))
    assert pending.status == "restore_required"
    return await runtime.accounts.restore(
        cookie=challenge.cookie,
        csrf=challenge.csrf_token,
        token=None,
        proof=pending.restore_token,
        now=NOW + timedelta(seconds=62),
    )


async def test_device_iam_denies_cross_account_and_wrong_csrf(runtime: Runtime) -> None:
    _, first = await runtime.link()
    second = await second_device(runtime)
    other_guest = await runtime.create_guest("other-account")
    other = await runtime.verify(
        await runtime.challenge(other_guest, email="other-synthetic@example.org"), other_guest
    )
    devices = await runtime.accounts.devices(first.token, now=NOW + timedelta(days=1))
    assert len(devices) == 2 and sum(row.current for row in devices) == 1
    other_devices = await runtime.accounts.devices(other.token, now=NOW + timedelta(days=1))
    with pytest.raises(AccountError, match="ACCOUNT_DEVICE_UNAVAILABLE"):
        await runtime.accounts.revoke_devices(
            first.token,
            first.csrf_token,
            device_id=other_devices[0].id,
            now=NOW + timedelta(days=1),
        )
    with pytest.raises(AccountError, match="LOGIN_CSRF_REJECTED"):
        await runtime.accounts.revoke_devices(
            first.token, "wrong", others=True, now=NOW + timedelta(days=1)
        )
    assert len(await runtime.accounts.devices(second.token, now=NOW + timedelta(days=1))) == 2
    assert await runtime.guests.resume(other.token, now=NOW + timedelta(days=1))


async def test_revoke_other_devices_preserves_profile_and_current_device(runtime: Runtime) -> None:
    _, first = await runtime.link()
    second = await second_device(runtime)
    assert not await runtime.accounts.revoke_devices(
        first.token, first.csrf_token, others=True, now=NOW + timedelta(days=1)
    )
    with pytest.raises(AccountError, match="ACCOUNT_SESSION_UNAVAILABLE"):
        await runtime.accounts.devices(second.token, now=NOW + timedelta(days=1))
    with pytest.raises(GuestDomainError):
        await runtime.guests.resume(second.token, now=NOW + timedelta(days=1))
    devices = await runtime.accounts.devices(first.token, now=NOW + timedelta(days=1))
    assert len(devices) == 1 and devices[0].current
    assert await runtime.accounts.revoke_devices(
        first.token, first.csrf_token, device_id=devices[0].id, now=NOW + timedelta(days=1)
    )
    with pytest.raises(AccountError, match="ACCOUNT_SESSION_UNAVAILABLE"):
        await runtime.accounts.devices(first.token, now=NOW + timedelta(days=1))
    assert await count(runtime, GuestSessionRow) == 1


async def test_wrong_code_five_attempts_then_locked_without_provider_or_guest_mutation(
    runtime: Runtime,
) -> None:
    guest = await runtime.create_guest()
    challenge = await runtime.challenge(guest)
    for _ in range(5):
        with pytest.raises(AccountError, match="LOGIN_VERIFICATION_FAILED"):
            await runtime.verify(challenge, guest, code="000000")
    calls = len(runtime.fake.calls)
    with pytest.raises(AccountError, match="LOGIN_CHALLENGE_USED"):
        await runtime.verify(challenge, guest)
    assert len(runtime.fake.calls) == calls == 6
    assert await runtime.guests.resume(guest.token, now=NOW, touch=False) == guest.guest
    assert await count(runtime, AccountRow) == 0
    async with runtime.database.sessions() as session:
        row = await session.scalar(select(LoginChallengeRow))
        assert row is not None and row.attempts == 5 and row.email_envelope is None


async def test_wrong_csrf_cookie_binding_expiry_and_replay_fail_closed(runtime: Runtime) -> None:
    guest = await runtime.create_guest()
    other = await runtime.create_guest("other")
    challenge = await runtime.challenge(guest)
    for cookie, csrf, token in (
        ("wrong", challenge.csrf_token, guest.token),
        (challenge.cookie, "wrong", guest.token),
        (challenge.cookie, challenge.csrf_token, other.token),
        (challenge.cookie, challenge.csrf_token, None),
    ):
        with pytest.raises(AccountError, match="LOGIN_CHALLENGE_REJECTED"):
            await runtime.accounts.verify(
                "123456", cookie=cookie, csrf=csrf, token=token, peer="synthetic-peer", now=NOW
            )
    with pytest.raises(AccountError, match="LOGIN_CHALLENGE_EXPIRED"):
        await runtime.verify(challenge, guest, now=NOW + timedelta(minutes=10))
    assert len(runtime.fake.calls) == 1
    await runtime.verify(challenge, guest)
    with pytest.raises(AccountError, match="LOGIN_CHALLENGE_USED"):
        await runtime.verify(challenge, guest)
    assert await count(runtime, AccountDeviceRow) == 1


async def test_first_login_requires_live_guest_and_explicit_storage_consent(
    runtime: Runtime,
) -> None:
    no_guest = await runtime.verify(await runtime.challenge())
    assert no_guest.status == "onboarding_required" and no_guest.token is None
    guest = await runtime.create_guest()
    no_consent = await runtime.verify(
        await runtime.challenge(
            guest,
            email="consent@example.org",
            consent=None,
        ),
        guest,
    )
    assert no_consent.status == "consent_required" and no_consent.token is None
    assert await count(runtime, AccountRow) == 0
    assert await runtime.guests.resume(guest.token, now=NOW, touch=False) == guest.guest


async def test_device_credential_clock_does_not_shorten_account_clock_and_cleanup_survives(
    runtime: Runtime,
) -> None:
    original, signed = await runtime.link()
    assert signed.guest is not None and signed.token and signed.csrf_token
    assert signed.guest.id == original.guest.id
    assert signed.guest.expires_at == NOW + timedelta(days=30)
    assert signed.profile_expires_at == NOW + timedelta(days=365)
    resumed = await runtime.guests.verify_csrf(
        signed.token, signed.csrf_token, now=NOW + timedelta(days=29)
    )
    assert resumed.id == original.guest.id
    assert resumed.csrf_hash == runtime.hasher.digest("guest-csrf", signed.csrf_token)
    assert resumed.expires_at == NOW + timedelta(days=59)
    # Older requests cannot shorten either monotonic clock.
    await runtime.guests.resume(signed.token, now=NOW + timedelta(days=2))
    async with runtime.database.sessions() as session:
        owner = await session.get(GuestSessionRow, original.guest.id)
        assert owner is not None and owner.expires_at == NOW + timedelta(days=394)
        device = await session.scalar(select(AccountDeviceRow))
        assert device is not None and device.expires_at == NOW + timedelta(days=59)
    assert await runtime.guests.cleanup(batch_size=20, now=NOW + timedelta(days=60)) == 0
    assert await count(runtime, AccountDeviceRow) == 0
    assert await count(runtime, AccountRow) == 1
    assert await count(runtime, GuestSessionRow) == 1
    # Account inactivity is still authoritative, not a permanent retention exemption.
    assert await runtime.guests.cleanup(batch_size=20, now=NOW + timedelta(days=394)) == 1
    assert await count(runtime, AccountRow) == 0


async def test_two_devices_logout_is_independent_and_expired_credentials_cannot_erase(
    runtime: Runtime,
) -> None:
    original, first = await runtime.link()
    challenge = await runtime.challenge(now=NOW + timedelta(seconds=61))
    pending = await runtime.verify(challenge, now=NOW + timedelta(seconds=61))
    assert pending.status == "restore_required" and pending.token is None
    second = await runtime.accounts.restore(
        cookie=challenge.cookie,
        csrf=challenge.csrf_token,
        token=None,
        proof=pending.restore_token,
        now=NOW + timedelta(seconds=62),
    )
    assert second.guest is not None and first.guest is not None
    assert second.guest.id == first.guest.id
    assert second.token != first.token and second.csrf_token != first.csrf_token
    await runtime.accounts.logout(first.token, first.csrf_token, now=NOW + timedelta(days=1))
    for token in (first.token, original.token):
        with pytest.raises(GuestExpired):
            await runtime.guests.resume(token, now=NOW + timedelta(days=1))
    assert (
        await runtime.guests.resume(second.token, now=NOW + timedelta(days=1))
    ).id == original.guest.id
    repo = PostgresGuestRepository(runtime.database.sessions)
    assert not await repo.delete_by_token_hash(
        runtime.hasher.digest("guest-credential", original.token), NOW
    )
    assert second.token is not None
    assert not await repo.delete_by_token_hash(
        runtime.hasher.digest("guest-credential", second.token), NOW + timedelta(days=32)
    )
    assert await count(runtime, AccountRow) == 1


async def test_delete_fences_pending_restore_and_never_resurrects_local_data(
    runtime: Runtime,
) -> None:
    original, signed = await runtime.link()
    challenge = await runtime.challenge(now=NOW + timedelta(seconds=61))
    pending = await runtime.verify(challenge, now=NOW + timedelta(seconds=61))
    await runtime.guests.delete(signed.token, now=NOW + timedelta(seconds=62))
    assert await count(runtime, GuestSessionRow) == 0
    assert await count(runtime, AccountRow) == 0
    assert await count(runtime, AccountDeviceRow) == 0
    with pytest.raises(AccountError):
        await runtime.accounts.restore(
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=None,
            proof=pending.restore_token,
            now=NOW + timedelta(seconds=63),
        )
    again = await runtime.challenge(now=NOW + timedelta(seconds=122))
    assert (
        await runtime.verify(again, now=NOW + timedelta(seconds=122))
    ).status == "onboarding_required"
    assert await count(runtime, GuestSessionRow) == 0
    # The same still-existing provider subject can opt into a NEW local profile,
    # never recover the erased ID / chart / history.
    new_guest = await runtime.create_guest("after-erasure")
    new = await runtime.verify(
        await runtime.challenge(new_guest, now=NOW + timedelta(seconds=183)),
        new_guest,
        now=NOW + timedelta(seconds=183),
    )
    assert new.guest is not None and new.guest.id != original.guest.id


async def test_restore_proof_is_one_time_expiring_and_cancel_works_provider_disabled(
    runtime: Runtime,
) -> None:
    await runtime.link()
    challenge = await runtime.challenge(now=NOW + timedelta(seconds=61))
    pending = await runtime.verify(challenge, now=NOW + timedelta(seconds=61))
    with pytest.raises(AccountError, match="LOGIN_CHALLENGE_USED"):
        await runtime.accounts.restore(
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=None,
            proof="wrong",
            now=NOW + timedelta(seconds=62),
        )
    with pytest.raises(AccountError, match="LOGIN_CHALLENGE_EXPIRED"):
        await runtime.accounts.restore(
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=None,
            proof=pending.restore_token,
            now=NOW + timedelta(seconds=361),
        )
    runtime.config.auth_enabled = False
    await runtime.accounts.cancel(
        cookie=challenge.cookie,
        csrf=challenge.csrf_token,
        token=None,
        now=NOW + timedelta(seconds=362),
    )
    assert await count(runtime, AccountDeviceRow) == 1
    assert await count(runtime, AccountRow) == 1


async def test_duplicate_verify_uses_database_claim_not_inprocess_lock(runtime: Runtime) -> None:
    guest = await runtime.create_guest()
    challenge = await runtime.challenge(guest)
    entered, release = asyncio.Event(), asyncio.Event()

    async def blocking(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/verify"):
            entered.set()
            await release.wait()
        return runtime.fake.handle(request)

    # A second engine/session factory simulates another application worker.
    second_db = Database(runtime.config.database_url)
    transport = httpx.MockTransport(blocking)
    first_service = AccountService(
        runtime.database.sessions,
        runtime.hasher,
        runtime.envelope,
        SupabaseOtpProvider(runtime.config, transport=transport),
        runtime.config,
    )
    second_service = AccountService(
        second_db.sessions,
        runtime.hasher,
        runtime.envelope,
        SupabaseOtpProvider(runtime.config, transport=transport),
        runtime.config,
    )

    async def run(service: AccountService) -> LoginResult:
        return await service.verify(
            "123456",
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=guest.token,
            peer="synthetic-peer",
            now=NOW,
        )

    first = asyncio.create_task(run(first_service))
    await asyncio.wait_for(entered.wait(), timeout=5)
    try:
        with pytest.raises(AccountError, match="LOGIN_CHALLENGE_USED"):
            await run(second_service)
        release.set()
        signed = await asyncio.wait_for(first, timeout=5)
        assert signed.status == "signed_in"
        assert len(runtime.fake.calls) == 2  # send and exactly one provider verification
        assert await count(runtime, AccountRow) == await count(runtime, AccountDeviceRow) == 1
    finally:
        release.set()
        await second_db.dispose()


async def test_concurrent_subject_link_preserves_unselected_guest_and_one_owner(
    runtime: Runtime,
) -> None:
    first, second = await runtime.create_guest("first"), await runtime.create_guest("second")
    a = await runtime.challenge(first)
    b = await runtime.challenge(second, now=NOW + timedelta(seconds=61))
    results = await asyncio.gather(
        runtime.verify(a, first), runtime.verify(b, second, now=NOW + timedelta(seconds=61))
    )
    assert sorted(item.status for item in results) == ["restore_required", "signed_in"]
    assert await count(runtime, AccountRow) == await count(runtime, AccountDeviceRow) == 1
    assert await count(runtime, GuestSessionRow) == 2
    unselected = first if results[0].status == "restore_required" else second
    assert await runtime.guests.resume(unselected.token, now=NOW, touch=False) == unselected.guest


async def test_distinct_subjects_racing_one_guest_cannot_relink_it(runtime: Runtime) -> None:
    guest = await runtime.create_guest()
    first = await runtime.challenge(guest, email="first@example.org")
    second = await runtime.challenge(guest, email="second@example.org")
    results = await asyncio.gather(runtime.verify(first, guest), runtime.verify(second, guest))
    assert sorted(item.status for item in results) == ["onboarding_required", "signed_in"]
    assert await count(runtime, AccountRow) == await count(runtime, AccountDeviceRow) == 1


async def test_cancel_during_provider_verification_fences_attachment(runtime: Runtime) -> None:
    guest = await runtime.create_guest()
    challenge = await runtime.challenge(guest)
    entered, release = asyncio.Event(), asyncio.Event()

    async def blocking(request: httpx.Request) -> httpx.Response:
        entered.set()
        await release.wait()
        return runtime.fake.handle(request)

    service = AccountService(
        runtime.database.sessions,
        runtime.hasher,
        runtime.envelope,
        SupabaseOtpProvider(runtime.config, transport=httpx.MockTransport(blocking)),
        runtime.config,
    )
    task = asyncio.create_task(
        service.verify(
            "123456",
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=guest.token,
            peer="synthetic-peer",
            now=NOW,
        )
    )
    await asyncio.wait_for(entered.wait(), timeout=5)
    await service.cancel(
        cookie=challenge.cookie, csrf=challenge.csrf_token, token=guest.token, now=NOW
    )
    release.set()
    with pytest.raises(AccountError):
        await asyncio.wait_for(task, timeout=5)
    assert await runtime.guests.resume(guest.token, now=NOW, touch=False) == guest.guest
    assert await count(runtime, AccountRow) == 0


async def test_account_erasure_racing_restore_cannot_leave_usable_device(runtime: Runtime) -> None:
    _, signed = await runtime.link()
    challenge = await runtime.challenge(now=NOW + timedelta(seconds=61))
    pending = await runtime.verify(challenge, now=NOW + timedelta(seconds=61))
    restored, erased = await asyncio.gather(
        runtime.accounts.restore(
            cookie=challenge.cookie,
            csrf=challenge.csrf_token,
            token=None,
            proof=pending.restore_token,
            now=NOW + timedelta(seconds=62),
        ),
        runtime.guests.delete(signed.token, now=NOW + timedelta(seconds=62)),
        return_exceptions=True,
    )
    assert erased is None
    assert await count(runtime, AccountRow) == await count(runtime, AccountDeviceRow) == 0
    if isinstance(restored, LoginResult):
        with pytest.raises(GuestExpired):
            await runtime.guests.resume(restored.token, now=NOW + timedelta(seconds=63))
    else:
        assert isinstance(restored, AccountError)


async def test_first_link_transaction_rolls_back_guest_consent_and_replay_envelope(
    runtime: Runtime,
) -> None:
    guest = await runtime.create_guest()
    challenge = await runtime.challenge(guest)

    def reject_device(session: AsyncSession, flush_context: object, instances: object) -> None:
        if any(isinstance(row, AccountDeviceRow) for row in session.new):
            raise RuntimeError("synthetic local issuance failure")

    event.listen(AsyncSession.sync_session_class, "before_flush", reject_device)
    try:
        with pytest.raises(RuntimeError, match="synthetic local issuance failure"):
            await runtime.verify(challenge, guest)
    finally:
        event.remove(AsyncSession.sync_session_class, "before_flush", reject_device)
    assert await runtime.guests.resume(guest.token, now=NOW, touch=False) == guest.guest
    assert await count(runtime, AccountRow) == await count(runtime, AccountDeviceRow) == 0
    async with runtime.database.sessions() as session:
        replay = await session.scalar(select(GuestCreationRow))
        assert replay is not None and replay.credential_envelope is not None
        consent = await session.scalar(
            select(ConsentRow).where(ConsentRow.purpose == "account_storage")
        )
        assert consent is None


async def test_durable_send_quotas_cover_email_peer_global_and_hash_only_storage(
    runtime: Runtime,
) -> None:
    await runtime.challenge()
    second_db = Database(runtime.config.database_url)
    service = AccountService(
        second_db.sessions,
        runtime.hasher,
        runtime.envelope,
        SupabaseOtpProvider(runtime.config, transport=httpx.MockTransport(runtime.fake.handle)),
        runtime.config,
    )
    try:
        with pytest.raises(AccountError) as resend:
            await service.request_code(
                EMAIL,
                token=None,
                csrf=None,
                consent=None,
                peer="different-peer",
                now=NOW + timedelta(seconds=59),
            )
        assert resend.value.status == 429 and resend.value.retry_after == 1
        for index in range(1, 5):
            await runtime.challenge(now=NOW + timedelta(seconds=60 * index))
        with pytest.raises(AccountError) as email_quota:
            await runtime.challenge(now=NOW + timedelta(seconds=300))
        assert email_quota.value.status == 429
        for index in range(5):
            await runtime.challenge(
                email=f"peer-{index}@example.org", now=NOW + timedelta(seconds=300)
            )
        with pytest.raises(AccountError) as peer_quota:
            await runtime.challenge(email="peer-over@example.org", now=NOW + timedelta(seconds=300))
        assert peer_quota.value.status == 429
        for index in range(90):
            await runtime.challenge(email=f"global-{index}@example.org", peer=f"peer-{index}")
        with pytest.raises(AccountError) as global_quota:
            await runtime.challenge(email="global-over@example.org", peer="new-peer")
        assert global_quota.value.status == 429
        assert len(runtime.fake.calls) == 100
        async with runtime.database.sessions() as session:
            quotas = list(await session.scalars(select(LoginQuotaRow)))
            assert all(
                isinstance(row.key_digest, bytes) and len(row.key_digest) == 32 for row in quotas
            )
            challenges = list(await session.scalars(select(LoginChallengeRow)))
            assert all(row.email_envelope and EMAIL not in row.email_envelope for row in challenges)
    finally:
        await second_db.dispose()


async def test_provider_identity_mismatch_never_links_user_metadata(runtime: Runtime) -> None:
    guest = await runtime.create_guest()
    challenge = await runtime.challenge(guest)
    runtime.fake.invalid_identity = True
    with pytest.raises(AccountError, match="LOGIN_VERIFICATION_FAILED"):
        await runtime.verify(challenge, guest)
    assert await count(runtime, AccountRow) == 0


async def test_digest_is_not_bearer_and_csrf_is_separate(runtime: Runtime) -> None:
    _, signed = await runtime.link()
    assert signed.guest is not None
    digest = signed.guest.token_hash.hex()
    with pytest.raises(GuestExpired):
        await runtime.guests.resume(digest, now=NOW)
    assert signed.guest.token_hash != signed.guest.csrf_hash
    assert (await runtime.guests.resume(signed.token, now=NOW)).id == signed.guest.id
    async with runtime.database.sessions() as session:
        account = await session.scalar(select(AccountRow))
        assert account is not None and account.subject_id == uuid5(NAMESPACE_URL, EMAIL)


async def test_provider_erasure_failure_keeps_retryable_identity_and_denies_restore(
    runtime: Runtime,
) -> None:
    _, signed = await runtime.link()
    runtime.fake.erase_status = 500
    with pytest.raises(AccountErasurePending):
        await runtime.guests.delete(signed.token, now=NOW + timedelta(seconds=1))
    assert await count(runtime, AccountRow) == 1
    with pytest.raises(GuestExpired):
        await runtime.guests.resume(signed.token, now=NOW + timedelta(seconds=2))
    runtime.fake.erase_status = 404
    assert await runtime.guests.cleanup(batch_size=100, now=NOW + timedelta(seconds=3)) == 1
    assert await count(runtime, AccountRow) == 0
    assert await count(runtime, AccountDeviceRow) == 0
    assert len([call for call in runtime.fake.calls if call.method == "DELETE"]) == 2
