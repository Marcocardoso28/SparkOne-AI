"""Document ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.repositories import (
    create_knowledge_document,
    insert_knowledge_chunks,
)
from app.infrastructure.embeddings import EmbeddingProvider

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class IngestionResult:
    document_id: int
    chunks_ingested: int


class DocumentIngestionService:
    """Transforms raw text documents into semantic chunks."""

    def __init__(self, session: AsyncSession, provider: EmbeddingProvider | None) -> None:
        self._session = session
        self._provider = provider

    async def ingest_text(
        self,
        *,
        title: str,
        source: str,
        text: str,
        metadata: dict | None = None,
        chunk_size: int = 400,
    ) -> IngestionResult:
        if self._provider is None:
            raise RuntimeError(
                "Embedding provider is required to ingest knowledge documents")

        chunks = self._split_text(text, chunk_size)
        if not chunks:
            raise ValueError("Text is empty or could not be chunked")

        vectors = await self._provider.generate(chunks)
        if len(vectors) != len(chunks):  # pragma: no cover - sanity check
            logger.warning("chunk_vector_mismatch",
                           chunks=len(chunks), vectors=len(vectors))

        document = await create_knowledge_document(
            self._session,
            title=title,
            source=source,
            metadata=metadata,
        )

        chunk_records = [
            (index, chunk, vector)
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False))
        ]
        await insert_knowledge_chunks(
            self._session,
            document_id=document.id,
            chunks=chunk_records,
        )

        return IngestionResult(document_id=document.id, chunks_ingested=len(chunk_records))

    def _split_text(self, text: str, chunk_size: int) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for paragraph in paragraphs:
            words = paragraph.split()
            if current_len + len(words) > chunk_size and current:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
            current.append(paragraph)
            current_len += len(words)
        if current:
            chunks.append(" ".join(current))
        if not chunks and text.strip():
            return [text.strip()]
        return chunks


class IngestionService:
    """High-level ingestion service for channel messages."""

    def __init__(
        self,
        session: AsyncSession,
        orchestrator=None,
        embedding_service=None,
        memory_service=None,
        dispatcher=None,
    ) -> None:
        self._session = session
        self._orchestrator = orchestrator
        self._embedding_service = embedding_service
        self._memory_service = memory_service
        self._dispatcher = dispatcher

    async def ingest(self, message) -> dict:
        """Ingest a channel message."""
        from app.infrastructure.database.models.repositories import (
            save_channel_message,
            append_conversation_message,
        )
        from app.infrastructure.database.models.memory import ConversationRole

        logger.info("message_ingested",
                   channel=message.channel,
                   sender=message.sender,
                   content_length=len(message.content))

        # Save channel message
        channel_msg = await save_channel_message(
            self._session,
            payload=message,
        )

        # Create user message in conversation
        user_msg = await append_conversation_message(
            self._session,
            conversation_id="default",  # Default conversation
            channel=message.channel,
            sender=message.sender,
            role=ConversationRole.USER,
            content=message.content,
        )

        await self._session.commit()

        logger.info("message_saved",
                   channel_message_id=channel_msg.id,
                   conversation_message_id=user_msg.id)

        return {
            "channel_message_id": channel_msg.id,
            "conversation_message_id": user_msg.id,
            "status": "saved",
        }

# Alias for backward compatibility
__all__ = ["DocumentIngestionService", "IngestionService", "IngestionResult"]
