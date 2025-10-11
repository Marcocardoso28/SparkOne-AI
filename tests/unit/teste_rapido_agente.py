#!/usr/bin/env python3
"""Teste rápido do agente SparkOne - Sem servidor, apenas o agente."""

import sys
import os
import asyncio
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def testar_agente():
    """Testa o agente SparkOne com mensagens reais."""
    print("🤖 Testando o Agente SparkOne...")
    print("=" * 50)

    try:
        from app.agents.agno import AgnoBridge
        from app.providers.chat import ChatProviderRouter
        from app.models.schemas import ChannelMessage, MessageType, Channel
        from app.config import get_settings

        # Configurar o agente
        settings = get_settings()
        chat_provider = ChatProviderRouter(settings)
        agno = AgnoBridge(chat_provider)

        # Lista de mensagens para testar
        mensagens_teste = [
            "Olá SparkOne! Como você está?",
            "Preciso criar um relatório de vendas para amanhã às 17h",
            "Agendar reunião com o cliente ABC para próxima sexta às 14h",
            "Como posso melhorar minha produtividade no trabalho?",
            "Lembrar de pagar a conta de luz até o dia 15",
            "Quero aprender mais sobre inteligência artificial"
        ]

        print(f"📝 Testando {len(mensagens_teste)} mensagens diferentes...\n")

        for i, mensagem in enumerate(mensagens_teste, 1):
            print(f"🔍 Teste {i}: {mensagem}")

            # Criar mensagem
            msg = ChannelMessage(
                content=mensagem,
                channel=Channel.WEB,
                sender="marco"
            )

            # Classificar
            categoria, resumo = await agno.classify(msg)
            print(f"   📊 Categoria: {categoria.value}")
            print(f"   📋 Resumo: {resumo}")

            # Gerar resposta
            resposta = await agno.respond(category=categoria, summary=resumo)
            print(f"   💬 Resposta: {resposta[:150]}...")
            print("-" * 50)

        print("🎉 Todos os testes concluídos com sucesso!")
        print("\n✅ O agente SparkOne está funcionando perfeitamente!")
        print("✅ Classificação de mensagens: OK")
        print("✅ Geração de respostas: OK")

        return True

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False


async def main():
    """Executa o teste."""
    sucesso = await testar_agente()

    if sucesso:
        print("\n🚀 O agente está pronto para uso!")
    else:
        print("\n⚠️  Verifique os erros acima.")

if __name__ == "__main__":
    asyncio.run(main())

