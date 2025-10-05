# ADR RF-015: ProactivityEngine Implementation

**Status**: 🟢 OPERACIONAL (Phase 9 Validado)
**Data**: 2025-10-09
**Decisor**: CODEx Phase 9

---

## 📋 Contexto

O requisito **RF-015** exige um motor proativo capaz de monitorar prazos e eventos para acionar notificações sem intervenção do usuário. As fases anteriores documentaram o plano, porém o worker ainda não existia em produção. Durante a Phase 9 o objetivo foi entregar a fundação operacional desse motor com monitoramento, DLQ e métricas prontas para observabilidade em Grafana/Prometheus.

---

## ✅ Decisão

1. **Worker dedicado**: executar o ProactivityEngine em um serviço próprio (`services/worker/app.py`) usando FastAPI + APScheduler.
2. **Monitoramento centralizado**: capturar execuções via `EventMonitor` com persistência em PostgreSQL (`worker_job_events`).
3. **Gestão de falhas**: enfileirar exceções em uma DLQ relacional (`worker_dlq`) com possibilidade futura de reprocessamento.
4. **Observabilidade nativa**: expor `/healthz` e `/metrics` diretamente no worker, incluindo métricas `sparkone_worker_job_count_total` e `sparkone_worker_job_latency_seconds`.
5. **Infra integrada**: atualizar `docker-compose.yml` para subir o worker com probes de saúde e expor a porta 9100 para métricas.

---

## 🛠️ Implementação

### Componentes Principais
- **Worker App** (`services/worker/app.py`)
  - FastAPI com lifecycle que inicializa APScheduler (timezone `settings.timezone`).
  - Jobs agendados a cada 5 minutos (`event-reminder`, `task-reminder`) executados imediatamente no boot para popular métricas/registros.
  - Instrumentação Prometheus e logs estruturados via `structlog`.
- **EventMonitor** (`services/worker/event_monitor.py`)
  - Registra execuções na tabela `worker_job_events` (status, duração, payload, erro).
  - Emite logs estruturados `worker_job_event` com preview de payload.
- **NotificationManager** (`services/worker/notification_manager.py`)
  - Stub síncrono que persiste falhas na tabela `worker_dlq` e gera alertas em log (`worker_alert_dispatched`).
  - Preparado para integrar canais reais (WhatsApp/E-mail) sem bloquear o scheduler.

### Dead Letter Queue e Auditoria
- Arquivo de referência SQL: `services/worker/dlq.sql`.
- Migração Alembic `1bc0f6b6be41_add_worker_tables` cria:
  - `worker_dlq(id, job_name, payload, error_message, scheduled_for, retry_count, created_at, processed_at)`.
  - `worker_job_events(id, job_name, status, scheduled_at, started_at, finished_at, runtime_seconds, payload, error_message, created_at)`.
- Índices em `job_name` e colunas temporais aceleram filtros operacionais.

### Observabilidade
- Prometheus:
  - `sparkone_worker_job_count_total{job_name,status}`
  - `sparkone_worker_job_latency_seconds{job_name}`
- Endpoints expostos na porta 9100:
  - `GET /healthz` → lista IDs dos jobs ativos.
  - `GET /metrics` → payload compatível com Prometheus (& Grafana dashboards existentes).
- Logs: todos os registros usam JSON via `structlog` (eventos `worker_job_succeeded`, `worker_job_event`, `worker_dlq_enqueued`).

### Docker Compose
```yaml
docker-compose.yml
  worker:
    command: uvicorn services.worker.app:app --host 0.0.0.0 --port 9100
    ports:
      - "9100:9100"
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:9100/healthz')\""]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## 🔎 Operação

| Item | Detalhe |
|------|---------|
| Jobs | `event-reminder` (eventos até +60 min), `task-reminder` (tarefas até +90 min) |
| Armazenamento | PostgreSQL (`worker_job_events`, `worker_dlq`) |
| Alertas | Logs estruturados → Grafana/Loki |
| Métricas | Prometheus → dashboards "Worker / Phase 9" |
| Reprocessamento | Manual (consultar `worker_dlq`, mover payload) |

### Fluxo de Execução
1. Scheduler dispara job (`IntervalTrigger` 5 min, `coalesce=True`).
2. Handler consulta banco assíncrono (`AsyncSession`).
3. Se encontrar itens:
   - Emite alerta via `NotificationManager.send_alert` (log, metadata com preview).
4. Ao finalizar:
   - `EventMonitor` persiste auditoria.
   - Métricas são atualizadas (contador + histograma).
5. Em erro:
   - Payload/erro vai para `worker_dlq`.
   - Log estrutural `worker_dlq_enqueued` + alerta crítico.

---

## 📊 Validação Fase 9
- Jobs executados e registrados nas tabelas (`worker_job_events` conta >= 2 entradas).
- Métricas `/metrics` exibem `sparkone_worker_job_count_total` e `sparkone_worker_job_latency_seconds` para ambos os jobs.
- Alertas visíveis no stack de observabilidade (Grafana/Loki) via campos `job_name`, `severity`.
- Healthcheck do container aprovado (Docker reports `healthy`).

---

## ⚠️ Riscos & Próximos Passos

| Risco | Mitigação |
|-------|-----------|
| Notificações reais ainda são stubs | Integrar `NotificationManager` com Evolution API / e-mail antes do GA |
| Crescimento do DLQ | Criar rotina de reprocessamento periódico ou painel operacional |
| Cobertura de testes limitada | Adicionar testes de integração para jobs e migrations |

### Sugestões Futuras
1. Habilitar notificação multi-canal real (`NotificationManager`).
2. Adicionar job de brief diário + integração com Evolution WhatsApp.
3. Expor API para reprocessar itens da DLQ.
4. Construir dashboard Grafana dedicado (latência, falhas, backlog DLQ).

---

**Status Final**: ✅ Motor proativo operacional com worker dedicado, DLQ e métricas integradas.

**Responsável**: CODEx Phase 9 Worker Team
