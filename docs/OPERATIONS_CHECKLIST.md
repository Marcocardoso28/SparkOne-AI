# SparkOne Operations Checklist

## Pré-deploy
- [ ] Conferir `.env` com credenciais válidas (OpenAI, Evolution, Notion, Redis, SMTP).
- [ ] Executar `python scripts/bootstrap_dev.py` (ou provisionar diretórios `uploads/` e `.env`).
- [ ] `make install-dev` e `make check` – garantir lint, mypy e testes passando.
- [ ] Atualizar imagem Docker (`docker compose build`) e rodar `docker compose up` para smoke local.
- [ ] Registrar hosts/CORS (`ALLOWED_HOSTS`, `CORS_*`) específicos do ambiente.

## Deploy
- [ ] Aplicar migrações: `docker compose exec api alembic upgrade head`.
- [ ] Rodar smoke tests pós-deploy: `python scripts/smoketest.py --base-url https://sparkone.example.com`.
- [ ] Validar health checks (`/health/*`) e métricas (`/metrics`).
- [ ] Confirmar webhook Evolution e Notion configurados no painel externo.

## Observabilidade
- [ ] Prometheus apontando para `/metrics` (alertas de Sheets/Notion/WhatsApp habilitados).
- [ ] Grafana importando dashboards (`ops/grafana/dashboard-overview.json`).
- [ ] Health checks monitorados (database, redis, openai, notion, evolution).
- [ ] Logs estruturados enviados para o agregador (verificar redaction funcionando).

## Backups & DR
- [ ] Habilitar workflow `backup.yml` com credenciais SSH (`SSH_HOST`, `SSH_USERNAME`, `SSH_KEY`).
- [ ] Testar `ops/backup.sh`, `ops/restore.sh` e `ops/verify_backup.sh` em staging.
- [ ] Validar restauração periódica (trimestral) – manual ou via job agendado.

## Segurança
- [ ] Revisar acesso à interface web (`WEB_PASSWORD` ou proteção adicional via proxy).
- [ ] Garantir HTTPS com HSTS ativado em produção.
- [ ] Rotacionar chaves/segredos críticos a cada 90 dias.
- [ ] Registrar incidentes em `SECURITY.md` (contato, SLA, histórico).

## Pós-deploy
- [ ] Registrar versão/mudanças no changelog interno.
- [ ] Notificar stakeholders (time, executivos) e check de smoke manual: ingestão web, webhook, brief.
- [ ] Revisar backlog de observabilidade (OpenTelemetry, traces, LGPD) e planejar próximo ciclo.
