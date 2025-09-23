# Documentação de Performance - SparkOne

## Visão Geral

Este documento descreve o sistema de profiling e monitoramento de performance implementado no SparkOne. O sistema coleta métricas detalhadas sobre queries de banco de dados, uso de recursos e gargalos de performance.

## Arquitetura do Sistema de Profiling

### Componentes Principais

1. **DatabaseProfiler** (`src/app/core/profiler.py`)
   - Profiler principal que monitora queries SQLAlchemy
   - Coleta métricas de tempo, memória e CPU
   - Detecta queries lentas automaticamente

2. **Decorators de Profiling**
   - `@profile_query`: Monitora funções individuais
   - `profile_session()`: Context manager para sessões de banco

3. **API de Profiling** (`src/app/routers/profiler.py`)
   - Endpoints REST para acessar dados de performance
   - Relatórios detalhados e análise de queries lentas

4. **Métricas Prometheus**
   - Integração com sistema de observabilidade existente
   - Métricas customizadas para profiling

## Configuração

### Variáveis de Ambiente

```bash
# Threshold para queries lentas (segundos)
PROFILER_SLOW_QUERY_THRESHOLD=0.5

# Habilitar/desabilitar profiler
PROFILER_ENABLED=true

# Tamanho máximo do histórico de queries
PROFILER_MAX_HISTORY=1000
```

### Inicialização

O profiler é inicializado automaticamente quando a aplicação inicia:

```python
from src.app.core.profiler import db_profiler

# O profiler é configurado automaticamente com event listeners
# do SQLAlchemy para capturar todas as queries
```

## Uso do Sistema de Profiling

### 1. Profiling Automático de Queries

Todas as queries executadas através do SQLAlchemy são automaticamente monitoradas:

```python
# Esta query será automaticamente profileada
async with get_db_session() as session:
    result = await session.execute(
        select(ChannelMessageORM).limit(10)
    )
```

### 2. Profiling Manual de Funções

Use o decorator `@profile_query` para monitorar funções específicas:

```python
from src.app.core.profiler import profile_query

@profile_query
async def process_complex_data(data: List[Dict]) -> ProcessedData:
    """
    Função crítica que processa grandes volumes de dados.
    Monitorada para detectar degradação de performance.
    """
    # Lógica de processamento
    return processed_data
```

### 3. Profiling de Sessões

Use o context manager `profile_session` para monitorar operações complexas:

```python
from src.app.core.profiler import profile_session

async def bulk_insert_messages(messages: List[Message]):
    async with get_db_session() as session:
        async with profile_session(session, "bulk_insert_messages"):
            for message in messages:
                session.add(ChannelMessageORM(**message.dict()))
            await session.commit()
```

## Métricas Coletadas

### Métricas de Query

- **Duração**: Tempo total de execução
- **Tipo de Query**: SELECT, INSERT, UPDATE, DELETE
- **Tabela**: Tabela principal afetada
- **Operação**: Tipo de operação SQL
- **Contagem de Linhas**: Número de linhas afetadas
- **Parâmetros**: Parâmetros da query (quando disponível)

### Métricas de Recursos

- **Uso de Memória**: Antes e depois da execução
- **CPU**: Percentual de uso durante execução
- **Stack Trace**: Para queries lentas (>500ms)

### Métricas Prometheus

```prometheus
# Duração de queries por tipo e tabela
sparkone_database_query_duration_seconds{query_type="read", table="messages", operation="SELECT"}

# Total de queries executadas
sparkone_database_queries_total{query_type="read", table="messages", operation="SELECT", status="success"}

# Queries lentas detectadas
sparkone_slow_queries_total{query_type="read", threshold="500ms"}

# Uso de recursos
sparkone_memory_usage_bytes{component="database"}
sparkone_cpu_usage_percent{component="database"}
```

## API de Profiling

### Endpoints Disponíveis

#### 1. Estatísticas Gerais
```http
GET /profiler/stats
```

Retorna estatísticas consolidadas de performance:

```json
{
  "status": "success",
  "data": {
    "enabled": true,
    "total_queries": 1250,
    "slow_queries": 15,
    "slow_query_percentage": 1.2,
    "avg_duration": 0.045,
    "max_duration": 2.341,
    "memory_usage_mb": 245.6,
    "cpu_usage_percent": 12.3,
    "queries_by_table": {
      "messages": 800,
      "tasks": 200,
      "events": 150,
      "embeddings": 100
    },
    "queries_by_operation": {
      "SELECT": 900,
      "INSERT": 250,
      "UPDATE": 80,
      "DELETE": 20
    }
  }
}
```

#### 2. Relatório Detalhado
```http
GET /profiler/report?last_n_queries=1000
```

Gera relatório completo com top queries lentas:

```json
{
  "status": "success",
  "data": {
    "total_queries": 1000,
    "slow_queries": 12,
    "slow_query_percentage": 1.2,
    "top_slow_queries": [
      {
        "query": "SELECT * FROM messages WHERE content ILIKE '%search%' ORDER BY created_at DESC",
        "duration": 2.341,
        "table": "messages",
        "operation": "SELECT",
        "memory_delta": 15.2,
        "cpu_percent": 45.6,
        "timestamp": 1703123456.789
      }
    ]
  }
}
```

#### 3. Análise de Queries Lentas
```http
GET /profiler/slow-queries?threshold=0.5&limit=20
```

Lista queries que excedem o threshold especificado:

```json
{
  "status": "success",
  "data": {
    "threshold_seconds": 0.5,
    "total_slow_queries": 15,
    "returned_queries": 15,
    "queries": [
      {
        "query": "SELECT m.*, e.embedding FROM messages m LEFT JOIN embeddings e ON m.id = e.message_id WHERE m.channel = 'whatsapp'",
        "duration": 1.234,
        "table": "messages",
        "operation": "SELECT",
        "query_type": "read",
        "memory_delta": 8.5,
        "cpu_percent": 23.4,
        "has_stack_trace": true
      }
    ]
  }
}
```

#### 4. Detalhes de Query Específica
```http
GET /profiler/query-details/123
```

Retorna detalhes completos incluindo stack trace:

```json
{
  "status": "success",
  "data": {
    "query": "SELECT * FROM messages WHERE content ILIKE '%search%'",
    "duration": 2.341,
    "table": "messages",
    "operation": "SELECT",
    "parameters": {"content": "%search%"},
    "stack_trace": [
      "File \"/app/routers/channels.py\", line 45, in search_messages",
      "File \"/app/models/repositories.py\", line 123, in search_by_content"
    ]
  }
}
```

#### 5. Controle do Profiler
```http
POST /profiler/toggle?enable=true
POST /profiler/reset
```

Habilita/desabilita profiler e limpa estatísticas.

#### 6. Health Check
```http
GET /profiler/health
```

Verifica saúde do sistema de profiling:

```json
{
  "status": "healthy",
  "enabled": true,
  "total_queries": 1250,
  "slow_queries": 15,
  "issues": []
}
```

## Queries Críticas Identificadas

### 1. Busca de Mensagens por Conteúdo

**Query**: `SELECT * FROM messages WHERE content ILIKE '%search%'`

**Problemas**:
- Scan completo da tabela
- Operação ILIKE sem índice
- Performance degrada com volume de dados

**Otimizações Recomendadas**:
```sql
-- Criar índice GIN para busca full-text
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('portuguese', content));

-- Query otimizada
SELECT * FROM messages WHERE to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', 'search');
```

### 2. Join com Embeddings

**Query**: `SELECT m.*, e.embedding FROM messages m LEFT JOIN embeddings e ON m.id = e.message_id`

**Problemas**:
- Join custoso com dados de embedding (arrays grandes)
- Transferência desnecessária de dados binários

**Otimizações Recomendadas**:
```sql
-- Separar queries: primeiro buscar mensagens, depois embeddings sob demanda
SELECT id, content, channel, created_at FROM messages WHERE conditions;

-- Buscar embeddings apenas quando necessário
SELECT embedding FROM embeddings WHERE message_id IN (ids);
```

### 3. Agregações por Canal

**Query**: `SELECT channel, COUNT(*) FROM messages GROUP BY channel`

**Problemas**:
- Scan completo para agregação
- Recalculo desnecessário de dados estáticos

**Otimizações Recomendadas**:
```sql
-- Criar índice para agregações
CREATE INDEX idx_messages_channel ON messages(channel);

-- Considerar materializar view para dados frequentemente acessados
CREATE MATERIALIZED VIEW channel_stats AS
SELECT channel, COUNT(*) as message_count, MAX(created_at) as last_message
FROM messages GROUP BY channel;
```

## Alertas de Performance

### Configuração no Prometheus

```yaml
# ops/prometheus/alerts.yml
groups:
  - name: performance-alerts
    rules:
      - alert: SlowQueryThreshold
        expr: sparkone_database_query_duration_seconds > 1.0
        for: 1m
        labels:
          severity: warning
          service: sparkone
        annotations:
          summary: "Query lenta detectada"
          description: "Query {{ $labels.operation }} na tabela {{ $labels.table }} levou {{ $value }}s"

      - alert: HighSlowQueryRate
        expr: rate(sparkone_slow_queries_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
          service: sparkone
        annotations:
          summary: "Taxa alta de queries lentas"
          description: "{{ $value }} queries lentas por segundo nos últimos 5 minutos"
```

### Dashboard Grafana

Painéis configurados em `ops/grafana/dashboard-overview.json`:

1. **Query Duration Percentiles**: P50, P95, P99 de duração de queries
2. **Slow Query Rate**: Taxa de queries lentas ao longo do tempo
3. **Memory Usage**: Uso de memória por componente
4. **Top Slow Queries**: Lista das queries mais lentas
5. **Query Distribution**: Distribuição por tipo e tabela

## Procedimentos Operacionais

### Investigação de Performance

1. **Verificar Health Check**:
   ```bash
   curl http://localhost:8000/profiler/health
   ```

2. **Analisar Queries Lentas**:
   ```bash
   curl "http://localhost:8000/profiler/slow-queries?threshold=0.5&limit=10"
   ```

3. **Gerar Relatório Completo**:
   ```bash
   curl "http://localhost:8000/profiler/report?last_n_queries=1000"
   ```

4. **Verificar Métricas Prometheus**:
   ```bash
   curl http://localhost:8000/metrics | grep sparkone_database
   ```

### Otimização de Queries

1. **Identificar Gargalos**:
   - Usar endpoint `/profiler/slow-queries`
   - Analisar stack traces para localizar origem
   - Verificar padrões de uso de recursos

2. **Implementar Otimizações**:
   - Criar índices apropriados
   - Reescrever queries problemáticas
   - Implementar cache quando apropriado

3. **Validar Melhorias**:
   - Resetar estatísticas: `POST /profiler/reset`
   - Executar testes de carga
   - Monitorar métricas por período

### Manutenção

1. **Limpeza Periódica**:
   ```python
   # Executar semanalmente
   db_profiler.reset_stats()
   ```

2. **Ajuste de Thresholds**:
   ```python
   # Ajustar baseado no perfil da aplicação
   db_profiler.slow_query_threshold = 0.3  # 300ms
   ```

3. **Monitoramento de Recursos**:
   - Verificar uso de memória do profiler
   - Ajustar tamanho do histórico se necessário

## Limitações e Considerações

### Performance Impact

- **Overhead**: ~2-5% de overhead adicional
- **Memória**: Histórico limitado a 1000 queries
- **CPU**: Event listeners adicionam processamento mínimo

### Segurança

- **Dados Sensíveis**: Parâmetros de query podem conter dados sensíveis
- **Autenticação**: Endpoints protegidos por autenticação
- **Logs**: Queries lentas são logadas (cuidado com dados sensíveis)

### Escalabilidade

- **Múltiplas Instâncias**: Cada instância mantém seu próprio histórico
- **Agregação**: Usar Prometheus para agregação entre instâncias
- **Retenção**: Configurar retenção apropriada no Prometheus

## Próximos Passos

### Melhorias Planejadas

1. **Query Plan Analysis**:
   - Integrar com EXPLAIN ANALYZE
   - Detectar queries sem índices

2. **Alertas Inteligentes**:
   - Machine learning para detectar anomalias
   - Alertas baseados em tendências

3. **Otimização Automática**:
   - Sugestões automáticas de índices
   - Cache inteligente baseado em padrões

4. **Integração com APM**:
   - Correlação com traces distribuídos
   - Análise de performance end-to-end

### Monitoramento Contínuo

1. **Revisão Semanal**:
   - Analisar top queries lentas
   - Identificar novos gargalos
   - Validar otimizações implementadas

2. **Alertas Proativos**:
   - Configurar alertas para degradação
   - Monitorar tendências de performance
   - Alertas para queries novas lentas

3. **Relatórios Mensais**:
   - Consolidar métricas de performance
   - Identificar oportunidades de otimização
   - Planejar melhorias de infraestrutura

## Referências

- [SQLAlchemy Events](https://docs.sqlalchemy.org/en/20/core/events.html)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/performance/)

---

**Última Atualização**: Dezembro 2024  
**Versão**: 1.0  
**Responsável**: Equipe de Arquitetura SparkOne