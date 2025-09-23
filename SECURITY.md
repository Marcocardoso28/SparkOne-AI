# SparkOne Security Guidelines

- **Contato para incidentes:** security@macspark.dev
- **Tempo alvo de resposta:** 24h úteis
- **Tempo alvo de mitigação:** 72h úteis

## Práticas já implementadas
- HTTPS obrigatório em produção (HSTS configurável).
- Rate limiting por IP e cabeçalhos de segurança (CSP, COOP/COEP, Permissions-Policy).
- Sanitização e limite de tamanho para mensagens ingestadas; CSRF + expiração de sessão na Web UI.
- Logs estruturados com remoção automática de segredos.

## Reporte responsável
1. Reproduza e documente o problema com detalhes mínimos necessários.
2. Não teste em ambientes de produção sem autorização prévia.
3. Envie e-mail para `security@macspark.dev` com título `[SparkOne Security]`.
4. A equipe confirmará recebimento em até 24h úteis e alinhará plano de mitigação.

## Cronograma de revisões
- Rotação de segredos a cada 90 dias.
- Pen-test interno anual ou após grandes releases.
- Revisão de dependências (SCA) mensal.

## Futuro próximo
- Integração com OAuth2/MFA (roadmap Q3).
- Observabilidade com OpenTelemetry + centralização de logs.
- Auditoria LGPD e runbooks de conformidade.
