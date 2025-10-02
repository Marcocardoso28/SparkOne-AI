# SparkOne — Traceability Matrix

Columns: Requirement ID → Backlog ID(s) → ADR(s) → Endpoint(s) → Code Path(s) → Tests

Note: UNASSIGNED indicates no definitive mapping available in the current docs/code.

---

## Functional (RF)

| Requirement ID | Backlog ID(s) | ADR(s) | Endpoint(s) | Code Path(s) | Tests |
|---|---|---|---|---|---|
| RF-001 WhatsApp (Evolution) | UNASSIGNED | UNASSIGNED | POST /webhooks/whatsapp | src/app/routers/webhooks.py | UNASSIGNED |
| RF-002 Web (HTTP Basic) | UNASSIGNED | ADR-009 | GET /web | src/app/routers/web.py | UNASSIGNED |
| RF-003 Google Sheets | UNASSIGNED | UNASSIGNED | POST /channels/sheets | src/app/routers/channels.py | UNASSIGNED |
| RF-004 Ingest API | UNASSIGNED | UNASSIGNED | POST /ingest | src/app/routers/ingest.py | UNASSIGNED |
| RF-005 Notion Sync | UNASSIGNED | ADR-010 | /tasks (CRUD) | src/app/services/tasks.py | UNASSIGNED |
| RF-006 Tasks list/filter | UNASSIGNED | UNASSIGNED | GET /tasks | src/app/routers/tasks.py | UNASSIGNED |
| RF-007 Google Calendar | UNASSIGNED | UNASSIGNED | /events | src/app/services/calendar.py; src/app/integrations/google_calendar.py | UNASSIGNED |
| RF-008 CalDAV | UNASSIGNED | UNASSIGNED | /events | src/app/integrations/caldav.py | UNASSIGNED |
| RF-009 Events CRUD | UNASSIGNED | UNASSIGNED | GET/POST/PUT /events | src/app/routers/events.py | UNASSIGNED |
| RF-010 Personal Coach | UNASSIGNED | UNASSIGNED | (service API) | src/app/services/personal_coach.py | UNASSIGNED |
| RF-011 Brief structured | UNASSIGNED | UNASSIGNED | GET /brief/structured | src/app/routers/brief.py | UNASSIGNED |
| RF-012 Brief text | UNASSIGNED | UNASSIGNED | GET /brief/text | src/app/routers/brief.py | UNASSIGNED |
| RF-013 Message classification | UNASSIGNED | ADR-002 | (internal) | src/app/agents/agno.py | UNASSIGNED |
| RF-014 Intelligent routing | UNASSIGNED | ADR-002 | (internal) | src/app/agents/agno.py | UNASSIGNED |
| RF-015 ProactivityEngine (P0) | RF-001 | UNASSIGNED | UNASSIGNED | UNASSIGNED | UNASSIGNED |
| RF-016 Recommendation (Places) (P1) | RF-004 | UNASSIGNED | UNASSIGNED | UNASSIGNED | UNASSIGNED |
| RF-017 Eventbrite (P2) | RF-005 | UNASSIGNED | UNASSIGNED | UNASSIGNED | UNASSIGNED |
| RF-018 Vector Search (P1) | RF-006 | ADR-003 | UNASSIGNED | UNASSIGNED | UNASSIGNED |

## Non-Functional (RNF)

| Requirement ID | Backlog ID(s) | ADR(s) | Endpoint(s) | Code Path(s) | Tests |
|---|---|---|---|---|---|
| RNF-001 Performance | UNASSIGNED | UNASSIGNED | n/a | src/app/main.py | UNASSIGNED |
| RNF-002 Throughput | UNASSIGNED | UNASSIGNED | n/a | src/app/main.py | UNASSIGNED |
| RNF-003 Startup | UNASSIGNED | UNASSIGNED | n/a | src/app/main.py | UNASSIGNED |
| RNF-004 Stateless | RNF-007 | UNASSIGNED | n/a | src/app/main.py | UNASSIGNED |
| RNF-005 Redis cache | RNF-006 | UNASSIGNED | n/a | src/app/main.py | UNASSIGNED |
| RNF-006 Multi-worker | UNASSIGNED | UNASSIGNED | n/a | docker-compose.yml | UNASSIGNED |
| RNF-007 HTTP Basic | UNASSIGNED | ADR-009 | GET /web | src/app/routers/web.py | UNASSIGNED |
| RNF-008 Rate limiting | RNF-001 | UNASSIGNED | all | src/app/main.py | UNASSIGNED |
| RNF-009 Security headers | RNF-002 | ADR-007 | all | src/app/main.py | UNASSIGNED |
| RNF-010 Input sanitization | UNASSIGNED | ADR-007 | all | src/app/main.py | UNASSIGNED |
| RNF-011 Log redaction | RNF-003 | ADR-008 | n/a | logging config / structlog | UNASSIGNED |
| RNF-012 Python 3.11+ | UNASSIGNED | UNASSIGNED | n/a | pyproject.toml | UNASSIGNED |
| RNF-013 PostgreSQL 15+ | UNASSIGNED | ADR-003 | n/a | docker-compose.yml | UNASSIGNED |
| RNF-014 Redis 7 | UNASSIGNED | ADR-005 | n/a | docker-compose.yml | UNASSIGNED |
| RNF-015 Docker Compose | UNASSIGNED | ADR-006 | n/a | docker-compose.yml | UNASSIGNED |
| RNF-016 Prometheus metrics | UNASSIGNED | UNASSIGNED | GET /metrics | src/app/routers/metrics.py | UNASSIGNED |
| RNF-017 Structured logs | RNF-003 | ADR-008 | n/a | structlog configuration | UNASSIGNED |
| RNF-018 Health checks | RNF-005 | UNASSIGNED | GET /health | src/app/routers/health.py | UNASSIGNED |
| RNF-019 OpenTelemetry (opt.) | RNF-008 | UNASSIGNED | n/a | config; inventory.json | UNASSIGNED |
| RNF-020 JWT Auth (P1) | RF-007 | ADR-011 | n/a | UNASSIGNED | UNASSIGNED |
| RNF-021 Secrets management | RNF-009 | UNASSIGNED | n/a | UNASSIGNED | UNASSIGNED |

---

Maintenance: Update this matrix when adding/modifying requirements, ADRs, endpoints, or code paths.
