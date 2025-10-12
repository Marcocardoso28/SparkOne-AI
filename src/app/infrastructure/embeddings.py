"""Embedding providers with OpenAI-compatible fallback logic."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.config import Settings


class EmbeddingProvider:
    """High-level interface for embedding generation."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._remote_client: AsyncOpenAI | None = None
        self._local_client: AsyncOpenAI | None = None

        if settings.openai_api_key:
            self._remote_client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )

        if settings.local_llm_url:
            self._local_client = AsyncOpenAI(
                api_key=settings.local_llm_api_key or "not-required",
                base_url=str(settings.local_llm_url),
            )

    async def generate(self, inputs: Sequence[str]) -> list[list[float]]:
        """Generate embeddings using the configured provider order."""

        errors: list[Exception] = []
        if self._settings.embedding_provider == "openai":
            order = ("remote", "local")
        else:
            order = ("local", "remote")

        for provider_name in order:
            if provider_name == "remote" and self._remote_client:
                try:
                    return await self._create_embeddings(
                        client=self._remote_client,
                        model=self._settings.openai_embedding_model,
                        inputs=inputs,
                    )
                except RuntimeError as exc:
                    errors.append(exc)
            if provider_name == "local" and self._local_client:
                try:
                    return await self._create_embeddings(
                        client=self._local_client,
                        model=self._settings.local_embedding_model,
                        inputs=inputs,
                    )
                except RuntimeError as exc:
                    errors.append(exc)

        detail = "; ".join(str(err) for err in errors) or "no providers configured"
        raise RuntimeError(f"Embedding provider failure: {detail}")

    async def _create_embeddings(
        self,
        *,
        client: AsyncOpenAI,
        model: str,
        inputs: Sequence[str],
    ) -> list[list[float]]:
        try:
            # Configure dimensions for text-embedding-3-large to match database schema (1536)
            embedding_params: dict[str, Any] = {
                "model": model,
                "input": list(inputs),
            }

            # text-embedding-3-large generates 3072 dimensions by default, but we need 1536
            if model == "text-embedding-3-large":
                embedding_params["dimensions"] = 1536

            response = await client.embeddings.create(**embedding_params)
        except OpenAIError as exc:  # pragma: no cover - network error path
            raise RuntimeError(f"Embedding request failed for model {model}") from exc

        return [embedding.embedding for embedding in response.data]


__all__ = ["EmbeddingProvider"]
