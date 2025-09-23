from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.services.tasks import TaskService
from src.app.models.db.base import Base
from src.app.models.db.tasks import TaskRecord
from src.app.models.schemas import Channel, ChannelMessage


class DummyNotionClient:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    async def create_page(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"id": "notion-page-id"}


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
async def test_task_service_creates_record(session: AsyncSession) -> None:
    notion = DummyNotionClient()
    service = TaskService(
        session=session,
        notion_client=notion,
        notion_database_id="db",
    )
    payload = ChannelMessage(
        channel=Channel.WEB,
        sender="tester",
        content="Preparar relatório",
        extra_data={"description": "Detalhar itens", "due_at": datetime.now(timezone.utc).isoformat()},
    )

    result = await service.handle(payload)
    await session.commit()

    assert result["status"] == "created"
    stored = (await session.execute(select(TaskRecord))).scalar_one()
    assert stored.title.startswith("Preparar")
    assert notion.payloads
