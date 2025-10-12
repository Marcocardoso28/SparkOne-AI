"""Rate limiting middleware para proteger contra abusos."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:  # pragma: no cover - opcional
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    Redis = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class RateLimitStore(Protocol):
    async def increment(self, key: str, ttl: int) -> tuple[int, float]:
        """Incrementa contador e retorna (count, expires_at)."""

    async def cleanup_expired(self) -> None:
        """Permite limpeza de itens expirados quando aplicável."""


class InMemoryRateLimitStore:
    """Store em memória simples com TTL."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def increment(self, key: str, ttl: int = 3600) -> tuple[int, float]:
        async with self._lock:
            current_time = time.time()
            record = self._store.get(key)

            if record is None or record.get("expires_at", 0.0) <= current_time:
                record = {
                    "count": 1,
                    "expires_at": current_time + ttl,
                    "first_request": current_time,
                }
                self._store[key] = record
            else:
                record["count"] += 1

            return record["count"], record["expires_at"]

    async def cleanup_expired(self) -> None:
        async with self._lock:
            current_time = time.time()
            expired = [
                k for k, v in self._store.items() if v.get("expires_at", 0.0) <= current_time
            ]
            for key in expired:
                del self._store[key]


class RedisRateLimitStore:
    """Store baseado em Redis usando operações atômicas."""

    def __init__(self, redis_url: str, *, prefix: str = "sparkone:rate_limit:") -> None:
        if Redis is None:  # pragma: no cover
            raise RuntimeError("redis.asyncio não está disponível")
        self._client = Redis.from_url(redis_url)
        self._prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def increment(self, key: str, ttl: int = 3600) -> tuple[int, float]:
        namespaced = self._key(key)
        async with self._client.pipeline(transaction=True) as pipe:  # type: ignore[attr-defined]
            pipe.incr(namespaced)
            pipe.expire(namespaced, ttl)
            count, _ = await pipe.execute()

        ttl_seconds = await self._client.ttl(namespaced)
        if ttl_seconds is None or ttl_seconds < 0:
            ttl_seconds = ttl
            await self._client.expire(namespaced, ttl)
        expires_at = time.time() + ttl_seconds
        return int(count), expires_at

    async def cleanup_expired(self) -> None:  # pragma: no cover - Redis gerencia via TTL
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting com diferentes limites por endpoint."""

    def __init__(
        self,
        app,
        *,
        store: RateLimitStore | None = None,
        default_requests: int = 100,
        default_window: int = 3600,
        endpoint_limits: dict[str, dict[str, int]] | None = None,
    ) -> None:
        super().__init__(app)
        self.store = store or InMemoryRateLimitStore()
        self.default_requests = default_requests
        self.default_window = default_window
        self.endpoint_limits = endpoint_limits or {
            "/web/login": {"requests": 5, "window": 900},
            "/web/logout": {"requests": 10, "window": 300},
            "/ingest": {"requests": 50, "window": 3600},
            "/channels/": {"requests": 30, "window": 3600},
            "/webhooks/": {"requests": 100, "window": 3600},
            "/web": {"requests": 200, "window": 3600},
            "/web/ingest": {"requests": 100, "window": 3600},
            "/health": {"requests": 1000, "window": 3600},
            "/metrics": {"requests": 500, "window": 3600},
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger.debug("rate_limit_middleware_entry", path=request.url.path)

        if self._should_skip_rate_limit(request):
            logger.debug("rate_limit_skipped", path=request.url.path)
            return await call_next(request)

        logger.debug("rate_limit_apply", path=request.url.path)
        client_id = self._get_client_identifier(request)
        limits = self._get_endpoint_limits(request.url.path)
        rate_limit_key = f"{client_id}:{request.url.path}"

        current_count, expires_at = await self.store.increment(rate_limit_key, limits["window"])
        logger.debug(
            "rate_limit_state",
            path=request.url.path,
            count=current_count,
            limit=limits["requests"],
            window=limits["window"],
        )

        if current_count > limits["requests"]:
            reset_time = int(expires_at)
            logger.warning(
                "Rate limit exceeded for %s on %s: %s/%s",
                client_id,
                request.url.path,
                current_count,
                limits["requests"],
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "limit": limits["requests"],
                    "window": limits["window"],
                    "reset_at": reset_time,
                },
                headers={
                    "X-RateLimit-Limit": str(limits["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(limits["window"]),
                },
            )

        response = await call_next(request)
        logger.debug("rate_limit_next_completed", path=request.url.path)
        remaining = max(0, limits["requests"] - current_count)
        self._set_rate_limit_headers(response, limits, remaining, int(expires_at))
        return response

    def _should_skip_rate_limit(self, request: Request) -> bool:
        static_extensions = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg"}
        path = request.url.path.lower()
        if path.endswith('/'):
            path = path.rstrip('/')
        if any(path.endswith(ext) for ext in static_extensions):
            return True
        # Do not skip health/metrics to allow tests to validate rate limiting
        # (In production, use Traefik/ingress rate limiting as needed.)
        return False

    def _get_client_identifier(self, request: Request) -> str:
        try:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.headers.get("X-Real-IP") or (
                    request.client.host if request.client else "unknown"
                )
            logger.debug("rate_limit_client_ip", client_ip=client_ip)

            # Safe handling for accessing cookies
            try:
                session_cookie = request.cookies.get("sparkone_session")
                if session_cookie:
                    identifier = f"{client_ip}:{session_cookie[:8]}"
                    return identifier
            except Exception as cookie_exc:
                logger.debug(
                    "rate_limit_cookie_access_error",
                    error_type=type(cookie_exc).__name__,
                    error=str(cookie_exc),
                )
                # If unable to access cookies, use only IP
                pass

            return client_ip
        except Exception as exc:
            logger.debug(
                "rate_limit_client_identifier_error",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            return "unknown"

    def _get_endpoint_limits(self, path: str) -> dict[str, int]:
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        return {"requests": self.default_requests, "window": self.default_window}

    @staticmethod
    def _set_rate_limit_headers(
        response: Response,
        limits: dict[str, int],
        remaining: int,
        reset_time: int,
    ) -> None:
        response.headers["X-RateLimit-Limit"] = str(limits["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)


async def cleanup_rate_limit_store(store: RateLimitStore, interval: int = 300) -> None:
    """Task para limpar entradas expiradas periodicamente."""
    while True:
        try:
            await store.cleanup_expired()
            await asyncio.sleep(interval)
        except Exception as exc:  # pragma: no cover - apenas loga
            logger.error("Error cleaning up rate limit store: %s", exc)
            await asyncio.sleep(interval)


rate_limit_store = InMemoryRateLimitStore()
_REDIS_STORES: dict[str, RedisRateLimitStore] = {}


def resolve_rate_limit_store(redis_url: str | None) -> RateLimitStore:
    """Resolve o store adequado com cache de conexões.

    Fora de produção, usa sempre store em memória para evitar dependência de Redis
    durante desenvolvimento e testes.
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if getattr(settings, "environment", "development") != "production":
            return rate_limit_store
    except Exception:  # pragma: no cover - fallback se settings indisponível
        pass

    if redis_url and Redis is not None:
        store = _REDIS_STORES.get(redis_url)
        if store is None:
            store = RedisRateLimitStore(redis_url)
            _REDIS_STORES[redis_url] = store
        return store
    return rate_limit_store


__all__ = [
    "RateLimitMiddleware",
    "cleanup_rate_limit_store",
    "rate_limit_store",
    "resolve_rate_limit_store",
]
