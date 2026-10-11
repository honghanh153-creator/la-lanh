import base64
import hashlib
import json
from datetime import datetime
from urllib.parse import urlencode
from uuid import UUID

import httpx

from app.config import Settings
from app.domains.accounts.models import AccountError, ProviderIdentity


class SupabaseOtpProvider:
    """Server-only managed Auth REST adapter; provider bearers never reach the browser."""

    def __init__(
        self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def request_code(self, email: str) -> None:
        await self._post("/otp", {"email": email, "create_user": True})

    async def verify_code(self, email: str, code: str) -> ProviderIdentity:
        result = await self._post("/verify", {"email": email, "token": code, "type": "email"})
        # Trust the TLS-authenticated provider response, not user_metadata or a
        # browser-supplied JWT. All returned access/refresh tokens are discarded.
        try:
            user = result["user"]
            if not isinstance(user, dict) or user.get("is_anonymous", False):
                raise ValueError
            returned_email = user["email"]
            if not isinstance(returned_email, str) or returned_email.casefold() != email:
                raise ValueError
            confirmed = user["email_confirmed_at"]
            if not isinstance(confirmed, str):
                raise ValueError
            if datetime.fromisoformat(confirmed.replace("Z", "+00:00")).tzinfo is None:
                raise ValueError
            subject = UUID(user["id"])
            if subject.int == 0:
                raise ValueError
        except (KeyError, ValueError, TypeError, AttributeError):
            raise AccountError("LOGIN_VERIFICATION_FAILED") from None
        local, domain = email.split("@")
        return ProviderIdentity(subject, f"{local[0]}***@{domain}")

    def google_authorize_url(self, verifier: str, state: str) -> str:
        self._google_enabled()
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        callback = str(self._settings.auth_google_callback_url) + "?" + urlencode({"state": state})
        return (
            str(self._settings.auth_supabase_url)
            + "/auth/v1/authorize?"
            + urlencode(
                {
                    "provider": "google",
                    "scopes": "openid email profile",
                    "redirect_to": callback,
                    "code_challenge": challenge,
                    "code_challenge_method": "s256",
                    "prompt": "select_account",
                }
            )
        )

    def _google_enabled(self) -> None:
        if not self._settings.auth_enabled or not self._settings.auth_google_enabled:
            raise AccountError("LOGIN_UNAVAILABLE", 503)

    async def exchange_google(self, code: str, verifier: str) -> ProviderIdentity:
        self._google_enabled()
        result = await self._post(
            "/token?grant_type=pkce", {"auth_code": code, "code_verifier": verifier}, google=True
        )
        try:
            user = result["user"]
            if not isinstance(user, dict) or user.get("is_anonymous", False):
                raise ValueError
            email, confirmed = user["email"], user["email_confirmed_at"]
            if not isinstance(email, str) or len(email) > 254 or email.count("@") != 1:
                raise ValueError
            local, domain = email.split("@")
            if not local or not domain or any(ord(char) < 32 for char in email):
                raise ValueError
            if (
                not isinstance(confirmed, str)
                or datetime.fromisoformat(confirmed.replace("Z", "+00:00")).tzinfo is None
            ):
                raise ValueError
            identities = user["identities"]
            if not isinstance(identities, list) or not any(
                isinstance(item, dict) and item.get("provider") == "google" for item in identities
            ):
                raise ValueError
            subject = UUID(user["id"])
            if subject.int == 0:
                raise ValueError
        except (KeyError, ValueError, TypeError, AttributeError):
            raise AccountError("LOGIN_VERIFICATION_FAILED") from None
        # Only verified provider subject is authority. No birth fields, browser JWT,
        # user_metadata role or Google access/refresh token is stored or returned.
        return ProviderIdentity(subject, f"{local[0]}***@{domain}")

    async def _post(
        self, path: str, payload: dict[str, object], *, google: bool = False
    ) -> dict[str, object]:
        settings = self._settings
        if not settings.auth_enabled or not (
            settings.auth_google_enabled if google else settings.auth_delivery_approved
        ):
            raise AccountError("LOGIN_UNAVAILABLE", 503)
        if settings.auth_supabase_url is None or settings.auth_supabase_publishable_key is None:
            raise AccountError("LOGIN_UNAVAILABLE", 503)
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(8.0),
                follow_redirects=False,
                trust_env=False,
            ) as client:
                async with client.stream(
                    "POST",
                    settings.auth_supabase_url + "/auth/v1" + path,
                    headers={"apikey": settings.auth_supabase_publishable_key.get_secret_value()},
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        raise AccountError("LOGIN_PROVIDER_REJECTED")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > 65_536:
                            raise AccountError("LOGIN_PROVIDER_REJECTED")
            decoded = json.loads(body)
            if not isinstance(decoded, dict):
                raise AccountError("LOGIN_PROVIDER_REJECTED")
            return decoded
        except (httpx.HTTPError, ValueError):
            raise AccountError("LOGIN_PROVIDER_REJECTED") from None
