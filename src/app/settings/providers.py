"""Provider-related configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderSettings:
    """Generic configuration for an LLM provider."""

    model: str
    base_url: str | None
    api_key: str | None


@dataclass(slots=True)
class EmbeddingSettings:
    """Configuration for embedding providers."""

    model: str
    base_url: str | None
    api_key: str | None


__all__ = ["ProviderSettings", "EmbeddingSettings"]
