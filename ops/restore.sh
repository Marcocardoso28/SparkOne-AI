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

docker compose exec -T db psql -U sparkone sparkone <"$BACKUP_FILE"
echo "Restore concluído a partir de $BACKUP_FILE"
