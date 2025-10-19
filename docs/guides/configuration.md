# Guia de Configuração do SparkOne

Versão: 1.0
Atualizado: 2025-10-19

Este guia ajuda a configurar rapidamente os backends de armazenamento (Notion, ClickUp, Google Sheets) e as preferências do ProactivityEngine (brief diário e lembretes).

---

## Pré‑requisitos
- API chave válida para cada serviço externo que desejar usar
- Servidor SparkOne rodando (API e, se possível, Worker)
- Acesso ao endpoint `/web/settings` (HTTP Basic)

---

## 1) Notion (Tasks)

1. Crie uma integração no Notion e copie o `Internal Integration Token` (token da API).
2. Compartilhe o Database de tarefas com a integração criada (grante acesso ao database).
3. Copie o `database_id` do database de tarefas.

Você pode configurar via UI em `http://localhost:8000/web/settings` ou via API:

Endpoint: `POST /api/v1/storage-configs`
Exemplo de payload:

```json
{
  "adapter_name": "notion",
  "is_active": true,
  "priority": 10,
  "config_json": {
    "token": "NOTION_API_KEY",
    "database_id": "xxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

Campos relevantes (config_json):
- `token` (string): token da integração Notion
- `database_id` (string): ID do database de tarefas

---

## 2) ClickUp (Tasks)

1. Gere um `Personal API Token` em ClickUp (Settings → Apps → API Token).
2. Identifique o `list_id` onde as tarefas serão criadas.

Via UI em `/web/settings` ou via API:

Endpoint: `POST /api/v1/storage-configs`
Exemplo de payload:

```json
{
  "adapter_name": "clickup",
  "is_active": true,
  "priority": 5,
  "config_json": {
    "token": "CLICKUP_API_TOKEN",
    "list_id": "123456789"
  }
}
```

Campos relevantes (config_json):
- `token` (string): token de API do ClickUp
- `list_id` (string/numérico): lista alvo para criação das tarefas

---

## 3) Google Sheets (Import/Sync)

1. Crie uma Service Account no Google Cloud com acesso ao Google Sheets API.
2. Baixe o JSON da credencial e salve localmente (ex.: `secrets/google-sheets.json`).
3. Compartilhe a planilha alvo com o email da Service Account.
4. Defina no `.env` (se usar sync automático):

```
GOOGLE_SHEETS_CREDENTIALS_PATH=secrets/google-sheets.json
GOOGLE_SHEETS_SYNC_SPREADSHEET_ID=<SPREADSHEET_ID>
GOOGLE_SHEETS_SYNC_RANGE=Sheet1!A:C
```

Para uso como backend de armazenamento (linhas → tarefas), crie uma configuração:

```json
{
  "adapter_name": "sheets",
  "is_active": true,
  "priority": 1,
  "config_json": {
    "credentials_path": "secrets/google-sheets.json",
    "spreadsheet_id": "<SPREADSHEET_ID>",
    "range": "Sheet1!A:C"
  }
}
```

Campos relevantes (config_json):
- `credentials_path` (string): caminho do JSON da service account
- `spreadsheet_id` (string): ID da planilha
- `range` (string): intervalo padrão para leitura/escrita

---

## 4) Preferências do Usuário e ProactivityEngine

O ProactivityEngine usa APScheduler para disparar:
- Brief diário (padrão 08:00)
- Lembretes de prazo (24h antes)
- Verificação de tarefas atrasadas (a cada 6h)
- Lembretes de eventos (30min antes)

Configure preferências para o usuário (ex.: horário do brief, timezone, canais):

Endpoint: `PUT /api/v1/user-preferences`
Exemplo de payload:

```json
{
  "brief_time": "08:00",
  "timezone": "America/Sao_Paulo",
  "notification_channels": ["whatsapp"]
}
```

Variáveis de ambiente úteis (WhatsApp via Evolution API):
- `WHATSAPP_NOTIFY_NUMBERS`: CSV de números que receberão notificações
- `EVOLUTION_API_BASE_URL`, `EVOLUTION_API_TOKEN`: credenciais do gateway WhatsApp

---

## 5) Executando o Worker (Scheduler)

Docker Compose (produção): o serviço `worker` executa o `scheduler.py`.

Comandos úteis (ambiente local):
```
docker-compose -f config/docker/docker-compose.prod.yml up -d worker
docker-compose -f config/docker/docker-compose.prod.yml logs -f worker
```

---

## 6) Troubleshooting

- Notion 403/404: confirme que a integração tem acesso ao database e o `database_id` está correto.
- ClickUp 401: valide o token de API e o `list_id` do workspace correto.
- Sheets PERMISSION_DENIED: compartilhe a planilha com o email da service account.
- Horário do brief incorreto: ajuste `timezone` nas preferências do usuário.
- Worker não dispara jobs: verifique logs do container `worker` e variáveis de ambiente.

---

## Referências
- Storage Adapters: `src/app/infrastructure/storage/adapters/`
- Storage Registry: `src/app/infrastructure/storage/registry.py`
- Scheduler/Jobs: `src/app/workers/`
- UI de Configuração: `http://localhost:8000/web/settings`

