from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_HASH_KEY = "bGEtbGFuaC1kZXYtaGFzaC1rZXktMzItYnl0ZXMhISE="
DEVELOPMENT_ENCRYPTION_KEY = "bGEtbGFuaC1kZXYtZW5jcnlwdGlvbi1rZXktMzIhISE="


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
    guest_cookie_secure: bool = False
    guest_ttl_days: int = Field(default=30, ge=1, le=30)
    guest_replay_minutes: int = Field(default=10, ge=1, le=10)
    guest_hash_key: SecretStr = SecretStr(DEVELOPMENT_HASH_KEY)
    guest_encryption_key: SecretStr = SecretStr(DEVELOPMENT_ENCRYPTION_KEY)

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_prefix="LA_LANH_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.environment in {"staging", "production"}:
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
        if self.guest_cookie_name.startswith("__Host-") and not self.guest_cookie_secure:
            if self.environment != "test":
                raise ValueError("__Host- cookies require Secure")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
