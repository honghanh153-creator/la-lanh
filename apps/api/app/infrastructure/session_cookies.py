import re

from fastapi import Response

from app.config import Settings

# Every credential or capability cookie the API sets is `secrets.token_urlsafe(32)`:
# 43 characters of the URL-safe base64 alphabet. Some values travel through the
# request first (renew echoes the presented guest cookie and CSRF header after
# verifying their hashes; a radar invite link carries its token in the path), so
# each value is checked against that exact shape before it reaches Set-Cookie.
_TOKEN_COOKIE_VALUE = re.compile(r"[A-Za-z0-9_-]{43}")


def is_token_cookie_value(value: object) -> bool:
    return isinstance(value, str) and _TOKEN_COOKIE_VALUE.fullmatch(value) is not None


def token_cookie_value(value: str) -> str:
    """Return ``value`` unchanged when it has the issued-token shape, else raise."""
    if not is_token_cookie_value(value):
        raise ValueError("cookie value is not an issued token")
    return value


def set_profile_cookies(response: Response, settings: Settings, token: str, csrf: str) -> None:
    # Check both before writing either, so a refusal never leaves half a pair behind.
    pair = (token_cookie_value(token), token_cookie_value(csrf))
    for name, value, private in (
        (settings.guest_cookie_name, pair[0], True),
        (settings.guest_csrf_cookie_name, pair[1], False),
    ):
        response.set_cookie(
            name,
            value,
            max_age=settings.guest_ttl_days * 86400,
            secure=settings.guest_cookie_secure,
            httponly=private,
            samesite="lax",
            path="/",
            domain=settings.cookie_domain,
        )


def clear_profile_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.guest_cookie_name, path="/", domain=settings.cookie_domain)
    response.delete_cookie(settings.guest_csrf_cookie_name, path="/", domain=settings.cookie_domain)
    response.delete_cookie(settings.owner_cookie_name, path="/v1", domain=settings.cookie_domain)
    response.delete_cookie("la_lanh_radar_invite", path="/v1/public/radar")
    response.delete_cookie("la_lanh_radar_receipt", path="/v1/public/radar/receipt")
