"""Embedding generation and persistence service."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.db.repositories import upsert_message_embedding
from ..models.db.message import ChannelMessageORM
from ..providers.embeddings import EmbeddingProvider

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Encapsulates embedding generation for messages."""

    def __init__(self, session: AsyncSession, provider: EmbeddingProvider | None) -> None:
        self._session = session
        self._provider = provider

    async def index_message(self, message: ChannelMessageORM) -> None:
        """Generate embeddings for the given message and persist them."""

        if self._provider is None:
            return
        try:
            vectors = await self._provider.generate([message.content])
        except RuntimeError as exc:
            logger.warning("embedding_generation_failed", error=str(exc))
            return
        if not vectors:
            logger.warning("embedding_generation_empty", message_id=message.id)
            return

        embedding = vectors[0]
        await upsert_message_embedding(
            self._session,
            message_id=message.id,
            embedding=embedding,
            content=message.content,
        )


__all__ = ["EmbeddingService"]
