# Phase 9 – Proactivity Engine Validation

## Overview
- Worker service: `uvicorn services.worker.app:app` (port 9100)
- Jobs: `event-reminder`, `task-reminder` (interval 5 min, run on startup)
- Storage: PostgreSQL tables `worker_job_events`, `worker_dlq`
- Metrics: Prometheus counters `sparkone_worker_job_count_total` and histogram `sparkone_worker_job_latency_seconds`

## Validation Checklist
1. **Containers**
   - `docker compose up worker` → container becomes `healthy` via Python healthcheck.
2. **Scheduler Jobs**
   - `SELECT job_name, status, runtime_seconds FROM worker_job_events ORDER BY created_at DESC LIMIT 5;`
   - Confirm entries for both `event-reminder` and `task-reminder`.
3. **Metrics Endpoint**
   - `curl http://localhost:9100/metrics | grep sparkone_worker_job_`
   - Expect counters for both job names and histogram buckets populated.
4. **DLQ Path**
   - Force failure (e.g. stop Postgres) → job error → `SELECT job_name, error_message FROM worker_dlq;`
   - Entry should mirror log `worker_dlq_enqueued`.
5. **Logs / Alerts**
   - View structured logs (Loki/Grafana): search `job_name="event-reminder"`.
   - Check for `worker_alert_dispatched` (info) and `worker_dlq_enqueued` (warning/critical).

## Observability Notes
- `/metrics` includes timestamped counters for Grafana dashboard `Worker / Phase 9`.
- `payload_preview` in logs limited to 200 chars para evitar vazamento de dados sensíveis.
- All timestamps emitidos em ISO8601 com timezone configurado (`settings.timezone`).

## Next Steps / TODOs
- Integrar canais reais no `NotificationManager` (WhatsApp/E-mail).
- Construir rotina de reprocessamento automático para `worker_dlq`.
- Adicionar testes automatizados cobrindo jobs e migrações.
