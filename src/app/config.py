"""Application configuration objects."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration resolved from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://sparkone:sparkone@localhost:5432/sparkone"
    vector_store_url: str = "postgresql://sparkone:sparkone@localhost:5432/sparkone"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str | None = None
    openai_base_url: AnyHttpUrl | None = None
    openai_model: str = "gpt-4.1"

    local_llm_url: AnyHttpUrl | None = None
    local_llm_api_key: str | None = None
    local_llm_model: str = "llama-3.1-8b-instruct"
    llm_request_timeout: float = 15.0
    llm_max_retries: int = 2

    embedding_provider: Literal["local", "openai"] = "local"
    openai_embedding_model: str = "text-embedding-3-large"
    local_embedding_model: str = "nomic-embed-text"

    persona_name: str = "SparkOne"
    timezone: str = "America/Sao_Paulo"
    allowed_hosts: str = "*"
    cors_origins: str = "*"
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,Accept"
    cors_allow_credentials: bool = True
    security_hsts_enabled: bool = True
    security_hsts_max_age: int = 63072000
    security_hsts_include_subdomains: bool = True
    security_hsts_preload: bool = False

    enable_event_dispatcher: bool = False
    event_webhook_url: AnyHttpUrl | None = None
    event_webhook_token: str | None = None

    web_password: str | None = None
    web_upload_dir: str = "uploads"
    web_max_upload_size: int = 10 * 1024 * 1024
    web_session_ttl_seconds: int = 1800

    google_sheets_sync_spreadsheet_id: str | None = None
    google_sheets_sync_range: str | None = None
    google_sheets_credentials_path: str | None = None
    google_calendar_credentials_path: str | None = None

    evolution_api_base_url: AnyHttpUrl | None = None
    evolution_api_key: str | None = None
    evolution_api_timeout: float = 10.0
    notion_api_key: str | None = None
    notion_database_id: str | None = None
    calendar_provider: Literal["caldav", "google", "none"] = "none"
    calendar_primary_id: str | None = None
    caldav_url: AnyHttpUrl | None = None
    caldav_username: str | None = None
    caldav_password: str | None = None
    whatsapp_notify_numbers: str | None = None
    fallback_email: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    require_agno: bool = False
    whatsapp_send_max_retries: int = 3
    ingestion_max_content_length: int = 6000

    @field_validator(
        "openai_base_url",
        "local_llm_url",
        "event_webhook_url",
        "google_sheets_credentials_path",
        "google_calendar_credentials_path",
        "caldav_url",
        mode="before",
    )
    @classmethod
    def _sanitize_optional_urls(cls, value: str | AnyHttpUrl | None):  # type: ignore[override]
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]
