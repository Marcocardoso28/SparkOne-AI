# State of Project — SparkOne (Jan/2025)

## Status Geral
- **Health**: ⚠️ Em atenção — duplicatas leves removidas, ausência de `requirements.txt`, backlog de observabilidade.
- **Cobertura de testes estimada**: ~55% (média pytest + smoke sugerido).
- **Velocidade da equipe**: 1 feature/sprint focando em integrações.

## Principais Direitos & Débitos
- Débito: unificar scripts de provisionamento local.
- Débito: alinhar docs (`docs/contexto.md`, README) para o estado atual dos serviços.
- Débito: instrumentação de segurança sem exporter de traces dedicado.
- Débito: restituir `requirements.txt` ou adotar totalmente `hatch`/`uv` com documentação oficial.

## Backlog Prioritário
1. Normalizar estrutura de diretórios (`api`, `domain`, `infra`) e separar testes unitários/integrados.
2. Concluir suíte de observabilidade (dashboards + alertas) alinhada ao Prometheus atual.
3. Implementar CI com cobertura e scan SCA (grype/trivy) integrado ao workflow principal.
4. Revisar segurança de webhook Evolution (assinaturas + rate limiting dedicado).

## Auto-verificação do plano
1. **Risco**: remoção do script errado — *Mitigado* com `cleanup.list` e revisão em PR.
2. **Risco**: perda de contexto histórico — *Mitigado* consolidando docs em `context.md` + `decisions.md`.
3. **Risco**: ajustes de CI quebrarem build — *Mitigado* fornecendo diffs incrementais e passo a passo.
4. **Risco**: testes amostrais desatualizados — *Mitigado* com arquivo `tests/smoke/test_health.py` e revisão periódica.
5. **Risco**: agentes IA sem guia claro — *Mitigado* com pasta `ai_context/` e guidelines específicas.

## Perguntas ao time
1. Qual ambiente será priorizado (local Docker vs. cloud) para definir defaults em `.env`?
2. Há dependência forte em `setup_local_db_fixed.ps1` em pipelines legados que não estão no repo?
3. Qual é a meta realista de cobertura (80% proposta) considerando escopo atual dos serviços?

## Checklist pós-auditoria
- Duplicatas resolvidas? ✅ — `setup_local_db_fixed.ps1` eliminado.
- Estrutura normalizada? ⚠️ — refatoração de pacotes pendente.
- Linting/Typing atualizados? ⚠️ — configs propostos precisam ser adotados e validados.
- Testes? ⚠️ — suite smoke adicionada, expandir cobertura.
- Observabilidade? ❌ — novos dashboards/alertas ainda a executar.
- Segurança? ⚠️ — baseline atualizado em `SECURITY.md`, aplicar roadmap.
- CI/CD? ⚠️ — workflow reforçado precisa ser ativado.
- Docs/AI context? ✅ — artefatos entregues com visão consolidada.
