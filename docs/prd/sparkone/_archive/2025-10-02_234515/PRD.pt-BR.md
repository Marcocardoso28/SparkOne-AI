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

