#!/usr/bin/env bash
set -euo pipefail

BASE="docs/prd/sparkone"
TS="$(date +%F_%H%M%S)"
ARCH="$BASE/_archive/$TS"
mkdir -p "$ARCH"

echo "==> Backup dos arquivos atuais em $ARCH"
cp -a "$BASE/decisions.md" "$ARCH/" 2>/dev/null || true
cp -a "$BASE/backlog.csv" "$ARCH/" 2>/dev/null || true
cp -a "$BASE/traceability.md" "$ARCH/" 2>/dev/null || true
cp -a "$BASE/PRD.en-US.md" "$ARCH/" 2>/dev/null || true
cp -a "$BASE/PRD.pt-BR.md" "$ARCH/" 2>/dev/null || true
cp -a "$BASE/prd_freeze_report.md" "$ARCH/" 2>/dev/null || true

echo "==> 1) Acrescentando ADR-012 e ADR-013 ao decisions.md (no final do arquivo)"
cat >>"$BASE/decisions.md" <<'EOF'

---

## ADR-012: ProactivityEngine Architecture (P0)

Date: 2025
Status: ✅ Accepted (Planned execution as P0)
Deciders: Marco Cardoso, Development Team

### Context
SparkOne precisa de comportamentos proativos além do fluxo reativo request/response. O ProactivityEngine irá agendar e disparar ações automáticas como brief diário, lembretes e notificações contextuais.

### Decision
Adotar um ProactivityEngine baseado em um processo/contêiner de worker dedicado (APScheduler). Execução fora do processo web para isolar falhas e aumentar confiabilidade.

Related Requirements: RF-015 (ProactivityEngine)  
Related Backlog: RF-001 (Implementar ProactivityEngine), RF-003 (Worker Container)  
Dependencies: APScheduler, serviço worker no Compose, Redis (opcional)

### Consequences
- ✅ Proatividade (brief/lembretes) sem ação do usuário  
- ✅ Separação API vs scheduler/worker  
- ⚠️ Overhead operacional (novo contêiner), timezone/DST/retries exigem cuidado

### Implementation Notes
- Serviço worker no Compose compartilhando código
- Schedules centralizados em `src/app/services/proactivity.py`
- Logs estruturados e métricas por job; idempotência e retry/backoff

---

## ADR-013: Vector Search Rollout (P1)

Date: 2025
Status: ✅ Accepted (Planned execution as P1)
Deciders: Marco Cardoso, Development Team

### Context
Infra para busca vetorial (PostgreSQL + pgvector) pronta, mas funcionalidade ainda não exposta.

### Decision
Implementar serviço de Vector Search com pgvector. Indexar entidades (tarefas, eventos) e expor `/search` para similaridade.

Related Requirements: RF-018 (Vector Search)  
Related Backlog: RF-006 (Vector Search Implementation)  
Dependencies: ADR-003 (pgvector), provedor de embeddings (agnóstico)

### Consequences
- ✅ Recuperação semântica sobre entidades  
- ✅ Reaproveita infra existente  
- ⚠️ Custo de geração/atualização de embeddings; ajuste fino de latência

### Implementation Notes
- `src/app/services/vector_search.py` + migração p/ colunas de embeddings
- Atualizar embeddings em updates de entidades
- Consultas `top_k`, meta p95 < 500ms; observabilidade de latência
EOF

echo "==> 2) Ajustando backlog.csv (ligar RF-001→ADR-012 e RF-006→ADR-013)"
# adiciona ADR-012 na linha RF-001 (sem duplicar se já existir)
sed -i -E '/^RF-001,/ {
  s/(ADR-002)([^0-9A-Z]|$)/\1;ADR-012\2/;
  s/;ADR-012;ADR-012/;ADR-012/g
}' "$BASE/backlog.csv"

# adiciona ADR-013 na linha RF-006
sed -i -E '/^RF-006,/ {
  s/(ADR-003)([^0-9A-Z]|$)/\1;ADR-013\2/;
  s/;ADR-013;ADR-013/;ADR-013/g
}' "$BASE/backlog.csv"

echo "==> 3) traceability.md: mapear RF-015→ADR-012 e RF-018→ADR-013"
sed -i -E 's#(\|[[:space:]]*RF-015[^|]*\|[^|]*\|)[[:space:]]*ADR-002[[:space:]]*\|#\1 ADR-002; ADR-012 |#' "$BASE/traceability.md" || true
sed -i -E 's#(\|[[:space:]]*RF-018[^|]*\|[^|]*\|)[[:space:]]*ADR-003[[:space:]]*\|#\1 ADR-003; ADR-013 |#' "$BASE/traceability.md" || true

echo "==> 4) PRD.en-US.md: referenciar ADR-013 em Vector Search e ADR-012 no Proactivity Engine"
# Tenta acrescentar ADR-013 na linha que cita ADR-003
sed -i -E 's#(see[[:space:]]+ADR-003)([,)])#\1, ADR-013\2#' "$BASE/PRD.en-US.md" || true
# Insere "References: ADR-012" logo após a linha "Context-aware suggestion engine"
awk '
/Context-aware suggestion engine/ && !p {print; print "    References: ADR-012"; p=1; next} {print}
' "$BASE/PRD.en-US.md" > "$BASE/PRD.en-US.md.tmp" && mv "$BASE/PRD.en-US.md.tmp" "$BASE/PRD.en-US.md"

echo "==> 5) PRD.pt-BR.md: Referências ADR-012 (RF-015) e ADR-013 (RF-018)"
# Adiciona linha de referências para RF-015 caso ainda não exista
awk '
/RF-015: ProactivityEngine/ {inrf=1}
inrf && /Critérios de Aceitação/ && !added15 {print; print ""; print "      - Referências: ADR-012"; added15=1; next}
{print}
' "$BASE/PRD.pt-BR.md" > "$BASE/PRD.pt-BR.md.tmp" && mv "$BASE/PRD.pt-BR.md.tmp" "$BASE/PRD.pt-BR.md"

# Garante ADR-013 em RF-018
grep -q 'RF-018' "$BASE/PRD.pt-BR.md" && sed -i -E '/RF-018:/{:a; n; /Referências:/ { s/$/ ADR-003; ADR-013/; b }; /RF-[0-9]+:|RNF-|^$/ q; ba }' "$BASE/PRD.pt-BR.md" || true

echo "==> 6) prd_freeze_report.md: refletir ADR-012/013"
sed -i -E 's/(11 complete ADRs.*ADR-011)/13 complete ADRs (ADR-001 through ADR-013)/' "$BASE/prd_freeze_report.md" || true
sed -i -E 's/(ProactivityEngine:.*ADR-002)([^0-9A-Z]|$)/\1, ADR-012\2/' "$BASE/prd_freeze_report.md" || true
sed -i -E 's/(Vector Search:.*ADR-003)([^0-9A-Z]|$)/\1, ADR-013\2/' "$BASE/prd_freeze_report.md" || true

echo "==> OK. Alterações aplicadas."
echo "Arquivos backup em: $ARCH"
