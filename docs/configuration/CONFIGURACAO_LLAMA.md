# Configuração LLAMA com SparkOne

## Opções de Configuração para LLM Local

### 1. Usando Ollama (Recomendado)

#### Instalação do Ollama
```bash
# Windows: Baixar de https://ollama.ai/download
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh
```

#### Baixar Modelos LLAMA
```bash
# LLAMA 3.1 8B (recomendado para desenvolvimento)
ollama pull llama3.1:8b

# LLAMA 2 7B (alternativa mais leve)
ollama pull llama2:7b

# LLAMA 3.1 70B (para produção, requer mais recursos)
ollama pull llama3.1:70b
```

#### Configuração no .env
```env
# Desabilitar OpenAI (opcional)
OPENAI_API_KEY=

# Configurar LLM Local
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_API_KEY=
LOCAL_LLM_MODEL=llama3.1:8b

# Configurar embeddings locais (opcional)
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

### 2. Usando vLLM (Para Produção)

#### Configuração no .env
```env
LOCAL_LLM_URL=http://localhost:8000
LOCAL_LLM_API_KEY=your-api-key
LOCAL_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
```

### 3. Usando LiteLLM (Proxy Universal)

#### Configuração no .env
```env
LOCAL_LLM_URL=http://localhost:4000
LOCAL_LLM_API_KEY=sk-1234
LOCAL_LLM_MODEL=ollama/llama3.1:8b
```

## Modelos Suportados

### LLAMA 3.1 (Recomendado)
- `llama3.1:8b` - Balanceado para desenvolvimento
- `llama3.1:70b` - Melhor qualidade, mais recursos
- `llama3.1:405b` - Estado da arte, requer cluster

### LLAMA 2
- `llama2:7b` - Mais leve, boa para testes
- `llama2:13b` - Melhor qualidade
- `llama2:70b` - Produção

### Code Llama (Para Código)
- `codellama:7b` - Especializado em código
- `codellama:13b` - Melhor para desenvolvimento
- `codellama:34b` - Produção de código

## Configurações de Performance

### Timeout e Retries
```env
# Timeout para requisições LLM (segundos)
LLM_REQUEST_TIMEOUT=30.0

# Número máximo de tentativas
LLM_MAX_RETRIES=3
```

### Parâmetros de Geração
Os parâmetros são configurados no código:
- **Temperature**: 0.2 (para respostas consistentes)
- **Max Tokens**: Automático baseado no modelo
- **Top P**: Padrão do modelo

## Testando a Configuração

### 1. Verificar se Ollama está rodando
```bash
curl http://localhost:11434/api/tags
```

### 2. Testar modelo específico
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Olá, como você está?",
  "stream": false
}'
```

### 3. Verificar logs do SparkOne
```bash
# Logs mostrarão qual provedor está sendo usado
tail -f logs/sparkone.log
```

## Troubleshooting

### Problema: "No chat providers configured"
- Verificar se `LOCAL_LLM_URL` está configurada
- Confirmar se Ollama está rodando na porta 11434

### Problema: "Connection refused"
- Verificar se o serviço LLM está ativo
- Testar conectividade com curl

### Problema: Respostas lentas
- Considerar modelo menor (7b ao invés de 70b)
- Aumentar `LLM_REQUEST_TIMEOUT`
- Verificar recursos de hardware (RAM/GPU)

### Problema: Qualidade das respostas
- Experimentar diferentes modelos
- Ajustar temperature no código se necessário
- Considerar fine-tuning para domínio específico

## Monitoramento

### Métricas Disponíveis
- Tempo de resposta por modelo
- Taxa de sucesso/falha
- Uso de recursos

### Logs Estruturados
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "chat_provider_primary_failed",
  "provider": "openai",
  "fallback": "local_llm",
  "model": "llama3.1:8b"
}
```