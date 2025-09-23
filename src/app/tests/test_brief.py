from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.main import create_application
from src.app.dependencies import get_brief_service
from src.app.models.db.base import Base
from src.app.models.db.tasks import TaskRecord, TaskStatus
from src.app.models.db.events import EventRecord, EventStatus
from src.app.models.db.memory import ConversationMessage, ConversationRole
from src.app.services.brief import BriefService


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
async def test_structured_brief_endpoint(monkeypatch, session: AsyncSession) -> None:
    # seed data
    session.add(
        TaskRecord(
            title="Task",
            description=None,
            due_at=datetime.now(timezone.utc),
            status=TaskStatus.TODO,
            channel="web",
            sender="user",
        )
    )
    session.add(
        EventRecord(
            title="Meeting",
            description=None,
            start_at=datetime.now(timezone.utc) + timedelta(hours=1),
            end_at=None,
            status=EventStatus.CONFIRMED,
            location=None,
            channel="web",
            sender="user",
        )
    )
    session.add(
        ConversationMessage(
            channel="web",
            sender="user",
            role=ConversationRole.USER,
            content="Olá",
        )
    )
    await session.commit()

    app = create_application()

    async def override_brief_service():
        yield BriefService(session=session, chat_provider=None)

    app.dependency_overrides[get_brief_service] = override_brief_service

    client = TestClient(app)
    response = client.get("/brief/structured")

    assert response.status_code == 200
    data = response.json()
    assert data["tasks"]
    assert data["events"]

    response_text = client.get("/brief/text")
    assert response_text.status_code == 200
    assert "brief" in response_text.json()

    app.dependency_overrides.clear()
