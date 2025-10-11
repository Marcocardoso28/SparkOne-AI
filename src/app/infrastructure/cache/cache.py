"""Smart caching system for LLM responses."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ResponseCache:
    """Cache inteligente para respostas de LLM."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def _generate_key(self, messages: list[dict], **kwargs: Any) -> str:
        """Gera chave única para a consulta."""
        # Remove task_type e outros parâmetros que não afetam o conteúdo
        cache_kwargs = {k: v for k, v in kwargs.items() if k not in ["task_type"]}

        content = {
            "messages": messages,
            "kwargs": cache_kwargs
        }

        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def get(self, messages: list[dict], **kwargs: Any) -> str | None:
        """Recupera resposta do cache se válida."""
        key = self._generate_key(messages, **kwargs)

        if key not in self._cache:
            return None

        cached_item = self._cache[key]

        # Verifica se ainda está válido
        if time.time() - cached_item["timestamp"] > self._ttl:
            del self._cache[key]
            return None

        logger.debug("cache_hit", key=key)
        return cached_item["response"]

    def set(self, messages: list[dict], response: str, **kwargs: Any) -> None:
        """Armazena resposta no cache."""
        key = self._generate_key(messages, **kwargs)

        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

        logger.debug("cache_set", key=key)

    def clear_expired(self) -> None:
        """Remove itens expirados do cache."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time - item["timestamp"] > self._ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug("cache_cleaned", removed_count=len(expired_keys))

    def size(self) -> int:
        """Retorna o número de itens no cache."""
        return len(self._cache)


# Cache global singleton
_global_cache: ResponseCache | None = None


def get_response_cache() -> ResponseCache:
    """Retorna instância global do cache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ResponseCache(ttl_seconds=1800)  # 30 minutos
    return _global_cache


__all__ = ["ResponseCache", "get_response_cache"]