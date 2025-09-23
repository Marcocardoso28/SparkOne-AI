"""Semantic retrieval over knowledge base."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.db.knowledge import KnowledgeChunkORM, KnowledgeDocumentORM
from ..providers.embeddings import EmbeddingProvider

logger = structlog.get_logger(__name__)


class SemanticRetriever:
    """Retrieves knowledge chunks using semantic similarity."""

    def __init__(self, session: AsyncSession, provider: EmbeddingProvider | None) -> None:
        self._session = session
        self._provider = provider

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._provider is None:
            logger.info("semantic_retrieval_disabled", reason="no embedding provider")
            return []

        embedding = (await self._provider.generate([query]))[0]

        if self._session.bind and self._session.bind.dialect.name == "postgresql":
            stmt = text(
                """
                SELECT kc.id, kc.content, kc.chunk_index, kd.title, kd.source
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kd.id = kc.document_id
                ORDER BY kc.embedding <-> :embedding
                LIMIT :limit
                """
            )
            result = await self._session.execute(stmt, {"embedding": embedding, "limit": limit})
            rows = result.mappings().all()
            return [dict(row) for row in rows]

        stmt = (
            select(
                KnowledgeChunkORM.id,
                KnowledgeChunkORM.content,
                KnowledgeChunkORM.chunk_index,
                KnowledgeDocumentORM.title,
                KnowledgeDocumentORM.source,
            )
            .join(KnowledgeDocumentORM, KnowledgeChunkORM.document_id == KnowledgeDocumentORM.id)
            .order_by(KnowledgeChunkORM.chunk_index)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "id": row.id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "title": row.title,
                "source": row.source,
            }
            for row in result
        ]


__all__ = ["SemanticRetriever"]
