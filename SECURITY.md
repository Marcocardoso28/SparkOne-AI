# SparkOne Security Baseline (2025)

## Contatos
- Responsável: security@macspark.dev
- SLA resposta: 24h úteis
- Canal de emergência: +55 11 9 9999 9999 (signal)

## Controles Atuais
- Rate limiting global (Redis quando disponível, com fallback em memória) e middleware dedicado por rota sensível.
- Headers de segurança: HSTS (prod), CSP (strict), Permissions-Policy e X-Content-Type-Options.
- Sanitização/validação por Pydantic + validadores customizados (`src/app/core/validation.py`).
- Logs estruturados (structlog) sem persistir PII; correlação por `X-Correlation-ID`.

## Roadmap de Segurança
1. Implementar webhook signature (HMAC) para Evolution API e callbacks internos.
2. Adicionar secret scanning automatizado (gitleaks/pre-commit + GitHub Advanced Security).
3. Automatizar rotação de credenciais (AWS Secrets Manager ou Doppler) e alertar expirações.
4. Expandir testes de segurança: fuzz em `/webhooks/*`, testes SSRF, validação de headers.

## Procedimentos
- **Incidentes**: abrir issue privada + Slack #security-alerts.
- **Dependências**: executar `pip-audit` a cada PR crítico e revisar `dependabot` semanalmente.
- **Infra**: backups criptografados (pg_dump + restic); restaurar mensalmente (`ops/verify_backup.sh`).

## Políticas
- Produção acessível apenas via VPN WireGuard.
- Tokens de provedores em `.env` com TTL ≤ 90 dias.
- Uso obrigatório de `make secrets-scan` antes de merges (adicionar ao CI).
