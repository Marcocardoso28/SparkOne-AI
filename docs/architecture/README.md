# SparkOne - Arquitetura e Design

## Visão Geral

O SparkOne é um assistente pessoal inteligente que combina ingestão multicanal (WhatsApp, Web, Sheets) com agentes especializados para lembrar compromissos, organizar tarefas e responder com a persona "SparkOne".

## Objetivos Estratégicos 2025

- **Confiabilidade**: Entregar um assistente confiável para uso diário focando em tarefas, agenda e briefs automáticos
- **Privacidade**: Garantir privacidade e segurança adequadas para dados pessoais (LGPD-ready)
- **Automação**: Abrir caminho para operação autônoma (integração com agentes externos e automação de rotinas)

## Domínios Principais

### Interação
- **Canais**: WhatsApp, Web UI, Google Sheets
- **Normalização**: Padronização de mensagens entre canais
- **Prompts**: Templates de interação com IA

### Produtividade
- **Tarefas**: Integração com Notion e Google Sheets
- **Agenda**: Sincronização com Google Calendar e CalDAV
- **Briefings**: Consolidação automática de informações

### Conhecimento
- **Ingestão**: Processamento de documentos e mensagens
- **Busca Semântica**: Recuperação inteligente de informações
- **Memória**: Armazenamento persistente de contexto

### Infraestrutura
- **Observabilidade**: Métricas, logs e traces
- **Backups**: Automação de backup e restore
- **Segurança**: Autenticação, autorização e conformidade

## Casos de Uso Prioritários

1. **Gerenciamento de Tarefas**: Receber tarefas via WhatsApp e sincronizar com Notion/Sheets
2. **Briefings Automáticos**: Consolidar agenda, tarefas e últimos contatos em um briefing matinal
3. **Memória Persistente**: Registrar insights (voz/texto) e armazenar em memória longa para consultas futuras
4. **Alertas Proativos**: Disparar alertas (ex.: compromissos em conflito, mensagens sem resposta)

## Macro-Arquitetura

```text
Canais → Normalizador → Orquestração (Agno) → Serviços Domínio → Persistência (PostgreSQL + Redis + pgvector)
                                          ↘ Observabilidade / Alertas ↘ Webhooks externos
```

## Princípios Arquiteturais

### Modularidade
- **Separação de Camadas**: API, Domain, Infrastructure
- **Desacoplamento**: Interfaces bem definidas entre componentes
- **Reutilização**: Componentes reutilizáveis e testáveis

### Segurança por Padrão
- **Rate Limiting**: Controle de taxa de requisições
- **Logging**: Rastreabilidade completa de ações
- **Secrets**: Política rígida de gerenciamento de segredos

### Observabilidade
- **Métricas**: Coleta de métricas de ponta a ponta
- **Logs**: Logging estruturado e centralizado
- **Tracing**: Rastreamento distribuído de requisições

### Automação
- **Provisionamento**: Docker/Compose para ambientes
- **CI/CD**: Testes automatizados em pipeline
- **Backups**: Pipelines automatizados de backup

## Registro de Decisões Arquiteturais (ADRs)

### ADA-001: FastAPI + Estrutura em Camadas
- **Data**: 2024-03-18
- **Decisão**: Manter FastAPI com routers finos, services aplicacionais e integrações externas desacopladas
- **Alternativas**: Litestar, Django Rest Framework
- **Consequências**: Compatibilidade com stack atual, menor esforço de migração; revisão prevista caso serviço cresça para multi-tenant

### ADA-002: Orquestração Agno com Migração para LangGraph
- **Data**: 2024-05-02
- **Decisão**: Utilizar Agno como núcleo de orquestração; preparar migração gradual para LangGraph
- **Alternativas**: LangChain, CrewAI
- **Consequências**: Controle total sobre prompts; necessidade de investimento em testes ao migrar

### ADA-003: Persistência PostgreSQL + Redis + pgvector
- **Data**: 2024-04-10
- **Decisão**: PostgreSQL 15 com extensão pgvector como banco primário; Redis para cache/rate limiting
- **Alternativas**: Supabase, Neon + Qdrant, DynamoDB
- **Consequências**: Stack conhecida; requer monitoração de storage vetorial e backups automatizados

### ADA-004: Segurança Web com Camadas Incrementais
- **Data**: 2024-08-22
- **Decisão**: Manter auth básica na Web UI em MVP com roadmap para OAuth2 + MFA
- **Alternativas**: Auth0, Clerk, Cloudflare Access
- **Consequências**: Simplicidade imediata; exige reforço antes de exposição pública

### ADA-005: Gestão de Conhecimento com Pipelines Controlados
- **Data**: 2024-09-30
- **Decisão**: Ingestão de documentos via scripts dedicados + revisão manual com tagging
- **Alternativas**: Automação via agentes autônomos completos
- **Consequências**: Curadoria mais lenta porém segura; investimento em metadados para escalar

## Tecnologias e Stack

### Backend
- **FastAPI**: Framework web moderno e performático
- **SQLAlchemy**: ORM com suporte assíncrono
- **PostgreSQL**: Banco de dados principal com pgvector
- **Redis**: Cache e rate limiting
- **Pydantic**: Validação de dados e configurações

### IA e ML
- **Agno**: Orquestração de agentes
- **LangChain/LangGraph**: Framework de LLM (futuro)
- **OpenAI**: Provedor de LLM principal
- **Embeddings**: Busca semântica

### Infraestrutura
- **Docker**: Containerização
- **Prometheus**: Métricas
- **Grafana**: Dashboards
- **Structlog**: Logging estruturado

### Integrações
- **WhatsApp**: Evolution API
- **Notion**: API para gerenciamento de tarefas
- **Google**: Calendar e Sheets
- **CalDAV**: Calendários externos

## Estrutura de Código

```
src/app/
├── api/                    # Camada de API (routers)
│   └── v1/                # Versionamento da API
├── domain/                 # Lógica de domínio
│   ├── models/            # Modelos de domínio
│   └── services/          # Serviços de domínio
├── infrastructure/         # Camada de infraestrutura
│   ├── database/          # Banco de dados
│   ├── cache/             # Cache Redis
│   ├── messaging/         # Sistema de mensagens
│   └── integrations/      # Integrações externas
├── core/                  # Funcionalidades core
├── middleware/            # Middlewares
└── web/                   # Interface web
```

## Próximos Passos

1. **Migração para LangGraph**: Implementar orquestração mais sofisticada
2. **Multi-tenant**: Preparar arquitetura para múltiplos usuários
3. **Microserviços**: Considerar separação em serviços menores
4. **Event Sourcing**: Implementar para auditoria completa
5. **CQRS**: Separar comandos e consultas para melhor performance

---

**Última Atualização**: Janeiro 2025  
**Versão**: v1.1.0
