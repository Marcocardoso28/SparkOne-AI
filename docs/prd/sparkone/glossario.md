# Glossário - SparkOne
## Termos-Chave, Bibliotecas e Componentes

**Versão:** 1.1
**Data:** Outubro 2025
**Público:** Desenvolvedores, Stakeholders, Documentação Técnica  

---

## A

### **Agno**
**Tipo:** Biblioteca/Framework  
**Definição:** Biblioteca de orquestração inteligente desenvolvida por Marco Cardoso para processamento contextual de mensagens e roteamento baseado em IA.  
**Status:** Em desenvolvimento  
**Uso no SparkOne:** Planejado para substituir o AgnoBridge atual  
**Referência:** `SPEC.md`, seção "Agno Orchestrator"

### **AgnoBridge**
**Tipo:** Componente/Serviço  
**Definição:** Implementação temporária que emula o comportamento do Agno usando LLMs para classificação de mensagens.  
**Arquivo:** `src/app/agents/agno.py`  
**Funcionalidade:** Classifica mensagens em tipos (TASK, CALENDAR, COACH, BRIEF, GENERAL) e roteia para serviços apropriados  
**Status:** Implementado (temporário)

### **APScheduler**
**Tipo:** Biblioteca Python
**Definição:** Advanced Python Scheduler - biblioteca para agendamento de tarefas em Python
**Uso:** ProactivityEngine para lembretes automáticos e notificações proativas
**Arquivo:** `src/app/workers/scheduler.py`
**Jobs Implementados:**
- Daily Brief (08:00 diário)
- Deadline Reminders (24h antes)
- Overdue Check (a cada 6h)
- Event Reminders (30 min antes)
**Status:** ✅ Implementado e em produção

### **ASGI**
**Tipo:** Protocolo/Interface  
**Definição:** Asynchronous Server Gateway Interface - sucessor assíncrono do WSGI para aplicações Python  
**Implementação:** Uvicorn como servidor ASGI para FastAPI  
**Referência:** `pyproject.toml`

---

## B

### **Brief**
**Tipo:** Funcionalidade/Serviço  
**Definição:** Sistema de resumo diário que agrega informações de tarefas, eventos e recomendações  
**Endpoints:** `/brief/structured`, `/brief/text`  
**Arquivo:** `src/app/routers/brief.py`  
**Status:** Implementado

---

## C

### **CalDAV**
**Tipo:** Protocolo
**Definição:** Calendaring Distributed Authoring and Versioning - protocolo para sincronização de calendários
**Uso:** Integração com Apple Calendar e outros clientes CalDAV
**Arquivo:** `src/app/integrations/caldav.py`
**Status:** Implementado

### **ClickUp**
**Tipo:** Plataforma Externa/SaaS
**Definição:** Plataforma de gerenciamento de projetos e tarefas
**Integração:** Via ClickUp API REST v2
**Adapter:** `src/app/infrastructure/storage/adapters/clickup_adapter.py`
**Funcionalidades:**
- CRUD completo de tarefas
- Suporte a listas e spaces
- Custom fields e prioridades
- Status e assignees
**Status:** ✅ Implementado com 24 testes unitários

### **CORS**
**Tipo:** Política de Segurança  
**Definição:** Cross-Origin Resource Sharing - mecanismo que permite recursos de uma página web serem acessados por outro domínio  
**Implementação:** CORSMiddleware no FastAPI  
**Configuração:** `src/app/main.py`

### **CSP**
**Tipo:** Header de Segurança  
**Definição:** Content Security Policy - header HTTP que previne ataques XSS definindo fontes confiáveis de conteúdo  
**Implementação:** SecurityHeadersMiddleware  
**Status:** Implementado

---

## D

### **Docker Compose**
**Tipo:** Ferramenta de Orquestração  
**Definição:** Ferramenta para definir e executar aplicações Docker multi-container  
**Arquivo:** `docker-compose.yml`  
**Serviços:** api, worker, db, cache, ngrok  
**Status:** Implementado

---

## E

### **Evolution API**
**Tipo:** API Externa  
**Definição:** API para integração com WhatsApp Business, permitindo envio e recebimento de mensagens  
**Arquivo:** `src/app/integrations/evolution_api.py`  
**Endpoint:** `/webhooks/whatsapp`  
**Status:** Implementado

### **Eventbrite**
**Tipo:** API Externa  
**Definição:** Plataforma de eventos com API para descoberta e recomendação de eventos  
**Uso Planejado:** RecommendationService para sugestões de eventos  
**Status:** Não implementado

---

## F

### **FastAPI**
**Tipo:** Framework Web  
**Definição:** Framework web moderno e rápido para construção de APIs com Python baseado em type hints  
**Versão:** 0.115+  
**Arquivo Principal:** `src/app/main.py`  
**Status:** Implementado (core do projeto)

---

## G

### **Google Calendar API**
**Tipo:** API Externa  
**Definição:** API do Google para integração com Google Calendar, permitindo CRUD de eventos  
**Arquivo:** `src/app/integrations/google_calendar.py`  
**Autenticação:** OAuth2 com service account  
**Status:** Implementado

### **Google Places API**
**Tipo:** API Externa  
**Definição:** API do Google para informações sobre locais e estabelecimentos  
**Uso Planejado:** RecommendationService para sugestões baseadas em localização  
**Status:** Não implementado

### **Google Sheets**
**Tipo:** Integração  
**Definição:** Planilhas do Google usadas como canal de entrada para o SparkOne  
**Endpoint:** `/channels/sheets`  
**Status:** Implementado

---

## H

### **HSTS**
**Tipo:** Header de Segurança  
**Definição:** HTTP Strict Transport Security - força conexões HTTPS  
**Implementação:** SecurityHeadersMiddleware  
**Status:** Implementado

### **HTTP Basic Authentication**
**Tipo:** Método de Autenticação  
**Definição:** Método simples de autenticação HTTP usando usuário e senha  
**Uso:** Autenticação da interface web (`/web`)  
**Arquivo:** `src/app/routers/web.py`  
**Status:** Implementado

---

## I

### **Ingestion Hub**
**Tipo:** Componente Arquitetural  
**Definição:** Ponto central de entrada para todas as mensagens no SparkOne  
**Endpoint:** `/ingest`  
**Arquivo:** `src/app/routers/ingest.py`  
**Funcionalidade:** Recebe mensagens de múltiplos canais e encaminha para processamento  
**Status:** Implementado

---

## J

### **Jarvis**
**Tipo:** Conceito/Inspiração  
**Definição:** Assistente pessoal fictício do Tony Stark (Homem de Ferro) que inspirou o conceito do SparkOne  
**Referência:** `README.md` - "assistente pessoal modular inspirado no Jarvis"

---

## L

### **LangGraph**
**Tipo:** Biblioteca  
**Definição:** Biblioteca para construção de aplicações com grafos de linguagem e agentes de IA  
**Status:** Migração planejada (mencionado em documentação)  
**Uso Futuro:** Possível substituição do sistema de orquestração atual

### **LLM**
**Tipo:** Tecnologia  
**Definição:** Large Language Model - modelos de linguagem de grande escala como GPT, Claude, etc.  
**Provedores Suportados:** OpenAI, modelos locais  
**Configuração:** `src/app/config.py`  
**Uso:** AgnoBridge, PersonalCoachService

---

## M

### **MessageType**
**Tipo:** Enum/Classificação  
**Definição:** Enumeração dos tipos de mensagem processados pelo SparkOne  
**Valores:** TASK, CALENDAR, COACH, BRIEF, GENERAL  
**Arquivo:** `src/app/agents/agno.py`  
**Uso:** Classificação e roteamento de mensagens

### **Middleware**
**Tipo:** Componente de Software  
**Definição:** Camada de software que processa requests HTTP antes de chegarem aos endpoints  
**Implementados:** CORS, CorrelationId, Prometheus, RateLimit, SecurityHeaders, SecurityLogging  
**Arquivo:** `src/app/main.py`

---

## N

### **Notion API**
**Tipo:** API Externa  
**Definição:** API da Notion para integração com workspace de produtividade  
**Uso:** Sincronização de tarefas e gerenciamento de projetos  
**Arquivo:** `src/app/integrations/notion.py`  
**Status:** Implementado

### **ngrok**
**Tipo:** Ferramenta  
**Definição:** Ferramenta para criar túneis seguros para localhost, útil para desenvolvimento com webhooks  
**Configuração:** `docker-compose.yml`  
**Uso:** Desenvolvimento local com webhooks externos

---

## O

### **OpenAI API**
**Tipo:** API Externa  
**Definição:** API da OpenAI para acesso a modelos GPT e outros serviços de IA  
**Configuração:** `OPENAI_API_KEY` em variáveis de ambiente  
**Uso:** Provedor LLM principal para AgnoBridge e PersonalCoachService  
**Status:** Implementado

### **OpenTelemetry**
**Tipo:** Framework de Observabilidade  
**Definição:** Framework para coleta de métricas, logs e traces distribuídos  
**Status:** Suporte opcional implementado  
**Configuração:** `src/app/config.py`

---

## P

### **PersonalCoachService**
**Tipo:** Serviço/Componente  
**Definição:** Serviço que fornece coaching pessoal, correções de texto e sugestões motivacionais  
**Arquivo:** `src/app/services/personal_coach.py`  
**Funcionalidades:** Correção de texto, orientação motivacional  
**Status:** Implementado

### **pgvector**
**Tipo:** Extensão PostgreSQL
**Definição:** Extensão que adiciona suporte a vetores e busca de similaridade no PostgreSQL
**Uso:** Armazenamento e busca de embeddings para funcionalidades de IA
**Configuração:** `docker-compose.yml`
**Status:** Implementado

### **ProactivityEngine**
**Tipo:** Sistema/Componente
**Definição:** Motor de proatividade que automatiza lembretes, briefs diários e notificações contextuais
**Arquivo:** `src/app/workers/`
**Componentes:**
- `scheduler.py` - APScheduler configuration
- `jobs.py` - Job implementations
**Jobs Automáticos:**
- Daily Brief (08:00 BRT)
- Deadline Reminders (24h antes)
- Overdue Check (a cada 6h)
- Event Reminders (30 min antes)
**Container:** Worker container separado
**Status:** ✅ Implementado e em produção

### **PostgreSQL**
**Tipo:** Banco de Dados  
**Definição:** Sistema de gerenciamento de banco de dados relacional open-source  
**Versão:** 15+ com extensão pgvector  
**Uso:** Banco de dados principal do SparkOne  
**Status:** Implementado

### **Prometheus**
**Tipo:** Sistema de Monitoramento  
**Definição:** Sistema de monitoramento e alerta com modelo de dados de séries temporais  
**Endpoint:** `/metrics`  
**Middleware:** PrometheusMiddleware  
**Status:** Implementado

### **ProactivityEngine**
**Tipo:** Componente/Serviço  
**Definição:** Motor de proatividade planejado para lembretes automáticos e notificações contextuais  
**Tecnologia Planejada:** APScheduler  
**Status:** Não implementado (P0 - crítico)  
**Funcionalidades Planejadas:** Brief automático, lembretes, notificações push

### **Pydantic**
**Tipo:** Biblioteca Python  
**Definição:** Biblioteca para validação de dados usando type hints do Python  
**Versão:** 2.8+  
**Uso:** Validação de modelos de dados, configurações, requests/responses  
**Status:** Implementado (core do FastAPI)

---

## R

### **Rate Limiting**
**Tipo:** Técnica de Segurança  
**Definição:** Limitação do número de requests por IP/usuário em um período de tempo  
**Implementação:** RateLimitMiddleware com Redis  
**Limite:** 100 requests/minuto por IP  
**Status:** Implementado

### **RecommendationService**
**Tipo:** Serviço/Componente  
**Definição:** Serviço planejado para recomendações baseadas em localização e preferências  
**APIs Planejadas:** Google Places, Eventbrite  
**Status:** Não implementado (P1 - importante)

### **Redis**
**Tipo:** Banco de Dados  
**Definição:** Estrutura de dados em memória usada como cache e broker de mensagens  
**Versão:** 7  
**Uso:** Cache, rate limiting, sessões  
**Status:** Implementado

---

## S

### **SparkOne**
**Tipo:** Projeto/Produto
**Definição:** Assistente pessoal modular inspirado no Jarvis, projeto principal deste documento
**Versão:** 0.2.0
**Status:** Desenvolvimento avançado (85% completo - 32/36 tarefas)

### **SQLAlchemy**
**Tipo:** ORM  
**Definição:** Object-Relational Mapping toolkit para Python  
**Versão:** 2.0+ (async)  
**Uso:** Mapeamento objeto-relacional, queries ao banco de dados  
**Status:** Implementado

### **SQLite**
**Tipo:** Banco de Dados
**Definição:** Banco de dados SQL embarcado, usado como fallback para desenvolvimento local
**Uso:** Desenvolvimento local quando PostgreSQL não está disponível
**Status:** Implementado (fallback)

### **StorageAdapter**
**Tipo:** Design Pattern/Interface
**Definição:** Pattern para abstrair acesso a diferentes backends de armazenamento (Notion, ClickUp, Google Sheets)
**Interface:** `src/app/domain/interfaces/storage_adapter.py`
**Implementações:**
- NotionAdapter - Integração Notion API
- ClickUpAdapter - Integração ClickUp API
- GoogleSheetsAdapter - Integração Google Sheets API
**Métodos:**
- `get_tasks()` - Buscar tarefas
- `save_task()` - Salvar/atualizar tarefa
- `delete_task()` - Deletar tarefa
- `health_check()` - Verificar saúde da integração
**Status:** ✅ Implementado com 70+ testes

### **StorageAdapterRegistry**
**Tipo:** Registry Pattern/Sistema
**Definição:** Sistema de registro dinâmico de storage adapters com seleção baseada em preferências do usuário
**Arquivo:** `src/app/infrastructure/storage/registry.py`
**Funcionalidades:**
- Registro dinâmico de adapters
- Health checks por adapter
- Seleção automática baseada em user preferences
- Fallback para adapters saudáveis
- Parallel saves com asyncio.gather()
**Status:** ✅ Implementado

### **structlog**
**Tipo:** Biblioteca de Logging  
**Definição:** Biblioteca para logging estruturado em Python  
**Uso:** Logs estruturados com correlation IDs  
**Status:** Implementado

---

## T

### **TaskService**
**Tipo:** Serviço/Componente  
**Definição:** Serviço para gerenciamento de tarefas com integração Notion  
**Arquivo:** `src/app/services/tasks.py`  
**Endpoints:** `/tasks` (CRUD completo)  
**Funcionalidades:** Sincronização Notion, snapshots PostgreSQL  
**Status:** Implementado

### **TOTP**
**Tipo:** Protocolo de Autenticação  
**Definição:** Time-based One-Time Password - protocolo para autenticação de dois fatores  
**Biblioteca:** pyotp  
**Status:** Suporte implementado (não ativo por padrão)

---

## U

### **User Preferences**
**Tipo:** Feature/Modelo
**Definição:** Sistema de preferências do usuário para configuração de storage backends
**Model:** `src/app/infrastructure/database/models/user_preferences.py`
**Configurações:**
- Default storage backend (notion/clickup/sheets)
- Timezone preference
- Notification settings
- Brief schedule
**API:** `/api/v1/storage-configs` (CRUD completo)
**Status:** ✅ Implementado

### **Uvicorn**
**Tipo:** Servidor ASGI
**Definição:** Servidor ASGI rápido para aplicações Python assíncronas
**Versão:** 0.30+
**Uso:** Servidor de aplicação para FastAPI
**Status:** Implementado

---

## V

### **Vector Search**
**Tipo:** Técnica  
**Definição:** Busca por similaridade usando vetores/embeddings  
**Implementação:** pgvector no PostgreSQL  
**Uso:** Busca semântica de conteúdo  
**Status:** Implementado (infraestrutura)

---

## W

### **Webhook**
**Tipo:** Padrão de Integração  
**Definição:** Método de comunicação onde uma aplicação envia dados para outra quando eventos específicos ocorrem  
**Implementado:** `/webhooks/whatsapp` para Evolution API  
**Arquivo:** `src/app/routers/webhooks.py`  
**Status:** Implementado

### **WhatsApp Business**
**Tipo:** Plataforma  
**Definição:** Versão do WhatsApp para empresas com API para automação  
**Integração:** Via Evolution API  
**Uso:** Canal de entrada principal para mensagens  
**Status:** Implementado

---

## Siglas e Acrônimos

| Sigla | Significado | Contexto |
|-------|-------------|----------|
| **ADR** | Architectural Decision Record | Documentação de decisões arquiteturais |
| **API** | Application Programming Interface | Interfaces de programação |
| **ASGI** | Asynchronous Server Gateway Interface | Protocolo para servidores Python |
| **CORS** | Cross-Origin Resource Sharing | Política de segurança web |
| **CRUD** | Create, Read, Update, Delete | Operações básicas de dados |
| **CSP** | Content Security Policy | Header de segurança |
| **HSTS** | HTTP Strict Transport Security | Header de segurança |
| **LLM** | Large Language Model | Modelos de linguagem |
| **MVP** | Minimum Viable Product | Produto mínimo viável |
| **ORM** | Object-Relational Mapping | Mapeamento objeto-relacional |
| **PRD** | Product Requirements Document | Documento de requisitos |
| **REST** | Representational State Transfer | Arquitetura de API |
| **TOTP** | Time-based One-Time Password | Autenticação 2FA |
| **UUID** | Universally Unique Identifier | Identificador único |
| **XSS** | Cross-Site Scripting | Vulnerabilidade de segurança |

---

## Convenções de Nomenclatura

### **Arquivos Python**
- **Serviços:** `*_service.py` ou `*.py` em `/services/`
- **Roteadores:** `*.py` em `/routers/`
- **Modelos:** `*.py` em `/models/`
- **Integrações:** `*.py` em `/integrations/`

### **Endpoints**
- **REST:** `/recurso` (plural)
- **Webhooks:** `/webhooks/{provider}`
- **Canais:** `/channels/{channel}`
- **Utilitários:** `/health`, `/metrics`, `/brief`

### **Variáveis de Ambiente**
- **Formato:** `UPPER_SNAKE_CASE`
- **Prefixo:** Sem prefixo específico
- **Exemplos:** `DATABASE_URL`, `OPENAI_API_KEY`, `WEB_PASSWORD`

### **Identificadores**
- **Requisitos Funcionais:** `RF-XXX`
- **Requisitos Não Funcionais:** `RNF-XXX`
- **Objetivos:** `OBJ-XXX`
- **Riscos:** `RISK-XXX`
- **ADRs:** `ADR-XXX`

---

## Referências Técnicas

### **Documentação Principal**
- `README.md` - Visão geral e setup
- `SPEC.md` - Especificação técnica detalhada
- `STATE_OF_PROJECT.md` - Status atual do projeto
- `pyproject.toml` - Dependências e configuração

### **Arquivos de Configuração**
- `docker-compose.yml` - Infraestrutura local
- `src/app/config.py` - Configurações da aplicação
- `src/app/main.py` - Bootstrap da aplicação

### **Documentação Externa**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Glossário mantido por:** Equipe de Desenvolvimento  
**Frequência de atualização:** A cada sprint  
**Última revisão:** Janeiro 2025