"""Minimal Google Sheets values client for the human Tarot bridge (US-24 U5, plan KTD7).

Server-to-server only: a dedicated service account that the owner shares on exactly one file, with
the ``spreadsheets`` scope (US-24 OD3, owner decision pending). No user ever signs in to Google and
no browser ever receives the file id or a credential. Three calls are used: read one range with
formulas left unevaluated, write ranges as RAW text, clear ranges. Errors carry a closed code and
never a response body, a token or cell content.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SHEETS_ORIGIN = "https://sheets.googleapis.com"
TOKEN_URI = "https://oauth2.googleapis.com/token"  # noqa: S105 - a public endpoint


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
    ) -> None:
        self._spreadsheet_id = spreadsheet_id
        self._account = account
        self._transport = transport
        self._timeout = httpx.Timeout(timeout_seconds)
        self._clock = clock
        self._token: str | None = None
        self._token_expires = 0.0

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
        if self._token is not None and now < self._token_expires - 60:
            return self._token
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
            raise SheetsAccessDenied
        if response.status_code >= 300:
            raise SheetsUnavailable
        body = response.json()
        return body if isinstance(body, dict) else {}
