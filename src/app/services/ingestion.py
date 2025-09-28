"""Service layer for handling incoming channel messages."""

from __future__ import annotations

import re
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import Orchestrator
from app.config import get_settings
from app.core.events import EventDispatcher
from app.core.metrics import INGESTION_COUNTER
from app.models.db.repositories import save_channel_message
from app.models.schemas import ChannelMessage
from .embeddings import EmbeddingService
from .memory import MemoryService

logger = structlog.get_logger(__name__)


class IngestionService:
    """Application service to process channel messages."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        orchestrator: Orchestrator,
        embedding_service: EmbeddingService,
        memory_service: MemoryService,
        dispatcher: EventDispatcher | None = None,
    ) -> None:
        self._session = session
        self._orchestrator = orchestrator
        self._embedding_service = embedding_service
        self._memory_service = memory_service
        self._dispatcher = dispatcher
        self._logger = logger

    async def ingest(self, payload: ChannelMessage) -> dict[str, Any] | None:
        """Persist the payload and trigger orchestrator hooks with instrumentation."""

        bound_logger = self._logger.bind(channel=payload.channel.value, sender=payload.sender)
        bound_logger.debug("ingestion_received")

        settings = get_settings()
        sanitized_content = _sanitize_text(payload.content)
        if sanitized_content != payload.content:
            payload = payload.model_copy(update={"content": sanitized_content})
        if len(payload.content) > settings.ingestion_max_content_length:
            raise ValueError(
                f"Conteúdo excede o limite de {settings.ingestion_max_content_length} caracteres."
            )

        try:
            message = await save_channel_message(self._session, payload)
        except Exception as exc:  # pragma: no cover - database failure path
            INGESTION_COUNTER.labels(status="failed").inc()
            bound_logger.exception("ingestion_persist_failed", error=str(exc))
            raise

        try:
            await self._embedding_service.index_message(message)
        except Exception as exc:  # pragma: no cover - embedding failure path
            bound_logger.warning("ingestion_embedding_failed", error=str(exc))

        try:
            await self._memory_service.store_user_message(payload)
        except Exception as exc:  # pragma: no cover - memory failure path
            bound_logger.warning("ingestion_memory_failed", error=str(exc))

        try:
            result = await self._orchestrator.handle(payload)
        except Exception as exc:  # pragma: no cover - orchestrator failure path
            INGESTION_COUNTER.labels(status="failed").inc()
            bound_logger.exception(
                "ingestion_orchestrator_failed", error=str(exc), message_id=message.id
            )
            raise

        INGESTION_COUNTER.labels(status="processed").inc()

        if self._dispatcher is not None:
            await self._dispatcher.emit(
                "message.processed",
                {
                    "message_id": message.id,
                    "channel": payload.channel.value,
                    "sender": payload.sender,
                    "classification": result.get("status") if isinstance(result, dict) else None,
                },
            )

        response_text = result.get("response") if isinstance(result, dict) else None
        if response_text:
            try:
                await self._memory_service.store_assistant_message(
                    channel=payload.channel.value,
                    content=response_text,
                )
            except Exception as exc:  # pragma: no cover - memory failure path
                bound_logger.warning("ingestion_assistant_memory_failed", error=str(exc))

        return result if isinstance(result, dict) else None


__all__ = ["IngestionService"]


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _sanitize_text(value: str) -> str:
    cleaned = _CONTROL_CHARS.sub("", value)
    return cleaned.strip()
