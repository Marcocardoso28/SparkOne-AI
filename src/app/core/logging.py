"""Logging configuration for structured logs (structlog)."""

from __future__ import annotations

import logging

import structlog
from structlog.contextvars import clear_contextvars

_SENSITIVE_KEYS = {
    "openai_api_key",
    "local_llm_api_key",
    "smtp_password",
    "smtp_username",
    "web_password",
    "token",
    "password",
    "secret",
}


def _strip_sensitive_data(_, __, event_dict: dict) -> dict:
    for key in list(event_dict.keys()):
        if any(pattern in key.lower() for pattern in _SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(debug: bool = False) -> None:
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.dict_tracebacks,
        _strip_sensitive_data,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        context_class=dict,
    )

    clear_contextvars()

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)


__all__ = ["configure_logging"]
