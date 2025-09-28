"""Event dispatcher and sinks to integrate with external automations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import structlog

logger = structlog.get_logger(__name__)


class EventSink(Protocol):  # pragma: no cover - protocol
    async def send(self, event_name: str, payload: dict[str, Any]) -> None:
        """Dispatch the event payload to the sink."""


@dataclass(slots=True)
class Event:
    name: str
    payload: dict[str, Any]


class EventDispatcher:
    """Simple asynchronous event dispatcher with pluggable sinks."""

    def __init__(self, sinks: list[EventSink] | None = None) -> None:
        self._sinks = sinks or []

    def register_sink(self, sink: EventSink) -> None:
        self._sinks.append(sink)

    async def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        if not self._sinks:
            return
        for sink in self._sinks:
            try:
                await sink.send(event_name, payload)
            except Exception as exc:  # pragma: no cover - network failure path
                logger.warning("event_dispatch_failed", sink=type(sink).__name__, error=str(exc))


class N8nWebhookSink:
    """Generic webhook sink compatible com n8n ou outros orquestradores."""

    def __init__(self, url: str, token: str | None = None, *, timeout: float = 5.0) -> None:
        self._url = url
        self._token = token
        self._timeout = timeout

    async def send(self, event_name: str, payload: dict[str, Any]) -> None:
        headers: dict[str, Any] = {"X-Event-Name": event_name}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url, json={"event": event_name, "payload": payload}, headers=headers
            )
            response.raise_for_status()


__all__ = ["Event", "EventDispatcher", "EventSink", "N8nWebhookSink"]
