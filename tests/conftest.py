"""Shared pytest fixtures and configuration."""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a test database session."""
    settings = get_settings()

    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Create tables
    from app.infrastructure.database.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def test_settings():
    """Get test settings."""
    settings = get_settings()
    settings.environment = "test"
    settings.debug = True
    return settings


@pytest.fixture
def mock_redis():
    """Mock Redis for tests."""
    class MockRedis:
        async def ping(self):
            return True

        async def get(self, key):
            return None

        async def set(self, key, value, ex=None):
            return True

        async def delete(self, key):
            return True

        async def close(self):
            pass

    return MockRedis()


@pytest.fixture
def mock_evolution_client():
    """Mock Evolution API client for tests."""
    class MockEvolutionClient:
        async def send_message(self, to: str, message: str):
            return {"status": "sent", "message_id": "test_123"}

        async def close(self):
            pass

    return MockEvolutionClient()


@pytest.fixture
def mock_notion_client():
    """Mock Notion client for tests."""
    class MockNotionClient:
        async def create_page(self, title: str, content: str):
            return {"id": "test_page_123", "title": title}

        async def close(self):
            pass

    return MockNotionClient()
