from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "test", "staging", "production"] = "development"
    service_name: str = "la-lanh-api"
    api_version: str = "v1"
    schema_version: str = "1.0.0"
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://la_lanh:la_lanh@127.0.0.1:5432/la_lanh"
    )
    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_prefix="LA_LANH_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
