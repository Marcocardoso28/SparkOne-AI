#!/usr/bin/env bash
set -euo pipefail

# Permite sobrescrever caminho dos manifests (-f) e nome do serviço do Postgres.
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
DB_SERVICE=${DB_SERVICE:-db}
DB_USER=${DB_USER:-sparkone}
DB_NAME=${DB_NAME:-sparkone}
TARGET_DIR=${1:-"backups"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${DB_NAME}_${TIMESTAMP}.sql"

mkdir -p "$TARGET_DIR"

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" pg_dump -U "$DB_USER" "$DB_NAME" >"${TARGET_DIR}/${FILENAME}"
echo "Backup salvo em ${TARGET_DIR}/${FILENAME}" >&2
