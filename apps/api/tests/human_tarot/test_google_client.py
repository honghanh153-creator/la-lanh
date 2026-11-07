"""US-24 U5 Google client over a mock transport: RAW writes, signed assertion, closed errors."""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import parse_qs, unquote

import httpx
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.infrastructure.google_sheets.client import (
    SCOPE,
    TOKEN_URI,
    GoogleSheetsClient,
    ServiceAccount,
    SheetsAccessDenied,
    SheetsRateLimited,
    SheetsUnavailable,
)

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ACCOUNT = ServiceAccount(
    client_email="synthetic-reader@example.iam.gserviceaccount.com",
    private_key_pem=KEY.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ),
)
SHEET_ID = "synthetic-sheet-id-0000000000"


def _decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


class Recorder:
    def __init__(self, status: int = 200, body: Any = None) -> None:
        self.requests: list[httpx.Request] = []
        self.status = status
        self.body = body if body is not None else {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if str(request.url) == TOKEN_URI:
            return httpx.Response(200, json={"access_token": "synthetic-token", "expires_in": 3600})
        return httpx.Response(self.status, json=self.body)


def _client(recorder: Recorder) -> GoogleSheetsClient:
    return GoogleSheetsClient(SHEET_ID, ACCOUNT, transport=httpx.MockTransport(recorder))


async def test_write_is_raw_and_the_assertion_is_signed_for_the_spreadsheets_scope() -> None:
    recorder = Recorder()
    client = _client(recorder)
    await client.write([("'Hôm nay'!A2:G2", [["LL-ABCDEF", "=1+1"]])])
    token_request, write_request = recorder.requests
    assertion = parse_qs(token_request.content.decode())["assertion"][0]
    header, claims, signature = assertion.split(".")
    KEY.public_key().verify(
        _decode(signature), f"{header}.{claims}".encode(), padding.PKCS1v15(), hashes.SHA256()
    )
    payload = json.loads(_decode(claims))
    assert payload["scope"] == SCOPE and payload["aud"] == TOKEN_URI
    assert payload["exp"] - payload["iat"] == 3600
    assert write_request.url.path.endswith(f"/spreadsheets/{SHEET_ID}/values:batchUpdate")
    assert write_request.headers["authorization"] == "Bearer synthetic-token"
    body = json.loads(write_request.content)
    assert body["valueInputOption"] == "RAW"
    assert body["data"] == [{"range": "'Hôm nay'!A2:G2", "values": [["LL-ABCDEF", "=1+1"]]}]


async def test_read_leaves_formulas_unevaluated_and_reuses_the_token() -> None:
    recorder = Recorder(body={"values": [["Mã yêu cầu"], ["LL-ABCDEF", "30/10/2026"]]})
    client = _client(recorder)
    rows = await client.read("'Hôm nay'!A1:Q11")
    await client.read("'Hôm nay'!A1:Q11")
    assert rows == [["Mã yêu cầu"], ["LL-ABCDEF", "30/10/2026"]]
    token_requests = [item for item in recorder.requests if str(item.url) == TOKEN_URI]
    assert len(token_requests) == 1
    read = recorder.requests[1]
    assert read.url.params["valueRenderOption"] == "FORMULA"
    assert unquote(read.url.raw_path.decode()).endswith(
        "/values/'Hôm nay'!A1:Q11?valueRenderOption=FORMULA&majorDimension=ROWS"
    )


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (429, SheetsRateLimited),
        (403, SheetsAccessDenied),
        (404, SheetsAccessDenied),
        (500, SheetsUnavailable),
    ],
)
async def test_errors_are_closed_codes_without_the_response_body(
    status: int, error: type[Exception]
) -> None:
    recorder = Recorder(status=status, body={"error": {"message": "secret cell value LL-ABCDEF"}})
    with pytest.raises(error) as raised:
        await _client(recorder).clear(["'Hôm nay'!A2:Q2"])
    assert "LL-ABCDEF" not in str(raised.value) and "secret" not in repr(raised.value)


async def test_a_transport_timeout_is_unavailable() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    client = GoogleSheetsClient(SHEET_ID, ACCOUNT, transport=httpx.MockTransport(timeout))
    with pytest.raises(SheetsUnavailable):
        await client.read("'Hôm nay'!A1:Q11")


def test_only_a_service_account_file_is_accepted(tmp_path: Any) -> None:
    path = tmp_path / "credential.json"
    path.write_text(json.dumps({"type": "authorized_user", "token_uri": TOKEN_URI}))
    with pytest.raises(SheetsAccessDenied):
        ServiceAccount.from_file(str(path))
