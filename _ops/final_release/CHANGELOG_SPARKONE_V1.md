# SparkOne v1.0.0 — Changelog

## Melhorias Principais
- Integração completa com AI Core Foundation (Orchestrator + AgnoBridge)
- Observability consolidada (Prometheus, Grafana, FastAPI /metrics)
- CI/CD workflows revisados (lint, typecheck, tests, deploy, backup)
- Segurança aprimorada: rate limiting, security headers, secret scanning baseline
- RAG/Knowledge Base com ingestão e embeddings OpenAI/local

## Fixes
- Normalização de modelos OpenAI-compat para embeddings (dimensões)
- Padronização de paths e schemas para vetor/knowledge
- Ajustes nos health checks e CORS seguros em produção

## Notas
- Cobertura de testes atual: 7.9% (coverage.xml). Recomendado elevar ≥72%.
- Secrets em `.env` gitignorado; adotar Vault/Secrets Manager conforme `SECURITY.md` e `SPEC.md`.

## Status Final
✅ Projeto concluído com sucesso e integrado à arquitetura de orquestração cognitiva (Mentor/Agno).

