"""Alembic environment configuration."""

from __future__ import annotations

import sys
from logging.config import fileConfig
import os
import asyncio
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ensure 'src' is on sys.path so we can import 'app.*' from src layout
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import all models so they are registered with Base.metadata (single source of truth)
from app.models.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

metadata = Base.metadata


def _get_urls() -> tuple[str, str]:
    """Return SQLAlchemy sync URL for Alembic.

    Prefer environment variables (ALEMBIC_DATABASE_URL or DATABASE_URL).
    If an async driver is used (e.g., postgresql+asyncpg), convert to a sync
    driver suitable for Alembic (e.g., postgresql+psycopg2 or plain postgresql).
    """
    config_url = config.get_main_option("sqlalchemy.url")
    env_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL") or config_url

    if not env_url:
        raise RuntimeError("No database URL configured for Alembic.")

    # Convert common async URLs to sync for Alembic migrations
    sync_url = env_url
    if env_url.startswith("postgresql+asyncpg"):
        sync_url = env_url.replace("postgresql+asyncpg", "postgresql")
    if env_url.startswith("sqlite+aiosqlite"):
        sync_url = env_url.replace("sqlite+aiosqlite", "sqlite")
    return env_url, sync_url

def run_migrations_offline() -> None:
    env_url, _ = _get_urls()
    context.configure(url=env_url, target_metadata=metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    env_url, sync_url = _get_urls()

    # If using async driver, run migrations with async engine
    if env_url.startswith("postgresql+asyncpg") or env_url.startswith("sqlite+aiosqlite"):
        async def _run_async() -> None:
            config.set_main_option("sqlalchemy.url", env_url)
            connectable = async_engine_from_config(
                config.get_section(config.config_ini_section, {}),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )

            async with connectable.connect() as connection:
                def do_migrations(connection_):
                    context.configure(connection=connection_, target_metadata=metadata)
                    with context.begin_transaction():
                        context.run_migrations()

                await connection.run_sync(do_migrations)

            await connectable.dispose()

        asyncio.run(_run_async())
        return

    # Otherwise, use sync engine
    config.set_main_option("sqlalchemy.url", sync_url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)

        with context.begin_transaction():
            context.run_migrations()


def main() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


if __name__ == "__main__":  # pragma: no cover - alembic script entry point
    main()
