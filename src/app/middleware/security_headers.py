"""Middleware to add common security headers."""

from __future__ import annotations

from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enable_hsts: bool = True,
        hsts_max_age: int = 63072000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
    ) -> None:
        super().__init__(app)
        self._enable_hsts = enable_hsts
        self._hsts_max_age = hsts_max_age
        self._hsts_include_subdomains = hsts_include_subdomains
        self._hsts_preload = hsts_preload

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "microphone=(), camera=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Resource-Policy": "same-site",
        }
        if self._enable_hsts:
            directives = [f"max-age={self._hsts_max_age}"]
            if self._hsts_include_subdomains:
                directives.append("includeSubDomains")
            if self._hsts_preload:
                directives.append("preload")
            headers["Strict-Transport-Security"] = "; ".join(directives)
        for key, value in headers.items():
            response.headers.setdefault(key, value)
        return response


__all__ = ["SecurityHeadersMiddleware"]
