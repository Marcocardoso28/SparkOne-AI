"""Script para inicializar o banco de dados e criar um usuário de teste."""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Importar os modelos
from src.app.models.db.base import Base
from src.app.models.db.user import User
from src.app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_database():
    """Criar todas as tabelas e um usuário de teste."""
    settings = get_settings()

    # Criar engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Criar todas as tabelas
    async with engine.begin() as conn:
        print("Criando tabelas...")
        await conn.run_sync(Base.metadata.create_all)
        print("[OK] Tabelas criadas com sucesso!")

    # Criar usuário de teste
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Verificar se já existe um usuário
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "teste@teste.com"))
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            print("Criando usuario de teste...")
            test_user = User(
                email="teste@teste.com",
                password_hash=pwd_context.hash("teste123"),
                is_active=True,
                is_verified=True
            )
            session.add(test_user)
            await session.commit()
            print("[OK] Usuario de teste criado:")
            print("   Email: teste@teste.com")
            print("   Senha: teste123")
        else:
            print("[AVISO] Usuario de teste ja existe")

    await engine.dispose()
    print("\n[OK] Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    asyncio.run(init_database())
