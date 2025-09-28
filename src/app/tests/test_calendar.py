from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.db.base import Base
from app.models.db.events import EventRecord
from app.models.schemas import Channel, ChannelMessage
from app.services.calendar import CalendarService


class DummyCalDAVClient:
    async def create_event(self, event: dict) -> None:
        self.event = event


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
async def test_calendar_service_creates_event(session: AsyncSession) -> None:
    caldav = DummyCalDAVClient()
    service = CalendarService(session=session, caldav_client=caldav)
    start = datetime.now(UTC)
    payload = ChannelMessage(
        channel=Channel.WEB,
        sender="tester",
        content="Reunião equipe",
        extra_data={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
            "location": "Sala 1",
            "description": "Bater metas",
        },
    )

    result = await service.handle(payload)
    await session.commit()

    assert result["status"] == "created"
    stored = (await session.execute(select(EventRecord))).scalar_one()
    assert stored.title.startswith("Reunião")
    assert hasattr(caldav, "event")
