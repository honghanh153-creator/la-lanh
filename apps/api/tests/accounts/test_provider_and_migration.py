from importlib import import_module
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.config import Settings
from app.db.base import Base
from app.domains.accounts.models import AccountError
from app.domains.accounts.provider import SupabaseOtpProvider
from tests.accounts.support import EMAIL, PROJECT, PUBLISHABLE


@pytest.mark.parametrize(
    "url",
    [
        "http://abcdefghijklmnopqrst.supabase.co",
        "https://127.0.0.1",
        "https://abcdefghijklmnopqrst.supabase.co.evil.example",
        "https://abcdefghijklmnopqrst.supabase.co/path",
        "https://abcdefghijklmnopqrst.supabase.co?redirect=https://evil.example",
        "https://user@abcdefghijklmnopqrst.supabase.co",
        "https://abcdefghijklmnopqrst.supabase.co:444",
        "https://abcdefghijklmnopqrst.supabase.co/#fragment",
    ],
)
def test_provider_url_is_fixed_https_project_not_ssrf(url: str) -> None:
    with pytest.raises(ValidationError, match="fixed HTTPS Supabase project origin"):
        Settings(_env_file=None, auth_supabase_url=url)


@pytest.mark.parametrize(
    "key", ["sb_secret_synthetic_12345678901234567890", "service_role", "eyJ.invalid.legacyJWT"]
)
def test_no_service_role_or_legacy_jwt_key(key: str) -> None:
    with pytest.raises(ValidationError, match="publishable key"):
        Settings(_env_file=None, auth_supabase_publishable_key=key)


def test_auth_requires_delivery_approval_and_secretstr_publishable_key() -> None:
    with pytest.raises(ValidationError, match="delivery approval"):
        Settings(
            _env_file=None,
            auth_enabled=True,
            auth_supabase_url=PROJECT,
            auth_supabase_publishable_key=PUBLISHABLE,
        )
    config = Settings(
        _env_file=None,
        auth_enabled=True,
        auth_delivery_approved=True,
        auth_supabase_url=PROJECT + "/",
        auth_supabase_publishable_key=PUBLISHABLE,
    )
    assert config.auth_supabase_url == PROJECT
    assert isinstance(config.auth_supabase_publishable_key, SecretStr)
    assert PUBLISHABLE not in repr(config)


@pytest.mark.parametrize("kind", ["redirect", "timeout", "oversize", "malformed", "unconfirmed"])
async def test_provider_rejects_unsafe_or_invalid_responses_neutrally(kind: str) -> None:
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if kind == "redirect":
            return httpx.Response(302, headers={"Location": "https://evil.example"})
        if kind == "timeout":
            raise httpx.ReadTimeout("synthetic email/code should not escape", request=request)
        if kind == "oversize":
            return httpx.Response(200, content=b"x" * 65_537)
        if kind == "malformed":
            return httpx.Response(200, content=b"not json with synthetic private detail")
        return httpx.Response(
            200,
            json={
                "user": {"id": "00000000-0000-0000-0000-000000000001", "email": EMAIL},
                "access_token": "private-provider-access",
            },
        )

    config = Settings(
        _env_file=None,
        auth_enabled=True,
        auth_delivery_approved=True,
        auth_supabase_url=PROJECT,
        auth_supabase_publishable_key=PUBLISHABLE,
    )
    provider = SupabaseOtpProvider(config, transport=httpx.MockTransport(handle))
    with pytest.raises(AccountError) as caught:
        await provider.verify_code(EMAIL, "123456")
    assert "private" not in str(caught.value)
    assert EMAIL not in str(caught.value)
    assert len(calls) == 1


async def test_disabled_provider_itself_has_zero_outbound_not_just_routes() -> None:
    def unexpected(request: httpx.Request) -> httpx.Response:
        raise AssertionError("disabled provider must never send")

    provider = SupabaseOtpProvider(
        Settings(_env_file=None), transport=httpx.MockTransport(unexpected)
    )
    for method, args in (
        (provider.request_code, (EMAIL,)),
        (provider.verify_code, (EMAIL, "123456")),
    ):
        with pytest.raises(AccountError, match="LOGIN_UNAVAILABLE"):
            await method(*args)


def test_migration_is_linear_additive_private_and_rollback_preserves_identity_data() -> None:
    migration = import_module("migrations.versions.20261010_0031_optional_accounts")
    assert migration.down_revision == "20261008_0030"
    assert migration.revision == "20261010_0031"
    with (
        patch.object(migration.op, "create_table") as tables,
        patch.object(migration.op, "create_index"),
        patch.object(migration.op, "execute") as execute,
    ):
        migration.upgrade()
    names = {call.args[0] for call in tables.call_args_list}
    assert names == {
        "accounts",
        "account_devices",
        "account_login_challenges",
        "account_login_quotas",
    }
    for table in names:
        columns = {
            column.name
            for column in next(
                call.args[1:] for call in tables.call_args_list if call.args[0] == table
            )
            if hasattr(column, "name") and column.name is not None
        }
        # Google PKCE columns are introduced later, not part of the IAM baseline.
        later = (
            {"oauth_verifier_envelope", "login_provider"}
            if table == "account_login_challenges"
            else set()
        )
        assert set(Base.metadata.tables[table].columns.keys()) - later <= columns
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    for table in names:
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC" in sql
        assert f"REVOKE ALL ON TABLE public.{table} FROM %I" in sql
    assert "'anon', 'authenticated'" in sql
    assert "GRANT" not in sql and "DELETE FROM" not in sql
    # New private tables are loaded before SQLite create_all / Alembic metadata.
    assert names <= set(Base.metadata.tables)
    devices = Base.metadata.tables["account_devices"]
    assert all(fk.ondelete == "CASCADE" for fk in devices.foreign_keys)
    from sqlalchemy.dialects.postgresql.base import PGDialect

    dialect = PGDialect()  # type: ignore[no-untyped-call] # SQLAlchemy dialect factory
    assert str(devices.c.credential_digest.type.compile(dialect=dialect)) == "BYTEA"
    with (
        patch.object(migration.op, "drop_table") as drop,
        patch.object(migration.op, "execute") as execute,
    ):
        migration.downgrade()
    drop.assert_not_called()
    execute.assert_not_called()


def test_google_migration_adds_private_proof_without_destructive_rollback() -> None:
    migration = import_module("migrations.versions.20261010_0033_google_pkce")
    assert migration.down_revision == "20261010_0032"
    with patch.object(migration.op, "add_column") as add:
        migration.upgrade()
    assert {call.args[1].name for call in add.call_args_list} == {
        "oauth_verifier_envelope",
        "login_provider",
    }
    assert all(call.args[0] == "account_login_challenges" for call in add.call_args_list)
    with patch.object(migration.op, "drop_column") as drop:
        migration.downgrade()
    drop.assert_not_called()
