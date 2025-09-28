"""Middleware para configuração de headers de segurança HTTP."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança HTTP."""

    def __init__(
        self,
        app,
        *,
        enable_hsts: bool = True,
        hsts_max_age: int = 63072000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        config: dict[str, str] | None = None,
    ) -> None:
        super().__init__(app)
        self._enable_hsts = enable_hsts
        self._hsts_max_age = hsts_max_age
        self._hsts_include_subdomains = hsts_include_subdomains
        self._hsts_preload = hsts_preload

        # Configuração padrão de headers de segurança
        self.default_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

        # CSP baseado no ambiente
        if self._is_development_mode():
            self.default_headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' ws: wss: http: https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            self.default_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        # Merge com configuração customizada
        self.headers = {**self.default_headers, **(config or {})}

        # Endpoints que não devem ter cache
        self.no_cache_endpoints = {
            "/web/login",
            "/web/logout",
            "/health",
            "/metrics",
            "/ingest",
            "/webhooks/whatsapp",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa request adicionando headers de segurança."""

        # Processar request
        response = await call_next(request)

        # Adicionar headers de segurança básicos
        for header_name, header_value in self.headers.items():
            response.headers.setdefault(header_name, header_value)

        # HSTS
        if self._enable_hsts:
            directives = [f"max-age={self._hsts_max_age}"]
            if self._hsts_include_subdomains:
                directives.append("includeSubDomains")
            if self._hsts_preload:
                directives.append("preload")
            response.headers.setdefault("Strict-Transport-Security", "; ".join(directives))

        # Headers específicos para endpoints sem cache
        if request.url.path in self.no_cache_endpoints:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Headers específicos para API endpoints
        if request.url.path.startswith(("/api/", "/ingest", "/channels/", "/webhooks/")):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
            response.headers.setdefault("Cache-Control", "no-cache, no-store, must-revalidate")

        # Headers específicos por tipo de conteúdo
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type in ("application/json", "text/html"):
            response.headers.setdefault("Cache-Control", "no-cache, no-store, must-revalidate")

        return response

    def _is_development_mode(self) -> bool:
        """Verifica se está em modo de desenvolvimento."""
        return os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev")


__all__ = ["SecurityHeadersMiddleware"]
