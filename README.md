# SparkOne

Assistente pessoal modular inspirado no "Jarvis" do Marco Cardoso. Este repositório contém o MVP em FastAPI com orquestração via Agno (a ser integrado), suporte a múltiplos provedores de modelo (OpenAI + fallback local) e infraestrutura local com Docker Compose.

> Para uma visão resumida em inglês, consulte `README_EN.md`.

## Pré-requisitos
- Python 3.11+
- Docker + Docker Compose
- Make (opcional)

## Configuração Rápida (stack Postgres)
1. Copie e ajuste credenciais no `.env` (já configurado para o Compose usar Postgres/Redis).
2. Suba os serviços com Make (ou docker compose direto):
   ```bash
   make dev-up
   ```
3. Rode as migrações iniciais em outro terminal:
   ```bash
   make migrate
   ```
4. Acesse a documentação interativa em `http://localhost:8000/docs`.
5. Interface web (HTTP Basic) em `http://localhost:8000/web`.
6. Para enviar payload bruto use `POST /channels/{nome}` (ex.: `/channels/whatsapp`).
7. Configure o webhook Evolution para `POST /webhooks/whatsapp`.
8. Briefs disponíveis em `GET /brief/structured` ou `GET /brief/text`.
9. Tarefas/eventos: `GET /tasks`, `PATCH /tasks/{id}`, `GET /events`.
10. Métricas Prometheus em `GET /metrics`; health em `/health`.

### Executar sem Docker (opcional)
1. Suba Postgres/Redis (por exemplo via Docker):
   ```bash
   docker compose up db cache
   ```
2. Instale dependências locais:
   ```bash
   pip install -e .[dev]
   ```
3. Ajuste `DATABASE_URL`/`VECTOR_STORE_URL` para `postgresql+asyncpg://sparkone:sparkone@localhost:5433/sparkone`.
4. Rode migrações e o servidor:
   ```bash
   alembic upgrade head
   uvicorn src.app.main:app --reload --port 8000
   ```

## Estrutura de Pastas
- `src/app/main.py`: inicialização FastAPI e registro de rotas.
- `src/app/routers/`: endpoints (`/health`, `/ingest`).
- `src/app/models/`: esquemas Pydantic como `ChannelMessage`.
- `src/app/providers/`: provedores de LLM/embeddings com fallback OpenAI ⇆ local.
- `src/app/workers/`: workers assíncronos (scheduler placeholder).

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
- Instale dependências diretamente:
  ```bash
  pip install -e .[dev]
  ```
- Rode o servidor em modo desenvolvimento:
  ```bash
  uvicorn src.app.main:app --reload
  ```
- Execute `make install-dev` na primeira vez para instalar dependências de desenvolvimento (ruff, mypy, pytest).
- Valide o código com `make check` (encadeia lint, formatação, mypy e pytest).
- Ingestão de conhecimento:
  ```bash
  python scripts/ingest_docs.py docs/meu_arquivo.md --source=wiki
  ```
- Makefile atualizado expõe rotinas úteis:
  - `make install-dev` para preparar o ambiente local.
  - `make fmt` / `make fmt-check` para formatação com Black.
  - `make lint` (Ruff) e `make typecheck` (mypy).
  - `make test` para Pytest; `make check` encadeia todas as verificações.

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
- `ops/staging-compose.yml` descreve um ambiente staging com API, Postgres, Redis e backup diário automático.
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
