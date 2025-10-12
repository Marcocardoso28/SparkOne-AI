#!/usr/bin/env sh
set -eu

echo "[entrypoint] Applying database migrations..."
alembic upgrade head || {
  echo "[entrypoint] WARNING: alembic upgrade failed. Continuing startup.";
}

echo "[entrypoint] Starting application: $@"
exec "$@"

