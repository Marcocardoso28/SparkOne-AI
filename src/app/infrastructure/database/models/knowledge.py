"""Knowledge base ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin
from .vector import EMBEDDING_TYPE


class KnowledgeDocumentORM(TimestampMixin, Base):
    """Represents a knowledge document ingested into the system."""

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    extra_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class KnowledgeChunkORM(TimestampMixin, Base):
    """Chunked content of documents with embeddings."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[Any] = mapped_column(EMBEDDING_TYPE, nullable=False)


__all__ = ["KnowledgeDocumentORM", "KnowledgeChunkORM"]
