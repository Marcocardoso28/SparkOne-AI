"""Alembic environment configuration."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure project root is on sys.path so we can import 'src.*'
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import all models so they are registered with Base.metadata
from src.app.models.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
