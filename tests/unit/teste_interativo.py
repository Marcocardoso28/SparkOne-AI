#!/usr/bin/env python3
"""Teste interativo do agente SparkOne - Você pode digitar suas próprias mensagens!"""

import sys
import os
import asyncio

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def testar_interativo():
    """Teste interativo onde você pode digitar suas próprias mensagens."""
    print("🤖 Teste Interativo do Agente SparkOne")
    print("=" * 50)
    print("💡 Digite suas mensagens e veja como o agente responde!")
    print("💡 Digite 'sair' para terminar o teste.")
    print("=" * 50)

    try:
        from app.agents.agno import AgnoBridge
        from app.providers.chat import ChatProviderRouter
        from app.models.schemas import ChannelMessage, Channel
        from app.config import get_settings

        # Configurar o agente
        settings = get_settings()
        chat_provider = ChatProviderRouter(settings)
        agno = AgnoBridge(chat_provider)

        print("✅ Agente configurado e pronto!")
        print()

        while True:
            # Receber mensagem do usuário
            mensagem = input("👤 Sua mensagem: ").strip()

            if mensagem.lower() in ['sair', 'exit', 'quit']:
                print("👋 Até logo!")
                break

            if not mensagem:
                print("⚠️  Digite uma mensagem válida.")
                continue

            print("🤖 Processando...")

            try:
                # Criar mensagem
                msg = ChannelMessage(
                    content=mensagem,
                    channel=Channel.WEB,
                    sender="marco"
                )

                # Classificar
                categoria, resumo = await agno.classify(msg)
                print(f"📊 Categoria: {categoria.value}")
                print(f"📋 Resumo: {resumo}")

                # Gerar resposta
                resposta = await agno.respond(category=categoria, summary=resumo)
                print(f"🤖 SparkOne: {resposta}")

            except Exception as e:
                print(f"❌ Erro: {e}")

            print("-" * 50)

        return True

    except Exception as e:
        print(f"❌ Erro ao configurar o agente: {e}")
        return False


async def main():
    """Executa o teste interativo."""
    await testar_interativo()

if __name__ == "__main__":
    asyncio.run(main())

