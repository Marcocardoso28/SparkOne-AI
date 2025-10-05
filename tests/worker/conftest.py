import pytest
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, Table, Text, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings


def _create_worker_tables(sync_conn) -> None:
    metadata = MetaData()

    Table(
        "worker_dlq",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("job_name", Text, nullable=False),
        Column("payload", Text, nullable=False, server_default=text("'{}'")),
        Column("error_message", Text, nullable=False),
        Column("scheduled_for", DateTime(timezone=False)),
        Column("retry_count", Integer, nullable=False, server_default=text("0")),
        Column("created_at", DateTime(timezone=False), server_default=text("CURRENT_TIMESTAMP")),
        Column("processed_at", DateTime(timezone=False)),
    )

    Table(
        "worker_job_events",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("job_name", Text, nullable=False),
        Column("status", Text, nullable=False),
        Column("scheduled_at", DateTime(timezone=False)),
        Column("started_at", DateTime(timezone=False), nullable=False),
        Column("finished_at", DateTime(timezone=False), nullable=False),
        Column("runtime_seconds", Float, nullable=False),
        Column("payload", Text, nullable=False, server_default=text("'{}'")),
        Column("error_message", Text),
        Column("created_at", DateTime(timezone=False), server_default=text("CURRENT_TIMESTAMP")),
    )

    metadata.create_all(sync_conn)


@pytest.fixture
async def sqlite_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_worker_tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture
def worker_settings() -> Settings:
    return Settings(
        evolution_api_base_url="http://localhost:8000",
        evolution_api_key="TOKEN_PLACEHOLDER",
        whatsapp_notify_numbers="+551199999999,+551198888888",
        fallback_email="ops@example.com",
        smtp_host="smtp.test",
        smtp_port=1025,
        smtp_username=None,
        smtp_password=None,
    )
