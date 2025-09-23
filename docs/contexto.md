# Contexto do SparkOne

## Visão Geral

O **SparkOne** é um agente de IA especializado, inspirado no estilo Iron Man, projetado para ser um assistente pessoal inteligente e proativo. O sistema combina múltiplos canais de entrada (WhatsApp, Google Sheets, Web UI) com serviços de domínio especializados para oferecer uma experiência de assistente pessoal completa.

## Missão

Criar um assistente de IA que:
- **Compreende contexto**: Mantém memória de conversas e preferências do usuário
- **Age proativamente**: Oferece briefings, lembretes e recomendações contextuais
- **Integra serviços**: Conecta-se com Notion, calendários, planilhas e outros sistemas
- **Mantém personalidade**: Responde com o estilo característico do SparkOne (Iron Man)

## Arquitetura de Alto Nível

```
[Canais de Entrada]
WhatsApp | Google Sheets | Web UI
         ↓
[Ingestion Hub - FastAPI]
         ↓
[Message Normalizer]
         ↓
[Agno Orchestrator]
    ↓        ↓        ↓
Classification  Tasks   Personal Coach
    Agent      Service    Service
         ↓
[Persistência: PostgreSQL + Redis]
         ↓
[Saídas: WhatsApp, Alertas, Notificações]
```

## Componentes Principais

### 1. Canais de Entrada
- **WhatsApp**: Via Evolution API para comunicação natural
- **Google Sheets**: Sincronização automática de dados estruturados
- **Web UI**: Interface minimalista para interação direta

### 2. Orquestração Inteligente
- **Agno Orchestrator**: Coordena agentes especializados
- **Classification Service**: Identifica tipo de mensagem (tarefa, evento, coaching)
- **Message Normalizer**: Padroniza payloads de diferentes canais

### 3. Serviços de Domínio
- **TaskService**: Integração com Notion para gerenciamento de tarefas
- **CalendarService**: Suporte a CalDAV e Google Calendar
- **PersonalCoachService**: Correções de texto e sugestões personalizadas
- **BriefService**: Resumos proativos e insights diários
- **MemoryService**: Gerenciamento de contexto e histórico

### 4. Persistência
- **PostgreSQL 15+**: Estado transacional, auditoria, preferências
- **pgvector**: Embeddings para busca semântica
- **Redis 7**: Cache, TTL, filas assíncronas, rate limiting

## Princípios de Design

### Modularidade
- Separação clara de responsabilidades entre serviços
- Injeção de dependências para testabilidade
- Adaptadores para diferentes integrações

### Segurança
- Autenticação básica na Web UI
- Gestão segura de credenciais via `.env`
- Headers de segurança (HSTS, CORS)
- Auditoria de operações críticas

### Observabilidade
- Logging estruturado com `structlog`
- Métricas com Prometheus
- Health checks específicos por serviço
- Tracing de requests com correlação

### Qualidade
- Testes automatizados (unitários, integração, E2E)
- Linting com Ruff, formatação com Black
- Type checking com mypy
- CI/CD com GitHub Actions

## Fluxo de Dados Típico

1. **Entrada**: Mensagem recebida via WhatsApp/Web/Sheets
2. **Normalização**: Conversão para `ChannelMessage` padronizado
3. **Classificação**: Identificação do tipo de mensagem
4. **Orquestração**: Roteamento para serviço apropriado
5. **Processamento**: Execução da lógica de negócio
6. **Persistência**: Armazenamento de estado e histórico
7. **Resposta**: Envio de feedback ao usuário

## Contexto Tecnológico

### Stack Principal
- **Python 3.11+**: Linguagem base
- **FastAPI**: Framework web assíncrono
- **SQLAlchemy**: ORM para PostgreSQL
- **Pydantic**: Validação e serialização de dados
- **Redis**: Cache e filas
- **Docker**: Containerização

### Integrações Externas
- **Evolution API**: WhatsApp Business
- **Notion API**: Gerenciamento de tarefas
- **Google APIs**: Calendar, Sheets, Places
- **CalDAV**: Calendários padrão
- **OpenAI**: Modelos de linguagem

## Ambiente de Desenvolvimento

O projeto utiliza:
- **Docker Compose**: Orquestração local
- **Alembic**: Migrações de banco
- **pre-commit**: Hooks de qualidade
- **pytest**: Framework de testes
- **Makefile**: Automação de tarefas

## Próximos Passos

Ver `roadmap.md` para detalhes sobre:
- Evolução multiagente com LangGraph
- Migração para Litestar
- Implementação de guidelines CISA AI Security
- Expansão para novos canais (Slack, email, voz)