# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- RecommendationService com Google Places API (RF-016)
- Busca Vetorial com pgvector (RF-018)
- Autenticação JWT (RNF-020)
- Interface mobile nativa

---

## [0.2.0] - 2025-01-27

### Added - Funcionalidades Principais
- **Multi-Storage Backend System (RF-019)**
  - Interface `StorageAdapter` com padrão adapter pattern
  - NotionAdapter com 100% test coverage
  - ClickUpAdapter com 87% test coverage
  - GoogleSheetsAdapter com 96% test coverage
  - StorageAdapterRegistry com auto-discovery
  - StorageService orchestrator com retry/fallback automático
  - Configuração via tabela `user_storage_configs` (JSONB)
  - Migration completa (commit 3e169ea)

- **ProactivityEngine para Lembretes Automáticos (RF-015)**
  - Worker process com APScheduler
  - Brief diário automático às 08:00 (configurável)
  - Lembretes de deadline 24h antes do prazo
  - Verificação de tarefas atrasadas a cada 6 horas
  - Lembretes de eventos 30 minutos antes
  - Timezone support (ZoneInfo)
  - Docker worker container configurado
  - Graceful shutdown handling

- **User Preferences Management (RF-020)**
  - CRUD API completa (`/api/v1/storage-configs`)
  - Interface web `/web/settings` com dark theme
  - Configuração de múltiplos backends simultâneos
  - Sistema de priorização de adapters
  - CSRF protection
  - Validação client-side e server-side
  - Suporte multi-tenant preparado

- **Arquitetura e Documentação**
  - ADR-014: Storage Adapter Pattern
  - ADR-015: User Preferences System
  - ADR-016: ProactivityEngine Architecture
  - PRD atualizado com RF-019 e RF-020
  - System map atualizado
  - 76 testes automatizados passando

### Changed - Melhorias
- Refatorado `TaskService` para usar `StorageService`
  - Código legado Notion-only removido
  - Suporte a múltiplos backends simultâneos
  - Backward compatibility mantida
- Atualizado modelo `TaskRecord`
  - Campo `external_id` adicionado
  - Campos `due_at` e `reminded_at` para ProactivityEngine
  - Enum `TaskStatus` com TODO/IN_PROGRESS/COMPLETED
- Database migrations consolidadas
  - Tabela `user_storage_configs`
  - Tabela `user_preferences`
  - Índices otimizados

### Fixed - Correções
- Substituído `datetime.utcnow()` deprecated por `datetime.now(timezone.utc)`
  - storage adapters (commit 08caefe)
  - ProactivityEngine jobs (commit 50bae97)
- Melhorado tratamento de erros em storage sync
  - Retry com exponential backoff
  - Logging estruturado por adapter
  - Health check granular por backend
- Timezone handling aprimorado
  - Suporte a ZoneInfo
  - DST handling correto
  - User timezone preference

### Technical Debt
- Cobertura de testes aumentada de ~40% para ~85% nos módulos core
- Documentação técnica completa (ADRs)
- Migration paths documentados
- Test coverage: NotionAdapter 100%, SheetsAdapter 96%, ClickUpAdapter 87%

---

## [0.1.0] - 2024-12-15

### Added - MVP Inicial
- FastAPI core application
- Interface WhatsApp via Evolution API (RF-001)
- Interface Web com HTTP Basic Auth (RF-002)
- Integração Google Sheets (RF-003)
- API REST para ingestão direta (RF-004)
- Sincronização com Notion (RF-005)
- Integração Google Calendar (RF-007)
- Suporte CalDAV (RF-008)
- Sistema de Brief estruturado (RF-011)
- Agno Bridge para orquestração (RF-013, RF-014)
- Middleware de segurança completo
  - CORS, Rate Limiting, Security Headers
  - CSRF Protection
  - Correlation IDs
- Observabilidade básica
  - Métricas Prometheus
  - Health checks
  - Logs estruturados
- Docker Compose para deployment
  - PostgreSQL 15 com pgvector
  - Redis 7
  - Traefik reverse proxy

### Infrastructure
- Ambiente de desenvolvimento local
- CI/CD básico
- Deployment em VPS
- Backup automático de database

---

## Formato das Mudanças

- **Added**: Novas funcionalidades
- **Changed**: Mudanças em funcionalidades existentes
- **Deprecated**: Funcionalidades que serão removidas
- **Removed**: Funcionalidades removidas
- **Fixed**: Correções de bugs
- **Security**: Correções de vulnerabilidades

---

## Links Úteis

- [PRD - Documento de Requisitos](docs/prd/sparkone/PRD.pt-BR.md)
- [Decisões Arquiteturais (ADRs)](docs/prd/sparkone/decisions.md)
- [System Map](docs/prd/sparkone/system-map.md)
- [Master Plan de Execução](MASTER_PLAN_EXECUTION.md)
