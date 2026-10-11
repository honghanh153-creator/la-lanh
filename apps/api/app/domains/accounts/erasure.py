from uuid import UUID

import httpx

from app.config import Settings
from app.domains.accounts.models import AccountError


class SupabaseIdentityEraser:
    """Hard-delete only the locally linked, verified subject; no browser authority."""

    def __init__(
        self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def __call__(self, subject: UUID) -> None:
        origin = self._settings.auth_supabase_url
        key = self._settings.auth_supabase_admin_key
        if origin is None or key is None:
            raise AccountError("ACCOUNT_ERASURE_PENDING", 503)
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(8.0),
                follow_redirects=False,
                trust_env=False,
            ) as client:
                async with client.stream(
                    "DELETE",
                    f"{origin}/auth/v1/admin/users/{subject}",
                    headers={"apikey": key.get_secret_value()},
                    json={"should_soft_delete": False},
                ) as response:
                    # Missing identity is the idempotent retry of an acknowledged erase.
                    if response.status_code not in (200, 204, 404):
                        raise AccountError("ACCOUNT_ERASURE_PENDING", 503)
        except httpx.HTTPError:
            # No upstream body, credential, email or bearer in public errors/logs.
            raise AccountError("ACCOUNT_ERASURE_PENDING", 503) from None
