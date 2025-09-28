#!/usr/bin/env python3
"""
Script de teste para validar conexão com LLM local (LLAMA via Ollama)
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Adicionar src ao path para importar módulos do SparkOne
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.config import get_settings
from src.app.providers.chat import ChatProviderRouter


async def test_ollama_direct():
    """Testa conexão direta com Ollama"""
    print("🔍 Testando conexão direta com Ollama...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Testar se Ollama está rodando
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json()
                print("✅ Ollama está rodando!")
                print(f"📋 Modelos disponíveis: {[m['name'] for m in models.get('models', [])]}")
                return True
            else:
                print(f"❌ Ollama respondeu com status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Ollama: {e}")
        return False


async def test_ollama_generate():
    """Testa geração de texto com Ollama"""
    print("\n🧠 Testando geração de texto com Ollama...")
    
    settings = get_settings()
    model = settings.local_llm_model
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "prompt": "Olá! Você pode me responder em português?",
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 100
                }
            }
            
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Modelo {model} respondeu:")
                print(f"💬 Resposta: {result.get('response', 'Sem resposta')}")
                return True
            else:
                print(f"❌ Erro na geração: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro na geração de texto: {e}")
        return False


async def test_sparkone_chat_provider():
    """Testa o ChatProviderRouter do SparkOne"""
    print("\n🚀 Testando ChatProviderRouter do SparkOne...")
    
    try:
        settings = get_settings()
        chat_router = ChatProviderRouter(settings)
        
        if not chat_router.available:
            print("❌ Nenhum provedor de chat disponível")
            return False
        
        print("✅ ChatProviderRouter inicializado")
        
        # Testar geração
        messages = [
            {"role": "system", "content": "Você é um assistente útil que responde em português."},
            {"role": "user", "content": "Olá! Como você está?"}
        ]
        
        response = await chat_router.generate(messages)
        print(f"💬 Resposta do SparkOne: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no ChatProviderRouter: {e}")
        return False


async def test_ingestion_flow():
    """Testa o fluxo completo de ingestão com LLM local"""
    print("\n📥 Testando fluxo de ingestão completo...")
    
    try:
        # Simular uma requisição para o endpoint de ingestão
        payload = {
            "content": "Olá SparkOne! Você está usando LLAMA?",
            "user_id": "test_user",
            "session_id": "test_session",
            "metadata": {"test": True}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/ingest",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Ingestão bem-sucedida!")
                print(f"📄 Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ Erro na ingestão: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste de ingestão: {e}")
        return False


def check_environment():
    """Verifica configurações de ambiente"""
    print("🔧 Verificando configurações de ambiente...")
    
    load_dotenv()
    settings = get_settings()
    
    print(f"📍 LOCAL_LLM_URL: {settings.local_llm_url}")
    print(f"🤖 LOCAL_LLM_MODEL: {settings.local_llm_model}")
    print(f"🔑 OPENAI_API_KEY: {'Configurada' if settings.openai_api_key and settings.openai_api_key != 'changeme' else 'Não configurada'}")
    print(f"🎯 EMBEDDING_PROVIDER: {settings.embedding_provider}")
    
    if not settings.local_llm_url:
        print("⚠️  LOCAL_LLM_URL não está configurada!")
        return False
    
    return True


async def main():
    """Função principal de teste"""
    print("🧪 Iniciando testes de conexão LLAMA com SparkOne\n")
    
    # Verificar ambiente
    if not check_environment():
        print("\n❌ Configuração de ambiente inválida!")
        return
    
    # Testes sequenciais
    tests = [
        ("Conexão Ollama", test_ollama_direct),
        ("Geração Ollama", test_ollama_generate),
        ("ChatProvider SparkOne", test_sparkone_chat_provider),
        ("Fluxo Ingestão", test_ingestion_flow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Executando: {test_name}")
        print('='*50)
        
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results[test_name] = False
    
    # Resumo dos resultados
    print(f"\n{'='*50}")
    print("📊 RESUMO DOS TESTES")
    print('='*50)
    
    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Resultado: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 Todos os testes passaram! LLAMA está configurado corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Verifique a configuração.")


if __name__ == "__main__":
    asyncio.run(main())