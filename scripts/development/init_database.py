#!/usr/bin/env python3
"""Script para inicializar o banco de dados do SparkOne."""

import sys
import os
import asyncio

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    print("=" * 60)
    print("  INICIALIZANDO BANCO DE DADOS SPARKONE")
    print("=" * 60)

    try:
        from app.core.database import get_engine
        from app.models.db.base import Base
        from sqlalchemy import text

        print("\n[1/3] Importando modelos...")
        # Import all models to register them with Base
        from app.models.db import (
            ChannelMessageORM,
            User,
            TaskRecord,
            EventRecord,
            ConversationMessage,
            KnowledgeDocumentORM,
            KnowledgeChunkORM,
            MessageEmbeddingORM,
            SheetsSyncStateORM,
        )
        print("  > Modelos importados com sucesso")

        # Get engine
        engine = get_engine()

        print("\n[2/3] Criando tabelas no banco de dados...")
        async with engine.begin() as conn:
            # Criar todas as tabelas
            await conn.run_sync(Base.metadata.create_all)
        print("  > Tabelas criadas com sucesso")

        print("\n[3/3] Verificando tabelas criadas...")
        async with engine.connect() as conn:
            # Verificar tabelas no SQLite
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result]

            print(f"  > Total de tabelas: {len(tables)}")
            for table in sorted(tables):
                print(f"    - {table}")

        print("\n" + "=" * 60)
        print("  ✓ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        print("\nVocê pode agora usar a aplicação normalmente.")
        print("Execute: uvicorn src.app.main:app --reload\n")

        return True

    except Exception as e:
        print(f"\n[X] ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(init_db())
    sys.exit(0 if success else 1)
