#!/usr/bin/env bash
set -euo pipefail

# ==== CONFIGURAÇÕES (ajuste se necessário) ====
export SPARKONE_HOST="sparkone-ai.macspark.dev"
export TRAEFIK_NETWORK="reverse-proxy"        # nome da rede do Traefik
export COMPOSE_FILE="docker-compose.prod.yml"  # ou docker-compose.yml
export GH_REPO=""                              # opcional: <owner>/<repo>
export RELEASE_TAG="v1.0.0"

# ==== 1. VALIDAR ARTEFATOS DE RELEASE ====
echo "🔍 Validando artefatos de release..."
test -f "_ops/final_release/FINAL_RELEASE_REPORT_SPARKONE.md"
test -f "_ops/final_release/FINAL_ACCEPTANCE_SPARKONE_V1.json"
test -f "_ops/final_release/CHANGELOG_SPARKONE_V1.md"
echo "✅ Artefatos OK"

# ==== 2. GARANTIR REDE DO TRAEFIK ====
docker network create "${TRAEFIK_NETWORK}" >/dev/null 2>&1 || true

# ==== 3. AJUSTAR SERVIÇO API PARA TER LABELS DO TRAEFIK ====
python3 - <<'PY'
import os, sys, yaml
f = os.environ.get("COMPOSE_FILE", "docker-compose.prod.yml")
data = yaml.safe_load(open(f))
svc_name = None
for name, svc in data.get("services", {}).items():
    # heurística simples pelo nome e porta
    if name in ("api", "sparkone-api") or "8000" in str(svc):
        svc_name = name; break
if not svc_name:
    print("❌ Não encontrei serviço API, ajuste manualmente.")
    sys.exit(1)
svc = data["services"][svc_name]
labels = svc.get("labels", [])
if not any("traefik.http.routers.sparkone-api" in str(l) for l in labels):
    labels += [
        "traefik.enable=true",
        "traefik.docker.network=reverse-proxy",
        "traefik.http.routers.sparkone-api.rule=Host(`sparkone-ai.macspark.dev`)",
        "traefik.http.routers.sparkone-api.entrypoints=websecure",
        "traefik.http.routers.sparkone-api.tls=true",
        "traefik.http.services.sparkone-api.loadbalancer.server.port=8000",
    ]
svc["labels"] = labels
nets = svc.get("networks", [])
if isinstance(nets, dict):
    nets = list(nets.keys())
if "reverse-proxy" not in nets:
    nets.append("reverse-proxy")
svc["networks"] = nets
data.setdefault("networks", {}).setdefault("reverse-proxy", {"external": True})
yaml.safe_dump(data, open(f, "w"), sort_keys=False)
print(f"✅ Labels e rede aplicadas no serviço {svc_name}")
PY

# ==== 4. SUBIR SERVIÇOS ====
echo "🚀 Subindo containers..."
docker compose -f "${COMPOSE_FILE}" up -d traefik || true
docker compose -f "${COMPOSE_FILE}" up -d api

# ==== 5. VALIDAR ROTAS ====
echo "⏳ Aguardando API responder..."
sleep 8

echo "→ Validando /health..."
curl -fsS "https://${SPARKONE_HOST}/health" && echo "✅ /health OK" || { echo "❌ /health falhou"; exit 1; }

echo "→ Validando /metrics..."
curl -fsS "https://${SPARKONE_HOST}/metrics" | head -n 20 | tee /tmp/metrics.head || true
grep -E "process_cpu_seconds_total|http_requests_total|sparkone_" /tmp/metrics.head >/dev/null && echo "✅ /metrics OK" || echo "⚠️ Métricas não apareceram nas primeiras linhas (verifique manualmente)."

# ==== 6. PUBLICAR RELEASE NO GITHUB (OPCIONAL) ====
if command -v gh >/dev/null 2>&1 && [ -n "${GH_REPO}" ]; then
  echo "📦 Publicando release ${RELEASE_TAG} em ${GH_REPO}..."
  gh release view "${RELEASE_TAG}" --repo "${GH_REPO}" >/dev/null 2>&1 || \
  gh release create "${RELEASE_TAG}" \
    _ops/final_release/FINAL_RELEASE_REPORT_SPARKONE.md \
    _ops/final_release/FINAL_ACCEPTANCE_SPARKONE_V1.json \
    _ops/final_release/CHANGELOG_SPARKONE_V1.md \
    --repo "${GH_REPO}" \
    --title "SparkOne ${RELEASE_TAG}" \
    --notes-file _ops/final_release/FINAL_RELEASE_REPORT_SPARKONE.md
  echo "✅ Release publicado!"
else
  echo "ℹ️ gh não configurado — publique manualmente no GitHub se desejar."
fi

# ==== 7. RESUMO FINAL ====
echo
echo "🎯 SparkOne-AI validado e finalizado!"
echo "• Host: https://${SPARKONE_HOST}"
echo "• Compose: ${COMPOSE_FILE}"
echo "• Rede Traefik: ${TRAEFIK_NETWORK}"
echo "• Release: ${RELEASE_TAG} (artefatos em _ops/final_release/)"
echo "✅ Projeto encerrado com sucesso!"

