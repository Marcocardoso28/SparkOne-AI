# Documentação da API SparkOne

## Visão Geral

A API do SparkOne é uma interface RESTful que permite integração com o sistema de assistente pessoal inteligente. A API processa mensagens de múltiplos canais (WhatsApp, Web, Google Sheets) e as transforma em ações estruturadas.

## Especificação OpenAPI

A especificação completa está disponível em [`openapi.yaml`](../openapi.yaml) na raiz do projeto.

## Autenticação

### Interface Web
```http
Authorization: Basic <base64(username:password)>
```

### Webhooks
Alguns endpoints de webhook podem usar validação por token quando configurado.

## Endpoints Principais

### 1. Health Checks

#### Verificação Geral de Saúde
```http
GET /health
```

**Resposta de Sucesso:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0"
}
```

**Resposta de Erro:**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "error": "Database connection failed"
}
```

#### Verificação do Banco de Dados
```http
GET /health/database
```

**Resposta:**
```json
{
  "status": "healthy",
  "database": "postgresql",
  "latency_ms": 12,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Ingestão de Mensagens

#### Ingestão Direta
```http
POST /ingest
Content-Type: application/json

{
  "channel": "whatsapp",
  "sender": "5511999999999",
  "content": "Preciso revisar o relatório de vendas até sexta-feira",
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "message_id": "msg_12345",
    "chat_id": "5511999999999@s.whatsapp.net"
  }
}
```

**Resposta:**
```json
{
  "status": "accepted",
  "channel": "whatsapp",
  "message_id": "msg_12345"
}
```

#### Ingestão por Canal Específico
```http
POST /channels/whatsapp
Content-Type: application/json

{
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "msg_12345"
    },
    "message": {
      "conversation": "Criar tarefa para revisar contratos"
    },
    "messageTimestamp": 1705312200
  }
}
```

### 3. Gerenciamento de Tarefas

#### Listar Tarefas
```http
GET /tasks?status=pending&limit=10&offset=0
```

**Resposta:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Revisar relatório mensal",
      "description": "Analisar métricas de performance",
      "status": "pending",
      "priority": "medium",
      "created_at": "2024-01-15T10:30:00Z",
      "due_date": "2024-01-19T17:00:00Z"
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0
}
```

#### Atualizar Status de Tarefa
```http
PATCH /tasks/1/status
Content-Type: application/json

{
  "status": "completed"
}
```

### 4. Eventos do Calendário

#### Listar Eventos
```http
GET /events?upcoming_only=true&limit=5
```

**Resposta:**
```json
[
  {
    "id": 1,
    "title": "Reunião de planejamento",
    "status": "scheduled",
    "start_at": "2024-01-18T14:00:00Z",
    "end_at": "2024-01-18T15:00:00Z",
    "location": "Sala de conferências"
  }
]
```

### 5. Briefs e Resumos

#### Brief Estruturado
```http
GET /brief/structured
```

**Resposta:**
```json
{
  "summary": {
    "pending_tasks": 5,
    "upcoming_events": 3,
    "recent_messages": 12
  },
  "tasks": [
    {
      "title": "Revisar relatório",
      "priority": "high",
      "due_date": "2024-01-19T17:00:00Z"
    }
  ],
  "events": [
    {
      "title": "Reunião de equipe",
      "start_at": "2024-01-16T09:00:00Z",
      "location": "Sala 201"
    }
  ],
  "insights": [
    "Você tem 3 tarefas com prazo para esta semana",
    "Próxima reunião em 2 dias"
  ]
}
```

#### Brief Textual
```http
GET /brief/text
```

**Resposta:**
```json
{
  "brief": "Bom dia! Aqui está seu resumo de hoje:\n\n📋 Tarefas Pendentes (5):\n• Revisar relatório mensal (prazo: sexta-feira)\n• Preparar apresentação (prazo: amanhã)\n\n📅 Próximos Eventos (3):\n• Reunião de equipe - Amanhã às 09:00\n• Apresentação para cliente - Quinta às 10:00\n\n💡 Insights:\n• Você tem 3 tarefas com prazo para esta semana\n• Considere priorizar a apresentação que vence amanhã"
}
```

### 6. Webhooks

#### Webhook do WhatsApp
```http
POST /webhooks/whatsapp
Content-Type: application/json

{
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "msg_12345"
    },
    "message": {
      "conversation": "Lembrar de comprar ingredientes para o jantar"
    },
    "messageTimestamp": 1705312200
  }
}
```

### 7. Sistema de Alertas

#### Webhook do Alertmanager
```http
POST /alerts/alertmanager
Content-Type: application/json

{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "NotionSyncFailures",
        "severity": "warning"
      },
      "annotations": {
        "summary": "Falha em sincronizações com Notion",
        "description": "Detectado ao menos 1 erro no Notion nos últimos 15 minutos"
      },
      "startsAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 8. Métricas e Observabilidade

#### Métricas Prometheus
```http
GET /metrics
```

**Resposta (formato Prometheus):**
```
# HELP sparkone_http_requests_total Total HTTP requests
# TYPE sparkone_http_requests_total counter
sparkone_http_requests_total{method="GET",path="/health",status="200"} 42
sparkone_http_requests_total{method="POST",path="/ingest",status="202"} 15

# HELP sparkone_http_request_latency_seconds Latency of HTTP requests
# TYPE sparkone_http_request_latency_seconds histogram
sparkone_http_request_latency_seconds_bucket{le="0.05"} 30
sparkone_http_request_latency_seconds_bucket{le="0.1"} 45
sparkone_http_request_latency_seconds_bucket{le="+Inf"} 57
sparkone_http_request_latency_seconds_sum 2.1
sparkone_http_request_latency_seconds_count 57
```

## Códigos de Status HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Operação bem-sucedida |
| 202 | Accepted | Mensagem aceita para processamento assíncrono |
| 400 | Bad Request | Payload inválido ou parâmetros incorretos |
| 401 | Unauthorized | Autenticação necessária |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Dados válidos mas não processáveis |
| 500 | Internal Server Error | Erro interno do servidor |
| 503 | Service Unavailable | Serviço temporariamente indisponível |

## Rate Limiting

- **Desenvolvimento**: 120 requests/minuto
- **Produção**: 60 requests/minuto

Quando o limite é excedido, a API retorna status `429 Too Many Requests`.

## Exemplos de Integração

### Python com requests
```python
import requests
import json

# Configuração
BASE_URL = "http://localhost:8000"
AUTH = ("username", "password")

# Enviar mensagem para ingestão
def send_message(channel, sender, content):
    payload = {
        "channel": channel,
        "sender": sender,
        "content": content,
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/ingest",
        json=payload,
        auth=AUTH
    )
    
    return response.json()

# Listar tarefas pendentes
def get_pending_tasks():
    response = requests.get(
        f"{BASE_URL}/tasks?status=pending",
        auth=AUTH
    )
    
    return response.json()

# Obter brief do dia
def get_daily_brief():
    response = requests.get(
        f"{BASE_URL}/brief/text",
        auth=AUTH
    )
    
    return response.json()["brief"]
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8000',
  auth: {
    username: 'username',
    password: 'password'
  }
});

// Enviar mensagem
async function sendMessage(channel, sender, content) {
  try {
    const response = await api.post('/ingest', {
      channel,
      sender,
      content,
      timestamp: new Date().toISOString(),
      metadata: {}
    });
    
    return response.data;
  } catch (error) {
    console.error('Erro ao enviar mensagem:', error.response.data);
    throw error;
  }
}

// Listar eventos próximos
async function getUpcomingEvents() {
  try {
    const response = await api.get('/events?upcoming_only=true&limit=10');
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar eventos:', error.response.data);
    throw error;
  }
}
```

### cURL
```bash
# Verificar saúde da API
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"

# Enviar mensagem via WhatsApp
curl -X POST "http://localhost:8000/ingest" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -u "username:password" \
  -d '{
    "channel": "whatsapp",
    "sender": "5511999999999",
    "content": "Criar tarefa para revisar documentos",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "message_id": "msg_12345"
    }
  }'

# Listar tarefas com filtro
curl -X GET "http://localhost:8000/tasks?status=pending&limit=5" \
  -H "accept: application/json" \
  -u "username:password"

# Atualizar status de tarefa
curl -X PATCH "http://localhost:8000/tasks/1/status" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -u "username:password" \
  -d '{"status": "completed"}'
```

## Tratamento de Erros

### Estrutura de Erro Padrão
```json
{
  "detail": "Descrição do erro",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Códigos de Erro Comuns

| Código | Descrição |
|--------|-----------|
| `VALIDATION_ERROR` | Dados de entrada inválidos |
| `CHANNEL_NOT_FOUND` | Canal especificado não existe |
| `MESSAGE_TOO_LONG` | Conteúdo da mensagem excede limite |
| `RATE_LIMIT_EXCEEDED` | Limite de requisições excedido |
| `TASK_NOT_FOUND` | Tarefa não encontrada |
| `INVALID_STATUS` | Status inválido para transição |

## Monitoramento e Observabilidade

### Métricas Disponíveis

- `sparkone_http_requests_total`: Total de requisições HTTP
- `sparkone_http_request_latency_seconds`: Latência das requisições
- `sparkone_notion_sync_failures_total`: Falhas de sincronização com Notion
- `sparkone_sheets_sync_failures_total`: Falhas de sincronização com Google Sheets
- `sparkone_whatsapp_notifications_total`: Total de notificações WhatsApp

### Health Checks

A API expõe múltiplos endpoints de health check:

- `/health`: Status geral da aplicação
- `/health/database`: Status do PostgreSQL
- `/health/redis`: Status do Redis

## Versionamento

A API segue versionamento semântico (SemVer). A versão atual é `0.1.0`.

Mudanças breaking serão comunicadas com antecedência e uma nova versão major será lançada.

## Suporte

Para dúvidas sobre a API, consulte:

1. Esta documentação
2. Especificação OpenAPI em [`openapi.yaml`](../openapi.yaml)
3. Código-fonte dos endpoints em [`src/app/routers/`](../src/app/routers/)
4. Testes de exemplo em [`src/app/tests/`](../src/app/tests/)

## Changelog

### v0.1.0 (2024-01-15)
- Versão inicial da API
- Endpoints de ingestão, tarefas, eventos e briefs
- Sistema de health checks
- Integração com Prometheus/Grafana
- Webhooks para WhatsApp e Alertmanager