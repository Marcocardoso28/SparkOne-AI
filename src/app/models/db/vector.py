"""Vector store ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

try:  # pragma: no cover - optional dependency hook
    from pgvector.sqlalchemy import Vector as PgVector
except ImportError:  # pragma: no cover - fallback for tests without pgvector
    PgVector = None  # type: ignore[assignment]

EMBEDDING_TYPE: Any
if PgVector is not None:
    EMBEDDING_TYPE = PgVector(1536)
else:
    EMBEDDING_TYPE = JSON


class MessageEmbeddingORM(TimestampMixin, Base):
    """Stores embeddings associated with channel messages."""

    __tablename__ = "message_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("channel_messages.id", ondelete="CASCADE"), unique=True
    )
    embedding: Mapped[Any] = mapped_column(EMBEDDING_TYPE, nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)


__all__ = ["MessageEmbeddingORM", "EMBEDDING_TYPE"]
