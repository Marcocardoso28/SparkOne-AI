"""Security-oriented middleware (rate limiting, input logging)."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """Simple per-IP rate limiter with token bucket semantics."""

    def __init__(
        self,
        app,
        *,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: defaultdict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host if request.client else "anonymous"
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds
            history = self._requests[client_ip]
            # remove expired entries
            while history and history[0] < window_start:
                history.pop(0)
            if len(history) >= self.max_requests:
                raise HTTPException(status_code=429, detail="Too many requests")
            history.append(now)

        return await call_next(request)


__all__ = ["InMemoryRateLimiter"]
