# Observabilidade SparkOne — 2025 refresh

## Objetivos
- Detectar falhas em <5 min.
- Obter tempo de resposta P95 < 2s nos principais canais.
- Rastrear ingestão → resposta com correlação única.

## Métricas Essenciais
| Categoria | Métrica | Fonte | Alerta |
| --- | --- | --- | --- |
| API | `sparkone_http_request_latency_seconds` | Middleware Prometheus | P95 > 2s por 3 min |
| Mensageria | `sparkone_message_processing_duration_seconds` | Instrumentação de serviços | P99 > 10s |
| Integrações | `sparkone_notion_sync_total{status="error"}` | Services | >3 falhas/5 min |
| Infra | `sparkone_db_pool_in_use` | Métricas SQLAlchemy | >80% 5 min |
| Segurança | `sparkone_rate_limit_hits_total` | Middleware | picos > 50/min |

## Logs
- `structlog` com enriquecimento (`request_id`, `channel`, `user_id`).
- Exportar para Loki ou CloudWatch via handler opcional (roadmap Q2).
- Política: reter 30 dias em staging, 90 dias em produção.

## Traces
- Adotar OpenTelemetry para FastAPI: `InstrumentationMiddleware` + exporter OTLP.
- Spans mínimos: ingestão, classificação, chamada LLM, persistência, resposta.

## Dashboards
- Atualizar `ops/grafana/dashboard-overview.json` com painéis: latência, filas Redis, falhas de webhook, consumo de tokens LLM.
- Criar dashboard secundário para segurança (tentativas falhas, rate limit, IPs bloqueados).

## Alertas Sugeridos (Prometheus)
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
  - name: sparkone.security
    rules:
      - alert: SuspiciousRateLimit
        expr: increase(sparkone_rate_limit_hits_total[5m]) > 50
        labels:
          severity: warning
        annotations:
          summary: "Muitos rate limits"
```

## Runbooks
- `docs/OPERATIONS.md`: atualizar com SOP para Prometheus/Grafana.
- Adicionar troubleshooting para `sparkone_message_processing_duration_seconds` alta (incluir flush de filas Redis).
