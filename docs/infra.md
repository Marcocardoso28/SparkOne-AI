# Infraestrutura SparkOne — Guia de Produção

Este documento consolida padrões operacionais que podem ser aplicados imediatamente, mesmo antes da automação completa na VPS.

## Reverse Proxy & TLS
- Os manifests do Traefik vivem em `ops/traefik/`.
- Execute com `docker compose -f ops/staging-compose.yml up -d reverse-proxy` após copiar `acme.json` para o servidor e configurar permissões (600).
- Ajuste os domínios em `ops/traefik/dynamic/sparkone.yml` conforme DNS (produção/staging).
- Métricas do Traefik disponíveis em `reverse-proxy:8082/metrics` para Prometheus.

## Banco de Dados & Redis
- `ops/staging-compose.yml` usa Postgres standalone; ao migrar para cluster/managed service mantenha a URL em `DATABASE_URL`/`VECTOR_STORE_URL`.
- Scripts `ops/backup.sh` e `ops/restore.sh` aceitam variáveis `COMPOSE_FILE`, `DB_SERVICE`, `DB_USER`, `DB_NAME` para reuso remoto.
- `pgbackups` container faz dumps diários; sincronize `staging-backups` para storage externo (S3/B2) via cron/rsync.

## Backups
1. Backup manual local: `COMPOSE_FILE=ops/staging-compose.yml ./ops/backup.sh /path/backups`.
2. Restore: `COMPOSE_FILE=ops/staging-compose.yml ./ops/restore.sh sparkone_YYYYMMDD.sql`.
3. Validação: `./ops/verify_backup.sh sparkone_YYYYMMDD.sql` cria Postgres efêmero e aplica o dump.

## Observabilidade
- Prometheus configurado em `ops/prometheus/`. Inclui scraping de API, Traefik, cAdvisor e node-exporter.
- Alertmanager configurado em `ops/alertmanager/alertmanager.yml`; defina `SLACK_ALERT_WEBHOOK` antes de subir.
- Compose staging agora levanta `cadvisor`, `node-exporter`, `prometheus` e `alertmanager`.
- Atualize dashboards no Grafana (`ops/grafana/dashboard-overview.json`) apontando para as novas métricas.

## Gerenciamento de Secrets
- Use SOPS (KMS ou age) ou Vault. Estrutura sugerida:
  - `secrets/production.sops.yaml`
  - `secrets/staging.sops.yaml`
- Campos mínimos: credenciais Postgres, Redis, Evolution, Notion, SMTP, tokens Slack.
- GitHub Actions: decriptar com `sops` e exportar para `.env` antes do deploy; never commit `.env`.
- Documente rota de rotação (ver `docs/security.md`) e registre expiração de chaves sensíveis.

## Hardening de Containers
- Imagens base mantidas em `Dockerfile` (python slim). Checar periodicamente `docker scout` ou `trivy`.
- Ative `read_only: true` e `tmpfs` em serviços idempotentes quando mover para Compose/K8s definitivo.
- Habilite `security_opt: no-new-privileges:true` para API/worker.

## Próximos Passos
1. Substituir Postgres standalone por cluster (Patroni ou serviço gerenciado) com replicação síncrona.
2. Configurar Redis Sentinel ou usar Redis Managed com TLS.
3. Automatizar backups externos (S3 lifecycle) e testes de restore mensais.
4. Escrever playbooks no `docs/OPERATIONS.md` incluindo métricas, dashboards e alerta → runbook.
