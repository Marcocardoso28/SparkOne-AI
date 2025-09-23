#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=${1:-"backups"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="sparkone_${TIMESTAMP}.sql"

mkdir -p "$TARGET_DIR"
docker compose exec -T db pg_dump -U sparkone sparkone >"${TARGET_DIR}/${FILENAME}"
echo "Backup salvo em ${TARGET_DIR}/${FILENAME}"
