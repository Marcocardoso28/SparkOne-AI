"""Cria o schema SQLite local utilizando os modelos oficiais."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from src.app.models.db import events, knowledge, memory, message, repositories, sheets, tasks, vector  # noqa: F401
from src.app.models.db.base import Base

LATEST_REVISION = "9876c53d37d2"
SQLITE_URL = "sqlite:///sparkone.db"


def create_sqlite_tables() -> None:
    """Sincroniza o banco SQLite local com o schema oficial."""

    db_path = Path("sparkone.db")
    if db_path.exists() and db_path.stat().st_size == 0:
        db_path.unlink()
        print("🗑️ Removido banco vazio")

    engine = create_engine(SQLITE_URL)
    print("🚀 Criando tabelas SQLite a partir dos modelos...")
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)"
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": LATEST_REVISION},
        )

    size = db_path.stat().st_size if db_path.exists() else 0
    print(f"✅ Schema sincronizado (revision={LATEST_REVISION})")
    print(f"📊 Tamanho do banco: {size} bytes")


if __name__ == "__main__":
    create_sqlite_tables()
