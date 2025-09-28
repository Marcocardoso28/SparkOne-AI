# Guidelines para Agentes / Engenheiros

1. **Planejar antes de executar**: usar `tasks/planner.md` como template.
2. **Evitar mudanças destrutivas**: preferir patches/diffs comentados.
3. **Segurança primeiro**: nunca commitar segredos; use `.env.example` e gitleaks.
4. **Coerência com docs**: toda alteração relevante deve refletir em `context.md`, `decisions.md` ou `STATE_OF_PROJECT.md`.
5. **Observabilidade**: garantir que novas features exponham métricas/logs compatíveis.
6. **Teste sempre**: rodar `make check` ou subset mínimo antes de concluir tarefa.
