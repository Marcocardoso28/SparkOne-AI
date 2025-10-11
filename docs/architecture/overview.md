# SparkOne - Visão Geral da Arquitetura

**Versão:** v1.1.0  
**Data:** Janeiro 2025  

---

## 🎯 Visão e Objetivos

### Visão
Criar um copiloto pessoal que combina ingestão multicanal (WhatsApp, Web, Sheets) com agentes especializados para lembrar compromissos, organizar tarefas e responder com a persona "SparkOne".

### Objetivos 2025
- ✅ Entregar um assistente confiável para uso diário focando em tarefas, agenda e briefs automáticos
- ✅ Garantir privacidade e segurança adequadas para dados pessoais (LGPD-ready)
- 🚀 Abrir caminho para operação autônoma (integração com agentes externos e automação de rotinas)

---

## 🏗️ Arquitetura Geral

### Macro-Arquitetura
```text
Canais → Normalizador → Orquestração (Agno) → Serviços Domínio → Persistência (PostgreSQL + Redis + pgvector)
                                          ↘ Observabilidade / Alertas ↘ Webhooks externos
```

### Componentes Principais
1. **Canais de Entrada** - WhatsApp, Web UI, Google Sheets
2. **Normalizador** - Conversão de mensagens para formato padrão
3. **Orquestração** - Agno como núcleo de coordenação
4. **Serviços Domínio** - Tasks, Calendar, Coach, Memory
5. **Persistência** - PostgreSQL + Redis + pgvector
6. **Observabilidade** - Prometheus, Grafana, Alertmanager

---

## 🎯 Domínios Principais

### 1. Interação
- **Canais:** WhatsApp (Evolution API), Web UI, Google Sheets
- **Normalização:** Conversão de mensagens para formato padrão
- **Prompts:** Templates para diferentes tipos de interação

### 2. Produtividade
- **Tarefas:** Sincronização com Notion
- **Agenda:** Integração Google Calendar/CalDAV
- **Briefings:** Consolidação automática de informações

### 3. Conhecimento
- **Ingestão:** Processamento de documentos
- **Busca:** Semântica com pgvector
- **Memória:** Armazenamento de insights e contexto

### 4. Infraestrutura
- **Observabilidade:** Métricas, logs, alertas
- **Backups:** Automatização e verificação
- **Segurança:** Rate limiting, autenticação, headers

---

## 🔄 Fluxo de Dados

### 1. Ingestão de Mensagens
```
Canal → IngestionService → ChannelMessage → Orchestrator
```

### 2. Processamento
```
Orchestrator → ClassificationService → Domain Services → Response
```

### 3. Persistência
```
Domain Services → Repository → PostgreSQL/Redis
```

### 4. Observabilidade
```
All Components → Metrics → Prometheus → Grafana
```

---

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web moderno e performático
- **SQLAlchemy** - ORM com suporte async
- **PostgreSQL** - Banco principal com pgvector para embeddings
- **Redis** - Cache e rate limiting
- **Pydantic** - Validação de dados

### IA e ML
- **Agno** - Orquestração de agentes
- **LangChain/LangGraph** - Preparado para migração
- **Embeddings** - Busca semântica híbrida

### Infraestrutura
- **Docker Compose** - Containerização
- **Prometheus** - Métricas
- **Grafana** - Dashboards
- **Alertmanager** - Alertas
- **Traefik** - Proxy reverso

### Observabilidade
- **Structlog** - Logging estruturado
- **Prometheus** - Métricas
- **Health checks** - Endpoints de saúde
- **Correlation IDs** - Rastreamento de requisições

---

## 🔒 Princípios Arquiteturais

### 1. Modular
- Separação clara de responsabilidades
- Interfaces bem definidas
- Desacoplamento entre camadas

### 2. Seguro por Padrão
- Rate limiting implementado
- Logging com rastreabilidade
- Política de secrets rígida
- Headers de segurança

### 3. Observável
- Métricas de ponta a ponta
- Tracing distribuído
- Health checks abrangentes
- Alertas automatizados

### 4. Automatizado
- Provisionamento via Docker
- Testes em CI/CD
- Pipelines de backup
- Deploy automatizado

---

## 📊 Status da Implementação

### ✅ **100% Implementado**
- **Estrutura Modular** - Separação clara de camadas
- **API REST** - Todos os endpoints funcionais
- **Autenticação** - Login/logout com verificação de senha
- **Health Checks** - Endpoints de saúde completos
- **Task Management** - CRUD completo com paginação
- **Message Ingestion** - Processamento de mensagens
- **Security Headers** - Headers de segurança configurados
- **Rate Limiting** - Limitação de requisições com Redis

### 🚀 **Preparado para Escala**
- **Database Schema** - Estrutura preparada para crescimento
- **Caching Layer** - Redis para performance
- **Monitoring** - Observabilidade completa
- **Backup Strategy** - Estratégia de backup automatizada

---

## 🎯 Casos de Uso Implementados

### 1. ✅ Gestão de Tarefas
- Receber tarefas via WhatsApp e sincronizar com Notion
- CRUD completo de tarefas via API
- Filtros e paginação
- Status tracking

### 2. ✅ Processamento de Mensagens
- Ingestão multicanal (WhatsApp, Web, REST)
- Normalização de mensagens
- Roteamento inteligente
- Persistência de contexto

### 3. ✅ Autenticação e Segurança
- Login com username/email
- Verificação de senha
- Headers de segurança
- Rate limiting

### 4. ✅ Monitoramento e Saúde
- Health checks abrangentes
- Métricas de sistema
- Logs estruturados
- Alertas automatizados

---

## 🔮 Roadmap Arquitetural

### Próximas Versões
- **v1.2.0** - ProactivityEngine e notificações automáticas
- **v1.3.0** - Vector search e recommendation service
- **v1.4.0** - Migração para LangGraph
- **v2.0.0** - Multi-tenant e escalabilidade avançada

### Evolução Planejada
- **Agents Autônomos** - Operação independente
- **Multi-Modal** - Suporte a voz e imagem
- **Real-time** - WebSockets e notificações push
- **Edge Computing** - Processamento distribuído

---

## 📚 Decisões Arquiteturais (ADRs)

### ADA-001 - FastAPI + Estrutura em Camadas
- **Decisão:** Manter FastAPI com routers finos e services aplicacionais
- **Alternativas:** Litestar, Django Rest Framework
- **Status:** ✅ Implementado

### ADA-002 - Orquestração Agno
- **Decisão:** Utilizar Agno como núcleo de orquestração
- **Alternativas:** LangChain, CrewAI
- **Status:** ✅ Implementado

### ADA-003 - Persistência PostgreSQL + Redis
- **Decisão:** PostgreSQL 15 com pgvector + Redis para cache
- **Alternativas:** Supabase, Neon + Qdrant
- **Status:** ✅ Implementado

### ADA-004 - Segurança Web Incremental
- **Decisão:** Auth básica com roadmap para OAuth2 + MFA
- **Alternativas:** Auth0, Clerk, Cloudflare Access
- **Status:** ✅ Implementado

### ADA-005 - Gestão de Conhecimento Controlada
- **Decisão:** Ingestão via scripts dedicados com revisão manual
- **Alternativas:** Automação via agentes autônomos
- **Status:** ✅ Implementado

---

**Arquitetura validada e pronta para produção em Janeiro 2025**
