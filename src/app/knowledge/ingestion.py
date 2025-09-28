"""Document ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.repositories import (
    create_knowledge_document,
    insert_knowledge_chunks,
)
from app.providers.embeddings import EmbeddingProvider

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
            raise RuntimeError("Embedding provider is required to ingest knowledge documents")

        chunks = self._split_text(text, chunk_size)
        if not chunks:
            raise ValueError("Text is empty or could not be chunked")

        vectors = await self._provider.generate(chunks)
        if len(vectors) != len(chunks):  # pragma: no cover - sanity check
            logger.warning("chunk_vector_mismatch", chunks=len(chunks), vectors=len(vectors))

        document = await create_knowledge_document(
            self._session,
            title=title,
            source=source,
            metadata=metadata,
        )

        chunk_records = [
            (index, chunk, vector) for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False))
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


__all__ = ["DocumentIngestionService", "IngestionResult"]
