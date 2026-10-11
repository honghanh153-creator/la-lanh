from fastapi import Response

from app.config import Settings


def set_profile_cookies(response: Response, settings: Settings, token: str, csrf: str) -> None:
    for name, value, private in (
        (settings.guest_cookie_name, token, True),
        (settings.guest_csrf_cookie_name, csrf, False),
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
