# SparkOne Cleanup Plan

| Grupo | Tipo | Principal (manter) | Candidatos (remover/ajustar) | Métricas | Decisão | Comandos sugeridos |
| --- | --- | --- | --- | --- | --- | --- |
| DUP-001 | Script PowerShell | `setup_local_db.ps1` | `setup_local_db_fixed.ps1` | sha256=09804c…, bytes=2074, similaridade=1.0 | Remover cópia redundante | `# git rm setup_local_db_fixed.ps1` |
| DUP-002 | Pacotes Python | `src/app/__init__.py` | outros 8 `__init__.py` vazios | sha256=e3b0c4…, bytes=0, similaridade=1.0 | Manter todos como marcadores | — |

## Notas rápidas
- Validar se algum script externo referencia `setup_local_db_fixed.ps1`; caso positivo, ajustar para o nome canônico antes da remoção.
- Após a limpeza, atualizar runbooks e scripts (`TESTE_LOCAL.md`, `docs/OPERATIONS.md`) para remover menções ao arquivo eliminado.
- Reexecutar `git status` para confirmar que apenas arquivos planejados foram afetados.

## Riscos e mitigação
1. **Automação quebrada em pipelines locais** — Mitigar revisando documentação e comunicando alteração no Slack interno.
2. **Arquivo reaparecer por cache** — Garantir que `cleanup.list` seja usada em hooks ou tarefas de build.
3. **Ação parcial** — Utilizar checklist ao final da sprint para assegurar aplicação completa do plano.

## Comandos comentados
```bash
# git rm setup_local_db_fixed.ps1
# git add CLEANUP_PLAN.md cleanup.list .gitignore
# git commit -m "chore: remove script duplicado e padroniza limpeza"
```
