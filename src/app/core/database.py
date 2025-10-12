"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import os
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return (and cache) the global async engine."""

    global _engine
    if _engine is None:
        settings = get_settings()

        # Configurações específicas para SQLite para evitar database locks
        engine_kwargs = {
            "echo": settings.debug,
            "future": True,
        }

        # Permite fallback automático para SQLite em ambiente de testes
        db_url = settings.database_url
        if os.getenv("PYTEST_CURRENT_TEST") and "sqlite" not in db_url:
            db_url = "sqlite+aiosqlite:///:memory:"

        # Configurações específicas por tipo de banco
        if "sqlite" in db_url:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "pool_pre_ping": True,
                "pool_recycle": -1,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,  # Timeout de 30 segundos para evitar locks
                },
            })
        elif "postgresql" in db_url:
            # Configurações para PostgreSQL
            engine_kwargs.update({
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # 1 hora
                "pool_size": 10,
                "max_overflow": 20,
                "connect_args": {
                    "command_timeout": 30,
                },
            })

        _engine = create_async_engine(db_url, **engine_kwargs)

        # Para SQLite, configurar WAL mode para melhor concorrência
        if "sqlite" in db_url:
            from sqlalchemy import event, text

            @event.listens_for(_engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                """Configura pragmas do SQLite para melhor performance e concorrência."""
                cursor = dbapi_connection.cursor()
                # WAL mode para melhor concorrência
                cursor.execute("PRAGMA journal_mode=WAL")
                # Timeout para operações de lock
                cursor.execute("PRAGMA busy_timeout=30000")  # 30 segundos
                # Sincronização normal (balance entre performance e segurança)
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Cache size otimizado
                cursor.execute("PRAGMA cache_size=10000")
                # Temp store em memória
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the global engine."""

    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        # Ensure schema exists in test mode with SQLite, even when using direct factories
        try:
            import os
            if os.getenv("PYTEST_CURRENT_TEST") and engine.dialect.name == "sqlite":
                from app.models.db.base import Base

                async def _init_schema() -> None:
                    async with engine.begin() as conn:  # type: ignore[attr-defined]
                        await conn.run_sync(Base.metadata.create_all)

                import asyncio as _asyncio

                # Run immediately if an event loop is present; otherwise, skip silently
                try:
                    loop = _asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(_init_schema())
                    else:
                        loop.run_until_complete(_init_schema())
                except RuntimeError:
                    # No running loop; best-effort schema creation will happen on first session use via get_db_session
                    pass
        except Exception:
            pass

        _session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""
    # Ensure schema exists for SQLite during tests (when lifespan may be skipped)
    try:
        import os
        if os.getenv("PYTEST_CURRENT_TEST"):
            engine = get_engine()
            if engine.dialect.name == "sqlite":
                from app.models.db.base import Base

                async with engine.begin() as conn:  # type: ignore[attr-defined]
                    await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass

    session = get_session_factory()()
    try:
        yield session
        # Garantir que a sessão seja commitada se houver mudanças pendentes
        if session.dirty or session.new or session.deleted:
            await session.commit()
    except Exception:
        # Em caso de erro, fazer rollback
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = ["get_engine", "get_session_factory", "get_db_session"]
