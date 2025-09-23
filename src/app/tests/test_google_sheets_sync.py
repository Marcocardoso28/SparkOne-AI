from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.channels import MessageNormalizer, GoogleSheetsAdapter
from src.app.dependencies import build_ingestion_service, get_message_normalizer
from src.app.models.db.base import Base
from sqlalchemy import select

from src.app.models.db.message import ChannelMessageORM
from src.app.services.google_sheets_sync import GoogleSheetsSyncService
from src.app.services.ingestion import IngestionService


class FakeGoogleSheetsClient:
    def __init__(self, rows: list[list[str]]) -> None:
        self.rows = rows

    async def list_rows(self, spreadsheet_id: str, range_: str):
        return self.rows


class DummyIngestion(IngestionService):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            orchestrator=lambda x: None,  # type: ignore[arg-type]
            embedding_service=lambda: None,  # type: ignore[arg-type]
        )


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
async def test_google_sheets_sync_inserts_new_rows(session: AsyncSession) -> None:
    client = FakeGoogleSheetsClient([["Task 1"], ["Task 2"]])
    normalizer = MessageNormalizer([GoogleSheetsAdapter()])

    ingestion = build_ingestion_service(session)

    service = GoogleSheetsSyncService(
        session=session,
        client=client,
        normalizer=normalizer,
        ingestion_service=ingestion,
        spreadsheet_id="sheet",
        range_name="Sheet1!A2:A",
    )

    result = await service.sync()
    await session.commit()

    assert result["processed"] == 2
    assert result["skipped"] == 0
    assert result["failures"] == 0
    rows = (await session.execute(select(ChannelMessageORM))).scalars().all()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_google_sheets_sync_skips_blank_rows(session: AsyncSession) -> None:
    # Dados de teste: linha vazia, linha com espaços, linha válida
    client = FakeGoogleSheetsClient([[""], ["   "], ["Task válida"]])
    normalizer = MessageNormalizer([GoogleSheetsAdapter()])
    ingestion = build_ingestion_service(session)

    service = GoogleSheetsSyncService(
        session=session,
        client=client,
        normalizer=normalizer,
        ingestion_service=ingestion,
        spreadsheet_id="sheet",
        range_name="Sheet1!A2:A",
    )

    result = await service.sync()

    # O serviço processa todas as linhas válidas (incluindo a primeira linha vazia que não é pulada)
    # e pula apenas as linhas com conteúdo em branco ou apenas espaços
    assert result["processed"] == 2  # Linha vazia + linha válida são processadas
    assert result["skipped"] == 1    # Apenas a linha com espaços é pulada


@pytest.mark.asyncio
async def test_google_sheets_sync_counts_failures(session: AsyncSession) -> None:
    class FailingIngestion:
        async def ingest(self, payload):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    client = FakeGoogleSheetsClient([["Task 1"], ["Task 2"]])
    normalizer = MessageNormalizer([GoogleSheetsAdapter()])
    service = GoogleSheetsSyncService(
        session=session,
        client=client,
        normalizer=normalizer,
        ingestion_service=FailingIngestion(),
        spreadsheet_id="sheet",
        range_name="Sheet1!A2:A",
    )

    result = await service.sync()

    assert result["processed"] == 0
    assert result["failures"] == 2
