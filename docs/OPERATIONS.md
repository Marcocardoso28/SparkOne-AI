# SparkOne Operação

## 1. Deploy
1. Ambiente local/staging: use `make dev-up` e `make migrate` para subir com Postgres/Redis.
2. Commit na branch `main` aciona `deploy-staging.yml` (imagem + deploy via SSH).
3. Secrets necessários: `SSH_HOST`, `SSH_USERNAME`, `SSH_KEY`, `STAGING_PATH`, `STAGING_URL`.
4. Verificar smoke tests no job (health, metrics, brief, tasks).

## 2. Monitoramento
- Prometheus: coletar `/metrics` do serviço (`sparkone_*`).
- Grafana: importar `ops/grafana/dashboard-overview.json`.
- Alertmanager: usar `ops/prometheus/alerts.yml` e apontar webhook para `/alerts/alertmanager`.

## 3. Rotina de Backups
- Workflow `backup.yml` roda `ops/backup.sh` via SSH diariamente.
- Para restore manual: `ops/restore.sh <arquivo.sql>`.
- Verificação periódica: `ops/verify_backup.sh <arquivo.sql>` (pode ser agendado em cron/GitHub Action).

## 4. Notificações
- WhatsApp: configurar `EVOLUTION_API_KEY` + `WHATSAPP_NOTIFY_NUMBERS`.
- Fallback: definir `FALLBACK_EMAIL` + `SMTP_*` para alertas e briefs se WhatsApp falhar.

## 5. Runbooks de Incidente
1. **Falha Notion** – verificar métricas `sparkone_notion_sync_total{status="failure"}`, logs e credenciais; replicar manualmente via API se necessário.
2. **Falha Google Sheets** – revisar `sparkone_sheets_sync_total{status="failure"}`, validar credenciais e estado da planilha.
3. **WhatsApp indisponível** – fallback dispara e-mail; validar Evolution Dashboard.
4. **Banco indisponível** – alertas via `/health/database`; considerar failover/restore a partir do último backup.

## 6. Segurança
- Habilitar TLS via Traefik/Nginx.
- Use `REQUIRE_AGNO=true` em produção para garantir provider configurado.
- Planejar OAuth2/MFA para `/web` (próxima etapa de hardening).
