#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${SMOKE_BASE_URL:-${1:-http://localhost:8000}}
TIMEOUT=${SMOKE_TIMEOUT:-10}

echo "[smoke] Base URL: $BASE_URL"

function check() {
  local path="$1"
  echo -n "[smoke] GET $path ... "
  http_code=$(curl -sS -m "$TIMEOUT" -o /dev/null -w "%{http_code}" "$BASE_URL$path")
  if [[ "$http_code" == "200" ]]; then
    echo "OK"
  else
    echo "FAIL ($http_code)" && exit 1
  fi
}

check "/health/"
check "/metrics"
check "/brief/text"
check "/tasks"

echo "[smoke] done."

