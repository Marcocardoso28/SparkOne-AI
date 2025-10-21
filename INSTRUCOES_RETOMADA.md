# 🔄 INSTRUÇÕES PARA RETOMADA DE SESSÃO

## 📋 COMO RETOMAR O TRABALHO

### Se você está usando **Claude Code** (terminal):
```
1. Abra nova sessão
2. Digite: "Continue o MASTER PLAN do arquivo MASTER_PLAN_EXECUTION.md"
3. Cole ou aponte para o arquivo
4. Claude continua automaticamente
```

### Se você está usando **GitHub Copilot / Codex**:
```
1. Abra o arquivo MASTER_PLAN_EXECUTION.md
2. Digite: "@workspace Continue executando as tarefas do MASTER PLAN"
3. Copilot continua de onde parou
```

### Se você está usando **outro assistente**:
```
1. Compartilhe o arquivo MASTER_PLAN_EXECUTION.md
2. Peça: "Execute as próximas tarefas deste plano"
3. O assistente identificará a próxima tarefa pendente
```

---

## 🤖 FERRAMENTAS DISPONÍVEIS

### MCP Gemini CLI (SEMPRE USE QUANDO POSSÍVEL)
```bash
# Para análises complexas de código
# Para buscar padrões em múltiplos arquivos
# Para refatorações grandes
# Para análise de documentação extensa

Comando: mcp__gemini-cli__ask-gemini
```

**Quando usar Gemini:**
- ✅ Análise de código complexo
- ✅ Refatoração em múltiplos arquivos
- ✅ Busca de padrões arquiteturais
- ✅ Análise de documentação
- ✅ Geração de código boilerplate
- ✅ Validação de implementações

**Exemplo de uso:**
```
"Use o Gemini para analisar todos os arquivos de storage adapters e verificar se seguem o mesmo padrão"
```

---

## ✅ PRÓXIMA TAREFA A EXECUTAR

**CHECKPOINT ATUAL:** FASE 1 - TAREFA 1.1
**TAREFA:** Criar ADR-014: Storage Adapter Pattern
**ARQUIVO:** docs/prd/sparkone/decisions.md
**STATUS:** ⬜ Não iniciado

---

## 📝 PROTOCOLO DE EXECUÇÃO

Para CADA tarefa:
1. ✅ Marcar como "em andamento" (🔄)
2. ✅ Executar a tarefa completamente
3. ✅ Rodar testes (se aplicável)
4. ✅ Fazer commit com mensagem descritiva
5. ✅ Marcar como completa (✅) no MASTER_PLAN_EXECUTION.md
6. ✅ Atualizar progresso da FASE
7. ✅ Ir para próxima tarefa

---

## 🎯 META FINAL

**OBJETIVO:** Completar 36 tarefas em 6 fases
**PROGRESSO ATUAL:** 0/36 (0%)
**TEMPO ESTIMADO:** 7-10 dias de trabalho

**Quando estiver 100% completo:**
- ✅ Storage Adapter Pattern funcionando
- ✅ ProactivityEngine enviando lembretes
- ✅ Documentação completa e sem duplicidades
- ✅ Todos testes passando (>85% cobertura)
- ✅ Interface web /settings funcional

---

## ⚠️ IMPORTANTE

### SEMPRE:
- ✅ Use Gemini para tarefas complexas
- ✅ Faça commits descritivos
- ✅ Atualize o MASTER_PLAN após cada tarefa
- ✅ Rode testes antes de marcar como completo
- ✅ Documente problemas na seção ISSUES

### NUNCA:
- ❌ Pule tarefas sem completar
- ❌ Faça commits sem testar
- ❌ Deixe documentação desatualizada
- ❌ Ignore warnings críticos

---

**PRONTO PARA COMEÇAR!** 🚀
**Próxima ação:** Executar TAREFA 1.1
