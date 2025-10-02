"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

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

        # Configurações específicas por tipo de banco
        if "sqlite" in settings.database_url:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "pool_pre_ping": True,
                "pool_recycle": -1,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,  # Timeout de 30 segundos para evitar locks
                },
            })
        elif "postgresql" in settings.database_url:
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

        _engine = create_async_engine(settings.database_url, **engine_kwargs)

        # Para SQLite, configurar WAL mode para melhor concorrência
        if "sqlite" in settings.database_url:
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
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""

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
