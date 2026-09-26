from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_HASH_KEY = "bGEtbGFuaC1kZXYtaGFzaC1rZXktMzItYnl0ZXMhISE="
DEVELOPMENT_ENCRYPTION_KEY = "bGEtbGFuaC1kZXYtZW5jcnlwdGlvbi1rZXktMzIhISE="
PINNED_OPENAI_MODEL: Literal["gpt-5.4-mini-2026-03-17"] = "gpt-5.4-mini-2026-03-17"


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
    guest_hash_key: SecretStr = SecretStr(DEVELOPMENT_HASH_KEY)
    guest_encryption_key: SecretStr = SecretStr(DEVELOPMENT_ENCRYPTION_KEY)
    generation_enabled: bool = False
    generation_provider: Literal["disabled", "openai"] = "disabled"
    generation_governance_approved: bool = False
    generation_openai_api_key: SecretStr | None = None
    generation_openai_model: Literal["gpt-5.4-mini-2026-03-17"] = PINNED_OPENAI_MODEL
    generation_timeout_seconds: float = Field(default=20.0, ge=1.0, le=60.0)
    generation_lease_seconds: int = Field(default=120, ge=30, le=600)
    generation_max_attempts: int = Field(default=2, ge=1, le=3)
    generation_retry_delay_seconds: int = Field(default=60, ge=10, le=3600)
    swisseph_license_mode: Literal["development", "agpl", "professional"] = "development"

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_prefix="LA_LANH_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.guest_csrf_cookie_name != "la_lanh_csrf":
            raise ValueError("guest CSRF cookie name is fixed by the app client contract")
        if self.generation_lease_seconds <= self.generation_timeout_seconds:
            raise ValueError("generation lease must exceed the provider timeout")
        if self.generation_enabled:
            if self.generation_provider != "openai":
                raise ValueError("enabled generation requires the pinned OpenAI provider")
            if self.generation_openai_api_key is None:
                raise ValueError("enabled generation requires an OpenAI API key")
            if not self.generation_governance_approved:
                raise ValueError("enabled generation requires explicit governance approval")
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
