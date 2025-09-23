# SparkOne – Especificação Técnica Consolidada 2025

## 1. Visão Geral
SparkOne é o assistente pessoal de Marco Cardoso, inspirado no conceito "Jarvis". Ele opera com persona fixa – "SparkOne, assistente pessoal do Marco Cardoso" – cuidando de agenda, equipe, lembretes, correções de texto e recomendações personalizadas. O sistema foi desenhado para crescer em módulos, iniciando por um MVP robusto e evoluindo para uma arquitetura multiagente de última geração conforme a maturidade aumentar.

### 1.1 Objetivos Principais
- Capturar tarefas/eventos por múltiplos canais (WhatsApp, Google Sheets, Web UI minimalista).
- Sincronizar compromissos com Apple Calendar (CalDAV) ou Google Calendar, selecionável por usuário.
- Manter brief diário, lembretes de SLA e cobranças automáticas.
- Guardar memória longa de conversas, normas internas e preferências.
- Corrigir textos, sugerir melhorias e atuar como assistente pessoal contextualizado.
- Recomendar atividades e lazer com base em localização e preferências.

### 1.2 Escopo Inicial
- MVP local com Docker Compose + ngrok, usando FastAPI, Agno, Postgres+pgvector e Redis.
- Evolução planejada para VPS com Traefik/HTTPS, observabilidade e hardening.
- Hooks preparados para migração futura para LangGraph, Litestar e Qdrant sem refatorações extensas.

### 1.3 Diferenciais
- Persona consistente e controle de linguagem (sem mencionar provedores).
- Memória híbrida (buffer recente + busca semântica) para personalização profunda.
- Design modular permitindo adicionar novos canais, integrações e agentes especializados.

---

## 2. Arquitetura do Sistema

### 2.1 Visão Macro (MVP)
```
[WhatsApp]   [Google Sheets]   [Web UI]
     │              │              │
     └──────► Ingestion Hub (FastAPI /routers)
                     │
             Message Normalizer
                     │
             Agno Orchestrator
          ┌─────────┼───────────────┐
          │         │               │
   Classification  Task/Calendar   Personal Coach
        Agent         Services          Agent
          │              │               │
          └──────────────┴───────┬──────┘
                                 │
            Postgres + pgvector (estado + memória)
                                 │
                               Redis
                                 │
                       WhatsApp Outbound / Alerts
```

### 2.2 Componentes Principais
- **Canais de Entrada**: Evolution API (WhatsApp), Google Sheets API, Web UI minimalista (FastAPI + Jinja2 ou microfrontend).
- **Ingestion Hub**: rotas `/ingest`, `/sheets`, `/webform`, `/docs` padronizam payloads (`ChannelMessage`).
- **Agno Orchestrator**: agentes para classificação, tarefas/calendário, personal coach, brief/insights e recomendações.
- **Serviços de Domínio**:
  - `TaskService`: integra Notion e mantém snapshots no Postgres.
  - `CalendarService`: interface de provider (CalDAV e Google AR). Permite seleção por usuário.
  - `ProactivityEngine`: scheduler (APScheduler) para brief, lembretes e notificações.
  - `PersonalCoachService`: correções de texto, sugestões e ações personalizadas.
  - `RecommendationService`: integra APIs de localização (Google Places/Eventbrite).
- **Persistência**:
  - Postgres 15+ (estado transacional, auditoria, preferências, histórico curto de conversas).
  - pgvector (extensão) para embeddings e busca semântica.
  - Redis 7 (cache, TTL de recomendações, filas assíncronas, rate limiting).
  - Storage externo (Google Drive/S3) para documentos pesados; Postgres guarda metadados/links.
- **Persona & Respostas**: prompts garantem voz SparkOne e bloqueiam menção a provedores externos.

### 2.3 Evolução Multiagente (Trilha Avançada)
```
┌─────────────── Input Channels ───────────────┐
│  WhatsApp    Google Sheets    Web UI         │
└─────────────┬───────────────────────────────┘
              │
         Litestar Gateway
              │
        LangGraph Router
  ┌────────────┼────────────┬─────────────┐
  │            │            │             │
Classifica-   Task       Personal      Memory
 tion Agent  Agent       Coach Agent   Agent
  │            │            │             │
  └────────────┴─────┬──────┴─────┬──────┘
                      │
                 Qdrant Vector
                      │
                 PostgreSQL Core
```
- LangGraph com handoffs inteligentes e estado compartilhado.
- Qdrant substitui pgvector para busca vetorial de alta performance.
- Litestar como gateway HTTP com melhor throughput e arquitetura modular.
- Camada de segurança alinhada às diretrizes CISA (detecção de prompt injection, auditoria reforçada).

---

## 3. Memória, Conhecimento e Dados
- **Memória de Conversa**: mensagens recentes em buffer (Redis ou memória Agno) + persistência no Postgres para histórico filtrável.
- **Memória Longa**: embeddings em pgvector (ou Qdrant) para lembrar fatos, normas, preferências. `Knowledge Ingestion Service` indexa documentos (PDF/Markdown) e anotações via UI/script (`scripts/ingest_docs.py`).
- **Preferências**: tabela dedicada no Postgres com estilo de comunicação, horários de preferência, temas de lazer.
- **Política de Retenção**: histórico completo por 12 meses; após isso arquivado em storage frio (Google Drive/S3) em formato cifrado.

---

## 4. Segurança e Compliance

### 4.1 Governança
- Separar ambientes (dev/staging/prod) com credenciais próprias e dados mascarados fora da produção.
- Gestão de segredos: `.env` protegido em dev e Secret Manager/Vault em produção.
- Controle de acesso por função (RBAC) na Web UI/API; MFA quando exposto externamente.
- Auditoria de mutações (tarefas, eventos, preferências) com trilha imutável no Postgres e exportação periódica para storage WORM.

### 4.2 Proteção de Dados
- TLS obrigatório (ngrok, Traefik com Let’s Encrypt).
- Banco em volume cifrado (LUKS/TDE) e backups criptografados (pg_dump + GPG ou serviço gerenciado).
- Mascaramento de PII em logs, versões e monitoramento.

### 4.3 Segurança das Integrações
- Evolution API: assinatura verificada a cada webhook, rate limiting com Redis, proteção contra replay (nonce/TTL).
- Notion/Google/Apple: tokens com escopo mínimo, armazenamento seguro, rotação automática e revogação em incidente.
- Storage externo: upload opcionalmente cifrado antes do envio (dependendo da sensibilidade).

### 4.4 Privacidade e LGPD
- Consentimento explícito e registro versionado.
- Anonimização/eliminação sob demanda.
- Data minimization: somente dados necessários para cada serviço.

### 4.5 Hardening Operacional
- Atualizações contínuas (SO, Python, dependências) com automação.
- Firewall + fail2ban no VPS; portas expostas apenas para serviços necessários.
- Monitoramento de vulnerabilidades (Dependabot, pip-audit) e testes de penetração periódicos.

### 4.6 Trilha Avançada – CISA AI Security
- Camada `AISecurityLayer` com `PromptInjectionGuard`, `DataSanitizer` e `AuditLogger`.
- Monitoramento de uso do agente, alertas em tempo real e respostas automatizadas a incidentes.

---

## 5. Observabilidade e Operação
- Endpoints `/health` (readiness/liveness) e checks específicos (`/health/database`, `/health/redis`).
- Logging estruturado (structlog) com correlação de request/agent.
- OpenTelemetry para tracing (gateway → agente → integrações).
- Sentry para captura de exceções.
- Prometheus/Grafana para métricas (tráfego, latência, falhas, consumo por agente) + alertas (pager/email/WhatsApp).

---

## 6. Stack Tecnológica

| Camada | MVP (2025 Q1) | Trilha Avançada (2025 Q3+) | Observações |
| --- | --- | --- | --- |
| Linguagem | Python 3.11 | Python 3.12 | Atualizar quando Libs 100% compatíveis |
| API | FastAPI | Litestar | Litestar oferece ~30% mais throughput |
| Orquestração | Agno | LangGraph | Handoffs e state management avançados |
| Banco | Postgres 15 + pgvector | Postgres 16 + Qdrant | Qdrant para coleções dedicadas |
| Cache/Fila | Redis 7 | Redis 7 (cluster opcional) | TTL de recomendações, rate limiting |
| Scheduler | APScheduler | LangGraph timers/Workers | Pode migrar para worker dedicado |
| Integrations | Evolution API, Notion, CalDAV, Google Calendar, Google Sheets, Google Places | + outros canais (Slack, e-mail, voz) | Via novos adaptadores |
| Observabilidade | structlog, OpenTelemetry, Sentry, Prometheus | + tracing distribuído, dashboards avançados | |
| Segurança | TLS + RBAC + backups cifrados | + CISA AI guidelines | Prompt injection guard, auditoria reforçada |
| Qualidade | pre-commit, Ruff, Black, mypy, pytest | idem | CI obrigatório |

---

## 7. Docker Compose (Ambiente Local – MVP)
```yaml
version: "3.9"

services:
  api:
    build: .
    command: uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DATABASE_URL=postgresql+asyncpg://sparkone:sparkone@db:5432/sparkone
      - VECTOR_STORE_URL=postgresql://sparkone:sparkone@db:5432/sparkone
      - REDIS_URL=redis://cache:6379/0
      - NOTION_API_KEY=${NOTION_API_KEY}
      - EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
      - CALDAV_URL=${CALDAV_URL}
      - CALDAV_USERNAME=${CALDAV_USERNAME}
      - CALDAV_PASSWORD=${CALDAV_PASSWORD}
      - GOOGLE_CALENDAR_CREDENTIALS_PATH=/secrets/google_calendar.json
      - GOOGLE_SHEETS_CREDENTIALS_PATH=/secrets/google_sheets.json
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - PERSONA_NAME=\"SparkOne\"
      - TZ=America/Sao_Paulo
    volumes:
      - .:/app
      - ./secrets:/secrets:ro
    ports:
      - "8000:8000"
    depends_on:
      - db
      - cache

  worker:
    build: .
    command: python -m src.app.workers.scheduler
    environment:
      - DATABASE_URL=postgresql+asyncpg://sparkone:sparkone@db:5432/sparkone
      - VECTOR_STORE_URL=postgresql://sparkone:sparkone@db:5432/sparkone
      - REDIS_URL=redis://cache:6379/0
      - TZ=America/Sao_Paulo
    volumes:
      - .:/app
      - ./secrets:/secrets:ro
    depends_on:
      - db
      - cache

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=sparkone
      - POSTGRES_USER=sparkone
      - POSTGRES_PASSWORD=sparkone
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    command: >
      postgres -c shared_preload_libraries=pg_stat_statements
               -c max_connections=200
               -c shared_buffers=256MB

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ngrok:
    image: ngrok/ngrok:latest
    command: http api:8000
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    depends_on:
      - api

volumes:
  pgdata:
```

### Produção
- Remover `--reload` e executar via Gunicorn/Uvicorn workers.
- Adicionar Traefik/Nginx com TLS, health checks e circuit breaker básico.
- Separar workers para scheduler/filas, habilitar backups automáticos.

### Overlay Avançado (quando migrar)
- Adicionar serviços `qdrant` e alterar variáveis para `QDRANT_URL`.
- Substituir `api` por `litestar run ...` e atualizar orquestração para LangGraph.

---

## 8. Estrutura de Pastas
```
SparkOne/
├── README.md
├── SPEC.md
├── docker-compose.yml
├── infra/
│   ├── traefik/
│   │   └── traefik.toml
│   └── nginx/
│       └── nginx.conf
├── src/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── settings/
│   │   │   ├── persona.py
│   │   │   └── providers.py
│   │   ├── routers/
│   │   │   ├── ingest.py
│   │   │   ├── sheets.py
│   │   │   ├── webform.py
│   │   │   ├── brief.py
│   │   │   └── health.py
│   │   ├── channels/
│   │   │   ├── whatsapp.py
│   │   │   ├── google_sheets.py
│   │   │   └── web_ui.py
│   │   ├── services/
│   │   │   ├── classification.py
│   │   │   ├── tasks.py
│   │   │   ├── calendar.py
│   │   │   ├── proactivity.py
│   │   │   ├── personal_coach.py
│   │   │   └── recommendations.py
│   │   ├── knowledge/
│   │   │   ├── ingestion.py
│   │   │   ├── retriever.py
│   │   │   └── vector_store.py
│   │   ├── integrations/
│   │   │   ├── evolution_api.py
│   │   │   ├── notion.py
│   │   │   ├── caldav.py
│   │   │   ├── google_calendar.py
│   │   │   └── google_places.py
│   │   ├── agents/
│   │   │   ├── orchestrator.py
│   │   │   ├── tools/
│   │   │   │   ├── whatsapp_tool.py
│   │   │   │   ├── notion_tool.py
│   │   │   │   ├── calendar_tool.py
│   │   │   │   ├── knowledge_tool.py
│   │   │   │   └── location_tool.py
│   │   │   └── prompts/
│   │   ├── models/
│   │   │   ├── schemas.py
│   │   │   └── db/
│   │   │       ├── base.py
│   │   │       ├── repositories.py
│   │   │       └── vector_models.py
│   │   └── workers/
│   │       ├── scheduler.py
│   │       └── tasks.py
│   ├── web/
│   │   ├── templates/
│   │   └── static/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── migrations/
├── scripts/
│   ├── bootstrap.sh
│   ├── seed_data.py
│   └── ingest_docs.py
├── .env.example
└── pyproject.toml
```
- Migração para LangGraph adiciona `src/app/graph/` (workflows, state models) e `src/app/security/` (prompt_injection, data_sanitizer, audit_logger).

---

## 9. Fluxos de Uso

### 9.1 Ingestão Geral
1. Usuário envia mensagem via WhatsApp / Web UI / atualiza planilha.
2. Ingestion Hub valida e normaliza, criando `ChannelMessage`.
3. Agno Classifier decide: `TAREFA`, `EVENTO`, `COACHING`, `OUTRO`.
4. Serviço especializado executa ação:
   - `TAREFA`: cria/atualiza no Notion + snapshot no Postgres.
   - `EVENTO`: sincroniza com provider escolhido (CalDAV/Google) + Postgres.
   - `COACHING`: PersonalCoachService corrige/sugere e registra contexto.
   - `OUTRO`: Brief/Recommendation/Follow-up conforme regras.
5. Conversa e contexto são persistidos (texto + embedding + metadados).
6. Resposta com persona SparkOne e contexto relevante.

### 9.2 Brief Diário (07h30)
- Scheduler dispara pipeline; consulta tarefas pendentes, eventos do dia, status da equipe, recomendações relevantes.
- Agno gera resumo executivo e envia via WhatsApp; histórico arquivado.

### 9.3 Recomendações de Lazer
- SparkOne obtém localização atual (entrada manual ou evento recente).
- Consulta Google Places/Event APIs e cruza com preferências.
- Envia lista personalizada e agenda follow-ups (ex.: reservar horário).

### 9.4 Correção de Textos
- Usuário solicita revisão; PersonalCoachService chama ferramenta de proofreading.
- Resposta inclui texto corrigido, justificativas e ações sugeridas (ex.: transformar em tarefa).

---

## 10. Roadmap de Desenvolvimento

### Sprint 0 – Fundamentos (Semana 1)
- Configurar repositório, CI, pre-commit, pipelines de qualidade.
- FastAPI skeleton (`/health`, `/ingest` placeholder) e persona básica.
- Docker Compose (API, worker, Postgres, Redis, ngrok) funcionando.
- Agno integrado com ferramentas mock; logs estruturados e mascaramento inicial.

### Sprint 1 – Ingestão Multicanal (Semanas 2–3)
- Implementar adaptadores WhatsApp (Evolution API) e Google Sheets.
- Criar Web UI minimalista com autenticação simples.
- Message normalizer + persistência de mensagens/embeddings.
- Testes unitários/integrados de ingestão.

### Sprint 2 – Classificação, Tarefas e Calendário (Semanas 4–5)
- Treinar classificador (TAREFA/EVENTO/OUTRO/COACHING).
- `TaskService` (Notion + Postgres), `CalendarService` (CalDAV/Google) com seleção por usuário.
- Auditoria de tarefas/eventos, notificações básicas.

### Sprint 3 – Proatividade & Brief (Semanas 6–7)
- Scheduler APScheduler + worker dedicado.
- Brief diário 07h30, lembretes SLA, follow-ups e notificações de falha.
- Métricas básicas de equipe.

### Sprint 4 – Memória & Conhecimento (Semanas 8–9)
- Knowledge ingestion (`scripts/ingest_docs.py`, upload UI).
- Integração pgvector com Agno (busca semântica).
- PersonalCoachService (correção, sugestões, preferências).
- Testes de recuperação semântica e QA manual.

### Sprint 5 – Segurança & Produção (Semanas 10–11)
- Autenticação avançada (OAuth2 + MFA) na Web UI.
- Traefik + HTTPS, firewall, fail2ban, rate limiting.
- Sentry, Prometheus, runbooks, backups automáticos e testes de restauração.
- Revisão LGPD e plano de resposta a incidentes.

### Sprint 6 – Recomendações Contextuais (Semanas 12–13)
- Captura de localização + preferências.
- RecommendationService (Google Places/Event APIs), caching e limites de uso.
- Relatórios de uso e ajustes de persona.

### Trilha Avançada (release separado)
- Migrar orquestração para LangGraph (multiagente) e Litestar.
- Introduzir Qdrant, security layer CISA e observabilidade distribuída.
- Novos canais (Slack, e-mail, voz) e dashboards analíticos.

---

## 11. Fluxo de Desenvolvimento Local
1. Copiar `.env.example` → `.env`, preencher credenciais (Evolution, Notion, CalDAV, Google, Places, ngrok).
2. Armazenar credenciais Google (`google_calendar.json`, `google_sheets.json`) em `secrets/` (montado como read-only).
3. Executar `docker-compose up --build`.
4. Configurar webhook Evolution API apontando para URL do ngrok.
5. Acessar `http://localhost:8000/docs` (Swagger) e `/web` (UI).
6. Rodar `alembic upgrade head`.
7. Popular base com `scripts/seed_data.py` (opcional) e `scripts/ingest_docs.py`.
8. Executar `pytest` e `pre-commit run --all-files` antes de commits.
9. Testar manualmente fluxos principais (tarefas, eventos, correções, recomendações).

---

## 12. Estratégia de Testes
- **Unitários**: serviços de domínio, adaptadores de canal, validações.
- **Integração**: Notion, calendários, Google APIs com mocks/sandboxes.
- **End-to-End**: fluxo WhatsApp ↔ FastAPI ↔ Agno ↔ integrações.
- **Performance**: testes de carga (picos de mensagens, rotação de briefings).
- **Segurança**: varreduras automatizadas, testes de penetração, validação de RBAC e rate limiting.
- **Observabilidade**: alertas para falhas no brief, erros de canal, uso de APIs.

---

## 13. Custos & Escalabilidade
- VPS inicial (12–16 USD/mês) suporta FastAPI + Postgres + Redis + Traefik.
- Armazenamento 20–50 GB (incluso na maioria dos planos); aumentar conforme normas/conversas.
- pgvector sem custo adicional; Qdrant pode rodar em container próprio (custo de disco) ou serviço gerenciado (planos free/baixo custo).
- Google Drive/S3 para documentos grandes (aproveitar plano existente).
- Escalar com particionamento de tabelas, storage frio, serviços gerenciados (RDS, Neon) conforme crescimento.

---

## 14. Trilha Avançada – Estado da Arte 2025
- **LangGraph Multi-Agent**: RouterAgent, TaskAgent, MemoryAgent, PersonalCoachAgent, RecommendationAgent com handoffs. Compartilhamento de estado via `StateGraph`.
- **Litestar Gateway**: API mais performática com suporte a injeção de dependências e timeouts granulares.
- **Qdrant Vector Store**: coleções `conversations` e `knowledge_base` (embeddings 1536, distância cosine), replicação e filtragem avançada.
- **Security Layer CISA**: defesa contra prompt injection, sanitização, auditoria, respostas automáticas.
- **Observabilidade Distribuída**: tracing full-stack (gateway → agente → integrações), dashboards e alertas refinados.
- Implantar após MVP estabilizado; manter compatibilidade com serviços existentes.

---

## 15. Próximos Passos
1. Revisar/aprovar este SPEC e criar issues da Sprint 0.
2. Configurar repositório (CI/CD, pre-commit, templates de PR) e preparar ambiente local.
3. Levantar credenciais e permissões (Evolution, Notion, Apple, Google, Places, ngrok).
4. Elaborar política interna de segurança/LGPD e runbooks operacionais.
5. Definir marcos para avaliar migração LangGraph/Litestar/Qdrant após MVP.

---

SparkOne está preparado para atender ao presente com um MVP sólido e evoluir para uma plataforma multiagente avançada, mantendo segurança, observabilidade e governança desde o início.
