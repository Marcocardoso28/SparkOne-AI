"""Startup validation utilities."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings

from .validation import ConfigurationError, validate_critical_config


async def validate_configuration() -> None:  # pragma: no cover - simple config check
    """Validate required configuration settings."""
    settings = get_settings()

    # Use the new comprehensive validation
    try:
        validate_critical_config(settings)
    except ConfigurationError as e:
        # Allow partial startup when explicitly enabled
        if getattr(settings, "allow_partial_startup", False):
            # Log and continue without aborting app startup
            import structlog

            structlog.get_logger(__name__).warning(
                "partial_startup_enabled", detail=str(e)
            )
        else:
            raise RuntimeError(str(e)) from e

    # Keep existing specific validations for backward compatibility
    missing: list[str] = []

    if settings.require_agno and not (settings.openai_api_key or settings.local_llm_url):
        missing.append("OpenAI_API_KEY ou LOCAL_LLM_URL")

    if settings.fallback_email:
        if not settings.smtp_host:
            missing.append("SMTP_HOST")
        if settings.smtp_username and not settings.smtp_password:
            missing.append("SMTP_PASSWORD")

    if settings.whatsapp_notify_numbers and not settings.evolution_api_key:
        missing.append("EVOLUTION_API_KEY")

    if settings.calendar_provider == "google":
        if not settings.google_calendar_credentials_path:
            missing.append("GOOGLE_CALENDAR_CREDENTIALS_PATH")
        if not settings.calendar_primary_id:
            missing.append("CALENDAR_PRIMARY_ID")
    elif settings.calendar_provider == "caldav":
        if not settings.caldav_url:
            missing.append("CALDAV_URL")
        if not settings.caldav_username or not settings.caldav_password:
            missing.append("CALDAV_USERNAME/CALDAV_PASSWORD")

    notion_keys = [settings.notion_api_key, settings.notion_database_id]
    if any(notion_keys) and not all(notion_keys):
        missing.append("NOTION_API_KEY e NOTION_DATABASE_ID")

    if missing:
        joined = ", ".join(sorted(set(missing)))
        raise RuntimeError(f"Configurações obrigatórias ausentes: {joined}")


def register_startup_validations(app: FastAPI) -> None:
    """Register startup validations using deprecated on_event (kept for compatibility)."""

    @app.on_event("startup")
    async def _validate_configuration() -> None:
        await validate_configuration()


__all__ = ["register_startup_validations", "validate_configuration"]
