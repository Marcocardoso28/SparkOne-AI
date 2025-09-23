"""Chat-oriented model providers with fallback support."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any, Protocol

import structlog
from openai import AsyncOpenAI, OpenAIError

from ..config import Settings

logger = structlog.get_logger(__name__)

ChatMessage = dict[str, Any]


class ChatProvider(Protocol):
    """Protocol implemented by chat model providers."""

    async def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:  # pragma: no cover - protocol
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
            except (OpenAIError, asyncio.TimeoutError) as exc:  # pragma: no cover - network path
                last_error = exc
                if attempt < self._max_retries:
                    await asyncio.sleep(0.2 * attempt)
                continue

            message = response.choices[0].message.content or ""
            if message.strip():
                return message
            last_error = LLMGenerationError("Empty response from provider")

        raise LLMGenerationError("Chat provider request failed") from last_error


class ChatProviderRouter:
    """Router that decides which provider should serve a request."""

    def __init__(self, settings: Settings) -> None:
        self._primary: OpenAICompatibleProvider | None = None
        self._fallback: OpenAICompatibleProvider | None = None

        timeout = settings.llm_request_timeout
        retries = settings.llm_max_retries

        if settings.openai_api_key:
            client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            self._primary = OpenAICompatibleProvider(
                client=client,
                model=settings.openai_model,
                timeout=timeout,
                max_retries=retries,
            )

        if settings.local_llm_url:
            client = AsyncOpenAI(
                api_key=settings.local_llm_api_key or "sparkone-local",
                base_url=str(settings.local_llm_url),
            )
            self._fallback = OpenAICompatibleProvider(
                client=client,
                model=settings.local_llm_model,
                timeout=timeout,
                max_retries=retries,
            )

    @property
    def available(self) -> bool:
        return self._primary is not None or self._fallback is not None

    async def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Try the primary provider and fallback to local if necessary."""

        if self._primary is None and self._fallback is None:
            raise RuntimeError("No chat providers configured. Check environment variables.")

        if self._primary is not None:
            try:
                return await self._primary.generate(messages, **kwargs)
            except LLMGenerationError as exc:
                logger.warning("chat_provider_primary_failed", error=str(exc))

        if self._fallback is not None:
            return await self._fallback.generate(messages, **kwargs)

        raise LLMGenerationError("Primary provider unavailable and no fallback configured")


__all__ = ["ChatProviderRouter", "ChatMessage", "LLMGenerationError"]
