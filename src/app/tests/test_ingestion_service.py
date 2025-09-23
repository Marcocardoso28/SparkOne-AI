from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from unittest.mock import patch

from src.app.models.db.base import Base
from src.app.config import get_settings
from src.app.models.db.message import ChannelMessageORM
from src.app.models.schemas import Channel, ChannelMessage, MessageType
from src.app.services.embeddings import EmbeddingService
from src.app.services.ingestion import IngestionService
from src.app.services.memory import MemoryService


class FakeOrchestrator:
    def __init__(self) -> None:
        self.calls: list[ChannelMessage] = []

    async def handle(self, payload: ChannelMessage) -> None:
        self.calls.append(payload)


class FakeEmbeddingService(EmbeddingService):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, provider=None)
        self.messages: list[ChannelMessageORM] = []

    async def index_message(self, message: ChannelMessageORM) -> None:
        self.messages.append(message)


class FakeMemoryService(MemoryService):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session)
        self.user_messages: list[ChannelMessage] = []
        self.assistant_messages: list[str] = []

    async def store_user_message(self, payload: ChannelMessage) -> None:
        self.user_messages.append(payload)

    async def store_assistant_message(self, *, channel: str, content: str) -> None:
        self.assistant_messages.append(content)


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
async def test_ingestion_service_persists_message(session: AsyncSession) -> None:
    orchestrator = FakeOrchestrator()
    embedding = FakeEmbeddingService(session)
    memory = FakeMemoryService(session)
    service = IngestionService(
        session=session,
        orchestrator=orchestrator,
        embedding_service=embedding,
        memory_service=memory,
        dispatcher=None,
    )
    payload = ChannelMessage(
        channel=Channel.WHATSAPP,
        sender="marco",
        content="Criar tarefa",
        message_type=MessageType.TASK,
    )

    await service.ingest(payload)
    await session.commit()

    result = await session.get(ChannelMessageORM, 1)
    assert result is not None
    assert result.sender == "marco"
    assert orchestrator.calls == [payload]
    assert embedding.messages and embedding.messages[0].sender == "marco"
    assert memory.user_messages == [payload]


@pytest.mark.asyncio
async def test_ingestion_service_rejects_long_message(session: AsyncSession) -> None:
    orchestrator = FakeOrchestrator()
    embedding = FakeEmbeddingService(session)
    memory = FakeMemoryService(session)
    service = IngestionService(
        session=session,
        orchestrator=orchestrator,
        embedding_service=embedding,
        memory_service=memory,
        dispatcher=None,
    )

    payload = ChannelMessage(
        channel=Channel.WHATSAPP,
        sender="marco",
        content="x" * 50,
    )

    settings = get_settings()

    with patch("src.app.services.ingestion.get_settings", return_value=settings.model_copy(update={"ingestion_max_content_length": 10})):
        with pytest.raises(ValueError):
            await service.ingest(payload)


@pytest.mark.asyncio
async def test_ingestion_service_sanitizes_control_chars(session: AsyncSession) -> None:
    orchestrator = FakeOrchestrator()
    embedding = FakeEmbeddingService(session)
    memory = FakeMemoryService(session)
    service = IngestionService(
        session=session,
        orchestrator=orchestrator,
        embedding_service=embedding,
        memory_service=memory,
        dispatcher=None,
    )

    payload = ChannelMessage(
        channel=Channel.WHATSAPP,
        sender="user",
        content="\x00\x01Olá",
    )

    await service.ingest(payload)
    await session.commit()

    stored = await session.get(ChannelMessageORM, 1)
    assert stored is not None
    assert stored.content == "Olá"
