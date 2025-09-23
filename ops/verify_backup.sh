#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Uso: $0 <arquivo.sql>"
  exit 1
fi

BACKUP_FILE=$1
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Arquivo não encontrado: $BACKUP_FILE"
  exit 1
fi

CONTAINER_NAME="sparkone-verify-$(date +%s)"
POSTGRES_IMAGE="postgres:15"

docker run --name "$CONTAINER_NAME" -e POSTGRES_PASSWORD=verify -e POSTGRES_DB=sparkone -d "$POSTGRES_IMAGE" >/dev/null
function cleanup {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# aguarda Postgres subir
for i in {1..10}; do
  if docker exec "$CONTAINER_NAME" pg_isready -U postgres >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U postgres sparkone >/dev/null

docker exec "$CONTAINER_NAME" psql -U postgres -d sparkone -c "SELECT NOW();" >/dev/null

echo "Backup verificado com sucesso contra container temporário ($CONTAINER_NAME)"
