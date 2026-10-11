import json
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.domains.accounts.erasure import SupabaseIdentityEraser
from app.domains.accounts.models import AccountError
from tests.accounts.support import ADMIN, PROJECT


@pytest.mark.parametrize("status", [200, 204, 404])
async def test_hard_erasure_is_idempotent_without_provider_body_or_browser_token(
    status: int,
) -> None:
    subject = uuid4()

    def handle(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{PROJECT}/auth/v1/admin/users/{subject}"
        assert request.method == "DELETE" and request.headers["apikey"] == ADMIN
        assert json.loads(request.content) == {"should_soft_delete": False}
        return httpx.Response(status)

    await SupabaseIdentityEraser(
        Settings(_env_file=None, auth_supabase_url=PROJECT, auth_supabase_admin_key=ADMIN),
        transport=httpx.MockTransport(handle),
    )(subject)


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
async def test_upstream_failure_does_not_acknowledge_erasure_or_expose_body(status: int) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="private upstream credential detail")

    with pytest.raises(AccountError, match="ACCOUNT_ERASURE_PENDING") as caught:
        await SupabaseIdentityEraser(
            Settings(_env_file=None, auth_supabase_url=PROJECT, auth_supabase_admin_key=ADMIN),
            transport=httpx.MockTransport(handle),
        )(uuid4())
    assert caught.value.status == 503 and "private" not in str(caught.value)


async def test_missing_admin_credential_never_sends_or_pretends_to_delete() -> None:
    def unexpected(request: httpx.Request) -> httpx.Response:
        raise AssertionError("missing credential must not send")

    with pytest.raises(AccountError, match="ACCOUNT_ERASURE_PENDING"):
        await SupabaseIdentityEraser(
            Settings(_env_file=None), transport=httpx.MockTransport(unexpected)
        )(uuid4())


def test_public_auth_requires_server_erasure_credential() -> None:
    with pytest.raises(ValidationError, match="identity erasure"):
        Settings(_env_file=None, environment="production", auth_enabled=True)
