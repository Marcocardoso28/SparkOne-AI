# SparkOne - Product Requirements Document (PRD)
## AI-Optimized Technical Specification

**Version:** 1.0  
**Date:** January 2025  
**Status:** Mid-Development (~60% Complete)  
**Author:** PRD Agent  
**Target Audience:** AI Systems, Technical Teams, Automated Analysis

---

## Executive Summary

**SparkOne** is a modular personal assistant inspired by Marco Cardoso's "Jarvis" concept, implementing a conversational AI agent with multi-channel integration and intelligent orchestration capabilities.

**Current State:** Mid-development with core infrastructure complete, 60% feature coverage  
**Architecture:** FastAPI + PostgreSQL + Redis + Docker Compose  
**Orchestration:** Agno Bridge (LLM-based routing) with planned migration to full Agno library  
**Deployment:** Local SQLite or Docker-based PostgreSQL stack  

---

## Technical Architecture

### System Components

#### Core Framework
```yaml
framework: FastAPI 0.115+
runtime: Python 3.11+
server: Uvicorn (ASGI)
validation: Pydantic 2.8+
orm: SQLAlchemy 2.0+ (async)
migration: Alembic 1.13+
```

#### Data Layer
```yaml
primary_db: PostgreSQL 15+ with pgvector extension
cache: Redis 7
local_dev: SQLite (fallback)
vector_search: pgvector for embeddings (infra ready; feature pending RF-018, P1; see ADR-003, ADR-013, backlog RF-006)
```

#### External Integrations
```yaml
llm_providers: [OpenAI, Local LLM]
messaging: Evolution API (WhatsApp Business)
productivity: Notion API, Google Calendar API, CalDAV
observability: Prometheus, OpenTelemetry (optional)
```

### Request Flow Architecture
```
[Input Channels] → [Ingestion Hub] → [Agno Bridge] → [Domain Services] → [Persistence Layer]
     ↓                    ↓               ↓              ↓                ↓
[WhatsApp/Web/API] → [/ingest] → [LLM Classification] → [TaskService] → [PostgreSQL]
                                                      → [CalendarService] → [Redis Cache]
                                                      → [CoachService]
```

---

## Functional Requirements

### Canonical Requirements (RF/RNF) — Bilingual Alignment

The following canonical list standardizes requirement IDs to RF-xxx (functional) and RNF-xxx (non-functional) to match the PT document. This section is authoritative; legacy FR/NFR labels below are retained for context.

#### Bilingual Mapping (Functional RF)

| RF ID | PT Title | EN Title |
|------|----------|----------|
| RF-001 | Interface WhatsApp via Evolution API | WhatsApp interface via Evolution API |
| RF-002 | Interface Web (HTTP Basic) | Web interface (HTTP Basic) |
| RF-003 | Integração Google Sheets | Google Sheets integration |
| RF-004 | API REST para ingestão direta | Direct REST ingestion API |
| RF-005 | Sincronização com Notion | Notion synchronization |
| RF-006 | Listagem/filtragem de tarefas | Task listing/filtering |
| RF-007 | Integração Google Calendar | Google Calendar integration |
| RF-008 | Suporte CalDAV | CalDAV support |
| RF-009 | Criação/sincronização de eventos | Create/sync calendar events |
| RF-010 | Coaching pessoal (texto) | Personal coaching (text) |
| RF-011 | Brief estruturado diário | Structured daily brief |
| RF-012 | Brief textual personalizado | Text brief |
| RF-013 | Classificação de mensagens | Message classification |
| RF-014 | Roteamento inteligente | Intelligent routing |
| RF-015 | ProactivityEngine | ProactivityEngine |
| RF-016 | RecommendationService (Google Places) | RecommendationService (Google Places) |
| RF-017 | Integração Eventbrite | Eventbrite integration |
| RF-018 | Implementação de Busca Vetorial | Vector Search implementation |

#### Bilingual Mapping (Non-Functional RNF)

| RNF ID | PT Title | EN Title |
|-------|----------|----------|
| RNF-001 | Performance (<2s p95) | Performance (<2s p95) |
| RNF-002 | Throughput (100 req/min/user) | Throughput (100 req/min/user) |
| RNF-003 | Startup (<10s) | Startup (<10s) |
| RNF-004 | Arquitetura stateless | Stateless architecture |
| RNF-005 | Cache Redis | Redis cache |
| RNF-006 | Multi-worker (Compose) | Multi-worker (Compose) |
| RNF-007 | HTTP Basic (Web UI) | HTTP Basic (Web UI) |
| RNF-008 | Rate limiting por IP | IP-based rate limiting |
| RNF-009 | Security headers (HSTS, CSP, COOP) | Security headers (HSTS, CSP, COOP) |
| RNF-010 | Sanitização de entrada | Input sanitization |
| RNF-011 | Logs sem dados sensíveis | Sensitive log redaction |
| RNF-012 | Compat.: Python 3.11+ | Compat.: Python 3.11+ |
| RNF-013 | Compat.: PostgreSQL 15+ | Compat.: PostgreSQL 15+ |
| RNF-014 | Compat.: Redis 7 | Compat.: Redis 7 |
| RNF-015 | Compat.: Docker Compose | Compat.: Docker Compose |
| RNF-016 | Métricas Prometheus | Prometheus metrics |
| RNF-017 | Logs estruturados (IDs) | Structured logs (correlation IDs) |
| RNF-018 | Health checks granulares | Granular health checks |
| RNF-019 | OpenTelemetry (opcional) | OpenTelemetry (optional) |
| RNF-020 | Autenticação JWT (P1) | JWT Authentication (P1) |
| RNF-021 | Gestão de segredos | Secrets management |

#### Acceptance Criteria (summary)

For each RF/RNF, add acceptance checks. Examples:

- RF-001: Requests to `POST /webhooks/whatsapp` are accepted, validated, and persisted; invalid payloads return 4xx.
- RF-002: `GET /web` requires HTTP Basic; unauthorized returns 401.
- RF-003: `POST /channels/sheets` ingests rows, deduplicates, and acknowledges.
- RF-004: `POST /ingest` accepts message, channel, user_id; returns `message_id`.
- RF-005: Notion sync creates/updates tasks; mismatch reconciled; audit logged.
- RF-006: `GET /tasks` supports `status`, `limit`, `offset` filters; stable sorting.
- RF-007/RF-008/RF-009: `GET/POST/PUT /events` works with Google and CalDAV providers; timezone-safe.
- RF-010: Coach service returns corrected text and rationale; PII not logged.
- RF-011/RF-012: Brief endpoints return structured JSON and human text; include tasks/events counts.
- RF-013: Messages are classified into one of 5 types; unknown -> GENERAL.
- RF-014: Router dispatches by type and returns 2xx; failures logged.
- RF-015 (P0): Scheduler can trigger daily brief and reminders; worker visible in logs.
- RF-016 (P1): Places recommendations return top-N with metadata; rate limits respected.
- RF-017 (P2): Eventbrite suggestions returned with category filters.
- RF-018 (P1): Vector similarity query returns ranked results from pgvector; latency <500ms p95 on sample.
- RNF-007 → RNF-021: Security/compat/observability checks pass; see Security Plan.

### FR-001: Multi-Channel Input System
**Status:** ✅ IMPLEMENTED  
**Components:**
- `src/app/routers/webhooks.py` - WhatsApp webhook handler
- `src/app/routers/web.py` - Web UI with HTTP Basic Auth
- `src/app/routers/channels.py` - Google Sheets integration
- `src/app/routers/ingest.py` - Direct REST API ingestion

**Endpoints:**
- `POST /webhooks/whatsapp` - Evolution API webhook
- `GET /web` - Web interface with auth
- `POST /channels/sheets` - Google Sheets sync
- `POST /ingest` - Direct message ingestion

### FR-002: Intelligent Message Orchestration
**Status:** ✅ IMPLEMENTED (Bridge Mode)  
**Component:** `src/app/agents/agno.py`  
**Functionality:**
- LLM-based message classification into MessageType enum
- Routing to appropriate domain services
- Context-aware response generation
- Planned migration to full Agno library integration

**Message Types:**
```python
class MessageType(Enum):
    TASK = "task"
    CALENDAR = "calendar" 
    COACH = "coach"
    BRIEF = "brief"
    GENERAL = "general"
```

### FR-003: Task Management Service
**Status:** ✅ IMPLEMENTED  
**Component:** `src/app/services/tasks.py`  
**Integration:** Notion API with PostgreSQL snapshots  
**Endpoints:**
- `GET /tasks` - List tasks with filtering
- `POST /tasks` - Create new task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

**Data Model:**
```python
class Task(Base):
    id: UUID
    title: str
    status: TaskStatus
    notion_id: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### FR-004: Calendar Integration Service
**Status:** ✅ IMPLEMENTED  
**Component:** `src/app/services/calendar.py`  
**Providers:** Google Calendar API, CalDAV (Apple Calendar)  
**Endpoints:**
- `GET /events` - List calendar events
- `POST /events` - Create new event
- `PUT /events/{id}` - Update event

**Configuration:**
```python
CALENDAR_PROVIDER: Literal["google", "caldav", "none"] = "google"
```

### FR-005: Personal Coaching Service
**Status:** ✅ IMPLEMENTED  
**Component:** `src/app/services/personal_coach.py`  
**Functionality:**
- Text correction and improvement suggestions
- Motivational guidance with personalized prompts
- LLM-powered writing enhancement

### FR-006: Daily Brief System
**Status:** ✅ IMPLEMENTED  
**Endpoints:**
- `GET /brief/structured` - JSON structured brief
- `GET /brief/text` - Human-readable text brief

### FR-007: Proactivity Engine
**Status:** ❌ NOT IMPLEMENTED  
**Priority:** P0 (Critical)  
**Planned Components:**
- APScheduler integration for automated reminders
- Proactive notification system
- Context-aware suggestion engine
    References: ADR-012

### FR-008: Recommendation Service
**Status:** ❌ NOT IMPLEMENTED  
**Priority:** P1 (Important)  
**Planned Integrations:**
- Google Places API for location-based recommendations
- Eventbrite API for event suggestions

---

## Non-Functional Requirements (RNF — Canonical)

### RNF-001: Performance Requirements
```yaml
response_time_p95: <2000ms
throughput: 100 requests/minute/user
startup_time: <10000ms
memory_usage: <512MB (base)
```

### RNF-007: Security Requirements
**Implementation Status:** ✅ IMPLEMENTED  
**Components:**
```python
# Middleware Stack (src/app/main.py)
- CORSMiddleware: Secure CORS configuration
- CorrelationIdMiddleware: Request tracing
- PrometheusMiddleware: Metrics collection
- RateLimitMiddleware: Redis-based rate limiting
- SecurityHeadersMiddleware: HSTS, CSP, COOP headers
- SecurityLoggingMiddleware: Security event auditing
```

**Security Features:**
- HTTP Basic Authentication for Web UI
- CSRF token protection for forms
- Input sanitization and validation
- Sensitive data redaction in logs
- File upload size limits
- 2FA support with TOTP

#### Staged Security Plan

- Current: HTTP Basic (internal use; RNF-007)
- P1: JWT Authentication (mandatory; RNF-020; see ADR-011, backlog RF-007)
- Future optional: 2FA with TOTP (toggleable)

### RNF-004: Scalability Requirements
```yaml
architecture: Stateless (horizontal scaling ready)
caching: Redis for query optimization
workers: Multi-worker support via Docker Compose
database: Connection pooling with SQLAlchemy
```

### RNF-016: Observability Requirements
**Status:** ✅ IMPLEMENTED  
**Components:**
- `src/app/routers/metrics.py` - Prometheus metrics endpoint
- `src/app/routers/health.py` - Health check endpoints
- Structured logging with correlation IDs
- Optional OpenTelemetry integration

**Metrics Exposed:**
```
/metrics - Prometheus format
/health - Application health
/health/database - Database connectivity
```

### RNF-012: Compatibility Requirements

- **RNF-012:** Python 3.11+
  - **Acceptance Criteria:** `python --version` returns 3.11.x or higher; CI pipeline validates version; all type hints compatible with 3.11+

- **RNF-013:** PostgreSQL 15+ with pgvector extension
  - **Acceptance Criteria:** `SELECT version()` returns PostgreSQL 15+; pgvector extension loads without errors (`CREATE EXTENSION IF NOT EXISTS vector`); vector queries execute successfully

- **RNF-014:** Redis 7 for cache
  - **Acceptance Criteria:** `redis-cli INFO server` returns version 7.x; connection established in < 100ms; basic commands (SET/GET) work

- **RNF-015:** Docker Compose for deployment
  - **Acceptance Criteria:** `docker-compose version` returns 2.0+; `docker-compose up` starts all services; health checks pass in < 30s

```yaml
python_version: ">=3.11"
postgresql_version: ">=15"
redis_version: ">=7"
docker_compose_version: ">=2.0"
```

---

## API Specification

### Authentication
```yaml
web_ui: HTTP Basic Authentication
api_endpoints: Internal (JWT planned, RNF-020)
rate_limiting: 100 requests/minute per IP
```

### Core Endpoints
```yaml
POST /ingest:
  description: Direct message ingestion
  payload: {message: str, channel: str, user_id: str}
  response: {status: str, message_id: str}

GET /tasks:
  description: List tasks with optional filtering
  parameters: {status?: str, limit?: int, offset?: int}
  response: {tasks: Task[], total: int}

GET /events:
  description: List calendar events
  parameters: {start_date?: str, end_date?: str}
  response: {events: Event[], total: int}

GET /brief/structured:
  description: Structured daily brief
  response: {tasks: Task[], events: Event[], recommendations: str[]}
```

### Webhook Endpoints
```yaml
POST /webhooks/whatsapp:
  description: Evolution API webhook handler
  payload: EvolutionWebhookPayload
  response: {status: "processed"}
```

---

## Data Models

### Core Entities
```python
# Task Entity
class Task(Base):
    __tablename__ = "tasks"
    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=255)
    description: Optional[str]
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    notion_id: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Event Entity  
class Event(Base):
    __tablename__ = "events"
    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=255)
    start_time: datetime
    end_time: datetime
    calendar_provider: str
    external_id: Optional[str] = Field(index=True)

# Message Entity
class Message(Base):
    __tablename__ = "messages"
    id: UUID = Field(primary_key=True)
    content: str
    channel: str
    user_id: str
    message_type: MessageType
    processed_at: datetime
```

### Configuration Schema
```python
class SparkOneConfig(BaseSettings):
    # Database
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(env="REDIS_URL")
    
    # AI Providers
    openai_api_key: Optional[str] = Field(env="OPENAI_API_KEY")
    local_llm_url: Optional[str] = Field(env="LOCAL_LLM_URL")
    
    # Integrations
    evolution_api_base_url: str = Field(env="EVOLUTION_API_BASE_URL")
    notion_api_key: Optional[str] = Field(env="NOTION_API_KEY")
    
    # Security
    web_password: str = Field(env="WEB_PASSWORD")
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
```

---

## Implementation Status Matrix

| Component | Implementation | Testing | Documentation | Priority |
|-----------|---------------|---------|---------------|----------|
| FastAPI Core | ✅ 100% | ❌ 30% | ✅ 80% | P0 |
| Multi-Channel Input | ✅ 100% | ❌ 40% | ✅ 70% | P0 |
| Agno Bridge | ✅ 70% | ❌ 20% | ❌ 50% | P0 |
| Task Service | ✅ 90% | ❌ 35% | ✅ 75% | P0 |
| Calendar Service | ✅ 85% | ❌ 25% | ✅ 60% | P1 |
| Coach Service | ✅ 80% | ❌ 15% | ❌ 40% | P1 |
| Brief System | ✅ 75% | ❌ 30% | ❌ 50% | P1 |
| Proactivity Engine | ❌ 0% | ❌ 0% | ❌ 0% | P0 |
| Recommendation Service | ❌ 0% | ❌ 0% | ❌ 0% | P1 |
| Security Middleware | ✅ 90% | ❌ 45% | ✅ 70% | P0 |
| Observability | ✅ 80% | ❌ 40% | ✅ 65% | P1 |

---

## Critical Gaps Analysis

### P0 (Critical) - Blocking Production
1. **Proactivity Engine Missing**
   - Impact: Core functionality unavailable
   - Effort: 2-3 sprints
   - Dependencies: APScheduler integration

2. **Test Coverage <85%**
   - Impact: Production reliability risk
   - Effort: 1-2 sprints
   - Dependencies: Mock external APIs

3. **Full Agno Integration**
   - Impact: Architecture debt
   - Effort: 1 sprint
   - Dependencies: Agno library stability

4. **Security Posture (JWT not implemented)**
   - Impact: Inadequate auth for broader usage
   - Effort: 1 sprint
   - Dependencies: RNF-020 (JWT), ADR-011

### P1 (Important) - Feature Completeness
1. **Recommendation Service**
   - Impact: Reduced user value
   - Effort: 1 sprint
   - Dependencies: Google Places API setup

2. **CI/CD Pipeline**
   - Impact: Development velocity
   - Effort: 0.5 sprint
   - Dependencies: GitHub Actions setup

3. **Vector Search Implementation**
   - Impact: Under-utilization of existing pgvector infra
   - Effort: 1 sprint
   - Dependencies: RF-018, ADR-003

### P2 (Nice to Have) - Future Enhancements
1. **Mobile Interface**
2. **Advanced Analytics**
3. **Plugin System**
4. **Multi-tenant Support**

---

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| External API Changes | Medium | High | Version pinning, adapter pattern |
| LLM Provider Outages | Medium | High | Local fallback, circuit breakers |
| Database Performance | High | Medium | Connection pooling, Redis cache |
| Agno Migration Complexity | High | Medium | Gradual migration, feature flags |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User Adoption | Low | High | Iterative feedback, UX improvements |
| Scaling Requirements | Low | High | Stateless architecture, containerization |
| Security Vulnerabilities | Medium | High | Regular audits, dependency updates |

---

## Deployment Architecture

### Local Development
```yaml
database: SQLite (file-based)
cache: Redis (optional)
server: uvicorn --reload
dependencies: pip install -e .
```

### Docker Compose (Recommended)
```yaml
services:
  api: FastAPI application
  worker: Background scheduler
  db: PostgreSQL 15 with pgvector
  cache: Redis 7
  ngrok: External tunnel (optional)
```

### Production (Planned)
```yaml
infrastructure: VPS with Docker Compose
reverse_proxy: Traefik with HTTPS
monitoring: Prometheus + Grafana
logging: Structured logs with correlation IDs
backup: Automated PostgreSQL backups
```

---

## Success Metrics

### Technical KPIs
```yaml
uptime: >99.5%
response_time_p95: <2000ms
error_rate: <1%
test_coverage: >85%
security_score: A+ (Mozilla Observatory)
```

### Product KPIs
```yaml
daily_interactions: >50/day
query_success_rate: >90%
user_satisfaction: >4.5/5
feature_adoption: >80% for core features
```

### Development KPIs
```yaml
sprint_velocity: 8-10 story points
lead_time: <3 days for small features
deployment_frequency: 2-3x per week
mttr: <2 hours for critical issues
```

---

## Migration Strategy

### Phase 1: Stabilization (Current Sprint)
- Complete Proactivity Engine implementation
- Achieve 85%+ test coverage
- Implement comprehensive error handling

### Phase 2: Agno Integration (Next Sprint)
- Replace AgnoBridge with full Agno library
- Migrate message classification logic
- Validate compatibility with existing services

### Phase 3: Feature Completion (Sprint +2)
- Implement Recommendation Service
- Complete API documentation
- Set up CI/CD pipeline

### Phase 4: Production Readiness (Sprint +3)
- Performance optimization
- Security audit and hardening
- Production deployment setup

---

## Conclusion

SparkOne represents a well-architected personal assistant system with solid foundations and clear technical direction. The current 60% completion rate reflects a mature core infrastructure with identified gaps in proactive features and testing coverage.

**Immediate Priorities:**
1. Implement Proactivity Engine (P0)
2. Achieve comprehensive test coverage (P0)
3. Complete Agno migration (P0)

**Technical Strengths:**
- Modular, extensible architecture
- Comprehensive security implementation
- Multi-channel integration capability
- Strong observability foundation

**Recommended Actions:**
1. Focus on P0 items for production readiness
2. Establish automated testing and CI/CD
3. Plan gradual Agno migration strategy
4. Implement comprehensive monitoring

---

**Document Generated:** January 2025  
**Target Audience:** AI Systems, Automated Analysis, Technical Teams  
**Format:** Machine-readable with structured data for AI consumption
