"""Validation utilities for application startup and configuration."""

from __future__ import annotations

from typing import Any

import structlog

from app.config import Settings

logger = structlog.get_logger(__name__)


class ConfigurationError(RuntimeError):
    """Raised when critical configuration is missing or invalid."""


def validate_critical_config(settings: Settings) -> None:
    """Validate critical configuration at startup.

    Raises:
        ConfigurationError: If critical configuration is missing or invalid.
    """
    errors: list[str] = []

    # Validate LLM providers
    if not settings.openai_api_key and not settings.local_llm_url:
        errors.append("No LLM provider configured. Set either OPENAI_API_KEY or LOCAL_LLM_URL.")

    # Validate OpenAI configuration if enabled
    if settings.openai_api_key:
        if settings.openai_api_key.strip() in ("", "changeme", "your-key-here"):
            errors.append("Invalid OPENAI_API_KEY. Please set a valid OpenAI API key.")

    # Validate Evolution API if configured
    if settings.evolution_api_base_url and not settings.evolution_api_key:
        errors.append("EVOLUTION_API_BASE_URL is set but EVOLUTION_API_KEY is missing.")

    if settings.evolution_api_key:
        if settings.evolution_api_key.strip() in ("", "changeme", "your-key-here"):
            errors.append("Invalid EVOLUTION_API_KEY. Please set a valid Evolution API key.")

    # Validate database configuration
    if not settings.database_url or settings.database_url.strip() == "":
        errors.append("DATABASE_URL is required and cannot be empty.")

    # Validate production-specific settings
    if settings.environment == "production":
        if settings.debug:
            errors.append("DEBUG should be false in production environment.")

        if settings.allowed_hosts == "*":
            errors.append(
                "ALLOWED_HOSTS should not be '*' in production. " "Specify allowed hostnames."
            )

        if settings.cors_origins == "*":
            errors.append(
                "CORS_ORIGINS should not be '*' in production. " "Specify allowed origins."
            )

        if not settings.security_hsts_enabled:
            errors.append("SECURITY_HSTS_ENABLED should be true in production.")

    # Log warnings for optional but recommended settings
    warnings: list[str] = []

    if not settings.redis_url:
        warnings.append("REDIS_URL not configured. Some features may be limited.")

    if not settings.fallback_email:
        warnings.append("FALLBACK_EMAIL not configured. Critical alerts may be lost.")

    if settings.web_password and settings.web_password in ("admin", "password", "123456"):
        warnings.append("WEB_PASSWORD appears to be weak. Consider using a stronger password.")

    # Log warnings
    for warning in warnings:
        logger.warning("configuration_warning", message=warning)

    # Raise error if any critical issues found
    if errors:
        error_message = "Critical configuration errors found:\n" + "\n".join(
            f"- {error}" for error in errors
        )
        logger.error("configuration_validation_failed", errors=errors)
        raise ConfigurationError(error_message)

    logger.info("configuration_validation_passed", warnings_count=len(warnings))


def validate_secrets_not_hardcoded(**kwargs: Any) -> None:
    """Validate that no secrets are hardcoded in the application.

    This function can be extended to check for hardcoded values in runtime.
    """
    hardcoded_patterns = [
        "changeme",
        "your-key-here",
        "sparkone-local",
        "admin",
        "password123",
    ]

    issues: list[str] = []

    for key, value in kwargs.items():
        if isinstance(value, str):
            for pattern in hardcoded_patterns:
                if pattern.lower() in value.lower():
                    issues.append(f"Potential hardcoded value in {key}: contains '{pattern}'")

    if issues:
        logger.warning("potential_hardcoded_secrets", issues=issues)


__all__ = ["validate_critical_config", "validate_secrets_not_hardcoded", "ConfigurationError"]
