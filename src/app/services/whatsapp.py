"""Service for outbound WhatsApp messages via Evolution API."""

from __future__ import annotations

import asyncio

import structlog

from app.integrations.evolution_api import EvolutionAPIClient
from app.models.schemas import Channel, ChannelMessage, MessageType

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


# Backwards-compatible normalizer stub used by tests when patched.
async def normalize_whatsapp_message(payload: dict) -> ChannelMessage:  # pragma: no cover - stub
    """Minimal normalizer to satisfy test patch targets.

    In production, normalization is handled by channel adapters. This function
    exists so tests can patch `src.app.services.whatsapp.normalize_whatsapp_message`.
    """
    sender = str(payload.get("from") or payload.get("sender") or "unknown")
    content = str(payload.get("message") or payload.get("text") or "")
    return ChannelMessage(
        channel=Channel.WHATSAPP,
        sender=sender,
        content=content,
        message_type=MessageType.FREE_TEXT,
        extra_data={"raw": {k: payload.get(k) for k in list(payload)[:10]}},
    )
