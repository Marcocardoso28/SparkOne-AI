"""Simple correlation ID middleware for structured logging."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

_LOGGER = structlog.get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        request.state.correlation_id = correlation_id
        token = structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            # Fix: reset_contextvars() doesn't take arguments in newer versions
            structlog.contextvars.reset_contextvars()
        response.headers.setdefault("X-Correlation-ID", correlation_id)
        return response


__all__ = ["CorrelationIdMiddleware"]
