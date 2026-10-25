import re
from datetime import date
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_HASH_KEY = "bGEtbGFuaC1kZXYtaGFzaC1rZXktMzItYnl0ZXMhISE="
DEVELOPMENT_ENCRYPTION_KEY = "bGEtbGFuaC1kZXYtZW5jcnlwdGlvbi1rZXktMzIhISE="
PINNED_OPENAI_MODEL: Literal["gpt-6-luna"] = "gpt-6-luna"


# Surfaces whose provider payload carries no direct chart facts (M1): no positions or labels.
# A coarse catalog choice may still reflect the chart (see the Luna runbook).
# Extend only with proof: Tarot reads no chart and sends only closed labels, catalog-traced card
# meanings and a fixed focus sentence, never the question (tests/content_rewrite/
# test_tarot_chart_free.py, Luna sprint S4). Allowing a surface does not turn it on: the
# operator still sets its rollout mode, within the shared Luna budget and pilot roster.
CHART_FREE_REWRITE_SURFACES = frozenset({"daily_home", "tarot"})


class Settings(BaseSettings):
    environment: Literal["development", "test", "staging", "production"] = "development"
    service_name: str = "la-lanh-api"
    api_version: str = "v1"
    schema_version: str = "1.0.0"
    database_url: str = "sqlite+aiosqlite:///./la_lanh_dev.db"
    cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [
            AnyHttpUrl("http://127.0.0.1:5173"),
            AnyHttpUrl("http://localhost:5173"),
        ]
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    consent_version: str = "birth-profile-v1"
    consent_purpose: str = "birth_profile_basic"
    guest_cookie_name: str = "la_lanh_guest"
    guest_csrf_cookie_name: str = "la_lanh_csrf"
    owner_cookie_name: str = "la_lanh_owner"
    cookie_domain: str | None = Field(
        default=None,
        pattern=r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$",
    )
    native_app_enabled: bool = False
    owner_ttl_days: int = Field(default=30, ge=1, le=30)
    guest_cookie_secure: bool = False
    guest_ttl_days: int = Field(default=30, ge=1, le=30)
    guest_replay_minutes: int = Field(default=10, ge=1, le=10)
    # Deletion journal (audit P07): keep facts at least as long as the oldest restorable backup.
    # App dumps live 14 days; raise this if the provider's own backups/PITR reach further back.
    erasure_journal_retention_days: int = Field(default=15, ge=15, le=60)
    guest_hash_key: SecretStr = SecretStr(DEVELOPMENT_HASH_KEY)
    guest_encryption_key: SecretStr = SecretStr(DEVELOPMENT_ENCRYPTION_KEY)
    auth_enabled: bool = False
    auth_delivery_approved: bool = False
    auth_google_enabled: bool = False
    auth_google_callback_url: str | None = None
    auth_supabase_url: str | None = None
    auth_supabase_publishable_key: SecretStr | None = None
    auth_supabase_admin_key: SecretStr | None = None
    generation_enabled: bool = False
    generation_worker_enabled: bool = False
    generation_provider: Literal["disabled", "openai"] = "disabled"
    generation_governance_approved: bool = False
    generation_spend_approved: bool = False
    generation_daily_token_budget: int = Field(default=0, ge=0, le=10_000_000)
    generation_daily_budget_cents: int = Field(default=0, ge=0, le=100)
    generation_monthly_budget_cents: int = Field(default=0, ge=0, le=100)
    generation_pilot_user_limit: int = Field(default=0, ge=0, le=20)
    generation_surface_rollout: dict[
        str, Literal["off", "shadow", "editorial", "beta_10", "beta_50", "full"]
    ] = Field(default_factory=dict)
    generation_openai_api_key: SecretStr | None = None
    generation_openai_project_id: str | None = Field(default=None, pattern=r"^proj_[A-Za-z0-9]+$")
    generation_openai_model: Literal["gpt-6-luna"] = PINNED_OPENAI_MODEL
    generation_timeout_seconds: float = Field(default=20.0, ge=1.0, le=60.0)
    generation_lease_seconds: int = Field(default=120, ge=30, le=600)
    generation_max_attempts: int = Field(default=2, ge=1, le=3)
    generation_retry_delay_seconds: int = Field(default=60, ge=10, le=3600)
    la_chung_accepting_new_activity: bool = False
    # Vòng Lá is deferred: no new matching profile, consent or pool membership (audit P02,
    # 2026-10-22). Withdrawal and leaving the pool stay available for data collected before.
    matching_accepting_new_activity: bool = False
    content_studio_enabled: bool = False
    content_studio_api_token: SecretStr | None = None
    content_studio_max_body_bytes: int = Field(default=262_144, ge=16_384, le=1_048_576)
    swisseph_license_mode: Literal["development", "agpl", "professional"] = "development"
    # B3-1a: first Daily note date (Asia/Ho_Chi_Minh) that uses the per-person rotation.
    # Unset keeps the date-only rotation. A note already opened for its scope is replayed
    # unchanged whatever this date is (US-21 AC04); prefer a day after the release.
    daily_variety_from: date | None = Field(default=None, ge=date(2026, 1, 1))

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_prefix="LA_LANH_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.auth_supabase_admin_key is not None and not re.fullmatch(
            r"sb_secret_[A-Za-z0-9_-]{20,256}",
            self.auth_supabase_admin_key.get_secret_value(),
        ):
            raise ValueError("account erasure requires a server-only Supabase secret key")
        if (
            self.auth_enabled
            and self.environment in {"staging", "production"}
            and self.auth_supabase_admin_key is None
        ):
            raise ValueError("public login requires provider identity erasure credentials")
        if self.auth_supabase_url is not None:
            if not re.fullmatch(r"https://[a-z0-9]{20}\.supabase\.co/?", self.auth_supabase_url):
                raise ValueError("auth requires a fixed HTTPS Supabase project origin")
            self.auth_supabase_url = self.auth_supabase_url.rstrip("/")
        if self.auth_supabase_publishable_key is not None and not re.fullmatch(
            r"sb_publishable_[A-Za-z0-9_-]{20,256}",
            self.auth_supabase_publishable_key.get_secret_value(),
        ):
            raise ValueError("auth accepts only a Supabase publishable key, never service_role")
        if self.auth_google_enabled:
            callback = urlsplit(self.auth_google_callback_url or "")
            origin = f"{callback.scheme}://{callback.netloc}"
            if (
                callback.path != "/auth/callback"
                or callback.query
                or callback.fragment
                or callback.username
                or callback.password
                or origin not in {str(value).rstrip("/") for value in self.cors_origins}
                or callback.scheme not in {"http", "https"}
                or (self.environment in {"staging", "production"} and callback.scheme != "https")
            ):
                raise ValueError(
                    "Google callback requires the exact trusted origin and /auth/callback path"
                )
        if self.auth_enabled and (
            not (self.auth_delivery_approved or self.auth_google_enabled)
            or self.auth_supabase_url is None
            or self.auth_supabase_publishable_key is None
        ):
            raise ValueError(
                "enabled auth requires delivery approval or "
                "Google approval, project and publishable key"
            )
        if self.guest_csrf_cookie_name != "la_lanh_csrf":
            raise ValueError("guest CSRF cookie name is fixed by the app client contract")
        if self.generation_lease_seconds <= self.generation_timeout_seconds:
            raise ValueError("generation lease must exceed the provider timeout")
        if self.generation_enabled:
            if self.generation_provider != "openai":
                raise ValueError("enabled generation requires the pinned OpenAI provider")
            if not self.generation_governance_approved:
                raise ValueError("enabled generation requires explicit governance approval")
            if not any(mode != "off" for mode in self.generation_surface_rollout.values()):
                raise ValueError("enabled generation requires an explicit surface rollout")
            allowed_surfaces = {
                "daily_home",
                "daily_detail",
                "reveal",
                "natal",
                "planet_insight",
                "house_insight",
                "aspect_insight",
                "transit_insight",
                "radar",
                "matching",
                "tarot",
                "share_card",
                "recap",
            }
            unknown_surfaces = set(self.generation_surface_rollout) - allowed_surfaces
            if unknown_surfaces:
                raise ValueError(
                    f"generation rollout contains unknown surfaces: {sorted(unknown_surfaces)}"
                )
            # M1 (2026-10-20): only payloads without direct chart facts may reach the provider.
            # Every other surface still sends chart-derived evidence, and shadow mode sends too.
            chart_bound = {
                surface
                for surface, mode in self.generation_surface_rollout.items()
                if mode != "off" and surface not in CHART_FREE_REWRITE_SURFACES
            }
            if chart_bound:
                raise ValueError(
                    f"generation rollout may only enable chart-free surfaces: {sorted(chart_bound)}"
                )
        if self.generation_worker_enabled:
            if not self.generation_enabled:
                raise ValueError("generation worker requires generation to be enabled")
            if self.generation_openai_api_key is None:
                raise ValueError("enabled generation worker requires an OpenAI API key")
            if not self.generation_spend_approved:
                raise ValueError("enabled generation worker requires explicit spend approval")
            if self.generation_daily_token_budget < 1_000:
                raise ValueError("enabled generation worker requires a positive daily token budget")
            if self.generation_daily_budget_cents < 1:
                raise ValueError("enabled generation worker requires a positive daily USD budget")
            if self.generation_monthly_budget_cents < 1:
                raise ValueError("enabled generation worker requires a positive monthly USD budget")
            if self.generation_pilot_user_limit < 1:
                raise ValueError("enabled generation worker requires a bounded pilot user limit")
            if self.generation_openai_project_id is None:
                raise ValueError("enabled generation worker requires an explicit OpenAI project")
            if not self.database_url.startswith("postgresql+asyncpg://"):
                raise ValueError("paid generation worker requires PostgreSQL lifecycle locks")
        if self.content_studio_enabled:
            if self.content_studio_api_token is None:
                raise ValueError("Content Studio requires an API token")
            if len(self.content_studio_api_token.get_secret_value()) < 32:
                raise ValueError("Content Studio API token must contain at least 32 characters")
            if self.environment in {"staging", "production"}:
                raise ValueError(
                    "Content Studio beta auth is not approved outside local development; "
                    "use the separate managed-identity deployment"
                )
        if self.environment in {"staging", "production"}:
            if self.swisseph_license_mode == "development":
                raise ValueError(
                    "a Swiss Ephemeris AGPL or professional license posture is required "
                    "outside local development"
                )
            if not self.database_url.startswith("postgresql+asyncpg://"):
                raise ValueError("PostgreSQL with asyncpg is mandatory outside local development")
            if not self.guest_cookie_secure:
                raise ValueError("secure guest cookies are mandatory outside local development")
            if any(origin.scheme != "https" for origin in self.cors_origins):
                raise ValueError("all trusted origins must use HTTPS outside local development")
            if self.guest_hash_key.get_secret_value() == DEVELOPMENT_HASH_KEY:
                raise ValueError("a managed guest hash key is required outside local development")
            if self.guest_encryption_key.get_secret_value() == DEVELOPMENT_ENCRYPTION_KEY:
                raise ValueError(
                    "a managed guest encryption key is required outside local development"
                )
            if self.native_app_enabled and self.cookie_domain is None:
                raise ValueError(
                    "a cookie domain is required for Capacitor native HTTP session persistence"
                )
        if self.cookie_domain is not None and any(
            name.startswith("__Host-")
            for name in (
                self.guest_cookie_name,
                self.guest_csrf_cookie_name,
                self.owner_cookie_name,
            )
        ):
            raise ValueError("__Host- cookies cannot be configured with a Domain attribute")
        if self.guest_cookie_name.startswith("__Host-") and not self.guest_cookie_secure:
            if self.environment != "test":
                raise ValueError("__Host- cookies require Secure")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
