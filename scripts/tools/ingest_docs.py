"""CLI helper to ingest knowledge documents."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import structlog

from src.app.config import get_settings
from src.app.core.database import get_session_factory
from src.app.knowledge.ingestion import DocumentIngestionService
from src.app.providers.embeddings import EmbeddingProvider

logger = structlog.get_logger(__name__)


async def _ingest_file(path: Path, source: str) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    if not (settings.openai_api_key or settings.local_llm_url):
        raise RuntimeError("Embedding provider not configured. Set OPENAI_API_KEY ou LOCAL_LLM_URL.")

    provider = EmbeddingProvider(settings)

    async with session_factory() as session:
        service = DocumentIngestionService(session=session, provider=provider)
        text = path.read_text(encoding="utf-8")
        result = await service.ingest_text(title=path.stem, source=source, text=text)
        await session.commit()
        logger.info("document_ingested", document_id=result.document_id, chunks=result.chunks_ingested)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into SparkOne knowledge base")
    parser.add_argument("path", type=Path, help="Path to a text/markdown file")
    parser.add_argument("--source", default="local", help="Source identifier for the document")
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"File {args.path} not found")

    asyncio.run(_ingest_file(args.path, args.source))


if __name__ == "__main__":
    main()
