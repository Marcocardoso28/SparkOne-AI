# SparkOne — Traceability Matrix

Columns: Requirement ID → Backlog ID(s) → ADR(s) → Endpoint(s) → Code Path(s) → Tests

Note: UNASSIGNED indicates no definitive mapping available in the current docs/code.

---

## Functional (RF)

| Requirement ID | Backlog ID(s) | ADR(s) | Endpoint(s) | Code Path(s) | Tests |
|---|---|---|---|---|---|
| RF-001 WhatsApp (Evolution) | BUG-001 | ADR-001 | POST /webhooks/whatsapp | src/app/routers/webhooks.py | tests/test_webhooks.py |
| RF-002 Web (HTTP Basic) | RF-007 | ADR-009, ADR-011 | GET /web | src/app/routers/web.py | tests/test_web.py |
| RF-003 Google Sheets | TECH-003 | ADR-001 | POST /channels/sheets | src/app/routers/channels.py | tests/test_channels.py |
| RF-004 Ingest API | TECH-003 | ADR-001 | POST /ingest | src/app/routers/ingest.py | tests/test_ingest.py |
| RF-005 Notion Sync | BUG-002 | ADR-010 | /tasks (CRUD) | src/app/services/tasks.py | tests/test_tasks.py |
| RF-006 Tasks list/filter | TECH-002 | ADR-010 | GET /tasks | src/app/routers/tasks.py | tests/test_tasks.py |
| RF-007 Google Calendar | BUG-003 | ADR-001 | /events | src/app/services/calendar.py; src/app/integrations/google_calendar.py | tests/test_calendar.py |
| RF-008 CalDAV | BUG-003 | ADR-001 | /events | src/app/integrations/caldav.py | tests/test_caldav.py |
| RF-009 Events CRUD | TECH-002 | ADR-001 | GET/POST/PUT /events | src/app/routers/events.py | tests/test_events.py |
| RF-010 Personal Coach | TECH-002 | ADR-004 | (service API) | src/app/services/personal_coach.py | tests/test_coach.py |
| RF-011 Brief structured | TECH-003 | ADR-001 | GET /brief/structured | src/app/routers/brief.py | tests/test_brief.py |
| RF-012 Brief text | TECH-003 | ADR-001 | GET /brief/text | src/app/routers/brief.py | tests/test_brief.py |
| RF-013 Message classification | RF-002 | ADR-002 | (internal) | src/app/agents/agno.py | tests/test_agno.py |
| RF-014 Intelligent routing | RF-002 | ADR-002 | (internal) | src/app/agents/agno.py | tests/test_agno.py |
| RF-015 ProactivityEngine (P0) | RF-001, RF-003 | ADR-002; ADR-012 | /proactivity/* (planned) | src/app/services/proactivity.py (planned) | tests/test_proactivity.py (planned) |
| RF-016 Recommendation (Places) (P1) | RF-004 | ADR-004 | /recommendations (planned) | src/app/services/recommendations.py (planned) | tests/test_recommendations.py (planned) |
| RF-017 Eventbrite (P2) | RF-005 | ADR-004 | /recommendations/events (planned) | src/app/services/recommendations.py (planned) | tests/test_recommendations.py (planned) |
| RF-018 Vector Search (P1) | RF-006 | ADR-003; ADR-013 | /search (planned) | src/app/services/vector_search.py (planned) | tests/test_vector_search.py (planned) |

## Non-Functional (RNF)

| Requirement ID | Backlog ID(s) | ADR(s) | Endpoint(s) | Code Path(s) | Tests |
|---|---|---|---|---|---|
| RNF-001 Performance | RNF-004 | ADR-001, ADR-005 | n/a | src/app/main.py | tests/test_performance.py (planned) |
| RNF-002 Throughput | RNF-004 | ADR-001, ADR-005 | n/a | src/app/main.py | tests/test_performance.py (planned) |
| RNF-003 Startup | RNF-004 | ADR-001, ADR-006 | n/a | src/app/main.py | tests/test_performance.py (planned) |
| RNF-004 Stateless | RNF-007 | ADR-004, ADR-006 | n/a | src/app/main.py | tests/test_architecture.py (planned) |
| RNF-005 Redis cache | RNF-006 | ADR-005 | n/a | src/app/main.py | tests/test_cache.py (planned) |
| RNF-006 Multi-worker | INFRA-001 | ADR-006 | n/a | docker-compose.yml | tests/test_deployment.py (planned) |
| RNF-007 HTTP Basic | RF-007 | ADR-009, ADR-011 | GET /web | src/app/routers/web.py | tests/test_auth.py |
| RNF-008 Rate limiting | RNF-001 | ADR-005, ADR-007 | all | src/app/main.py | tests/test_middleware.py |
| RNF-009 Security headers | RNF-002 | ADR-007 | all | src/app/main.py | tests/test_security.py |
| RNF-010 Input sanitization | TECH-004 | ADR-007 | all | src/app/main.py | tests/test_security.py |
| RNF-011 Log redaction | RNF-003 | ADR-008 | n/a | logging config / structlog | tests/test_logging.py (planned) |
| RNF-012 Python 3.11+ | INFRA-001 | ADR-001 | n/a | pyproject.toml | tests/test_compatibility.py (planned) |
| RNF-013 PostgreSQL 15+ | INFRA-001 | ADR-003 | n/a | docker-compose.yml | tests/test_database.py (planned) |
| RNF-014 Redis 7 | INFRA-001 | ADR-005 | n/a | docker-compose.yml | tests/test_cache.py (planned) |
| RNF-015 Docker Compose | INFRA-001 | ADR-006 | n/a | docker-compose.yml | tests/test_deployment.py (planned) |
| RNF-016 Prometheus metrics | RNF-004 | ADR-007 | GET /metrics | src/app/routers/metrics.py | tests/test_metrics.py (planned) |
| RNF-017 Structured logs | RNF-003 | ADR-008 | n/a | structlog configuration | tests/test_logging.py (planned) |
| RNF-018 Health checks | RNF-005 | ADR-001 | GET /health | src/app/routers/health.py | tests/test_health.py |
| RNF-019 OpenTelemetry (opt.) | RNF-008 | ADR-007 | n/a | config; inventory.json | tests/test_observability.py (planned) |
| RNF-020 JWT Auth (P1) | RF-007 | ADR-011 | /auth/* (planned) | src/app/routers/auth.py (planned) | tests/test_auth.py (planned) |
| RNF-021 Secrets management | RNF-009 | ADR-006 | n/a | .env, config | tests/test_security.py (planned) |

---

Maintenance: Update this matrix when adding/modifying requirements, ADRs, endpoints, or code paths.
