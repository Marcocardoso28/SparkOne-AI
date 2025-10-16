# 🚀 SPARKONE - MASTER PLAN DE EXECUÇÃO COMPLETA
**Versão:** 1.0
**Data Início:** 2025-01-27
**Status Geral:** 🔄 EM ANDAMENTO

---

## 📋 RESUMO EXECUTIVO

Este plano contém TODAS as tarefas para:
1. ✅ Implementar Storage Adapter Pattern (multi-backend)
2. ✅ Implementar ProactivityEngine (lembretes automáticos)
3. ✅ Atualizar toda documentação
4. ✅ Criar testes completos
5. ✅ Verificar duplicidades
6. ✅ Testar todas funcionalidades

**TOTAL DE TAREFAS:** 36
**PROGRESSO ATUAL:** 8/36 (22%)
**CHECKPOINT ATUAL:** FASE 2 - STORAGE ADAPTERS (TAREFA 2.5)

---

## 🎯 COMO USAR ESTE DOCUMENTO

### SE A SESSÃO CAIR:
```
1. Abra nova sessão com Claude
2. Diga: "Continue o MASTER PLAN do arquivo MASTER_PLAN_EXECUTION.md"
3. Cole o conteúdo deste arquivo
4. Claude continua exatamente de onde parou
```

### MARCAÇÃO DE PROGRESSO:
- ⬜ Não iniciado
- 🔄 Em andamento
- ✅ Completo
- ❌ Com problema (ver seção ISSUES)

---

## 📊 CHECKPOINTS E FASES

### FASE 1: DOCUMENTAÇÃO ARQUITETURAL (ADRs)
**Status:** ✅ COMPLETO (4/4 tarefas)
**Duração Real:** 2 horas
**Arquivos Criados:** 3 ADRs + PRD atualizado

### FASE 2: IMPLEMENTAÇÃO STORAGE ADAPTERS
**Status:** 🔄 EM ANDAMENTO (4/9 tarefas - 44%)
**Duração Estimada:** 1-2 dias
**Arquivos Criados:** ~15 arquivos

### FASE 3: IMPLEMENTAÇÃO PROACTIVITY ENGINE
**Status:** ⬜ NÃO INICIADO
**Duração Estimada:** 2-3 dias
**Arquivos Criados:** ~10 arquivos

### FASE 4: INTERFACE WEB E APIs
**Status:** ⬜ NÃO INICIADO
**Duração Estimada:** 1-2 dias
**Arquivos Criados:** ~8 arquivos

### FASE 5: TESTES COMPLETOS
**Status:** ⬜ NÃO INICIADO
**Duração Estimada:** 2-3 dias
**Arquivos Criados:** ~20 arquivos de teste

### FASE 6: DOCUMENTAÇÃO FINAL
**Status:** ⬜ NÃO INICIADO
**Duração Estimada:** 1 dia
**Arquivos Atualizados:** ~10 docs

---

## 📝 TAREFAS DETALHADAS

---

### FASE 1: DOCUMENTAÇÃO ARQUITETURAL

#### TAREFA 1.1: Criar ADR-014: Storage Adapter Pattern
**Status:** ✅ COMPLETO
**Arquivo:** `docs/prd/sparkone/decisions.md`
**Commit:** 575b191 "docs: Add ADR-014 Storage Adapter Pattern"
**Critérios de Conclusão:**
- [x] ADR criado com contexto completo
- [x] Decisão documentada
- [x] Consequências listadas
- [x] Exemplos de código incluídos

**Conteúdo do ADR:**
```markdown
## ADR-014: Storage Adapter Pattern

**Date:** 2025-01-27
**Status:** ✅ Accepted
**Deciders:** Marco Cardoso, Development Team

### Context
SparkOne precisa suportar múltiplos backends de armazenamento (Notion, ClickUp, Google Sheets, etc) sem acoplamento forte com APIs específicas. Usuários devem poder configurar múltiplos destinos simultaneamente.

### Decision
Implementar padrão Adapter com registry dinâmico de storage backends. Cada backend (Notion, ClickUp, Sheets) implementa interface comum `StorageAdapter`.

**Related Requirements:** RF-019 (Multi-Storage Backend)
**Related Backlog:** TECH-005 (Extensibilidade)

### Consequences
**Positive:**
- ✅ Adicionar novos backends sem modificar core
- ✅ Múltiplos backends ativos simultaneamente
- ✅ Fácil testar (mock adapters)
- ✅ Fallback automático se um falhar

**Negative:**
- ⚠️ Complexidade adicional (abstração)
- ⚠️ Performance overhead (múltiplas APIs)
- ⚠️ Sincronização pode falhar parcialmente

### Implementation
```python
class StorageAdapter(ABC):
    @abstractmethod
    async def save_task(self, task: Task) -> str: ...
    @abstractmethod
    async def health_check(self) -> dict: ...

# Registry auto-discovery
StorageAdapterRegistry.register(NotionAdapter)
StorageAdapterRegistry.register(ClickUpAdapter)
```

**Migration Path:**
1. Criar interface base
2. Migrar código Notion existente
3. Adicionar ClickUp e Sheets
4. UI de configuração
```

**Checklist:**
- [ ] Copiar template acima
- [ ] Adicionar no decisions.md
- [ ] Commit: "docs: Add ADR-014 Storage Adapter Pattern"

---

#### TAREFA 1.2: Criar ADR-015: User Preferences System
**Status:** ✅ COMPLETO
**Arquivo:** `docs/prd/sparkone/decisions.md`
**Commit:** 8161be7 "docs: Add ADR-015 User Preferences System"
**Conteúdo:**
```markdown
## ADR-015: User Preferences System

**Date:** 2025-01-27
**Status:** ✅ Accepted
**Deciders:** Marco Cardoso

### Context
Usuários precisam configurar preferências de armazenamento, horários de notificação, backends ativos, sem modificar código ou .env.

### Decision
Criar tabela `user_storage_configs` com schema JSONB flexível para guardar configurações específicas de cada adapter.

**Related Requirements:** RF-020 (User Settings)

### Consequences
**Positive:**
- ✅ Configuração via UI
- ✅ Multi-tenant ready (user_id column)
- ✅ JSONB permite configs flexíveis
- ✅ Priorização de backends

**Negative:**
- ⚠️ Validação de schema necessária
- ⚠️ Migration complexa

### Database Schema
```sql
CREATE TABLE user_storage_configs (
    id UUID PRIMARY KEY,
    user_id UUID,
    adapter_name VARCHAR(50) NOT NULL,
    config_json JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_storage_active ON user_storage_configs(user_id, is_active);
```
```

**Checklist:**
- [ ] Adicionar ADR no decisions.md
- [ ] Commit: "docs: Add ADR-015 User Preferences System"

---

#### TAREFA 1.3: Criar ADR-016: ProactivityEngine Architecture
**Status:** ✅ COMPLETO (Já existia como ADR-012)
**Arquivo:** `docs/prd/sparkone/decisions.md`
**Nota:** ADR-012 já documenta ProactivityEngine completamente
**Conteúdo:**
```markdown
## ADR-016: ProactivityEngine Architecture

**Date:** 2025-01-27
**Status:** ✅ Accepted
**Deciders:** Marco Cardoso

### Context
SparkOne precisa de comportamentos proativos (brief diário, lembretes de prazo, notificações) executados em background sem intervenção do usuário.

### Decision
Criar processo worker separado usando APScheduler com jobs configuráveis via database.

**Related Requirements:** RF-015 (ProactivityEngine)

### Consequences
**Positive:**
- ✅ Isolamento de falhas (worker vs API)
- ✅ Jobs configuráveis por usuário
- ✅ Retry automático
- ✅ Logs estruturados por job

**Negative:**
- ⚠️ Container adicional (overhead)
- ⚠️ Timezone/DST complexidade
- ⚠️ Sincronização com API

### Architecture
```yaml
services:
  api:
    # FastAPI web server
  worker:
    # APScheduler daemon
    command: python -m app.workers.scheduler
    depends_on:
      - db
      - cache
```

### Job Types
1. `daily_brief` - 08:00 AM todo dia
2. `deadline_reminder` - 1 dia antes do prazo
3. `overdue_check` - A cada 6 horas
4. `event_reminder` - 30 min antes de eventos
```

**Checklist:**
- [ ] Adicionar ADR no decisions.md
- [ ] Commit: "docs: Add ADR-016 ProactivityEngine Architecture"

---

#### TAREFA 1.4: Atualizar PRD com novos requisitos
**Status:** ✅ COMPLETO
**Arquivo:** `docs/prd/sparkone/PRD.pt-BR.md`
**Commit:** 1f64920 "docs: Update PRD with new requirements RF-019, RF-020"
**Modificações:**

**1. Adicionar RF-019 na seção de Requisitos Funcionais (linha ~230):**
```markdown
- **RF-019:** Multi-Storage Backend System
  - **Status:** 🔄 Em Implementação
  - **Prioridade:** P0 (crítico)
  - **Critérios de Aceitação:**
    - Suporte a múltiplos backends simultâneos (Notion + ClickUp + Sheets)
    - Interface de configuração via /web/settings
    - Registry de adapters extensível
    - Health check por adapter
    - Retry automático com backoff exponencial
```

**2. Adicionar RF-020:**
```markdown
- **RF-020:** User Preferences Management
  - **Status:** 🔄 Em Implementação
  - **Prioridade:** P1
  - **Critérios de Aceitação:**
    - CRUD de preferências via API
    - UI de configuração em /web/settings
    - Validação de schema de configurações
    - Suporte a multi-tenant (preparação futura)
```

**3. Atualizar status RF-015 (ProactivityEngine):**
```markdown
- **RF-015:** ProactivityEngine para lembretes automáticos
  - **Status:** 🔄 Em Implementação (era: ❌ Não implementado)
  - **Prioridade:** P0 (crítico)
```

**4. Atualizar Matriz de Implementação (linha ~442):**
```markdown
| ProactivityEngine | 🔄 40% | ❌ 0% | ❌ 20% | P0 |
| Multi-Storage Backend | 🔄 30% | ❌ 0% | ✅ 80% | P0 |
```

**Checklist:**
- [x] Adicionar RF-019 e RF-020
- [x] Atualizar status de RF-015
- [x] Atualizar matriz de implementação
- [x] Atualizar mapeamento bilíngue
- [x] Commit: "docs: Update PRD with new requirements RF-019, RF-020"

---

### FASE 2: IMPLEMENTAÇÃO STORAGE ADAPTERS

#### TAREFA 2.1: Criar estrutura de diretórios
**Status:** ✅ COMPLETO
**Commit:** 43a262d "refactor: Create storage adapter directory structure"

**Checklist:**
- [x] Diretórios criados
- [x] __init__.py files adicionados
- [x] Commit realizado

---

#### TAREFA 2.2: Criar interface base StorageAdapter
**Status:** ✅ COMPLETO
**Arquivo:** `src/app/domain/interfaces/storage_adapter.py`
**Commit:** 79b7f65 "feat: Add StorageAdapter base interface"

**Checklist:**
- [x] Arquivo criado com 210 linhas
- [x] Todos os métodos abstratos definidos (save, update, delete, get, health_check)
- [x] Docstrings completas com exemplos
- [x] Type hints corretos
- [x] StorageAdapterError exception criada
- [x] Commit realizado

---

#### TAREFA 2.3: Criar StorageAdapterRegistry
**Status:** ✅ COMPLETO
**Arquivo:** `src/app/infrastructure/storage/registry.py`
**Commit:** d0fc34c "feat: Add StorageAdapterRegistry with auto-discovery"

**Checklist:**
- [x] Singleton pattern implementado
- [x] Auto-discovery via auto_discover_adapters() funcional
- [x] register() manual funcional
- [x] get_adapter() funcional com validação
- [x] list_available() funcional (sorted)
- [x] get_adapter_info() com detalhes completos
- [x] Commit realizado

---

#### TAREFA 2.4: Migrar código Notion para NotionAdapter
**Status:** ✅ COMPLETO
**Arquivo:** `src/app/infrastructure/storage/adapters/notion_adapter.py`
**Commits:**
- 1d0e1c7 "feat: Add external_id field to TaskRecord"
- f350ed8 "refactor: Migrate Notion integration to NotionAdapter"

**Checklist:**
- [x] NotionAdapter implementa StorageAdapter (295 linhas)
- [x] Código migrado de TaskService (_build_notion_payload)
- [x] save_task() completamente implementado
- [x] update/delete/get placeholders (NotionClient limitado)
- [x] health_check() com latência implementado
- [x] external_id field adicionado ao TaskRecord model
- [x] Commits realizados

---

#### TAREFA 2.5: Implementar ClickUpAdapter
**Status:** ⬜
**Arquivo:** `src/app/infrastructure/storage/adapters/clickup_adapter.py`
**Checklist:**
- [ ] save_task implementado
- [ ] update_task implementado
- [ ] delete_task implementado
- [ ] health_check implementado
- [ ] Testes criados
- [ ] Commit: "feat: Add ClickUpAdapter integration"

---

#### TAREFA 2.6: Implementar GoogleSheetsAdapter
**Status:** ⬜
**Arquivo:** `src/app/infrastructure/storage/adapters/sheets_adapter.py`
**Checklist:**
- [ ] Adaptador completo
- [ ] Sincronização bidirecional
- [ ] Testes criados
- [ ] Commit: "feat: Add GoogleSheetsAdapter integration"

---

#### TAREFA 2.7: Criar Migration para user_storage_configs
**Status:** ⬜
**Arquivo:** `alembic/versions/XXXXX_add_user_storage_configs.py`
**Comando:**
```bash
cd /home/marcocardoso/projects/SparkOne-AI
alembic revision -m "add_user_storage_configs"
```

**Checklist:**
- [ ] Migration criada
- [ ] Schema SQL correto
- [ ] Índices criados
- [ ] Migration testada (upgrade/downgrade)
- [ ] Commit: "db: Add user_storage_configs table"

---

#### TAREFA 2.8: Implementar StorageService
**Status:** ⬜
**Arquivo:** `src/app/domain/services/storage.py`
**Checklist:**
- [ ] save_task com retry
- [ ] Múltiplos backends simultâneos
- [ ] Queue de retry implementada
- [ ] Logging estruturado
- [ ] Commit: "feat: Add StorageService orchestrator"

---

#### TAREFA 2.9: Atualizar TaskService para usar StorageService
**Status:** ⬜
**Arquivo:** `src/app/domain/services/tasks.py`
**Checklist:**
- [ ] Integração com StorageService
- [ ] Código legado removido
- [ ] Testes atualizados
- [ ] Commit: "refactor: Integrate TaskService with StorageService"

---

### FASE 3: IMPLEMENTAÇÃO PROACTIVITY ENGINE

#### TAREFA 3.1: Criar estrutura do worker
**Status:** ⬜
**Comandos:**
```bash
mkdir -p src/app/workers
touch src/app/workers/__init__.py
touch src/app/workers/scheduler.py
touch src/app/workers/jobs.py
```

**Checklist:**
- [ ] Estrutura criada
- [ ] Commit: "feat: Create worker structure for ProactivityEngine"

---

#### TAREFA 3.2: Implementar ProactivityEngine com APScheduler
**Status:** ⬜
**Arquivo:** `src/app/workers/scheduler.py`
**Checklist:**
- [ ] APScheduler configurado
- [ ] Timezone correto
- [ ] Logging estruturado
- [ ] Graceful shutdown
- [ ] Commit: "feat: Implement ProactivityEngine scheduler"

---

#### TAREFA 3.3: Implementar Job: Brief Diário
**Status:** ⬜
**Arquivo:** `src/app/workers/jobs.py` (função: `send_daily_brief`)
**Checklist:**
- [ ] Busca tarefas e eventos do dia
- [ ] Formata brief
- [ ] Envia via WhatsApp
- [ ] Logging de execução
- [ ] Commit: "feat: Add daily brief job"

---

#### TAREFA 3.4: Implementar Job: Lembretes de Prazo
**Status:** ⬜
**Arquivo:** `src/app/workers/jobs.py` (função: `check_deadlines`)
**Checklist:**
- [ ] Busca tarefas com prazo em 24h
- [ ] Envia lembretes
- [ ] Marca como notificado
- [ ] Commit: "feat: Add deadline reminder job"

---

#### TAREFA 3.5: Implementar Job: Verificação de Atrasadas
**Status:** ⬜
**Arquivo:** `src/app/workers/jobs.py` (função: `check_overdue`)
**Checklist:**
- [ ] Identifica tarefas atrasadas
- [ ] Notifica usuário
- [ ] Commit: "feat: Add overdue check job"

---

#### TAREFA 3.6: Implementar Job: Lembretes de Eventos
**Status:** ⬜
**Arquivo:** `src/app/workers/jobs.py` (função: `event_reminders`)
**Checklist:**
- [ ] Busca eventos próximos (30 min)
- [ ] Envia lembretes
- [ ] Commit: "feat: Add event reminder job"

---

#### TAREFA 3.7: Criar Worker Container no Docker Compose
**Status:** ⬜
**Arquivo:** `docker-compose.yml`
**Modificação:**
```yaml
  worker:
    build: .
    command: python -m app.workers.scheduler
    depends_on:
      - db
      - cache
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EVOLUTION_API_BASE_URL=${EVOLUTION_API_BASE_URL}
      - EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
    restart: unless-stopped
```

**Checklist:**
- [ ] Serviço worker adicionado
- [ ] Variáveis de ambiente corretas
- [ ] Restart policy configurada
- [ ] Commit: "docker: Add worker container for ProactivityEngine"

---

### FASE 4: INTERFACE WEB E APIs

#### TAREFA 4.1: Criar endpoints /api/v1/storage-configs
**Status:** ⬜
**Arquivo:** `src/app/api/v1/storage_configs.py`
**Endpoints:**
- GET /api/v1/storage-configs (listar configurações)
- POST /api/v1/storage-configs (criar nova)
- PUT /api/v1/storage-configs/{id} (atualizar)
- DELETE /api/v1/storage-configs/{id} (deletar)
- GET /api/v1/storage-configs/available (listar adapters disponíveis)

**Checklist:**
- [ ] Todos endpoints implementados
- [ ] Validação Pydantic
- [ ] Testes de API
- [ ] OpenAPI docs gerado
- [ ] Commit: "feat: Add storage-configs API endpoints"

---

#### TAREFA 4.2: Criar página /web/settings
**Status:** ⬜
**Arquivo:** `src/app/web/templates/settings.html`
**Checklist:**
- [ ] Formulário de configuração
- [ ] Lista de adapters disponíveis
- [ ] Configurações ativas
- [ ] Test connection button
- [ ] CSS styling
- [ ] JavaScript interativo
- [ ] Commit: "feat: Add web settings page"

---

#### TAREFA 4.3: Adicionar rota /web/settings
**Status:** ⬜
**Arquivo:** `src/app/api/v1/web.py`
**Checklist:**
- [ ] Rota GET /web/settings
- [ ] Rota POST /web/settings/save
- [ ] Autenticação requerida
- [ ] Commit: "feat: Add settings route to web interface"

---

### FASE 5: TESTES COMPLETOS

#### TAREFA 5.1: Testes unitários StorageAdapter
**Status:** ⬜
**Arquivo:** `tests/unit/infrastructure/storage/test_adapters.py`
**Checklist:**
- [ ] Test NotionAdapter
- [ ] Test ClickUpAdapter
- [ ] Test SheetsAdapter
- [ ] Mock de APIs externas
- [ ] Cobertura > 85%
- [ ] Commit: "test: Add unit tests for storage adapters"

---

#### TAREFA 5.2: Testes integração StorageService
**Status:** ⬜
**Arquivo:** `tests/integration/storage/test_storage_service.py`
**Checklist:**
- [ ] Test múltiplos backends
- [ ] Test retry logic
- [ ] Test fallback
- [ ] Commit: "test: Add integration tests for StorageService"

---

#### TAREFA 5.3: Testes ProactivityEngine
**Status:** ⬜
**Arquivo:** `tests/unit/workers/test_jobs.py`
**Checklist:**
- [ ] Test daily brief
- [ ] Test deadline reminders
- [ ] Test overdue check
- [ ] Test event reminders
- [ ] Mock APScheduler
- [ ] Commit: "test: Add tests for ProactivityEngine jobs"

---

#### TAREFA 5.4: Testes E2E WhatsApp
**Status:** ⬜
**Arquivo:** `tests/integration/test_whatsapp_flow.py`
**Checklist:**
- [ ] Envio de tarefa via WhatsApp
- [ ] Recebimento de confirmação
- [ ] Brief diário via WhatsApp
- [ ] Lembretes via WhatsApp
- [ ] Commit: "test: Add E2E tests for WhatsApp integration"

---

#### TAREFA 5.5: Testes E2E Web
**Status:** ⬜
**Arquivo:** `tests/integration/test_web_flow.py`
**Checklist:**
- [ ] Login
- [ ] Envio de tarefa
- [ ] Configuração de storage
- [ ] Página settings
- [ ] Commit: "test: Add E2E tests for web interface"

---

#### TAREFA 5.6: Executar suite completa de testes
**Status:** ⬜
**Comando:**
```bash
cd /home/marcocardoso/projects/SparkOne-AI
pytest --cov=src --cov-report=term-missing --cov-report=html
```

**Critérios:**
- [ ] Cobertura > 85%
- [ ] Todos testes passando
- [ ] Nenhum warning crítico
- [ ] Report HTML gerado

---

### FASE 6: DOCUMENTAÇÃO FINAL

#### TAREFA 6.1: Verificar duplicidade de documentação
**Status:** ⬜
**Comando:**
```bash
find docs/ -name "*.md" -exec echo "=== {} ===" \; -exec head -20 {} \;
```

**Checklist:**
- [ ] Listar todos .md em docs/
- [ ] Identificar conteúdo duplicado
- [ ] Consolidar em documento único
- [ ] Remover duplicatas
- [ ] Commit: "docs: Remove duplicate documentation"

---

#### TAREFA 6.2: Atualizar PRD (Status Final)
**Status:** ⬜
**Arquivo:** `docs/prd/sparkone/PRD.pt-BR.md`
**Atualizações:**
- [ ] RF-015: ❌ → ✅
- [ ] RF-019: 🔄 → ✅
- [ ] RF-020: 🔄 → ✅
- [ ] Matriz de implementação atualizada
- [ ] Progresso: 60% → 85%
- [ ] Commit: "docs: Update PRD with implementation status"

---

#### TAREFA 6.3: Atualizar System Map
**Status:** ⬜
**Arquivo:** `docs/prd/sparkone/system-map.md`
**Adições:**
- [ ] Diagrama com StorageAdapterRegistry
- [ ] Worker container no diagrama
- [ ] Fluxo de ProactivityEngine
- [ ] Commit: "docs: Update system map with new architecture"

---

#### TAREFA 6.4: Atualizar Glossário
**Status:** ⬜
**Arquivo:** `docs/prd/sparkone/glossario.md`
**Novos termos:**
- [ ] StorageAdapter
- [ ] StorageAdapterRegistry
- [ ] ProactivityEngine
- [ ] APScheduler
- [ ] ClickUp
- [ ] User Preferences
- [ ] Commit: "docs: Add new terms to glossary"

---

#### TAREFA 6.5: Criar guia de configuração
**Status:** ⬜
**Arquivo:** `docs/guides/configuration.md` (NOVO)
**Conteúdo:**
- [ ] Como configurar Notion
- [ ] Como configurar ClickUp
- [ ] Como configurar Google Sheets
- [ ] Como configurar brief diário
- [ ] Troubleshooting
- [ ] Commit: "docs: Add configuration guide"

---

#### TAREFA 6.6: Atualizar README.md
**Status:** ⬜
**Arquivo:** `README.md`
**Atualizações:**
- [ ] Adicionar ProactivityEngine nas features
- [ ] Adicionar Multi-Storage Backend
- [ ] Atualizar instruções de setup
- [ ] Adicionar screenshots (se aplicável)
- [ ] Commit: "docs: Update README with new features"

---

#### TAREFA 6.7: Criar CHANGELOG.md
**Status:** ⬜
**Arquivo:** `CHANGELOG.md` (NOVO)
**Conteúdo:**
```markdown
# Changelog

## [0.2.0] - 2025-01-27

### Added
- Multi-Storage Backend System (Notion, ClickUp, Google Sheets)
- ProactivityEngine with automatic reminders
- Daily brief automation
- User preferences management
- Web settings interface

### Changed
- Refactored TaskService to use StorageService
- Updated documentation with new ADRs

### Fixed
- Improved error handling in storage sync
- Better timezone handling in scheduler
```

**Checklist:**
- [ ] CHANGELOG criado
- [ ] Versionamento semântico
- [ ] Commit: "docs: Add CHANGELOG.md"

---

## 📊 CRITÉRIOS DE CONCLUSÃO

### DEFINIÇÃO DE "PRONTO":
Cada tarefa está completa quando:
- [ ] Código implementado e funcionando
- [ ] Testes criados e passando
- [ ] Documentação atualizada
- [ ] Commit feito com mensagem descritiva
- [ ] Nenhum warning crítico

### PROJETO COMPLETO QUANDO:
- [ ] Todas 50 tarefas marcadas como ✅
- [ ] Cobertura de testes > 85%
- [ ] Documentação sem duplicidades
- [ ] Todas funcionalidades testadas manualmente
- [ ] Docker Compose funciona completo
- [ ] README atualizado

---

## 🐛 ISSUES ENCONTRADAS

### TEMPLATE PARA REGISTRAR PROBLEMAS:
```markdown
### ISSUE #X: [Título]
**Tarefa Afetada:** X.X
**Severidade:** Alta | Média | Baixa
**Descrição:** ...
**Solução Proposta:** ...
**Status:** Aberto | Em Análise | Resolvido
```

---

## 📈 PROGRESSO POR FASE

```
FASE 1: DOCUMENTAÇÃO        ✅✅✅✅ 4/4  (100%)
FASE 2: STORAGE ADAPTERS    ✅✅✅✅⬜⬜⬜⬜⬜ 4/9  (44%)
FASE 3: PROACTIVITY ENGINE  ⬜⬜⬜⬜⬜⬜⬜ 0/7  (0%)
FASE 4: WEB & APIs          ⬜⬜⬜ 0/3  (0%)
FASE 5: TESTES              ⬜⬜⬜⬜⬜⬜ 0/6  (0%)
FASE 6: DOCS FINAIS         ⬜⬜⬜⬜⬜⬜⬜ 0/7  (0%)

TOTAL: 8/36 tarefas (22%)
```

---

## 🚀 COMANDOS RÁPIDOS

### Rodar todos os testes:
```bash
pytest --cov=src --cov-report=term-missing
```

### Subir ambiente completo:
```bash
docker-compose up -d
```

### Verificar logs do worker:
```bash
docker-compose logs -f worker
```

### Criar migration:
```bash
alembic revision -m "description"
```

### Aplicar migrations:
```bash
alembic upgrade head
```

---

## 📞 CHECKPOINT DE RETOMADA

**ÚLTIMA TAREFA COMPLETA:** 2.4 - NotionAdapter (Commits: 1d0e1c7, f350ed8)
**PRÓXIMA TAREFA:** 2.5 - Implementar ClickUpAdapter
**FASE ATUAL:** FASE 2 - IMPLEMENTAÇÃO STORAGE ADAPTERS (44% completo)
**PROGRESSO GERAL:** 8/36 tarefas (22%)
**DATA ÚLTIMA ATUALIZAÇÃO:** 2025-01-27

---

**FIM DO MASTER PLAN**
**Última atualização:** 2025-01-27 às 12:00 UTC
