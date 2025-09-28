# Provedores de LLM Suportados pelo SparkOne

## Visão Geral

O SparkOne suporta múltiplos provedores de LLM através de uma arquitetura flexível com fallback automático. O sistema prioriza o provedor primário (OpenAI) e, em caso de falha, utiliza o provedor local configurado.

## Arquitetura de Provedores

### ChatProviderRouter
- **Localização**: `src/app/providers/chat.py`
- **Função**: Gerencia múltiplos provedores com fallback automático
- **Configuração**: Baseada em variáveis de ambiente

### Fluxo de Fallback
1. **Provedor Primário**: OpenAI (se configurado)
2. **Provedor Fallback**: LLM Local (se configurado)
3. **Erro**: Se nenhum provedor disponível

## Provedores Suportados

### 1. OpenAI (Provedor Primário)

#### Configuração
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # Opcional
OPENAI_MODEL=gpt-4o-mini
```

#### Modelos Suportados
- `gpt-4o` - Mais avançado
- `gpt-4o-mini` - Balanceado (padrão)
- `gpt-4` - Versão anterior
- `gpt-3.5-turbo` - Mais rápido e econômico

#### Características
- ✅ Alta qualidade de resposta
- ✅ Suporte a múltiplos idiomas
- ✅ Resposta rápida
- ❌ Requer chave de API paga
- ❌ Dependência de internet

### 2. LLM Local (Provedor Fallback)

#### Configuração Base
```env
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_API_KEY=  # Opcional
LOCAL_LLM_MODEL=llama3.1:8b
LLM_REQUEST_TIMEOUT=30.0
LLM_MAX_RETRIES=3
```

#### Opções de Implementação

##### A. Ollama (Recomendado)
```env
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3.1:8b
```

**Modelos Disponíveis:**
- `llama3.1:8b` - Balanceado para desenvolvimento
- `llama3.1:70b` - Alta qualidade
- `llama2:7b` - Mais leve
- `codellama:7b` - Especializado em código
- `mistral:7b` - Alternativa ao LLAMA
- `phi3:mini` - Muito leve (3.8B parâmetros)

**Instalação:**
```bash
# Windows: Baixar de https://ollama.ai/download
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama3.1:8b
```

##### B. vLLM (Produção)
```env
LOCAL_LLM_URL=http://localhost:8000
LOCAL_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
```

**Características:**
- ✅ Alta performance
- ✅ Suporte a GPU
- ✅ Otimizado para produção
- ❌ Configuração mais complexa

##### C. LiteLLM (Proxy Universal)
```env
LOCAL_LLM_URL=http://localhost:4000
LOCAL_LLM_MODEL=ollama/llama3.1:8b
```

**Características:**
- ✅ Suporte a múltiplos backends
- ✅ API unificada
- ✅ Monitoramento integrado
- ❌ Camada adicional de abstração

##### D. Text Generation WebUI
```env
LOCAL_LLM_URL=http://localhost:5000
LOCAL_LLM_MODEL=llama-2-7b-chat
```

**Características:**
- ✅ Interface web amigável
- ✅ Suporte a múltiplos modelos
- ✅ Configuração via interface
- ❌ Mais pesado

### 3. Provedores Compatíveis com OpenAI

#### Azure OpenAI
```env
OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_MODEL=gpt-4
```

#### Anthropic Claude (via proxy)
```env
LOCAL_LLM_URL=http://localhost:8080  # LiteLLM proxy
LOCAL_LLM_MODEL=claude-3-sonnet
```

#### Google Gemini (via proxy)
```env
LOCAL_LLM_URL=http://localhost:8080  # LiteLLM proxy
LOCAL_LLM_MODEL=gemini-pro
```

## Configuração de Embeddings

### OpenAI Embeddings
```env
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

### Local Embeddings
```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

## Monitoramento e Logs

### Logs Estruturados
O sistema gera logs detalhados sobre o uso dos provedores:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "chat_provider_primary_failed",
  "provider": "openai",
  "fallback": "local_llm",
  "model": "llama3.1:8b",
  "error": "API key invalid"
}
```

### Métricas Disponíveis
- Tempo de resposta por provedor
- Taxa de sucesso/falha
- Uso de fallback
- Tokens consumidos

## Cenários de Uso

### Desenvolvimento Local
```env
# Usar apenas LLM local
OPENAI_API_KEY=
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3.1:8b
```

### Produção com Fallback
```env
# OpenAI primário, local como backup
OPENAI_API_KEY=sk-real-key
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3.1:70b
```

### Apenas OpenAI
```env
# Sem fallback local
OPENAI_API_KEY=sk-real-key
LOCAL_LLM_URL=
```

## Troubleshooting

### Problema: "No chat providers configured"
**Causa**: Nenhum provedor configurado corretamente
**Solução**: Configurar pelo menos um provedor (OpenAI ou local)

### Problema: Respostas lentas
**Causa**: Modelo muito grande ou hardware insuficiente
**Solução**: 
- Usar modelo menor (7b ao invés de 70b)
- Aumentar timeout
- Verificar recursos de hardware

### Problema: Qualidade baixa das respostas
**Causa**: Modelo inadequado para o caso de uso
**Solução**:
- Experimentar diferentes modelos
- Ajustar parâmetros de geração
- Considerar fine-tuning

### Problema: Falhas de conexão
**Causa**: Serviço LLM não está rodando
**Solução**:
- Verificar se Ollama/vLLM está ativo
- Testar conectividade com curl
- Verificar logs do serviço

## Scripts de Teste

### Teste Rápido
```bash
python test_llama_connection.py
```

### Teste Manual
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Olá, como você está?",
  "stream": false
}'
```

## Recomendações

### Para Desenvolvimento
- **Modelo**: `llama3.1:8b` via Ollama
- **Configuração**: Local apenas
- **Hardware**: 16GB RAM mínimo

### Para Produção
- **Primário**: OpenAI `gpt-4o-mini`
- **Fallback**: `llama3.1:70b` via vLLM
- **Hardware**: GPU recomendada para local

### Para Testes
- **Modelo**: `phi3:mini` (mais leve)
- **Configuração**: Ollama local
- **Hardware**: 8GB RAM suficiente