"""Chat-oriented model providers with fallback support."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any, Protocol

import structlog
from openai import AsyncOpenAI, OpenAIError

from app.config import Settings
from app.infrastructure.cache.cache import get_response_cache

logger = structlog.get_logger(__name__)

ChatMessage = dict[str, Any]


class ChatProvider(Protocol):
    """Protocol implemented by chat model providers."""

    async def generate(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> str:  # pragma: no cover - protocol
        """Return a textual response for the given chat messages."""


class LLMGenerationError(RuntimeError):
    """Raised when a provider fails to return a valid response."""


class OpenAICompatibleProvider:
    """Provider that leverages OpenAI-compatible APIs (OpenAI, LiteLLM, vLLM)."""

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        *,
        timeout: float,
        max_retries: int,
    ) -> None:
        self._client = client
        self._model = model
        self._timeout = max(timeout, 1.0)
        self._max_retries = max(1, max_retries)

    async def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Execute the chat completion call with simple retry/backoff."""

        temperature = kwargs.get("temperature", 0.2)
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                async with asyncio.timeout(self._timeout):
                    response = await self._client.chat.completions.create(
                        model=self._model,
                        messages=list(messages),
                        temperature=temperature,
                    )
            except (TimeoutError, OpenAIError) as exc:  # pragma: no cover - network path
                last_error = exc
                if attempt < self._max_retries:
                    await asyncio.sleep(0.2 * attempt)
                continue

            message = response.choices[0].message.content or ""
            if message.strip():
                return message
            last_error = LLMGenerationError("Empty response from provider")

        raise LLMGenerationError(
            "Chat provider request failed") from last_error


class ChatProviderRouter:
    """Router that intelligently selects the best model for each task."""

    def __init__(self, settings: Settings) -> None:
        self._primary: OpenAICompatibleProvider | None = None
        self._fallback: OpenAICompatibleProvider | None = None
        self._fast_local: OpenAICompatibleProvider | None = None
        self._smart_local: OpenAICompatibleProvider | None = None

        timeout = settings.llm_request_timeout
        retries = settings.llm_max_retries

        if settings.openai_api_key:
            client = AsyncOpenAI(
                api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            self._primary = OpenAICompatibleProvider(
                client=client,
                model=settings.openai_model,
                timeout=timeout,
                max_retries=retries,
            )

        if settings.local_llm_url:
            client = AsyncOpenAI(
                api_key=settings.local_llm_api_key or "not-required",
                base_url=str(settings.local_llm_url),
            )

            # Modelo padrão (compatibilidade)
            self._fallback = OpenAICompatibleProvider(
                client=client,
                model=settings.local_llm_model,
                timeout=timeout,
                max_retries=retries,
            )

            # Modelo rápido para tarefas simples
            self._fast_local = OpenAICompatibleProvider(
                client=client,
                model=settings.local_llm_fast_model,
                timeout=timeout // 2,  # Timeout reduzido
                max_retries=1,
            )

            # Modelo inteligente para tarefas complexas
            self._smart_local = OpenAICompatibleProvider(
                client=client,
                model=settings.local_llm_smart_model,
                timeout=timeout,
                max_retries=retries,
            )

    @property
    def available(self) -> bool:
        return self._primary is not None or self._fallback is not None

    def _select_optimal_provider(self, task_type: str = "default") -> OpenAICompatibleProvider | None:
        """Seleciona o melhor provedor baseado no tipo de tarefa."""

        # Tarefas rápidas: classificação, perguntas simples
        if task_type == "fast" and self._fast_local:
            return self._fast_local

        # Tarefas inteligentes: coaching, respostas complexas
        if task_type == "smart" and self._smart_local:
            return self._smart_local

        # Fallback padrão
        if self._primary:
            return self._primary

        return self._fallback

    async def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Generate response using the optimal provider for the task."""

        # Verificar cache primeiro
        cache = get_response_cache()
        messages_list = list(messages)

        cached_response = cache.get(messages_list, **kwargs)
        if cached_response:
            return cached_response

        task_type = kwargs.pop("task_type", "default")
        optimal_provider = self._select_optimal_provider(task_type)

        if optimal_provider is None:
            raise RuntimeError(
                "No chat providers configured. Check environment variables.")

        try:
            response = await optimal_provider.generate(messages, **kwargs)
            # Armazenar no cache
            cache.set(messages_list, response, task_type=task_type, **kwargs)
            return response
        except LLMGenerationError as exc:
            logger.warning("chat_provider_optimal_failed",
                           task_type=task_type, error=str(exc))

            # Fallback para outros provedores se o ótimo falhar
            fallback_providers = [
                self._primary,
                self._smart_local,
                self._fast_local,
                self._fallback
            ]

            for provider in fallback_providers:
                if provider and provider != optimal_provider:
                    try:
                        response = await provider.generate(messages, **kwargs)
                        # Armazenar resposta de fallback no cache
                        cache.set(messages_list, response,
                                  task_type=task_type, **kwargs)
                        return response
                    except LLMGenerationError:
                        continue

            raise LLMGenerationError("All providers failed") from exc


__all__ = ["ChatProviderRouter", "ChatMessage", "LLMGenerationError"]
