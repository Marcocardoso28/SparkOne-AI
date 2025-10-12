# SparkOne - Infraestrutura e Observabilidade

**Versão:** v1.1.0  
**Data:** Janeiro 2025  

---

## 🏗️ Arquitetura de Infraestrutura

### Stack de Produção
- **Aplicação:** FastAPI + Python 3.11+
- **Banco de Dados:** PostgreSQL 15+ com pgvector
- **Cache:** Redis 7
- **Proxy Reverso:** Traefik com Let's Encrypt
- **Containerização:** Docker Compose
- **Monitoramento:** Prometheus + Grafana + Alertmanager

### Componentes de Infraestrutura
```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Traefik       │    │   FastAPI       │    │   PostgreSQL    │
│   (Proxy)       │────│   (API)         │────│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │   Prometheus    │    │     Redis       │
│   (Dashboards)  │────│   (Metrics)     │────│     (Cache)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 Configuração de Produção

### 1. Reverse Proxy & TLS
- **Traefik:** Configurado em `ops/traefik/`
- **SSL:** Let's Encrypt automático
- **Domínios:** Configuráveis em `ops/traefik/dynamic/sparkone.yml`
- **Métricas:** Disponível em `reverse-proxy:8082/metrics`

### 2. Banco de Dados
- **PostgreSQL 15+** com extensão pgvector
- **Connection Pooling** configurado
- **Backups:** Automáticos via `ops/backup.sh`
- **Migrations:** Alembic para versionamento

### 3. Cache e Sessões
- **Redis 7** para cache e rate limiting
- **Session Storage** para autenticação
- **Queue Backend** para APScheduler (futuro)

### 4. Observabilidade
- **Prometheus** para coleta de métricas
- **Grafana** para visualização
- **Alertmanager** para notificações
- **Structlog** para logging estruturado

---

## 📊 Sistema de Monitoramento

### Métricas Essenciais

| Categoria | Métrica | Fonte | Alerta |
|-----------|---------|-------|--------|
| **API** | `sparkone_http_request_latency_seconds` | Middleware | P95 > 2s por 3 min |
| **Mensageria** | `sparkone_message_processing_duration_seconds` | Services | P99 > 10s |
| **Integrações** | `sparkone_notion_sync_total{status="error"}` | Services | >3 falhas/5 min |
| **Infra** | `sparkone_db_pool_in_use` | SQLAlchemy | >80% por 5 min |
| **Segurança** | `sparkone_rate_limit_hits_total` | Middleware | >50 hits/min |

### Health Checks
- **`/health`** - Status geral da aplicação
- **`/health/database`** - Conectividade do banco
- **`/health/redis`** - Status do Redis
- **`/metrics`** - Métricas Prometheus

---

## 🔍 Observabilidade

### 1. Logging Estruturado
```python
# Configuração Structlog
import structlog

logger = structlog.get_logger()
logger.info("Processando mensagem", 
           request_id="abc123",
           channel="whatsapp",
           user_id="user456")
```

### 2. Métricas Personalizadas
```python
# Exemplo de métrica customizada
from prometheus_client import Counter, Histogram

request_count = Counter('sparkone_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('sparkone_request_duration_seconds', 'Request duration')
```

### 3. Tracing Distribuído
- **OpenTelemetry** integrado (opcional)
- **Correlation IDs** para rastreamento
- **Spans** para operações críticas

---

## 🚨 Sistema de Alertas

### Alertas Críticos
```yaml
groups:
  - name: sparkone.api
    rules:
      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, rate(sparkone_http_request_latency_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Latência P95 alta"
          description: "P95 > 2s nos últimos 5m"
      
      - alert: DatabaseConnectionHigh
        expr: sparkone_db_pool_in_use > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pool de conexões alto"
          description: "Pool DB > 80% por 5 minutos"
```

### Alertas de Segurança
```yaml
  - name: sparkone.security
    rules:
      - alert: SuspiciousRateLimit
        expr: increase(sparkone_rate_limit_hits_total[5m]) > 50
        labels:
          severity: warning
        annotations:
          summary: "Muitos rate limits"
          description: "Rate limit hits > 50 em 5 minutos"
```

---

## 📈 Performance e Profiling

### Sistema de Profiling
- **DatabaseProfiler** - Monitora queries SQLAlchemy
- **Métricas de Performance** - Tempo, memória, CPU
- **Detecção Automática** - Queries lentas
- **API de Profiling** - Endpoints para análise

### Configuração de Profiling
```bash
# Threshold para queries lentas (segundos)
PROFILER_SLOW_QUERY_THRESHOLD=0.5

# Habilitar/desabilitar profiler
PROFILER_ENABLED=true

# Tamanho máximo do histórico
PROFILER_MAX_HISTORY=1000
```

### Métricas de Performance
- **Query Duration** - Tempo de execução de queries
- **Memory Usage** - Uso de memória por operação
- **CPU Usage** - Consumo de CPU
- **Slow Queries** - Queries acima do threshold

---

## 🔒 Segurança de Infraestrutura

### 1. Hardening de Containers
- **Imagens Base** - Python slim mantidas
- **Read-only** - Sistemas de arquivo read-only
- **No New Privileges** - `security_opt: no-new-privileges:true`
- **Scans de Segurança** - `docker scout` ou `trivy`

### 2. Gerenciamento de Secrets
- **SOPS** ou **Vault** para criptografia
- **Rotação Automática** - Política de rotação
- **GitHub Actions** - Decriptação durante deploy
- **Never Commit** - `.env` nunca no repositório

### 3. Network Security
- **Firewall** - UFW configurado (portas 22, 80, 443)
- **TLS** - Let's Encrypt automático
- **Rate Limiting** - Redis-based rate limiting
- **CORS** - Configuração restritiva

---

## 💾 Backup e Recuperação

### Estratégia de Backup
```bash
# Backup manual
COMPOSE_FILE=ops/staging-compose.yml ./ops/backup.sh /path/backups

# Restore
COMPOSE_FILE=ops/staging-compose.yml ./ops/restore.sh sparkone_YYYYMMDD.sql

# Validação
./ops/verify_backup.sh sparkone_YYYYMMDD.sql
```

### Cronograma de Backup
- **Diário** - Backup completo do banco
- **Semanal** - Backup de arquivos e configurações
- **Mensal** - Teste de restore completo
- **Trimestral** - Auditoria de backup

### Retenção
- **Produção** - 90 dias
- **Staging** - 30 dias
- **Desenvolvimento** - 7 dias

---

## 🚀 Deploy e CI/CD

### Pipeline de Deploy
1. **Build** - Docker image build
2. **Test** - Testes automatizados
3. **Security Scan** - Verificação de vulnerabilidades
4. **Deploy** - Deploy automatizado
5. **Health Check** - Verificação pós-deploy

### GitHub Actions
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Deploy
        run: |
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml up -d
```

---

## 📋 Checklist de Operações

### Diário
- [ ] Verificar health checks
- [ ] Monitorar métricas de performance
- [ ] Verificar logs de erro
- [ ] Confirmar backups

### Semanal
- [ ] Análise de performance
- [ ] Verificação de segurança
- [ ] Atualização de dependências
- [ ] Teste de restore

### Mensal
- [ ] Auditoria de segurança
- [ ] Revisão de capacidade
- [ ] Rotação de secrets
- [ ] Teste de disaster recovery

---

## 🔧 Troubleshooting

### Problemas Comuns

**1. Latência Alta**
```bash
# Verificar métricas
curl http://localhost:9090/api/v1/query?query=sparkone_http_request_latency_seconds

# Verificar logs
docker-compose logs api | grep "slow query"
```

**2. Banco de Dados Lento**
```bash
# Verificar pool de conexões
curl http://localhost:9090/api/v1/query?query=sparkone_db_pool_in_use

# Verificar queries lentas
curl http://localhost:8000/profiler/slow-queries
```

**3. Redis Indisponível**
```bash
# Verificar status
docker-compose exec redis redis-cli ping

# Verificar logs
docker-compose logs redis
```

---

## 📊 Dashboards

### Dashboard Principal (Grafana)
- **API Metrics** - Latência, throughput, erros
- **Database** - Pool connections, query performance
- **Redis** - Memory usage, hit ratio
- **System** - CPU, memory, disk usage

### Dashboard de Segurança
- **Rate Limiting** - Tentativas bloqueadas
- **Authentication** - Logins falhados
- **Errors** - 4xx/5xx responses
- **Threats** - IPs suspeitos

---

**Infraestrutura validada e pronta para produção em Janeiro 2025**
