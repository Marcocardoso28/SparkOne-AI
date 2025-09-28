from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_application


def test_healthcheck_returns_ok() -> None:
    app = create_application()
    client = TestClient(app)

    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health_returns_ok() -> None:
    # Cria uma sessão de teste em memória
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.database import get_db_session
    from app.models.db.base import Base

    async def create_test_session():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            yield session
        await engine.dispose()

    app = create_application()
    app.dependency_overrides[get_db_session] = create_test_session
    client = TestClient(app)

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # Limpa os overrides
    app.dependency_overrides.clear()


def test_redis_health_without_config_returns_503() -> None:
    app = create_application()
    client = TestClient(app)

    base_settings = get_settings()
    previous = base_settings.redis_url

    with patch("src.app.routers.health.get_settings", return_value=base_settings):
        base_settings.redis_url = None
        response = client.get("/health/redis")

    base_settings.redis_url = previous

    assert response.status_code == 503


def test_openai_health_returns_503_when_unavailable() -> None:
    app = create_application()
    client = TestClient(app)

    response = client.get("/health/openai")

    assert response.status_code == 503


def test_openai_health_returns_ok_when_available() -> None:
    app = create_application()
    client = TestClient(app)

    class DummyProvider:
        available = True

    with patch("src.app.routers.health.get_chat_provider", return_value=DummyProvider()):
        response = client.get("/health/openai")

    assert response.status_code == 200


def test_notion_health_requires_configuration() -> None:
    app = create_application()
    client = TestClient(app)

    response = client.get("/health/notion")

    assert response.status_code == 503


def test_notion_health_returns_ok_when_configured() -> None:
    app = create_application()
    client = TestClient(app)

    class DummyClient:
        async def close(self) -> None:
            pass

    with patch("src.app.routers.health.get_notion_client", return_value=DummyClient()):
        response = client.get("/health/notion")

    assert response.status_code == 200


def test_evolution_health_requires_configuration() -> None:
    app = create_application()
    client = TestClient(app)

    response = client.get("/health/evolution")

    assert response.status_code == 503


def test_evolution_health_returns_ok_when_configured() -> None:
    app = create_application()
    client = TestClient(app)

    class DummyClient:
        async def close(self) -> None:
            pass

    with patch("src.app.routers.health.get_evolution_client", return_value=DummyClient()):
        response = client.get("/health/evolution")

    assert response.status_code == 200
