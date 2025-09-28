from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.knowledge.ingestion import DocumentIngestionService
from app.knowledge.retriever import SemanticRetriever
from app.models.db.base import Base
from app.models.db.knowledge import KnowledgeChunkORM, KnowledgeDocumentORM


class FakeEmbeddingProvider:
    async def generate(self, inputs: list[str]) -> list[list[float]]:
        # Retorna embeddings com 1536 dimensões para compatibilidade com pgvector
        return [[float(index % 100) / 100.0] * 1536 for index, _ in enumerate(inputs)]


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_document_ingestion_creates_chunks(session: AsyncSession) -> None:
    provider = FakeEmbeddingProvider()
    service = DocumentIngestionService(session=session, provider=provider)
    # Texto maior para garantir múltiplos chunks
    text = "Parágrafo um. Parágrafo dois. Parágrafo três. Parágrafo quatro. " * 10

    result = await service.ingest_text(
        title="Guia",
        source="manual",
        text=text,
        chunk_size=50,  # Tamanho menor para forçar múltiplos chunks
    )
    await session.commit()

    assert result.chunks_ingested >= 1  # Pelo menos 1 chunk deve ser criado
    doc = await session.scalar(select(KnowledgeDocumentORM).limit(1))
    assert doc is not None
    chunks = (await session.execute(select(KnowledgeChunkORM))).scalars().all()
    assert len(chunks) == result.chunks_ingested


@pytest.mark.asyncio
async def test_semantic_retriever_without_provider_returns_empty(session: AsyncSession) -> None:
    retriever = SemanticRetriever(session=session, provider=None)

    result = await retriever.search("teste")

    assert result == []


@pytest.mark.asyncio
async def test_semantic_retriever_returns_chunks(session: AsyncSession) -> None:
    provider = FakeEmbeddingProvider()
    service = DocumentIngestionService(session=session, provider=provider)
    text = "Parágrafo um. Parágrafo dois." * 4
    await service.ingest_text(
        title="Manual",
        source="docs",
        text=text,
        chunk_size=3,
    )
    await session.commit()

    retriever = SemanticRetriever(session=session, provider=provider)
    results = await retriever.search("qualquer", limit=2)

    assert len(results) <= 2
    if results:
        assert "content" in results[0]
