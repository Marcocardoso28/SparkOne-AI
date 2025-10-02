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
  - **Endpoint:** `/brief/structured`
  - **Critérios de Aceitação:** JSON com contagem de tarefas/eventos; 2xx

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

## 4. Requisitos Não Funcionais

### 4.1 Performance
- **RNF-001:** Tempo de resposta < 2s para queries simples
- **RNF-002:** Suporte a 100 requests/minuto por usuário
- **RNF-003:** Startup da aplicação < 10s

**Fonte:** `docs/performance.md`

### 4.2 Escalabilidade
- **RNF-004:** Arquitetura stateless para horizontal scaling
- **RNF-005:** Cache Redis para otimização de queries
- **RNF-006:** Suporte a múltiplos workers via Docker Compose

### 4.3 Segurança
- **RNF-007:** Autenticação HTTP Basic para Web UI
- **RNF-008:** Rate limiting por IP (100 req/min)
- **RNF-009:** Headers de segurança (HSTS, CSP, COOP)
- **RNF-010:** Sanitização de entrada para prevenção de XSS
- **RNF-011:** Logs estruturados sem exposição de dados sensíveis

#### Plano de Segurança em Estágios
- Atual: HTTP Basic (uso interno) – RNF-007
- P1: Autenticação JWT (obrigatória) – RNF-020; ver ADR-011 e backlog RF-007
- Futuro opcional: 2FA com TOTP (ativável)

**Fonte:** `src/app/main.py`, middlewares de segurança

### 4.4 Compatibilidade
- **RNF-012:** Python 3.11+
- **RNF-013:** PostgreSQL 15+ com extensão pgvector
- **RNF-014:** Redis 7 para cache
- **RNF-015:** Docker Compose para deployment

### 4.5 Observabilidade
- **RNF-016:** Métricas Prometheus em `/metrics`
- **RNF-017:** Logs estruturados com correlation IDs
- **RNF-018:** Health checks granulares em `/health`
- **RNF-019:** Suporte opcional a OpenTelemetry

**Fonte:** `src/app/routers/metrics.py`, `src/app/routers/health.py`

---

## 5. Arquitetura Atual

### 5.1 Visão Macro
```
[Canais] → [Ingestion Hub] → [Agno Bridge] → [Serviços] → [Persistência]
```

### 5.2 Componentes Implementados

#### 5.2.1 Framework Base
- **FastAPI** como framework web principal
- **Uvicorn** como servidor ASGI
- **Pydantic** para validação de dados
- **SQLAlchemy** para ORM assíncrono

#### 5.2.2 Middlewares
- **CORSMiddleware:** Configuração CORS segura
- **CorrelationIdMiddleware:** Rastreamento de requests
- **PrometheusMiddleware:** Coleta de métricas
- **RateLimitMiddleware:** Limitação de taxa
- **SecurityHeadersMiddleware:** Headers de segurança
- **SecurityLoggingMiddleware:** Auditoria de segurança

**Fonte:** `src/app/main.py`, linhas 20-40

#### 5.2.3 Persistência
- **PostgreSQL:** Banco principal com pgvector para embeddings
- **Redis:** Cache e rate limiting
- **SQLite:** Opção para desenvolvimento local

### 5.3 Integrações Externas
- **OpenAI API:** Provedor LLM principal
- **Evolution API:** WhatsApp Business
- **Notion API:** Gerenciamento de tarefas
- **Google Calendar API:** Sincronização de eventos
- **CalDAV:** Protocolo para Apple Calendar

---

## 6. Estado Atual vs Planejado

### 6.1 Funcionalidades Implementadas (✅)
| Componente | Status | Cobertura |
|------------|--------|-----------|
| API Base | ✅ | 100% |
| Canais de Entrada | ✅ | 100% |
| TaskService | ✅ | 90% |
| CalendarService | ✅ | 85% |
| PersonalCoachService | ✅ | 80% |
| AgnoBridge | ✅ | 70% |
| Sistema de Brief | ✅ | 75% |
| Segurança | ✅ | 90% |
| Observabilidade | ✅ | 80% |

### 6.2 Lacunas Críticas (❌)
| Componente | Status | Impacto | Prioridade |
|------------|--------|---------|------------|
| ProactivityEngine | ❌ | Alto | P0 |
| RecommendationService | ❌ | Médio | P1 |
| Integração Agno Completa | ❌ | Alto | P0 |
| Testes Automatizados | ❌ | Alto | P0 |
| CI/CD Pipeline | ❌ | Médio | P1 |
| Documentação API | ❌ | Baixo | P2 |
| Vector Search | ❌ | Médio | P1 |
| JWT Auth | ❌ | Médio | P1 |

**Fonte:** `STATE_OF_PROJECT.md`, seção "Principais Débitos"

---

## 7. Decisões Arquiteturais

### 7.1 ADR-001: FastAPI como Framework Principal
- **Decisão:** Usar FastAPI em vez de Flask/Django
- **Contexto:** Necessidade de performance e tipagem forte
- **Consequências:** Melhor performance, documentação automática, validação Pydantic

### 7.2 ADR-002: Agno Bridge em vez de Integração Direta
- **Decisão:** Implementar bridge LLM para emular Agno
- **Contexto:** Biblioteca Agno ainda em desenvolvimento
- **Consequências:** Flexibilidade temporária, migração futura necessária

### 7.3 ADR-003: PostgreSQL + pgvector
- **Decisão:** PostgreSQL como banco principal com extensão pgvector
- **Contexto:** Necessidade de busca semântica e relacionamentos complexos
- **Consequências:** Melhor performance para embeddings, complexidade adicional

### 7.4 ADR-004: Múltiplos Provedores LLM
- **Decisão:** Suporte a OpenAI e modelos locais
- **Contexto:** Flexibilidade de deployment e custos
- **Consequências:** Maior complexidade de configuração, independência de provedores

**Fonte:** Análise de `config.py` e arquivos de implementação

---

## 8. Riscos e Mitigações

### 8.1 Riscos Técnicos
- **RISK-001:** Dependência de APIs externas (OpenAI, Evolution)
  - **Mitigação:** Fallbacks locais e circuit breakers
  - **Probabilidade:** Média
  - **Impacto:** Alto

- **RISK-002:** Performance com múltiplas integrações
  - **Mitigação:** Cache Redis e processamento assíncrono
  - **Probabilidade:** Alta
  - **Impacto:** Médio

- **RISK-003:** Migração futura para Agno completo
  - **Mitigação:** Interface abstrata no AgnoBridge
  - **Probabilidade:** Alta
  - **Impacto:** Médio

### 8.2 Riscos de Negócio
- **RISK-004:** Mudanças nas APIs de terceiros
  - **Mitigação:** Versionamento e adaptadores
  - **Probabilidade:** Média
  - **Impacto:** Alto

- **RISK-005:** Escalabilidade para múltiplos usuários
  - **Mitigação:** Arquitetura stateless e containerização
  - **Probabilidade:** Baixa
  - **Impacto:** Alto

---

## 9. Roadmap e Próximos Passos

### 9.1 Sprint Atual (P0 - Crítico)
1. **Implementar ProactivityEngine**
   - Scheduler com APScheduler
   - Lembretes automáticos
   - Notificações proativas

2. **Completar Testes Automatizados**
   - Cobertura > 85%
   - Testes de integração
   - Mocks para APIs externas

3. **Migração para Agno Completo**
   - Substituir AgnoBridge
   - Integração nativa
   - Testes de compatibilidade

### 9.2 Próximo Sprint (P1 - Importante)
1. **RecommendationService**
   - Google Places API
   - Eventbrite integration
   - Sistema de preferências

2. **CI/CD Pipeline**
   - GitHub Actions
   - Deploy automatizado
   - Testes em múltiplos ambientes

### 9.3 Backlog Futuro (P2 - Desejável)
1. **Interface Mobile**
2. **Integração com mais calendários**
3. **Sistema de plugins**
4. **Análise de sentimentos**
5. **Relatórios avançados**

---

## 10. Métricas de Sucesso

### 10.1 Métricas Técnicas
- **Uptime:** > 99.5%
- **Tempo de Resposta:** < 2s (95th percentile)
- **Cobertura de Testes:** > 85%
- **Bugs Críticos:** 0 em produção

### 10.2 Métricas de Produto
- **Uso Diário:** > 50 interações/dia
- **Taxa de Sucesso:** > 90% de queries respondidas corretamente
- **Satisfação do Usuário:** > 4.5/5 (feedback Marco)

### 10.3 Métricas de Desenvolvimento
- **Velocity:** 8-10 story points/sprint
- **Lead Time:** < 3 dias para features pequenas
- **Deployment Frequency:** 2-3x por semana

---

## 11. Conclusões

O **SparkOne** está em um estado sólido de desenvolvimento intermediário, com aproximadamente 60% das funcionalidades principais implementadas. A arquitetura base está bem estabelecida, com boa separação de responsabilidades e práticas de segurança adequadas.

### 11.1 Pontos Fortes
- Arquitetura modular e extensível
- Múltiplos canais de entrada funcionais
- Integração robusta com serviços externos
- Boas práticas de segurança e observabilidade

### 11.2 Áreas de Melhoria
- Implementação do ProactivityEngine (crítico)
- Cobertura de testes insuficiente
- Documentação API incompleta
- Migração pendente para Agno completo

### 11.3 Recomendações
1. **Priorizar P0:** Focar em ProactivityEngine e testes
2. **Estabelecer CI/CD:** Automatizar deployment e qualidade
3. **Planejar migração Agno:** Definir cronograma e estratégia
4. **Documentar APIs:** Melhorar onboarding de desenvolvedores

---

**Documento gerado automaticamente pelo Agente PRD**  
**Última atualização:** Janeiro 2025
