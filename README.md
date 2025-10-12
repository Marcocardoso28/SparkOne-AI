# SparkOne

Assistente pessoal modular inspirado no "Jarvis" do Marco Cardoso. Este repositório contém o MVP em FastAPI com orquestração via Agno (a ser integrado), suporte a múltiplos provedores de modelo (OpenAI + fallback local) e infraestrutura local com Docker Compose ou SQLite.

> Para uma visão resumida em inglês, consulte `README_EN.md`.

## Pré-requisitos
- Python 3.11+
- Docker + Docker Compose (opcional)
- Make (opcional)

## Configuração Rápida (SQLite - Desenvolvimento Local)
1. Clone o repositório e navegue até a pasta:
   ```bash
   git clone <repo-url>
   cd SparkOne
   ```
2. **Setup automatizado** (recomendado):
   ```bash
   make setup
   ```
   Ou manualmente:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # ou source venv/bin/activate  # Linux/Mac
   pip install -e .[dev]
   ```
3. Configure as variáveis de ambiente:
   ```bash
   cp config/env.example .env
   ```
4. Crie as tabelas do banco SQLite:
   ```bash
   python scripts/development/setup_local_db.ps1  # Windows
   # ou python scripts/development/setup_local_db.py  # Linux/Mac
   ```
5. Inicie o servidor:
   ```bash
   python scripts/development/start_server.ps1  # Windows
   # ou uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
6. Acesse a documentação interativa em `http://localhost:8000/docs`.

## Configuração com Docker (stack Postgres)
1. Configure as variáveis de ambiente:
   ```bash
   cp config/env.example .env
   # Edite .env com suas configurações de Postgres/Redis
   ```
2. Suba os serviços com Docker Compose:
   ```bash
   docker-compose -f config/docker/docker-compose.yml up -d
   ```
3. Rode as migrações iniciais:
   ```bash
   docker-compose -f config/docker/docker-compose.yml run --rm api alembic upgrade head
   ```
4. Acesse a documentação interativa em `http://localhost:8000/docs`.

## Endpoints Principais
- **Documentação**: `http://localhost:8000/docs` - Interface Swagger da API
- **Health Check**: `GET /health` - Status da aplicação
- **Tarefas**: `GET /tasks` - Lista de tarefas
- **Métricas**: `GET /metrics` - Métricas Prometheus
- **Interface Web**: `http://localhost:8000/web` - Interface web (HTTP Basic)
- **Webhooks**: `POST /webhooks/whatsapp` - Webhook Evolution API
- **Canais**: `POST /channels/{nome}` - Envio de mensagens por canal
- **Briefs**: `GET /brief/structured` ou `GET /brief/text` - Resumos estruturados
- **Eventos**: `GET /events` - Lista de eventos do sistema

## Estrutura de Pastas
```
SparkOne/
├── src/app/                    # Código da aplicação
│   ├── domain/                 # Lógica de domínio
│   ├── infrastructure/         # Infraestrutura
│   ├── api/                    # Camada API
│   ├── routers/                # Endpoints FastAPI
│   ├── models/                 # Schemas Pydantic
│   ├── services/               # Lógica de negócio
│   └── main.py                 # Inicialização da aplicação
├── docs/                       # Documentação completa
│   ├── architecture/           # Arquitetura e decisões
│   ├── operations/             # Guias de deploy e operações
│   ├── development/            # Guias de desenvolvimento
│   ├── prd/                    # Product Requirements
│   └── reports/                # Relatórios e status
├── tests/                      # Testes organizados
│   ├── unit/                   # Testes unitários
│   ├── integration/            # Testes de integração
│   ├── e2e/                    # Testes end-to-end
│   ├── smoke/                  # Smoke tests
│   └── testsprite/             # Testes TestSprite
├── scripts/                    # Scripts de automação
│   ├── development/            # Setup e desenvolvimento
│   ├── maintenance/            # Organização e health check
│   ├── production/             # Deploy e produção
│   └── tools/                  # Ferramentas utilitárias
├── config/                     # Configurações
│   ├── docker/                 # Docker files
│   └── *.env                   # Variáveis de ambiente
├── data/                       # Dados e migrações
│   ├── databases/              # Bancos de dados
│   ├── backups/                # Backups
│   └── uploads/                # Uploads
├── ops/                        # Operações de infraestrutura
│   ├── monitoring/             # Prometheus, Grafana
│   ├── traefik/                # Reverse proxy
│   └── scripts/                # Scripts de ops
└── tools/                      # Ferramentas de validação
    ├── validation/             # Validação de PRD
    └── automation/             # Automação
```

## Provedores de Modelo
A configuração padrão utiliza OpenAI (`gpt-4.1`) como primário e um endpoint OpenAI-compatível self-hosted (ex.: vLLM com `llama-3.1-8b-instruct`) como fallback. Ajuste as variáveis no `.env` conforme o seu gateway local.

## Dispatcher de Eventos
Defina `ENABLE_EVENT_DISPATCHER=true` e `EVENT_WEBHOOK_URL` para encaminhar eventos `message.processed` a orquestradores externos (ex.: n8n). O token opcional (`EVENT_WEBHOOK_TOKEN`) é enviado no header `Authorization`.

## Web UI
O endpoint `/web` disponibiliza uma interface minimalista e responsiva para envio manual de solicitações.
- Entradas suportadas: texto, upload de imagem e gravação de áudio (MediaRecorder) com pré-visualização.
- Um modo de ditado utiliza a Web Speech API quando disponível.
- Defina `WEB_PASSWORD` no `.env` para proteger o acesso via HTTP Basic (usuário livre, somente senha é validada).
- As submissões exigem token CSRF: o cookie `sparkone_csrftoken` e o campo oculto `csrf_token` (ou header `X-SparkOne-CSRF`) precisam corresponder.

## Exemplos de Payload
- **WhatsApp (POST `/channels/whatsapp`)**
  ```json
  {
    "from": "5511999999999",
    "message": "Criar tarefa preparar relatório até amanhã",
    "metadata": {"due_at": "2025-01-15T17:00:00-03:00"}
  }
  ```
- **Webhook Evolution (POST `/webhooks/whatsapp`)** – use o mesmo corpo do canal acima.
- **Google Sheets** – cada linha convertida em mensagem (`row_index` preenchido no sync):
  ```json
  {
    "row": ["Criar evento", "2025-01-20", "10:00"],
    "sheet_id": "<SPREADSHEET_ID>",
    "user": "sheets",
    "row_index": 12
  }
  ```
- **Brief estruturado (GET `/brief/structured`)** retorna JSON com tarefas, eventos e últimas conversas; para texto amigável use `GET /brief/text`.

## Sincronização com Google Sheets
- Preencha `GOOGLE_SHEETS_CREDENTIALS_PATH`, `GOOGLE_SHEETS_SYNC_SPREADSHEET_ID` e `GOOGLE_SHEETS_SYNC_RANGE`.
- O worker agenda sincronização a cada 5 minutos (`sheets-sync`). Cada linha nova é normalizada e enviada para o pipeline padrão.

## Automação / n8n
- Ative `ENABLE_EVENT_DISPATCHER` e defina `EVENT_WEBHOOK_URL` para receber notificações `message.processed` contendo `message_id`, `channel`, `sender` e status/classificação.
- No n8n use um **Webhook Trigger** com header `X-Event-Name` para filtrar eventos e acionar fluxos (ex.: enviar notificação, abrir ticket).

## Desenvolvimento Local

### Scripts de Automação
O projeto inclui scripts organizados por propósito:

- **Desenvolvimento**: `scripts/development/`
  - `setup_dev.py` - Setup completo do ambiente
  - `bootstrap_dev.py` - Bootstrap inicial
  - `start_server.ps1` - Inicialização do servidor
- **Manutenção**: `scripts/maintenance/`
  - `organize_project.py` - Organização automática do projeto
  - `project_health_check_updated.py` - Verificação de saúde (100/100)
- **Produção**: `scripts/production/`
  - `setup_production.sh` - Setup de produção
  - `smoketest.py` - Testes de smoke

### Comandos Make Disponíveis
```bash
make setup      # Setup completo do ambiente
make test       # Executar testes
make organize   # Organizar projeto
make health     # Health check do projeto
make fmt        # Formatar código com Black
make lint       # Linting com Ruff
make typecheck  # Verificação de tipos com MyPy
make check      # Todas as verificações
```

### Validação e Qualidade
- **Health Check**: `python scripts/maintenance/project_health_check_updated.py`
- **Validação PRD**: `python tools/validation/prd_validator.py`
- **Organização**: `python scripts/maintenance/organize_project.py`

### Ingestão de Conhecimento
```bash
python scripts/tools/ingest_docs.py docs/meu_arquivo.md --source=wiki
```

## Documentação

O projeto possui documentação completa e organizada em `docs/`:

### 📚 Navegação Principal
- **[Índice Mestre](docs/INDEX.md)** - Guia centralizado de toda documentação
- **[README Principal](docs/README.md)** - Visão geral do projeto
- **[Status Atual](docs/reports/current-status.md)** - Status consolidado

### 🏗️ Arquitetura
- **[Visão Geral](docs/architecture/overview.md)** - Contexto e decisões arquiteturais
- **[Infraestrutura](docs/architecture/infrastructure.md)** - Deploy, monitoramento e segurança

### ⚙️ Operações
- **[Guia de Deploy](docs/operations/deployment-guide.md)** - Deploy em produção
- **[Runbook](docs/operations/operations-runbook.md)** - Operações e troubleshooting

### 💻 Desenvolvimento
- **[Guia de Desenvolvimento](docs/development/development-guide.md)** - Setup e padrões
- **[Estratégia de Testes](docs/development/testing-strategy.md)** - Testes e validações

### 📋 PRD (100/100 - A+)
- **[PRD Português](docs/prd/sparkone/PRD.pt-BR.md)** - Requisitos em português
- **[PRD Inglês](docs/prd/sparkone/PRD.en-US.md)** - Requirements in English
- **[Relatório de Validação](docs/prd/sparkone/FREEZE_REPORT.md)** - Auditoria completa

## Integração Contínua
- Workflow `CI` (`.github/workflows/ci.yml`) roda em push/PR nos ramos padrão:
  - Instala dependências com `pip install -e .[dev]`.
  - Executa `ruff`, `mypy` e `pytest` garantindo qualidade antes do merge.

## Variáveis de Ambiente Relevantes
- `NOTION_API_KEY` / `NOTION_DATABASE_ID`: habilitam criação automática de páginas no Notion.
- `CALENDAR_PROVIDER` (`none`, `google`, `caldav`) e credenciais correspondentes (`GOOGLE_CALENDAR_CREDENTIALS_PATH`, `CALDAV_*`).
- `GOOGLE_SHEETS_*`: controle da sincronização periódica de Planilhas.
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: caminho do JSON de conta de serviço para acesso ao Sheets.
- `GOOGLE_CALENDAR_CREDENTIALS_PATH`: credencial usada pelo provider Google Calendar.
- O JSON deve estar habilitado com o escopo `https://www.googleapis.com/auth/calendar` e acesso ao calendário alvo.
- `WHATSAPP_NOTIFY_NUMBERS`: lista de números separados por vírgula que recebem o brief diário via Evolution API.
- `WHATSAPP_SEND_MAX_RETRIES`: tentativas de reenvio ao Evolution API antes de acionar fallback (padrão 3).
- `FALLBACK_EMAIL`: e-mail usado para fallback (log/alerta) quando notificações WhatsApp falham.
- `SMTP_HOST/PORT/USERNAME/PASSWORD`: credenciais SMTP para fallback de e-mail.
- `REQUIRE_AGNO=true` força validação de provider configurado para AgnoBridge na inicialização.
- `EVOLUTION_API_TIMEOUT`: timeout (segundos) para chamadas à Evolution API (padrão 10s).
- `LLM_REQUEST_TIMEOUT`: timeout (segundos) para chamadas aos modelos de linguagem (padrão 15s).
- `LLM_MAX_RETRIES`: tentativas de repetição para chamadas aos modelos (padrão 2).
- `WEB_UPLOAD_DIR`: diretório para armazenar uploads feitos pela interface web (padrão `uploads`).
- `WEB_MAX_UPLOAD_SIZE`: tamanho máximo (bytes) aceito para arquivos enviados pela web (padrão 10485760).
- `WEB_SESSION_TTL_SECONDS`: duração da sessão da Web UI antes de exigir nova autenticação (padrão 1800 segundos).
- `INGESTION_MAX_CONTENT_LENGTH`: comprimento máximo permitido (caracteres) para mensagens ingestadas (padrão 6000).
- `ALLOWED_HOSTS`: hosts permitidos (CSV) para `TrustedHostMiddleware` (`*` para liberar geral).
- `CORS_ORIGINS` / `CORS_ALLOW_METHODS` / `CORS_ALLOW_HEADERS` / `CORS_ALLOW_CREDENTIALS`: controle detalhado de CORS.
- `SECURITY_HSTS_ENABLED`, `SECURITY_HSTS_MAX_AGE`, `SECURITY_HSTS_INCLUDE_SUBDOMAINS`, `SECURITY_HSTS_PRELOAD`: configuram o cabeçalho `Strict-Transport-Security`.

## Automação / n8n
- Ative `ENABLE_EVENT_DISPATCHER` e defina `EVENT_WEBHOOK_URL` para receber notificações `message.processed` contendo `message_id`, `channel`, `sender` e classificação.
- Use um **Webhook Trigger** no n8n filtrando o header `X-Event-Name` para acionar fluxos (ex.: criar ticket, disparar aviso).

## Staging & Backups
- `ops/staging-compose.yml` descreve um ambiente staging com API, Postgres, Redis, Traefik (TLS automático), Prometheus, Alertmanager, cAdvisor e backup diário.
- Scripts utilitários:
  - `ops/backup.sh [destino]` → gera dump `pg_dump` via container `db`.
  - `ops/restore.sh <arquivo.sql>` → restaura dump selecionado.
  - `ops/verify_backup.sh <arquivo.sql>` → valida backup restaurando em container temporário.

### Pipeline de Deploy
- Workflow `deploy-staging.yml` (GitHub Actions) constrói imagem Docker e publica no GHCR; configure os seguintes secrets na organização/repo:
  - `SSH_HOST`, `SSH_USERNAME`, `SSH_KEY` (para publicar em staging via SSH)
  - `STAGING_PATH` apontando para diretório com `docker-compose.yml`
  - `STAGING_URL` para smoke tests externos via `curl`
- O job final pode ser estendido com smoke tests após o deploy.

### Observabilidade
- Importar `ops/grafana/dashboard-overview.json` no Grafana para visualizar métricas principais (requests, sync failures, notificações).
- Adicionar `ops/prometheus/alerts.yml` no Alertmanager para alertas de Notion/Sheets/tráfego.
- Definir `SLACK_ALERT_WEBHOOK` ao subir `alertmanager` para que regras de alerta enviem notificações ao Slack.

### Backups Automatizados
- Workflow `backup.yml` agenda (cron 0 2 * * *) execução remota de `ops/backup.sh` via SSH. Configure `SSH_HOST`, `SSH_USERNAME`, `SSH_KEY`, `STAGING_PATH` para habilitar.
- Instruções operacionais e runbooks em `docs/OPERATIONS.md`.

## Métricas & Observabilidade
- Métricas Prometheus expostas em `/metrics` (contagem e latência por endpoint). É recomendado:
  - Executar o container oficial `prom/prometheus` apontando para este endpoint;
  - Carregar `ops/prometheus/alerts.yml` no Alertmanager para receber alertas de Notion/Sheets/alto tráfego;
  - Utilizar Grafana (podcast `grafana/grafana`) importando dashboards de HTTP/general e adicionando gráficos derivados das métricas `sparkone_*`.
- Health checks adicionais expostos em `/health`:
  - `/health/openai` verifica disponibilidade do provedor LLM configurado.
  - `/health/notion` e `/health/evolution` garantem credenciais válidas para integrações externas.
  - `/health/database`, `/health/redis` monitoram infraestrutura local.
- Métricas específicas de integrações:
  - `sparkone_notion_sync_total{status="success|failure"}` – sucesso/falha ao sincronizar tarefas com Notion.
  - `sparkone_sheets_sync_total{status="success|failure|skipped"}` – status de sincronização com Google Sheets.
- `ops/prometheus/alerts.yml` fornece regras de alerta exemplo (Notion/Sheets/alto tráfego) para uso com Alertmanager.
- Health checks específicos:
  - `/health/` (básico)
  - `/health/database` (valida conexão Postgres)
  - `/health/redis` (valida Redis)
- Logs estruturados JSON via structlog; configure agregadores externos conforme o ambiente.
- Recomenda-se configurar Grafana consumindo `/metrics` e aplicar os dashboards/alertas conforme o arquivo `ops/prometheus/alerts.yml`.

## 🎉 Status do Projeto

**Score de Qualidade: 100/100 - A+** ✅

O projeto SparkOne está **completamente organizado** e em **estado excelente**:

### ✅ Organização Completa
- **Estrutura profissional** com separação clara de responsabilidades
- **Documentação consolidada** e hierárquica
- **Testes organizados** por tipo (unit, integration, e2e, smoke)
- **Scripts categorizados** por propósito (dev, maintenance, production)
- **Configurações centralizadas** em `config/`
- **Dados organizados** em `data/`

### 🛠️ Ferramentas de Qualidade
- **Health Check automatizado** (100/100)
- **Validação de PRD** (Score 100/100 - A+)
- **Scripts de organização** automática
- **Makefile** com comandos padronizados

### 📚 Documentação Perfeita
- **PRDs bilíngues** completos (Português/Inglês)
- **Guias de desenvolvimento** e operações
- **Arquitetura documentada** com decisões
- **Índices de navegação** centralizados

### 🚀 Pronto para Produção
- **Deploy automatizado** com Docker
- **Monitoramento completo** (Prometheus, Grafana)
- **Backups automatizados**
- **Operações documentadas**

Para mais detalhes, consulte:
- **[Relatório de Organização](docs/reports/ORGANIZATION_COMPLETE.md)**
- **[Resumo Executivo](docs/reports/ORGANIZATION_SUMMARY.md)**
- **[Status Atual](docs/reports/current-status.md)**
