# PRD - SparkOne
## Documento de Requisitos do Produto

**Versão:** 1.0  
**Data:** Janeiro 2025  
**Status:** Desenvolvimento Intermediário (~60% completo)  
**Autor:** Agente PRD  

---

## 1. Visão Geral

### 1.1 Visão do Produto
O **SparkOne** é um assistente pessoal modular inspirado no "Jarvis" do Marco Cardoso, projetado para ser um agente de IA conversacional que integra múltiplos canais de comunicação e serviços externos para fornecer uma experiência personalizada e proativa.

**Fonte:** `README.md`, linha 1-5

### 1.2 Objetivos Estratégicos
- **OBJ-001:** Criar um assistente pessoal que funcione como um "segundo cérebro" digital
- **OBJ-002:** Integrar múltiplos canais de entrada (WhatsApp, Web, Google Sheets, API REST)
- **OBJ-003:** Fornecer orquestração inteligente via Agno para processamento contextual
- **OBJ-004:** Manter arquitetura modular e extensível para futuras integrações
- **OBJ-005:** Garantir operação local com opções de deployment flexíveis

**Fonte:** `SPEC.md`, seção "Visão Geral e Objetivos"

### 1.3 Público-Alvo
- **Primário:** Marco Cardoso (usuário principal)
- **Secundário:** Desenvolvedores interessados em assistentes pessoais modulares
- **Terciário:** Comunidade open-source para contribuições futuras

---

## 2. Escopo e Diferenciais

### 2.1 Escopo Inicial (MVP)
- **ESC-001:** Interface conversacional multicanal
- **ESC-002:** Integração com Notion para gerenciamento de tarefas
- **ESC-003:** Sincronização de calendário (Google Calendar, CalDAV)
- **ESC-004:** Coaching pessoal com correções de texto
- **ESC-005:** Sistema de brief diário estruturado

**Fonte:** `SPEC.md`, seção "Escopo Inicial"

### 2.2 Diferenciais Competitivos
- **DIF-001:** **Orquestração via Agno:** Uso de biblioteca própria para processamento contextual
- **DIF-002:** **Deployment Local:** Funciona completamente offline com SQLite
- **DIF-003:** **Múltiplos Provedores LLM:** Suporte a OpenAI e modelos locais
- **DIF-004:** **Arquitetura Modular:** Serviços independentes e extensíveis
- **DIF-005:** **Segurança por Design:** Headers de segurança, rate limiting, logs estruturados

**Fonte:** `SPEC.md`, seção "Diferenciais"

---

## 3. Requisitos Funcionais

### Canonicalização de IDs (RF/RNF) — Mapeamento Bilíngue

Esta seção padroniza os IDs para RF-xxx (funcionais) e RNF-xxx (não funcionais) e define o mapeamento com o PRD em inglês. Esta é a referência canônica.

#### Mapeamento Bilíngue (RF)

| ID | PT (título) | EN (título) |
|----|--------------|--------------|
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

### 3.1 Canais de Entrada
- **RF-001:** Interface WhatsApp via Evolution API
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/routers/webhooks.py`
  - **Endpoint:** `/webhooks/whatsapp`
  - **Critérios de Aceitação:** Receber webhook Evolution API; validar payload; persistir mensagem; retornar 2xx; erros 4xx/5xx logados

- **RF-002:** Interface Web com autenticação HTTP Basic
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/routers/web.py`
  - **Endpoint:** `/web`
  - **Critérios de Aceitação:** Requer HTTP Basic; acesso não autorizado → 401; sem vazamento de PII em logs

- **RF-003:** Integração com Google Sheets
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/routers/channels.py`
  - **Endpoint:** `/channels/sheets`
  - **Critérios de Aceitação:** Ingestão de linhas; deduplicação básica; resposta de confirmação

- **RF-004:** API REST para ingestão direta
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/routers/ingest.py`
  - **Endpoint:** `/ingest`
  - **Critérios de Aceitação:** Aceitar `{message, channel, user_id}`; retornar `{status, message_id}`; validação de entrada

### 3.2 Serviços de Domínio

#### 3.2.1 Gerenciamento de Tarefas
- **RF-005:** Sincronização com Notion
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/services/tasks.py`
  - **Funcionalidades:** CRUD de tarefas, snapshots no Postgres
  - **Critérios de Aceitação:** Upsert consistente; reconciliação de conflito; auditoria de sync

- **RF-006:** Listagem e filtragem de tarefas
  - **Status:** ✅ Implementado
  - **Endpoint:** `/tasks`
  - **Critérios de Aceitação:** Filtros `status`, `limit`, `offset`; ordenação estável

#### 3.2.2 Calendário
- **RF-007:** Integração com Google Calendar
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/services/calendar.py`
  - **Critérios de Aceitação:** CRUD de eventos; token válido; erro tratado; timezone correto

- **RF-008:** Suporte a CalDAV (Apple Calendar)
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/integrations/caldav.py`
  - **Critérios de Aceitação:** Conexão CalDAV válida; criação/atualização com retorno de ID externo

- **RF-009:** Criação e sincronização de eventos
  - **Status:** ✅ Implementado
  - **Endpoint:** `/events`
  - **Critérios de Aceitação:** `GET/POST/PUT /events` funcionam; coerência com Google/CalDAV; timezone-safe

#### 3.2.3 Coaching Pessoal
- **RF-010:** Correções de texto e sugestões
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/services/personal_coach.py`
  - **Funcionalidades:** Melhorias de escrita, orientação motivacional
  - **Critérios de Aceitação:** Retorna texto corrigido + justificativa; sem PII em logs

#### 3.2.4 Sistema de Brief
- **RF-011:** Brief estruturado diário
  - **Status:** ✅ Implementado

### 3.3 Gestão de Technical Debt

#### 3.3.1 Bugs Críticos
- **BUG-001:** Melhoria do tratamento de erros da Evolution API
  - **Status:** 🔄 Planejado
  - **Prioridade:** P0
  - **Arquivo:** `src/app/integrations/evolution_api.py`
  - **Critérios de Aceitação:** Retry logic, circuit breaker, error logging detalhado

- **BUG-002:** Resolver condições de corrida na sincronização Notion
  - **Status:** 🔄 Planejado
  - **Prioridade:** P1
  - **Arquivo:** `src/app/services/tasks.py`
  - **Critérios de Aceitação:** Locks apropriados, transações atômicas, conflict resolution

- **BUG-003:** Corrigir problemas de timezone em eventos
  - **Status:** 🔄 Planejado
  - **Prioridade:** P1
  - **Arquivo:** `src/app/services/calendar.py`
  - **Critérios de Aceitação:** Timezone correto, DST handling, user timezone preference

#### 3.3.2 Melhorias Técnicas
- **TECH-001:** Refatorar arquivos com mais de 300 linhas
  - **Status:** 🔄 Planejado
  - **Prioridade:** P0
  - **Critérios de Aceitação:** Arquivos < 300 linhas, responsabilidade única, testabilidade

- **TECH-002:** Adicionar testes unitários para serviços críticos
  - **Status:** 🔄 Planejado
  - **Prioridade:** P1
  - **Critérios de Aceitação:** Cobertura > 80%, testes de integração, CI/CD pipeline

- **TECH-003:** Melhorar documentação da API com exemplos
  - **Status:** 🔄 Planejado
  - **Prioridade:** P1
  - **Critérios de Aceitação:** Exemplos completos, error responses, authentication docs

- **TECH-004:** Melhorar qualidade do código com linting rigoroso
  - **Status:** 🔄 Planejado
  - **Prioridade:** P2
  - **Critérios de Aceitação:** Linting score > 9.0, type hints 100%, docstrings completas

- **RF-012:** Brief textual personalizado
  - **Status:** ✅ Implementado
  - **Endpoint:** `/brief/text`
  - **Critérios de Aceitação:** Texto legível; inclui itens prioritários do dia

### 3.3 Orquestração (Agno Bridge)
- **RF-013:** Classificação de mensagens por tipo
  - **Status:** ✅ Implementado
  - **Arquivo:** `src/app/agents/agno.py`
  - **Tipos:** TASK, CALENDAR, COACH, BRIEF, GENERAL
  - **Critérios de Aceitação:** Classificação em um dos 5 tipos; desconhecido → GENERAL

- **RF-014:** Roteamento inteligente baseado em contexto
  - **Status:** ✅ Implementado
  - **Funcionalidade:** LLM classifica e roteia mensagens
  - **Critérios de Aceitação:** Encaminhamento ao serviço correto; 2xx; falhas registradas

### 3.4 Funcionalidades Planejadas (Não Implementadas)
- **RF-015:** ProactivityEngine para lembretes automáticos
  - **Status:** ❌ Não implementado
  - **Prioridade:** P0 (crítico)
  - **Critérios de Aceitação:** Scheduler dispara brief diário e lembretes; logs de execução do worker

- **RF-016:** RecommendationService com Google Places
  - **Status:** ❌ Não implementado
  - **Prioridade:** P1 (importante)
  - **Critérios de Aceitação:** Recomendações top-N com metadados; respeita rate limit

- **RF-017:** Integração com Eventbrite
  - **Status:** ❌ Não implementado
  - **Prioridade:** P2 (desejável)
  - **Critérios de Aceitação:** Sugestões por categoria; paginação

- **RF-018:** Implementação de Busca Vetorial
  - **Status:** ❌ Não implementado
  - **Prioridade:** P1 (importante)
  - **Critérios de Aceitação:** Consulta de similaridade retorna ranking por embeddings (pgvector); p95 < 500ms em dataset de exemplo

---

## 4. Requisitos Não-Funcionais (RNF — Canônico)

### Mapeamento Bilíngue (RNF)

| RNF ID | PT (título) | EN (título) |
|--------|-------------|-------------|
| RNF-001 | Performance (<2s p95) | Performance (<2s p95) |
| RNF-002 | Throughput (100 req/min/usuário) | Throughput (100 req/min/user) |
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

### RNF-001: Requisitos de Performance
```yaml
response_time_p95: <2000ms
throughput: 100 requisições/minuto/usuário
startup_time: <10000ms
memory_usage: <512MB (base)
```

### RNF-007: Requisitos de Segurança
**Status de Implementação:** ✅ IMPLEMENTADO
**Componentes:**
```python
# Stack de Middleware (src/app/main.py)
- CORSMiddleware: Configuração CORS segura
- CorrelationIdMiddleware: Rastreamento de requisições
- PrometheusMiddleware: Coleta de métricas
- RateLimitMiddleware: Rate limiting baseado em Redis
- SecurityHeadersMiddleware: Headers HSTS, CSP, COOP
- SecurityLoggingMiddleware: Auditoria de eventos de segurança
```

**Funcionalidades de Segurança:**
- Autenticação HTTP Basic para Web UI
- Proteção CSRF para formulários
- Sanitização e validação de entrada
- Redação de dados sensíveis em logs
- Limites de tamanho para upload de arquivos
- Suporte a 2FA com TOTP

#### Plano de Segurança Escalonado

- Atual: HTTP Basic (uso interno; RNF-007)
- P1: Autenticação JWT (obrigatória; RNF-020; ver ADR-011, backlog RF-007)
- Futuro opcional: 2FA com TOTP (configurável)

### RNF-004: Requisitos de Escalabilidade
```yaml
architecture: Stateless (pronta para escalonamento horizontal)
caching: Redis para otimização de consultas
workers: Suporte multi-worker via Docker Compose
database: Connection pooling com SQLAlchemy
```

### RNF-016: Requisitos de Observabilidade
**Status:** ✅ IMPLEMENTADO
**Componentes:**
- `src/app/routers/metrics.py` - Endpoint de métricas Prometheus
- `src/app/routers/health.py` - Endpoints de health check
- Logging estruturado com IDs de correlação
- Integração opcional com OpenTelemetry

**Métricas Expostas:**
```
/metrics - Formato Prometheus
/health - Saúde da aplicação
/health/database - Conectividade do banco de dados
```

### RNF-012: Requisitos de Compatibilidade

- **RNF-012:** Python 3.11+
  - **Critérios de Aceitação:** `python --version` retorna 3.11.x ou superior; pipeline CI valida versão; todos os type hints compatíveis com 3.11+

- **RNF-013:** PostgreSQL 15+ com extensão pgvector
  - **Critérios de Aceitação:** `SELECT version()` retorna PostgreSQL 15+; extensão pgvector carrega sem erros (`CREATE EXTENSION IF NOT EXISTS vector`); consultas vetoriais executam com sucesso

- **RNF-014:** Redis 7 para cache
  - **Critérios de Aceitação:** `redis-cli INFO server` retorna versão 7.x; conexão estabelecida em < 100ms; comandos básicos (SET/GET) funcionam

- **RNF-015:** Docker Compose para deployment
  - **Critérios de Aceitação:** `docker-compose version` retorna 2.0+; `docker-compose up` inicia todos os serviços; health checks passam em < 30s

```yaml
python_version: ">=3.11"
postgresql_version: ">=15"
redis_version: ">=7"
docker_compose_version: ">=2.0"
```

---

## 5. Especificação de API

### Autenticação
```yaml
web_ui: Autenticação HTTP Basic
api_endpoints: Interno (JWT planejado, RNF-020)
rate_limiting: 100 requisições/minuto por IP
```

### Endpoints Principais
```yaml
POST /ingest:
  description: Ingestão direta de mensagens
  payload: {message: str, channel: str, user_id: str}
  response: {status: str, message_id: str}

GET /tasks:
  description: Listar tarefas com filtragem opcional
  parameters: {status?: str, limit?: int, offset?: int}
  response: {tasks: Task[], total: int}

GET /events:
  description: Listar eventos de calendário
  parameters: {start_date?: str, end_date?: str}
  response: {events: Event[], total: int}

GET /brief/structured:
  description: Brief diário estruturado
  response: {tasks: Task[], events: Event[], recommendations: str[]}
```

### Endpoints de Webhook
```yaml
POST /webhooks/whatsapp:
  description: Handler de webhook da Evolution API
  payload: EvolutionWebhookPayload
  response: {status: "processed"}
```

---

## 6. Modelos de Dados

### Entidades Principais
```python
# Entidade Task
class Task(Base):
    __tablename__ = "tasks"
    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=255)
    description: Optional[str]
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    notion_id: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Entidade Event
class Event(Base):
    __tablename__ = "events"
    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=255)
    start_time: datetime
    end_time: datetime
    calendar_provider: str
    external_id: Optional[str] = Field(index=True)

# Entidade Message
class Message(Base):
    __tablename__ = "messages"
    id: UUID = Field(primary_key=True)
    content: str
    channel: str
    user_id: str
    message_type: MessageType
    processed_at: datetime
```

### Schema de Configuração
```python
class SparkOneConfig(BaseSettings):
    # Database
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(env="REDIS_URL")

    # Provedores de AI
    openai_api_key: Optional[str] = Field(env="OPENAI_API_KEY")
    local_llm_url: Optional[str] = Field(env="LOCAL_LLM_URL")

    # Integrações
    evolution_api_base_url: str = Field(env="EVOLUTION_API_BASE_URL")
    notion_api_key: Optional[str] = Field(env="NOTION_API_KEY")

    # Segurança
    web_password: str = Field(env="WEB_PASSWORD")
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
```

---

## 7. Matriz de Status de Implementação

| Componente | Implementação | Testes | Documentação | Prioridade |
|-----------|--------------|--------|--------------|-----------|
| FastAPI Core | ✅ 100% | ❌ 30% | ✅ 80% | P0 |
| Entrada Multi-Canal | ✅ 100% | ❌ 40% | ✅ 70% | P0 |
| Agno Bridge | ✅ 70% | ❌ 20% | ❌ 50% | P0 |
| Serviço de Tarefas | ✅ 90% | ❌ 35% | ✅ 75% | P0 |
| Serviço de Calendário | ✅ 85% | ❌ 25% | ✅ 60% | P1 |
| Serviço de Coach | ✅ 80% | ❌ 15% | ❌ 40% | P1 |
| Sistema de Brief | ✅ 75% | ❌ 30% | ❌ 50% | P1 |
| Proactivity Engine | ❌ 0% | ❌ 0% | ❌ 0% | P0 |
| Serviço de Recomendação | ❌ 0% | ❌ 0% | ❌ 0% | P1 |
| Middleware de Segurança | ✅ 90% | ❌ 45% | ✅ 70% | P0 |
| Observabilidade | ✅ 80% | ❌ 40% | ✅ 65% | P1 |

---

## 8. Análise de Lacunas Críticas

### P0 (Crítico) - Bloqueando Produção
1. **Proactivity Engine Ausente**
   - Impacto: Funcionalidade core indisponível
   - Esforço: 2-3 sprints
   - Dependências: Integração APScheduler

2. **Cobertura de Testes <85%**
   - Impacto: Risco de confiabilidade em produção
   - Esforço: 1-2 sprints
   - Dependências: Mock de APIs externas

3. **Integração Completa do Agno**
   - Impacto: Débito arquitetural
   - Esforço: 1 sprint
   - Dependências: Estabilidade da biblioteca Agno

4. **Postura de Segurança (JWT não implementado)**
   - Impacto: Autenticação inadequada para uso amplo
   - Esforço: 1 sprint
   - Dependências: RNF-020 (JWT), ADR-011

### P1 (Importante) - Completude de Funcionalidades
1. **Serviço de Recomendação**
   - Impacto: Valor reduzido para o usuário
   - Esforço: 1 sprint
   - Dependências: Configuração Google Places API

2. **Pipeline CI/CD**
   - Impacto: Velocidade de desenvolvimento
   - Esforço: 0.5 sprint
   - Dependências: Configuração GitHub Actions

3. **Implementação de Busca Vetorial**
   - Impacto: Subutilização da infraestrutura pgvector existente
   - Esforço: 1 sprint
   - Dependências: RF-018, ADR-003

### P2 (Desejável) - Melhorias Futuras
1. **Interface Mobile**
2. **Analytics Avançado**
3. **Sistema de Plugins**
4. **Suporte Multi-tenant**

---

## 9. Avaliação de Riscos

### Riscos Técnicos
| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Mudanças em APIs Externas | Médio | Alto | Fixação de versão, padrão adapter |
| Indisponibilidade de Provedor LLM | Médio | Alto | Fallback local, circuit breakers |
| Performance do Banco de Dados | Alto | Médio | Connection pooling, cache Redis |
| Complexidade da Migração Agno | Alto | Médio | Migração gradual, feature flags |

### Riscos de Negócio
| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Adoção de Usuários | Baixo | Alto | Feedback iterativo, melhorias UX |
| Requisitos de Escalabilidade | Baixo | Alto | Arquitetura stateless, containerização |
| Vulnerabilidades de Segurança | Médio | Alto | Auditorias regulares, atualização de dependências |

---

## 10. Arquitetura de Deploy

### Desenvolvimento Local
```yaml
database: SQLite (baseado em arquivo)
cache: Redis (opcional)
server: uvicorn --reload
dependencies: pip install -e .
```

### Docker Compose (Recomendado)
```yaml
services:
  api: Aplicação FastAPI
  worker: Agendador em background
  db: PostgreSQL 15 com pgvector
  cache: Redis 7
  ngrok: Túnel externo (opcional)
```

### Produção (Planejado)
```yaml
infrastructure: VPS com Docker Compose
reverse_proxy: Traefik com HTTPS
monitoring: Prometheus + Grafana
logging: Logs estruturados com IDs de correlação
backup: Backups automáticos do PostgreSQL
```

---

## 11. Métricas de Sucesso

### KPIs Técnicos
```yaml
uptime: >99.5%
response_time_p95: <2000ms
error_rate: <1%
test_coverage: >85%
security_score: A+ (Mozilla Observatory)
```

### KPIs de Produto
```yaml
daily_interactions: >50/dia
query_success_rate: >90%
user_satisfaction: >4.5/5
feature_adoption: >80% para funcionalidades core
```

### KPIs de Desenvolvimento
```yaml
sprint_velocity: 8-10 story points
lead_time: <3 dias para features pequenas
deployment_frequency: 2-3x por semana
mttr: <2 horas para issues críticos
```

---

## 12. Estratégia de Migração

### Fase 1: Estabilização (Sprint Atual)
- Completar implementação do Proactivity Engine
- Atingir 85%+ de cobertura de testes
- Implementar tratamento abrangente de erros

### Fase 2: Integração Agno (Próximo Sprint)
- Substituir AgnoBridge pela biblioteca Agno completa
- Migrar lógica de classificação de mensagens
- Validar compatibilidade com serviços existentes

### Fase 3: Completude de Funcionalidades (Sprint +2)
- Implementar Serviço de Recomendação
- Completar documentação da API
- Configurar pipeline CI/CD

### Fase 4: Prontidão para Produção (Sprint +3)
- Otimização de performance
- Auditoria e hardening de segurança
- Configuração de deployment em produção

---

## 13. Conclusão

O SparkOne representa um sistema de assistente pessoal bem arquitetado com fundações sólidas e direção técnica clara. A taxa de conclusão atual de 60% reflete uma infraestrutura core madura com lacunas identificadas em funcionalidades proativas e cobertura de testes.

**Prioridades Imediatas:**
1. Implementar Proactivity Engine (P0)
2. Atingir cobertura abrangente de testes (P0)
3. Completar migração Agno (P0)

**Pontos Fortes Técnicos:**
- Arquitetura modular e extensível
- Implementação abrangente de segurança
- Capacidade de integração multi-canal
- Fundação sólida de observabilidade

**Ações Recomendadas:**
1. Focar em itens P0 para prontidão em produção
2. Estabelecer testes automatizados e CI/CD
3. Planejar estratégia de migração gradual do Agno
4. Implementar monitoramento abrangente

---

## 8. Timeline e Marcos

### 8.1 Roadmap de Desenvolvimento

#### **Q1 2025 - Estabilização (Jan-Mar)**
- **Jan 2025:** ✅ Infraestrutura base completa
- **Fev 2025:** ProactivityEngine e Worker Container
- **Mar 2025:** Migração para Agno Library

#### **Q2 2025 - Expansão (Abr-Jun)**
- **Abr 2025:** RecommendationService (Google Places)
- **Mai 2025:** Vector Search Implementation
- **Jun 2025:** JWT Authentication

#### **Q3 2025 - Otimização (Jul-Set)**
- **Jul 2025:** Advanced Analytics Dashboard
- **Ago 2025:** Multi-tenant Support
- **Set 2025:** Performance Optimization

### 8.2 Marcos Críticos

| Marco | Data | Entregáveis | Critérios de Sucesso |
|-------|------|-------------|---------------------|
| **MVP Production Ready** | Fev 2025 | ProactivityEngine funcional | Brief automático às 8h, lembretes contextuais |
| **Full Feature Set** | Jun 2025 | Todos os RF P0 implementados | 100% dos requisitos funcionais |
| **Enterprise Ready** | Set 2025 | Multi-tenant + Analytics | Suporte a múltiplos usuários |

---

## 9. Análise de Riscos

### 9.1 Riscos Técnicos

#### **🔴 Alto Risco**
- **Risco:** Dependência do Agno Library
  - **Probabilidade:** Média (30%)
  - **Impacto:** Alto (atraso de 2-3 meses)
  - **Mitigação:** Manter AgnoBridge como fallback, roadmap alternativo

- **Risco:** Complexidade de integração WhatsApp
  - **Probabilidade:** Baixa (15%)
  - **Impacto:** Alto (perda de funcionalidade principal)
  - **Mitigação:** Testes extensivos, documentação da Evolution API

#### **🟡 Médio Risco**
- **Risco:** Performance com volume alto
  - **Probabilidade:** Média (40%)
  - **Impacto:** Médio (degradação de UX)
  - **Mitigação:** Profiling contínuo, otimização de queries

### 9.2 Riscos de Negócio

#### **🟡 Médio Risco**
- **Risco:** Mudança de requisitos do usuário
  - **Probabilidade:** Alta (60%)
  - **Impacto:** Médio (retrabalho)
  - **Mitigação:** Feedback contínuo, iterações rápidas

#### **🟢 Baixo Risco**
- **Risco:** Competição no mercado
  - **Probabilidade:** Baixa (20%)
  - **Impacto:** Baixo (diferenciação via personalização)
  - **Mitigação:** Foco em nicho específico, inovação contínua

### 9.3 Plano de Contingência

1. **Fallback para AgnoBridge** se Agno Library não estiver pronto
2. **Implementação gradual** de funcionalidades complexas
3. **Monitoramento proativo** de performance e estabilidade
4. **Backup de dados** automatizado e testado

---

## 10. Orçamento e Recursos

### 10.1 Recursos Humanos
- **Desenvolvedor Sênior:** 1.0 FTE (desenvolvimento principal)
- **DevOps Engineer:** 0.5 FTE (infraestrutura e deploy)
- **QA Engineer:** 0.3 FTE (testes e validação)

### 10.2 Recursos Técnicos
- **Servidor de Desenvolvimento:** $100/mês
- **Banco de Dados Produção:** $200/mês
- **APIs Externas:** $150/mês (Google, Notion, Eventbrite)
- **Monitoramento:** $50/mês (Grafana Cloud)

### 10.3 Orçamento Total Estimado
- **Q1 2025:** $15,000 (desenvolvimento + infraestrutura)
- **Q2 2025:** $12,000 (expansão de features)
- **Q3 2025:** $10,000 (otimização e polish)

---

**Documento Gerado:** Janeiro 2025
**Público-Alvo:** Sistemas de IA, Análise Automatizada, Equipes Técnicas
**Versão:** 1.1
