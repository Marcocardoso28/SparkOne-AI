"""Service for outbound WhatsApp messages via Evolution API."""

from __future__ import annotations

import asyncio

import structlog

from ..integrations.evolution_api import EvolutionAPIClient

logger = structlog.get_logger(__name__)


class WhatsAppService:
    def __init__(self, client: EvolutionAPIClient, *, max_retries: int = 3) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    async def send_text(self, to: str, message: str) -> None:
        payload = {"to": to, "message": message}
        delay = 0.5
        for attempt in range(1, self._max_retries + 1):
            try:
                await self._client.send_message(payload)
                logger.info("whatsapp_send_success", to=to)
                return
            except Exception as exc:  # pragma: no cover - network failure path
                logger.warning("whatsapp_send_failed", error=str(exc), to=to, attempt=attempt)
                if attempt == self._max_retries:
                    raise
                await asyncio.sleep(delay)
                delay = min(delay * 2, 5.0)


__all__ = ["WhatsAppService"]
