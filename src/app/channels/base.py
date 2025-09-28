"""Channel adapter definitions."""

from __future__ import annotations

from typing import Any, Protocol

from app.models.schemas import ChannelMessage


class ChannelAdapter(Protocol):  # pragma: no cover - protocol
    """Protocol implemented by concrete channel adapters."""

    channel_name: str

    async def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        """Transform raw payload into a normalized ChannelMessage."""


class ChannelNotRegisteredError(ValueError):
    """Raised when no adapter is registered for a given channel."""


class MessageNormalizer:
    """Registry-based normalizer that delegates to channel adapters."""

    def __init__(self, adapters: list[ChannelAdapter]) -> None:
        self._registry = {adapter.channel_name: adapter for adapter in adapters}

    async def normalize(self, channel_name: str, payload: dict[str, Any]) -> ChannelMessage:
        adapter = self._registry.get(channel_name)
        if adapter is None:
            raise ChannelNotRegisteredError(f"Channel '{channel_name}' is not configured")
        return await adapter.normalize(payload)


__all__ = ["ChannelAdapter", "ChannelNotRegisteredError", "MessageNormalizer"]
