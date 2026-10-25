from datetime import UTC, datetime
from typing import Literal

from app.domains.accounts.postgres import account_transaction, owned_credential
from app.domains.guest.errors import CsrfRejected, GuestExpired
from app.domains.history.errors import HistoryBusy
from app.domains.history.postgres import PostgresHistoryRepository, activate_policy
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.infrastructure.crypto import SecretHasher


class HistoryService:
    def __init__(self, repository: PostgresHistoryRepository, hasher: SecretHasher) -> None:
        self._repository = repository
        self._hasher = hasher

    async def request(
        self,
        action: Literal["status", "activate", "clear"],
        token: str | None,
        csrf: str | None = None,
    ) -> datetime | None:
        now = datetime.now(UTC)
        digest = self._hasher.digest("guest-credential", token) if token else None
        # Revalidate device expiry/revocation and CSRF under the same owner lock as erasure.
        async with account_transaction(self._repository._sessions) as session:
            owned = await owned_credential(session, digest, now)
            if owned is None:
                raise GuestExpired
            guest, device = owned
            now = datetime.now(UTC)
            if guest.expires_at <= now or (device is not None and device.expires_at <= now):
                raise GuestExpired
            if action != "status":
                expected = device.csrf_digest if device else guest.csrf_hash
                if not csrf or not self._hasher.verify("guest-csrf", csrf, expected):
                    raise CsrfRejected
            if action == "activate":
                return await activate_policy(session, guest.id, now)
            if action == "clear":
                if await self._repository._busy(session, guest.id, now):
                    raise HistoryBusy
                await self._repository.clear_in_session(session, guest.id, now)
                return None
            row = await session.get(HistoryRetentionPolicyRow, guest.id)
            return row.activated_at if row else None
