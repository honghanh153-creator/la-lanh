"""Minimal Google Sheets values client for the human Tarot bridge (US-24 U5, plan KTD7).

Server-to-server only: a dedicated service account that the owner shares on exactly one file, with
the ``spreadsheets`` scope (US-24 OD3, owner decision pending). No user ever signs in to Google and
no browser ever receives the file id or a credential. Three calls are used: read one range with
formulas left unevaluated, write ranges as RAW text, clear ranges. Errors carry a closed code and
never a response body, a token or cell content.

The access token is kept across processes in a private file (``FileTokenCache``): the minute job is
a new process every minute, and minting a token each time would spend the daily budget on OAuth
alone (Codex auto-1 on PR #127). The file is 0600 in a 0700 directory owned by this user, on the
container's RAM-backed ``/tmp``; it never reaches a backup, a log or the repository.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import stat
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote
from uuid import uuid4

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SHEETS_ORIGIN = "https://sheets.googleapis.com"
TOKEN_URI = "https://oauth2.googleapis.com/token"  # noqa: S105 - a public endpoint
TOKEN_MARGIN_SECONDS = 60
_TOKEN_FILE = "google-token.json"  # noqa: S105 - a file name, not a credential
_MAX_TOKEN_FILE_BYTES = 8192

logger = logging.getLogger(__name__)


class SheetsError(Exception):
    code = "SHEETS_UNAVAILABLE"


class SheetsUnavailable(SheetsError):
    code = "SHEETS_UNAVAILABLE"


class SheetsRateLimited(SheetsError):
    code = "SHEETS_RATE_LIMITED"


class SheetsAccessDenied(SheetsError):
    code = "SHEETS_ACCESS_DENIED"


class SheetsGateway(Protocol):
    async def read(self, range_a1: str) -> list[list[Any]]: ...

    async def write(self, updates: list[tuple[str, list[list[str]]]]) -> None: ...

    async def clear(self, ranges: list[str]) -> None: ...


@dataclass(frozen=True)
class ServiceAccount:
    client_email: str
    private_key_pem: bytes

    @classmethod
    def from_file(cls, path: str) -> ServiceAccount:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("type") != "service_account" or raw.get("token_uri") != TOKEN_URI:
            raise SheetsAccessDenied("credential file is not a Google service account")
        return cls(
            client_email=str(raw["client_email"]), private_key_pem=raw["private_key"].encode()
        )


class TokenCache(Protocol):
    def load(self, key: str) -> tuple[str, float] | None: ...

    def store(self, key: str, token: str, expires_at: float) -> None: ...

    def discard(self) -> None: ...


class FileTokenCache:
    """One access token in a private file, shared by the app process and the minute job.

    Fails safe: any doubt about the directory or the file (not ours, readable by others, a symlink,
    unreadable, another account) means no cached token, so the client asks Google again.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self._directory = Path(directory)

    @classmethod
    def default(cls, directory: str | None = None) -> FileTokenCache:
        return cls(directory or Path(tempfile.gettempdir()) / "la-lanh-google-sheets")

    def _private_directory(self) -> Path | None:
        try:
            self._directory.mkdir(mode=0o700, exist_ok=True)
            info = os.lstat(self._directory)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
                raise PermissionError
            if stat.S_IMODE(info.st_mode) & 0o077:
                os.chmod(self._directory, 0o700)
        except OSError:
            logger.warning("google_token_cache_unavailable")
            return None
        return self._directory

    def load(self, key: str) -> tuple[str, float] | None:
        directory = self._private_directory()
        if directory is None:
            return None
        try:
            descriptor = os.open(directory / _TOKEN_FILE, os.O_RDONLY | os.O_NOFOLLOW)
        except OSError:
            return None
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o077
                or info.st_size > _MAX_TOKEN_FILE_BYTES
            ):
                return None
            raw = json.loads(os.read(descriptor, _MAX_TOKEN_FILE_BYTES))
        except (OSError, ValueError):
            return None
        finally:
            os.close(descriptor)
        if not isinstance(raw, dict) or raw.get("key") != key:
            return None
        token, expires_at = raw.get("access_token"), raw.get("expires_at")
        if not isinstance(token, str) or not token or not isinstance(expires_at, int | float):
            return None
        return token, float(expires_at)

    def store(self, key: str, token: str, expires_at: float) -> None:
        directory = self._private_directory()
        if directory is None:
            return
        staging = directory / f".{_TOKEN_FILE}.{uuid4().hex}"
        body = json.dumps({"key": key, "access_token": token, "expires_at": expires_at}).encode()
        try:
            descriptor = os.open(
                staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            try:
                os.write(descriptor, body)
            finally:
                os.close(descriptor)
            os.replace(staging, directory / _TOKEN_FILE)
        except OSError:
            logger.warning("google_token_cache_unavailable")
            staging.unlink(missing_ok=True)

    def discard(self) -> None:
        try:
            (self._directory / _TOKEN_FILE).unlink(missing_ok=True)
        except OSError:
            logger.warning("google_token_cache_unavailable")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def signed_assertion(account: ServiceAccount, now: int) -> str:
    """An RS256 JWT bearer assertion (RFC 7523) for the spreadsheets scope, valid one hour."""

    key = serialization.load_pem_private_key(account.private_key_pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise SheetsAccessDenied("service account key must be RSA")
    header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = _b64(
        json.dumps(
            {
                "iss": account.client_email,
                "scope": SCOPE,
                "aud": TOKEN_URI,
                "iat": now,
                "exp": now + 3600,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{claims}".encode()
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{claims}.{_b64(signature)}"


class GoogleSheetsClient:
    def __init__(
        self,
        spreadsheet_id: str,
        account: ServiceAccount,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 8.0,
        clock: Any = time.time,
        reserve: Callable[[], Awaitable[None]] | None = None,
        token_cache: TokenCache | None = None,
    ) -> None:
        self._spreadsheet_id = spreadsheet_id
        self._account = account
        self._transport = transport
        self._timeout = httpx.Timeout(timeout_seconds)
        self._clock = clock
        self._token: str | None = None
        self._token_expires = 0.0
        # The application budget covers every Google HTTP request (Codex r56). The caller reserves
        # one call per Sheets operation; the token request takes its own reservation here.
        self._reserve = reserve
        self._token_cache = token_cache
        # Names the account and scope a cached token belongs to, without writing the email.
        self._cache_key = hashlib.sha256(
            f"{account.client_email}|{SCOPE}|{TOKEN_URI}".encode()
        ).hexdigest()

    async def read(self, range_a1: str) -> list[list[Any]]:
        body = await self._call(
            "GET",
            f"/values/{quote(range_a1, safe='')}",
            params={"valueRenderOption": "FORMULA", "majorDimension": "ROWS"},
        )
        values = body.get("values", [])
        return [list(row) for row in values] if isinstance(values, list) else []

    async def write(self, updates: list[tuple[str, list[list[str]]]]) -> None:
        await self._call(
            "POST",
            "/values:batchUpdate",
            json={
                # RAW: a question starting with "=" stays text, never a formula (plan KTD7).
                "valueInputOption": "RAW",
                "data": [{"range": range_a1, "values": values} for range_a1, values in updates],
            },
        )

    async def clear(self, ranges: list[str]) -> None:
        await self._call("POST", "/values:batchClear", json={"ranges": ranges})

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        now = float(self._clock())
        if self._token is not None and now < self._token_expires - TOKEN_MARGIN_SECONDS:
            return self._token
        if self._token_cache is not None:
            cached = self._token_cache.load(self._cache_key)
            if cached is not None and now < cached[1] - TOKEN_MARGIN_SECONDS:
                self._token, self._token_expires = cached
                return self._token
        if self._reserve is not None:
            await self._reserve()
        response = await client.post(
            TOKEN_URI,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": signed_assertion(self._account, int(now)),
            },
        )
        if response.status_code in (400, 401, 403):
            raise SheetsAccessDenied
        if response.status_code != 200:
            raise SheetsUnavailable
        payload = response.json()
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise SheetsUnavailable
        self._token = token
        self._token_expires = now + float(payload.get("expires_in", 3600))
        if self._token_cache is not None:
            self._token_cache.store(self._cache_key, token, self._token_expires)
        return token

    async def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{SHEETS_ORIGIN}/v4/spreadsheets/{self._spreadsheet_id}{path}"
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self._timeout,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                token = await self._access_token(client)
                response = await client.request(
                    method, url, headers={"Authorization": f"Bearer {token}"}, **kwargs
                )
        except httpx.HTTPError:
            raise SheetsUnavailable from None
        if response.status_code == 429:
            raise SheetsRateLimited
        if response.status_code in (401, 403, 404):
            if response.status_code == 401:
                self._token = None
                if self._token_cache is not None:
                    self._token_cache.discard()
            raise SheetsAccessDenied
        if response.status_code >= 300:
            raise SheetsUnavailable
        body = response.json()
        return body if isinstance(body, dict) else {}
