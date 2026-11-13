import secrets
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.config import Settings
from app.infrastructure.session_cookies import (
    is_token_cookie_value,
    set_profile_cookies,
    token_cookie_value,
)
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
ISSUED = "A" * 21 + "b9_-" + "z" * 18

BAD_VALUES = [
    "",
    "A" * 42,
    "A" * 44,
    "A" * 42 + ";",
    "A" * 41 + "\r\n",
    "A" * 42 + " ",
    "A" * 42 + "=",
    "A" * 42 + "/",
    "A" * 42 + "Đ",
    "A" * 42 + "\x00",
]


def test_issued_tokens_have_the_cookie_shape() -> None:
    assert len(ISSUED) == 43
    assert token_cookie_value(ISSUED) == ISSUED
    for _ in range(200):
        value = secrets.token_urlsafe(32)
        assert token_cookie_value(value) == value


@pytest.mark.parametrize("value", BAD_VALUES)
def test_cookie_values_outside_the_issued_shape_are_refused(value: str) -> None:
    assert is_token_cookie_value(value) is False
    with pytest.raises(ValueError):
        token_cookie_value(value)


def test_non_string_cookie_values_are_refused() -> None:
    assert is_token_cookie_value(None) is False
    assert is_token_cookie_value(b"A" * 43) is False


@pytest.mark.parametrize("field", ["token", "csrf"])
def test_profile_cookies_refuse_a_malformed_value_without_writing_cookies(field: str) -> None:
    response = Response()
    values = {"token": ISSUED, "csrf": ISSUED, field: "A" * 42 + ";"}
    with pytest.raises(ValueError):
        set_profile_cookies(response, Settings(environment="test"), values["token"], values["csrf"])
    assert all(key != b"set-cookie" for key, _ in response.raw_headers)


def test_profile_cookies_set_both_issued_values() -> None:
    response = Response()
    set_profile_cookies(response, Settings(environment="test"), ISSUED, ISSUED)
    cookies = [value.decode() for key, value in response.raw_headers if key == b"set-cookie"]
    assert len(cookies) == 2
    assert all(f"={ISSUED};" in cookie for cookie in cookies)


@pytest.mark.parametrize(
    "token",
    ["A" * 42, "A" * 44, "A" * 42 + "%3B", "A" * 42 + "%20", "A" * 42 + "%0D"],
)
def test_public_radar_preview_never_turns_a_malformed_path_token_into_a_cookie(
    tmp_path: Path, token: str
) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'radar-cookie.db'}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url=ORIGIN) as client:
        response = client.get(f"/v1/public/radar/{token}")
    assert response.status_code == 404
    assert "set-cookie" not in response.headers
